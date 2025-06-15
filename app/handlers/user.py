import math
import re
from aiogram import Router, F, Bot
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, Document
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.exceptions import TelegramBadRequest
import logging

from app.lexicon.lexicon_ru import LEXICON, ORDER_STATUSES
from app.keyboards import builders as kb
from app.keyboards.reply import main_menu_reply_keyboard
from app.keyboards.builders import (
    ViewProduct, AddToCart, CatalogPage,
    CancelCheckout, UserViewOrder, ConfirmReceipt
)
from app.database import requests as rq
from app.config import config

# Создаем роутер для пользовательских обработчиков
router = Router()

# Определяем состояния для конечного автомата (FSM) оформления заказа
class Checkout(StatesGroup):
    waiting_for_pickup_point = State()  # Ожидание ввода пункта выдачи
    waiting_for_full_name = State()       # Ожидание ввода ФИО
    waiting_for_phone_number = State()  # Ожидание ввода номера телефона
    waiting_for_receipt = State()       # Ожидание отправки чека


# --- Основное меню и навигация ---

async def show_main_menu(bot: Bot, chat_id: int, user_id: int, username: str | None, session: AsyncSession):
    """
    Универсальная функция для отправки главного меню.
    Создает/обновляет пользователя в БД и отправляет ему сообщение с клавиатурой.
    """
    await rq.get_user(session, user_id, username)  # Убеждаемся, что пользователь есть в БД
    is_admin = user_id in config.admin_ids  # Проверяем, является ли пользователь админом
    await bot.send_message(
        chat_id=chat_id,
        text=LEXICON['start_message'],
        reply_markup=kb.main_menu_keyboard(is_admin) # Отправляем клавиатуру (с админ-кнопкой или без)
    )


@router.message(F.text == LEXICON['main_menu_button'])
async def cmd_menu_button(message: Message, session: AsyncSession, bot: Bot):
    """Обработчик для Reply-кнопки 'Меню'."""
    await show_main_menu(bot, message.chat.id, message.from_user.id, message.from_user.username, session)


@router.message(F.text == '/start')
async def cmd_start(message: Message, session: AsyncSession, bot: Bot):
    """
    Обработчик команды /start. Устанавливает Reply-клавиатуру и отправляет
    приветственное сообщение с инлайн-клавиатурой главного меню.
    """
    # Отправляем приветствие и устанавливаем постоянную клавиатуру с кнопкой "Меню"
    await message.answer(
        "👋 Добро пожаловать в бот-магазин!",
        reply_markup=main_menu_reply_keyboard()
    )
    # Показываем главное меню
    await show_main_menu(bot, message.chat.id, message.from_user.id, message.from_user.username, session)


@router.callback_query(F.data == 'to_main_menu')
async def to_main_menu(callback: CallbackQuery, state: FSMContext, session: AsyncSession, bot: Bot):
    """Обработчик для кнопки 'Назад в главное меню'."""
    await state.clear()  # Сбрасываем FSM-состояние, если оно было
    try:
        await callback.message.delete()  # Удаляем предыдущее сообщение
    except TelegramBadRequest:
        pass  # Ничего страшного, если сообщение уже удалено
    await show_main_menu(bot, callback.message.chat.id, callback.from_user.id, callback.from_user.username, session)
    await callback.answer()


# --- Каталог и товары ---

@router.callback_query(F.data == 'catalog')
@router.callback_query(CatalogPage.filter())
async def catalog(callback: CallbackQuery, session: AsyncSession, callback_data: CatalogPage | None = None):
    """
    Обработчик для отображения каталога товаров.
    Реагирует на нажатие кнопки 'Каталог' и на кнопки пагинации.
    """
    page = callback_data.page if callback_data else 1  # Определяем текущую страницу
    page_size = 5  # Количество товаров на странице

    total_products = await rq.count_products(session)  # Считаем общее количество товаров
    total_pages = math.ceil(total_products / page_size)  # Вычисляем общее количество страниц

    products = await rq.get_products(session, page=page, page_size=page_size)  # Получаем товары для текущей страницы
    products_list = list(products)

    try:
        # Пытаемся отредактировать текущее сообщение, чтобы показать каталог
        await callback.message.edit_text(
            text=LEXICON['catalog_title'],
            reply_markup=kb.catalog_keyboard(products_list, page, total_pages)
        )
    except TelegramBadRequest:
        # Если редактирование не удалось (например, сообщение слишком старое), удаляем старое и отправляем новое
        try:
            await callback.message.delete()
            await callback.message.answer(
                text=LEXICON['catalog_title'],
                reply_markup=kb.catalog_keyboard(products_list, page, total_pages)
            )
        except TelegramBadRequest:
            pass  # Игнорируем ошибки, если и это не удалось

    await callback.answer()


@router.callback_query(ViewProduct.filter())
async def product_detail(callback: CallbackQuery, callback_data: ViewProduct, session: AsyncSession):
    """Обработчик для просмотра детальной информации о товаре."""
    product = await session.get(rq.Product, callback_data.product_id)
    if product:
        # Формируем подпись к фото
        caption_text = f"<b>{product.name}</b>\n"
        if product.description:
            caption_text += f"{product.description}\n\n"
        caption_text += f"Цена: {int(product.price)} руб."

        try:
            await callback.message.delete()
        except TelegramBadRequest:
            pass
        
        # Отправляем фото с подписью и клавиатурой
        await callback.message.answer_photo(
            photo=product.photo_id,
            caption=caption_text,
            reply_markup=kb.product_detail_keyboard(product.id, 'catalog_page_1')
        )
    await callback.answer()


# --- Корзина ---

@router.callback_query(AddToCart.filter())
async def add_to_cart(callback: CallbackQuery, callback_data: AddToCart, session: AsyncSession):
    """Обработчик добавления товара в корзину."""
    user = await rq.get_user(session, callback.from_user.id, callback.from_user.username)
    await rq.add_to_cart(session, user.id, callback_data.product_id)

    await callback.answer(LEXICON['item_added_to_cart'])  # Показываем всплывающее уведомление

    try:
        # Обновляем клавиатуру под фото товара
        await callback.message.edit_reply_markup(
            reply_markup=kb.product_added_to_cart_keyboard(callback_data.product_id, 'catalog_page_1')
        )
    except TelegramBadRequest:
        pass


@router.callback_query(F.data == 'my_cart')
async def my_cart(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Обработчик для просмотра содержимого корзины."""
    await state.clear()
    user = await rq.get_user(session, callback.from_user.id, callback.from_user.username)
    cart_items = await rq.get_cart_items(session, user.id)
    items = cart_items.all()

    try:
        await callback.message.delete()
    except TelegramBadRequest:
        pass

    if not items:
        # Если корзина пуста
        await callback.message.answer(LEXICON['empty_cart'], reply_markup=kb.back_to_main_menu_keyboard())
        await callback.answer()
        return

    # Формируем текст с содержимым корзины
    cart_text = f"{LEXICON['cart_title']}\n\n"
    total_price = 0
    for item in items:
        cart_text += f"▫️ {item.name} x{item.quantity} - {int(item.price * item.quantity)} руб.\n"
        total_price += item.price * item.quantity
    cart_text += f"\nИтого: {int(total_price)} руб."

    await callback.message.answer(cart_text, reply_markup=kb.cart_keyboard(items))
    await callback.answer()


@router.callback_query(F.data == 'clear_cart')
async def clear_cart(callback: CallbackQuery, session: AsyncSession):
    """Обработчик для очистки корзины."""
    user = await rq.get_user(session, callback.from_user.id, callback.from_user.username)
    await rq.clear_cart(session, user.id)
    try:
        await callback.message.edit_text(LEXICON['empty_cart'], reply_markup=kb.back_to_main_menu_keyboard())
    except TelegramBadRequest:
        pass
    await callback.answer()


# --- Оформление заказа (Checkout FSM) ---

@router.callback_query(CancelCheckout.filter())
async def cancel_checkout(callback: CallbackQuery, callback_data: CancelCheckout, state: FSMContext, session: AsyncSession, bot: Bot):
    """Обработчик отмены процесса оформления заказа."""
    order_id = callback_data.order_id
    if order_id:
        # Если заказ уже был создан в БД, меняем его статус на 'canceled'
        await rq.update_order_status(session, order_id, 'canceled')
        # Уведомляем админов об отмене
        for admin_id in config.admin_ids:
            try:
                await bot.send_message(
                    admin_id,
                    LEXICON['admin_order_canceled_notification'].format(
                        order_id=order_id,
                        username=callback.from_user.username or "N/A",
                        user_id=callback.from_user.id
                    )
                )
            except Exception as e:
                logging.error(f"Не удалось отправить уведомление об отмене админу {admin_id}: {e}")

    await state.clear()  # Сбрасываем состояние FSM
    try:
        await callback.message.edit_text(
            LEXICON['checkout_canceled'],
            reply_markup=kb.back_to_main_menu_keyboard()
        )
    except TelegramBadRequest:
        pass


@router.callback_query(F.data == 'checkout')
async def checkout_start(callback: CallbackQuery, state: FSMContext):
    """Начало процесса оформления заказа. Шаг 1: Запрос пункта выдачи."""
    await state.set_state(Checkout.waiting_for_pickup_point)
    try:
        await callback.message.edit_text(
            LEXICON['checkout_enter_pickup_point'],
            reply_markup=kb.pickup_point_keyboard()
        )
    except TelegramBadRequest:
        try:
            await callback.message.delete()
        except TelegramBadRequest:
            pass
        await callback.message.answer(
            LEXICON['checkout_enter_pickup_point'],
            reply_markup=kb.pickup_point_keyboard()
        )
    await callback.answer()


@router.message(Checkout.waiting_for_pickup_point, F.text)
async def process_pickup_point(message: Message, state: FSMContext):
    """Шаг 2: Обработка пункта выдачи и запрос ФИО."""
    await state.update_data(pickup_point=message.text)
    await state.set_state(Checkout.waiting_for_full_name)
    await message.answer(
        LEXICON['checkout_enter_full_name'],
        reply_markup=kb.cancel_checkout_keyboard()
    )


@router.message(Checkout.waiting_for_full_name, F.text)
async def process_full_name(message: Message, state: FSMContext):
    """Шаг 3: Обработка ФИО и запрос номера телефона."""
    await state.update_data(full_name=message.text)
    await state.set_state(Checkout.waiting_for_phone_number)
    await message.answer(
        LEXICON['checkout_enter_phone_number'],
        reply_markup=kb.cancel_checkout_keyboard()
    )


@router.message(Checkout.waiting_for_phone_number, F.text)
async def process_phone_number(message: Message, state: FSMContext, session: AsyncSession):
    """Последний шаг: обработка номера телефона, создание заказа и запрос чека."""
    # Проверка номера телефона с помощью регулярного выражения
    phone_pattern = re.compile(r'^(\+7|8)[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}$')
    if not phone_pattern.match(message.text):
        await message.answer(LEXICON['checkout_invalid_phone'])
        return

    await state.update_data(phone=message.text)

    user = await rq.get_user(session, message.from_user.id, message.from_user.username)
    delivery_details = await state.get_data()

    # Получаем товары из корзины для создания заказа
    cart_items = await rq.get_cart_items_for_order(session, user.id)
    items = cart_items.all()

    if not items: # Проверка на случай, если корзина опустела
        await message.answer(LEXICON['empty_cart'], reply_markup=kb.back_to_main_menu_keyboard())
        await state.clear()
        return

    # Собираем текстовое представление заказа
    products_text = ""
    total_price = 0
    for item in items:
        products_text += f"▫️ {item.name} ({int(item.price)} руб.)\n"
        total_price += item.price

    # Создаем заказ в базе данных
    order_id = await rq.place_order(session, user.id, delivery_details)

    if not order_id: # Если по какой-то причине заказ не создался
        await message.answer(LEXICON['error_message'])
        await state.clear()
        return
        
    await state.update_data(order_id=order_id)
    await state.set_state(Checkout.waiting_for_receipt) # Переходим в состояние ожидания чека
            
    # Отправляем финальное сообщение с инструкциями по оплате
    await message.answer(
        text=LEXICON['checkout_final_prompt'].format(
            card_owner=config.bank_card_owner,
            card_number=config.bank_card_number,
            products=products_text,
            total_price=int(total_price),
            pickup_point=delivery_details.get('pickup_point'),
            full_name=delivery_details.get('full_name'),
            phone=delivery_details.get('phone')
        ),
        reply_markup=kb.cancel_checkout_keyboard(order_id=order_id)
    )
    # Очищаем корзину после успешного оформления
    await rq.clear_cart(session, user.id)


@router.message(Checkout.waiting_for_receipt, F.document)
async def process_receipt(message: Message, state: FSMContext, session: AsyncSession, bot: Bot):
    """Обработка полученного чека."""
    # Проверяем, что присланный документ - это PDF
    if message.document.mime_type != 'application/pdf':
        await message.answer(LEXICON['not_a_pdf'])
        return

    data = await state.get_data()
    order_id = data.get('order_id')

    # Обновляем статус заказа и прикрепляем ID файла с чеком
    await rq.update_order_status(session, order_id, 'paid')
    await rq.attach_receipt_to_order(session, order_id, message.document.file_id)

    await message.answer(LEXICON['receipt_received'])

    # Уведомляем всех администраторов о новом оплаченном заказе
    for admin_id in config.admin_ids:
        try:
            await bot.send_message(
                admin_id,
                LEXICON['admin_receipt_notification'].format(
                    order_id=order_id,
                    username=message.from_user.username or 'N/A',
                    user_id=message.from_user.id
                ),
                reply_markup=kb.admin_receipt_notification_keyboard()
            )
        except Exception as e:
            logging.error(f"Не удалось отправить уведомление админу {admin_id}: {e}")

    # Завершающее сообщение для пользователя
    await message.answer(
        LEXICON['order_finalized'].format(order_id=order_id),
        reply_markup=kb.back_to_main_menu_keyboard()
    )
    await state.clear()


# --- История заказов пользователя ---

@router.callback_query(F.data == 'my_orders')
async def my_orders(callback: CallbackQuery, session: AsyncSession):
    """Обработчик для просмотра истории заказов."""
    user = await rq.get_user(session, callback.from_user.id, callback.from_user.username)
    orders = await rq.get_user_orders(session, user.id)
    orders_list = orders.all()

    try:
        await callback.message.edit_text(
            text=LEXICON['no_orders'] if not orders_list else LEXICON['order_history_title'],
            reply_markup=kb.user_orders_keyboard(orders_list)
        )
    except TelegramBadRequest:
        try:
            await callback.message.delete()
        except TelegramBadRequest:
            pass
        await callback.message.answer(
            text=LEXICON['no_orders'] if not orders_list else LEXICON['order_history_title'],
            reply_markup=kb.user_orders_keyboard(orders_list)
        )
    await callback.answer()


@router.callback_query(UserViewOrder.filter())
async def view_user_order(callback: CallbackQuery, callback_data: UserViewOrder, session: AsyncSession):
    """Обработчик для просмотра деталей конкретного заказа пользователем."""
    user = await rq.get_user(session, callback.from_user.id)
    # Получаем детали заказа, убедившись, что он принадлежит этому пользователю
    order, order_items = await rq.get_user_order_details(session, callback_data.order_id, user.id)

    if not order:
        await callback.answer("Заказ не найден!", show_alert=True)
        return
        
    # Формируем текст с деталями заказа
    products_text = "\n".join([f"  - {item.product_name} ({int(item.product_price)} руб.)" for item in order_items])
    total_price = sum(item.product_price for item in order_items)
    products_text += f"\n\n<b>Итого: {int(total_price)} руб.</b>"

    text = LEXICON['user_order_details'].format(
        order_id=order.id,
        status=ORDER_STATUSES.get(order.status, order.status),
        full_name=order.recipient_full_name,
        phone=order.recipient_phone_number,
        pickup_point=order.delivery_pickup_point,
        products=products_text
    )

    try:
        await callback.message.edit_text(
            text=text,
            reply_markup=kb.user_order_detail_keyboard(
                order_id=order.id, 
                status=order.status,
                track_number=order.cdek_track_number # Передаем трек-номер для создания кнопки
            )
        )
    except TelegramBadRequest:
        pass
    await callback.answer()


@router.callback_query(ConfirmReceipt.filter())
async def confirm_order_receipt(callback: CallbackQuery, callback_data: ConfirmReceipt, session: AsyncSession, bot: Bot):
    """Обработчик подтверждения получения заказа пользователем."""
    await rq.update_order_status(session, callback_data.order_id, 'completed')

    # Уведомляем админов о завершении заказа
    for admin_id in config.admin_ids:
        try:
            await bot.send_message(
                admin_id,
                LEXICON['admin_receipt_confirmed_notification'].format(
                    order_id=callback_data.order_id,
                    username=callback.from_user.username or "N/A"
                )
            )
        except Exception as e:
            logging.error(f"Ошибка отправки уведомления админу о завершении заказа: {e}")

    try:
        await callback.message.edit_text(text=LEXICON['order_receipt_confirmed_user'])
    except TelegramBadRequest:
        pass

    # Обновляем список заказов
    await my_orders(callback, session)
    await callback.answer()