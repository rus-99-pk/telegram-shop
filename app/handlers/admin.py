import asyncio
import logging
from datetime import datetime
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.exceptions import TelegramBadRequest

from app.config import config
from app.lexicon.lexicon_ru import LEXICON, ORDER_STATUSES
from app.keyboards import builders as kb
from app.keyboards.builders import (
    ViewOrder, ChangeStatus, ManageProduct, EditProduct,
    DeleteProduct, CancelFSM, ViewReceipt, PromptStatus  # <-- ДОБАВЛЕН ИМПОРТ
)
from app.database import requests as rq
from app.services.report_generator import create_orders_excel_report

router = Router()
router.message.filter(F.from_user.id.in_(config.admin_ids))
router.callback_query.filter(F.from_user.id.in_(config.admin_ids))


class AddProduct(StatesGroup):
    name = State()
    price = State()
    photo = State()
    description = State()

class CancelOrder(StatesGroup):
    waiting_for_reason = State()
    order_id = State()

class ShipOrder(StatesGroup):
    waiting_for_track_number = State()
    order_id = State()

class EditProductState(StatesGroup):
    waiting_for_new_price = State()
    waiting_for_new_name = State()
    waiting_for_new_description = State()
    product_id = State()

class Mailing(StatesGroup):
    waiting_for_text = State()


# <--- СЕРВИСНАЯ ФУНКЦИЯ ДЛЯ ОТПРАВКИ ДЕТАЛЕЙ ЗАКАЗА --->
async def send_order_details(message: Message, bot: Bot, session: AsyncSession, order_id: int):
    """
    Получает детали заказа и отправляет их в виде нового сообщения.
    УДАЛЯЕТ предыдущее сообщение, чтобы избежать дублирования.
    """
    try:
        await message.delete()
    except TelegramBadRequest:
        pass  # Не страшно, если не удалось удалить

    order_info, order_items = await rq.get_order_details(session, order_id)

    if not order_info:
        await message.answer("Заказ не найден!")
        return

    products_text = "\n".join([f"  - {item.product_name} ({int(item.product_price)} руб.)" for item in order_items])
    total_price = sum(item.product_price for item in order_items)
    products_text += f"\n\n<b>Итого: {int(total_price)} руб.</b>"

    text = LEXICON['admin_order_details'].format(
        order_id=order_id,
        username=order_info.username or "N/A",
        user_id=order_info.tg_id,
        status=ORDER_STATUSES.get(order_info.status, order_info.status),
        pickup_point=order_info.delivery_pickup_point,
        full_name=order_info.recipient_full_name,
        phone=order_info.recipient_phone_number,
        products=products_text
    )

    reply_markup = kb.manage_order_keyboard(
        order_id=order_id,
        has_receipt=(order_info.receipt_file_id is not None),
        status=order_info.status,
        track_number=order_info.cdek_track_number
    )
    
    await bot.send_message(message.chat.id, text, reply_markup=reply_markup)


@router.callback_query(F.data == 'admin_panel')
async def admin_panel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    try:
        await callback.message.edit_text(
            LEXICON['admin_start_message'],
            reply_markup=kb.admin_panel_keyboard()
        )
    except TelegramBadRequest:
        await callback.answer()


@router.callback_query(CancelFSM.filter())
async def cancel_fsm_action(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    try:
        await callback.message.edit_text(
            LEXICON['action_canceled'],
            reply_markup=kb.admin_panel_keyboard()
        )
    except TelegramBadRequest:
        try:
            await callback.message.delete()
        except TelegramBadRequest:
            pass
        await callback.message.answer(
            LEXICON['action_canceled'],
            reply_markup=kb.admin_panel_keyboard()
        )
    await callback.answer()


@router.callback_query(F.data == 'admin_add_product')
async def add_product_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AddProduct.name)
    try:
        await callback.message.edit_text(
            LEXICON['admin_add_product_name'],
            reply_markup=kb.cancel_fsm_keyboard()
        )
    except TelegramBadRequest:
        await callback.answer()


@router.message(AddProduct.name)
async def add_product_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(AddProduct.price)
    await message.answer(
        LEXICON['admin_add_product_price'],
        reply_markup=kb.cancel_fsm_keyboard()
    )


@router.message(AddProduct.price)
async def add_product_price(message: Message, state: FSMContext):
    try:
        price = float(message.text)
        await state.update_data(price=price)
        await state.set_state(AddProduct.photo)
        await message.answer(
            LEXICON['admin_add_product_photo'],
            reply_markup=kb.cancel_fsm_keyboard()
        )
    except ValueError:
        await message.answer(
            "Пожалуйста, введите корректную цену (число).",
            reply_markup=kb.cancel_fsm_keyboard()
        )


@router.message(AddProduct.photo, F.photo)
async def add_product_photo(message: Message, state: FSMContext, session: AsyncSession):
    photo_id = message.photo[-1].file_id
    await state.update_data(photo_id=photo_id)
    await state.set_state(AddProduct.description)
    await message.answer(
        LEXICON['admin_add_product_description'],
        reply_markup=kb.cancel_fsm_keyboard()
    )


@router.message(AddProduct.description)
async def add_product_description(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    description = None if message.text == '-' else message.text

    await rq.add_product(session, data['name'], data['price'], data['photo_id'], description)
    await state.clear()

    await message.answer(
        LEXICON['admin_product_added'].format(name=data['name']),
        reply_markup=kb.admin_panel_keyboard()
    )


@router.callback_query(F.data == 'admin_list_orders')
async def list_orders(callback: CallbackQuery | Message, session: AsyncSession):
    orders = await rq.get_all_orders(session)
    orders_list = orders.all()

    sender = callback.message if isinstance(callback, CallbackQuery) else callback

    try:
        if not orders_list:
            text = LEXICON['admin_no_orders']
            markup = kb.admin_panel_keyboard()
        else:
            text = LEXICON['admin_list_orders_title']
            markup = kb.admin_list_orders_keyboard(orders_list)

        if isinstance(callback, CallbackQuery):
            await sender.edit_text(text, reply_markup=markup)
        else:
            await sender.answer(text, reply_markup=markup)
            
    except TelegramBadRequest:
        if isinstance(callback, CallbackQuery):
            await callback.answer()


@router.callback_query(ViewOrder.filter())
async def view_order_detail(callback: CallbackQuery, callback_data: ViewOrder, session: AsyncSession, bot: Bot):
    """
    Обрабатывает нажатие на кнопку заказа из списка ИЛИ кнопку "назад к деталям".
    Удаляет текущее сообщение и отправляет детали заново.
    """
    await send_order_details(callback.message, bot, session, callback_data.order_id)
    await callback.answer()


@router.callback_query(ViewReceipt.filter())
async def view_receipt_handler(callback: CallbackQuery, callback_data: ViewReceipt, session: AsyncSession, bot: Bot):
    order_info, _ = await rq.get_order_details(session, callback_data.order_id)
    if order_info and order_info.receipt_file_id:
        try:
            await bot.send_document(
                chat_id=callback.from_user.id,
                document=order_info.receipt_file_id,
                caption=f"Чек к заказу #{callback_data.order_id}"
            )
        except TelegramBadRequest:
            await callback.answer("Не удалось отправить файл. Возможно, он был удален.", show_alert=True)
    else:
        await callback.answer("Чек для этого заказа не найден.", show_alert=True)
    await callback.answer()


# <-- НОВЫЙ ХЭНДЛЕР ДЛЯ ОТОБРАЖЕНИЯ КНОПОК СТАТУСОВ -->
@router.callback_query(PromptStatus.filter())
async def prompt_change_status(callback: CallbackQuery, callback_data: PromptStatus):
    """
    Обрабатывает нажатие кнопки 'Изменить статус' и показывает клавиатуру со статусами.
    """
    order_id = callback_data.order_id
    try:
        await callback.message.edit_text(
            text=LEXICON['admin_choose_new_status'].format(order_id=order_id),
            reply_markup=kb.change_status_keyboard(order_id)
        )
    except TelegramBadRequest:
        pass
    await callback.answer()
# ----------------------------------------------------

@router.callback_query(ChangeStatus.filter(F.action == 'prompt_reason'))
async def prompt_cancellation_reason(callback: CallbackQuery, callback_data: ChangeStatus, state: FSMContext):
    order_id = callback_data.order_id
    await state.set_state(CancelOrder.waiting_for_reason)
    await state.update_data(order_id=order_id)

    try:
        await callback.message.edit_text(
            text=LEXICON['admin_enter_cancellation_reason'].format(order_id=order_id),
            reply_markup=kb.cancel_fsm_keyboard()
        )
    except TelegramBadRequest:
        await callback.answer()


@router.callback_query(ChangeStatus.filter(F.action == 'prompt_track_number'))
async def prompt_cdek_track_number(callback: CallbackQuery, callback_data: ChangeStatus, state: FSMContext):
    order_id = callback_data.order_id
    await state.set_state(ShipOrder.waiting_for_track_number)
    await state.update_data(order_id=order_id)
    try:
        await callback.message.edit_text(
            text=LEXICON['admin_enter_cdek_track_number'].format(order_id=order_id),
            reply_markup=kb.cancel_fsm_keyboard()
        )
    except TelegramBadRequest:
        await callback.answer()


@router.callback_query(ChangeStatus.filter(F.action.is_(None)))
async def change_order_status(callback: CallbackQuery, callback_data: ChangeStatus, session: AsyncSession, bot: Bot):
    order_id = callback_data.order_id
    new_status = callback_data.new_status

    await rq.update_order_status(session, order_id, new_status)

    order_info, _ = await rq.get_order_details(session, order_id)

    notification_text = ""
    if new_status == 'processing':
        notification_text = LEXICON['user_order_processing_notification']
    else:
        notification_text = LEXICON['user_order_status_changed'].format(
            order_id=order_id,
            status=ORDER_STATUSES.get(new_status, new_status)
        )
    
    try:
        await bot.send_message(chat_id=order_info.tg_id, text=notification_text)
    except Exception as e:
        logging.error(f"Не удалось отправить уведомление пользователю {order_info.tg_id}: {e}")

    await callback.answer(LEXICON['admin_status_updated'])
    
    # Возвращаемся к деталям заказа
    await send_order_details(callback.message, bot, session, order_id)


@router.message(CancelOrder.waiting_for_reason, F.text)
async def process_cancellation_reason(message: Message, state: FSMContext, session: AsyncSession, bot: Bot):
    reason = message.text
    data = await state.get_data()
    order_id = data.get('order_id')

    await state.clear()

    if order_id:
        await rq.update_order_status(session, order_id, 'canceled')
        order_info, _ = await rq.get_order_details(session, order_id)
        
        try:
            await bot.send_message(
                chat_id=order_info.tg_id,
                text=LEXICON['user_order_canceled_with_reason'].format(
                    order_id=order_id,
                    reason=reason
                )
            )
        except Exception as e:
            logging.error(f"Не удалось отправить уведомление об отмене пользователю {order_info.tg_id}: {e}")
    
    await message.answer(LEXICON['admin_status_updated'])
    await list_orders(message, session)


@router.message(ShipOrder.waiting_for_track_number, F.text)
async def process_cdek_track_number(message: Message, state: FSMContext, session: AsyncSession, bot: Bot):
    track_number = message.text
    data = await state.get_data()
    order_id = data.get('order_id')

    await state.clear()

    if order_id:
        await rq.set_cdek_track_number(session, order_id, track_number)
        await rq.update_order_status(session, order_id, 'shipped')
        
        order_info, _ = await rq.get_order_details(session, order_id)
        
        try:
            await bot.send_message(
                chat_id=order_info.tg_id,
                text=LEXICON['user_order_shipped_notification'].format(
                    order_id=order_id,
                    track_number=track_number
                ),
                reply_markup=kb.shipped_order_notification_keyboard(track_number)
            )
        except Exception as e:
            logging.error(f"Не удалось отправить уведомление об отправке пользователю {order_info.tg_id}: {e}")
            
        await message.answer(LEXICON['admin_status_updated'])
        
        await send_order_details(message, bot, session, order_id)


@router.callback_query(F.data == 'admin_report')
async def download_report(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    try:
        await callback.message.edit_text(LEXICON['generating_report'])
    except TelegramBadRequest:
        await callback.answer(LEXICON['generating_report'])

    orders_with_users = await rq.get_all_orders_with_user_info(session)
    
    if not orders_with_users:
        await callback.message.edit_text(
            LEXICON['report_no_orders'],
            reply_markup=kb.admin_panel_keyboard()
        )
        await callback.answer()
        return

    all_items = await rq.get_all_order_items(session)
    
    report_file_bytes = create_orders_excel_report(orders_with_users, all_items)
    
    filename = f"orders_report_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.xlsx"
    file_to_send = BufferedInputFile(report_file_bytes.getvalue(), filename=filename)

    await bot.send_document(
        chat_id=callback.from_user.id,
        document=file_to_send,
        caption=LEXICON['report_ready']
    )
    
    try:
        await callback.message.edit_text(
            LEXICON['admin_start_message'],
            reply_markup=kb.admin_panel_keyboard()
        )
    except TelegramBadRequest:
        pass
    
    await callback.answer()

@router.callback_query(F.data == 'admin_manage_products')
async def manage_products(callback: CallbackQuery, session: AsyncSession):
    products = await rq.get_all_products(session)
    try:
        await callback.message.delete()
    except TelegramBadRequest:
        pass
    await callback.message.answer(
        LEXICON['admin_manage_products_title'],
        reply_markup=kb.manage_products_keyboard(products.all())
    )
    await callback.answer()


@router.callback_query(ManageProduct.filter())
async def manage_single_product(callback: CallbackQuery, callback_data: ManageProduct, session: AsyncSession):
    product = await session.get(rq.Product, callback_data.product_id)
    if not product:
        await callback.answer("Товар не найден!", show_alert=True)
        return

    caption = f"Товар: <b>{product.name}</b>\n"
    if product.description:
        caption += f"Описание: {product.description}\n"
    caption += f"\nЦена: {int(product.price)} руб."

    try:
        await callback.message.delete()
    except TelegramBadRequest:
        pass
        
    await callback.message.answer_photo(
        photo=product.photo_id,
        caption=caption,
        reply_markup=kb.product_management_keyboard(product.id)
    )
    await callback.answer()


@router.callback_query(EditProduct.filter(F.action == 'choose'))
async def choose_edit_action(callback: CallbackQuery, callback_data: EditProduct):
    try:
        await callback.message.edit_caption(
            caption=LEXICON['choose_edit_action'],
            reply_markup=kb.product_edit_actions_keyboard(callback_data.product_id)
        )
    except TelegramBadRequest:
        pass


@router.callback_query(EditProduct.filter(F.action == 'price'))
async def edit_product_price_start(callback: CallbackQuery, callback_data: EditProduct, state: FSMContext, session: AsyncSession):
    product = await session.get(rq.Product, callback_data.product_id)
    await state.set_state(EditProductState.waiting_for_new_price)
    await state.update_data(product_id=callback_data.product_id)
    try:
        await callback.message.edit_caption(
            caption=LEXICON['enter_new_price'].format(name=product.name),
            reply_markup=kb.cancel_fsm_keyboard()
        )
    except TelegramBadRequest:
        pass


@router.message(EditProductState.waiting_for_new_price)
async def process_new_price(message: Message, state: FSMContext, session: AsyncSession):
    try:
        new_price = float(message.text)
        data = await state.get_data()
        await rq.update_product_price(session, data['product_id'], new_price)
        await state.clear()
        await message.answer(LEXICON['price_updated'], reply_markup=kb.admin_panel_keyboard())
    except ValueError:
        await message.answer(
            "Пожалуйста, введите корректную цену (число).",
            reply_markup=kb.cancel_fsm_keyboard()
        )


@router.callback_query(EditProduct.filter(F.action == 'name'))
async def edit_product_name_start(callback: CallbackQuery, callback_data: EditProduct, state: FSMContext, session: AsyncSession):
    product = await session.get(rq.Product, callback_data.product_id)
    await state.set_state(EditProductState.waiting_for_new_name)
    await state.update_data(product_id=callback_data.product_id)
    try:
        await callback.message.edit_caption(
            caption=LEXICON['enter_new_name'].format(name=product.name),
            reply_markup=kb.cancel_fsm_keyboard()
        )
    except TelegramBadRequest:
        pass


@router.message(EditProductState.waiting_for_new_name)
async def process_new_name(message: Message, state: FSMContext, session: AsyncSession):
    new_name = message.text
    data = await state.get_data()
    await rq.update_product_name(session, data['product_id'], new_name)
    await state.clear()
    await message.answer(LEXICON['name_updated'], reply_markup=kb.admin_panel_keyboard())


@router.callback_query(EditProduct.filter(F.action == 'description'))
async def edit_product_description_start(callback: CallbackQuery, callback_data: EditProduct, state: FSMContext, session: AsyncSession):
    product = await session.get(rq.Product, callback_data.product_id)
    await state.set_state(EditProductState.waiting_for_new_description)
    await state.update_data(product_id=callback_data.product_id)
    try:
        await callback.message.edit_caption(
            caption=LEXICON['enter_new_description'].format(name=product.name),
            reply_markup=kb.cancel_fsm_keyboard()
        )
    except TelegramBadRequest:
        pass


@router.message(EditProductState.waiting_for_new_description)
async def process_new_description(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    product_id = data['product_id']
    new_description = None if message.text == '-' else message.text

    await rq.update_product_description(session, product_id, new_description)
    await state.clear()

    await message.answer(LEXICON['description_updated'], reply_markup=kb.admin_panel_keyboard())


@router.callback_query(DeleteProduct.filter(F.confirm == False))
async def confirm_delete(callback: CallbackQuery, callback_data: DeleteProduct, session: AsyncSession):
    product = await session.get(rq.Product, callback_data.product_id)
    try:
        await callback.message.edit_caption(
            caption=LEXICON['confirm_delete_product'].format(name=product.name),
            reply_markup=kb.confirm_delete_keyboard(callback_data.product_id)
        )
    except TelegramBadRequest:
        pass


@router.callback_query(DeleteProduct.filter(F.confirm == True))
async def process_delete(callback: CallbackQuery, callback_data: DeleteProduct, session: AsyncSession):
    await rq.delete_product(session, callback_data.product_id)
    try:
        await callback.message.delete()
    except TelegramBadRequest:
        pass
    await callback.message.answer(LEXICON['product_deleted_message'], reply_markup=kb.admin_panel_keyboard())


@router.callback_query(F.data == 'admin_stats')
async def get_statistics(callback: CallbackQuery, session: AsyncSession):
    stats = await rq.get_stats(session)
    try:
        await callback.message.edit_text(
            text=LEXICON['stats_message'].format(**stats),
            reply_markup=kb.admin_panel_keyboard()
        )
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            await callback.answer() # Просто закрываем "часики"
        else:
            logging.error(f"Ошибка при обновлении статистики: {e}")
            await callback.answer("Произошла ошибка при обновлении статистики.")


@router.callback_query(F.data == 'admin_mailing')
async def start_mailing(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Mailing.waiting_for_text)
    try:
        await callback.message.edit_text(
            text=LEXICON['enter_mailing_text'],
            reply_markup=kb.cancel_keyboard('admin_panel')
        )
    except TelegramBadRequest:
        pass


@router.message(Mailing.waiting_for_text, F.text)
async def process_mailing_text(message: Message, state: FSMContext, session: AsyncSession, bot: Bot):
    await state.clear()
    await message.answer(LEXICON['mailing_started'])

    user_ids = await rq.get_all_user_ids(session)
    sent_count = 0
    for user_id in user_ids:
        try:
            await bot.send_message(chat_id=user_id, text=message.html_text)
            sent_count += 1
            await asyncio.sleep(0.1) # Защита от rate-limit
        except Exception as e:
            logging.error(f"Не удалось отправить сообщение пользователю {user_id}: {e}")

    await message.answer(LEXICON['mailing_completed'].format(count=sent_count))
    await message.answer(LEXICON['admin_start_message'], reply_markup=kb.admin_panel_keyboard())