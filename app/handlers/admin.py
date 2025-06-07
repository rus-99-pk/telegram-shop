from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.exceptions import TelegramBadRequest

from app.config import config
from app.lexicon.lexicon_ru import LEXICON, ORDER_STATUSES
from app.keyboards import builders as kb
from app.keyboards.builders import ViewOrder, ChangeStatus
from app.database import requests as rq

router = Router()
router.message.filter(F.from_user.id.in_(config.admin_ids))
router.callback_query.filter(F.from_user.id.in_(config.admin_ids))


# --- FSM для добавления товара ---
class AddProduct(StatesGroup):
    name = State()
    price = State()
    photo = State()

# --- FSM для отмены заказа ---
class CancelOrder(StatesGroup):
    waiting_for_reason = State()
    order_id = State() # Будем хранить ID заказа в состоянии


@router.callback_query(F.data == 'admin_panel')
async def admin_panel(callback: CallbackQuery):
    try:
        await callback.message.edit_text(
            LEXICON['admin_start_message'],
            reply_markup=kb.admin_panel_keyboard()
        )
    except TelegramBadRequest:
        await callback.answer()


# --- Хэндлеры для добавления товара ---
@router.callback_query(F.data == 'admin_add_product')
async def add_product_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AddProduct.name)
    try:
        await callback.message.edit_text(LEXICON['admin_add_product_name'])
    except TelegramBadRequest:
        await callback.answer()

@router.message(AddProduct.name)
async def add_product_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(AddProduct.price)
    await message.answer(LEXICON['admin_add_product_price'])

@router.message(AddProduct.price)
async def add_product_price(message: Message, state: FSMContext):
    try:
        price = float(message.text)
        await state.update_data(price=price)
        await state.set_state(AddProduct.photo)
        await message.answer(LEXICON['admin_add_product_photo'])
    except ValueError:
        await message.answer("Пожалуйста, введите корректную цену (число).")

@router.message(AddProduct.photo, F.photo)
async def add_product_photo(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    photo_id = message.photo[-1].file_id
    await rq.add_product(session, data['name'], data['price'], photo_id)
    await state.clear()
    await message.answer(LEXICON['admin_product_added'].format(name=data['name']),
                         reply_markup=kb.admin_panel_keyboard())


# --- Хэндлеры для управления заказами ---

@router.callback_query(F.data == 'admin_list_orders')
async def list_orders(callback: CallbackQuery | Message, session: AsyncSession):
    """
    Этот хэндлер может быть вызван как из CallbackQuery (нажатие кнопки),
    так и из Message (после отмены заказа).
    """
    orders = await rq.get_all_orders(session)
    orders_list = orders.all()
    
    # Определяем, как отвечать: редактировать сообщение или отправлять новое
    # Это нужно для случая, когда мы приходим сюда после отправки причины отмены (из Message)
    sender = callback.message if isinstance(callback, CallbackQuery) else callback

    try:
        if not orders_list:
            await sender.edit_text(
                LEXICON['admin_no_orders'],
                reply_markup=kb.admin_panel_keyboard()
            )
            return

        # Если вызывается через CallbackQuery, редактируем, иначе отправляем новое
        if isinstance(callback, CallbackQuery):
            await sender.edit_text(
                LEXICON['admin_list_orders_title'],
                reply_markup=kb.admin_list_orders_keyboard(orders_list)
            )
        else: # isinstance(callback, Message)
            await sender.answer(
                LEXICON['admin_list_orders_title'],
                reply_markup=kb.admin_list_orders_keyboard(orders_list)
            )
            
    except TelegramBadRequest:
        if isinstance(callback, CallbackQuery):
            await callback.answer()


@router.callback_query(ViewOrder.filter())
async def view_order_detail(callback: CallbackQuery, callback_data: ViewOrder, session: AsyncSession):
    order_id = callback_data.order_id
    order_info, order_items = await rq.get_order_details(session, order_id)

    if not order_info:
        await callback.answer("Заказ не найден!", show_alert=True)
        return

    products_text = "\n".join([f"  - {item.product_name} ({int(item.product_price)} руб.)" for item in order_items])
    
    text = LEXICON['admin_order_details'].format(
        order_id=order_info.id,
        username=order_info.username or "N/A",
        user_id=order_info.tg_id,
        status=ORDER_STATUSES.get(order_info.status, order_info.status),
        products=products_text
    )
    
    try:
        await callback.message.edit_text(text, reply_markup=kb.manage_order_keyboard(order_id))
    except TelegramBadRequest:
        await callback.answer()

# Хэндлер для кнопки "Отменить"
@router.callback_query(ChangeStatus.filter(F.action == 'prompt_reason'))
async def prompt_cancellation_reason(callback: CallbackQuery, callback_data: ChangeStatus, state: FSMContext):
    order_id = callback_data.order_id
    await state.set_state(CancelOrder.waiting_for_reason)
    await state.update_data(order_id=order_id)
    
    try:
        await callback.message.edit_text(text=LEXICON['admin_enter_cancellation_reason'].format(order_id=order_id))
    except TelegramBadRequest:
        await callback.answer()

# Хэндлер, который ловит причину отмены
@router.message(CancelOrder.waiting_for_reason, F.text)
async def process_cancellation_reason(message: Message, state: FSMContext, session: AsyncSession, bot: Bot):
    reason = message.text
    data = await state.get_data()
    order_id = data.get('order_id')
    
    await state.clear()
    
    await rq.update_order_status(session, order_id, 'canceled')
    
    order_info, _ = await rq.get_order_details(session, order_id)
    
    # Уведомляем пользователя с причиной
    try:
        await bot.send_message(
            chat_id=order_info.tg_id,
            text=LEXICON['user_order_canceled_with_reason'].format(
                order_id=order_id,
                reason=reason
            )
        )
    except Exception as e:
        print(f"Не удалось отправить уведомление об отмене пользователю {order_info.tg_id}: {e}")
    
    await message.answer(LEXICON['admin_status_updated'])
    
    # Возвращаемся к списку заказов
    await list_orders(message, session)

# Хэндлер для всех остальных статусов (кроме отмены)
@router.callback_query(ChangeStatus.filter(F.action.is_(None)))
async def change_order_status(callback: CallbackQuery, callback_data: ChangeStatus, session: AsyncSession, bot: Bot):
    order_id = callback_data.order_id
    new_status = callback_data.new_status
    
    await rq.update_order_status(session, order_id, new_status)
    
    order_info, _ = await rq.get_order_details(session, order_id)
    
    # Уведомляем пользователя
    try:
        await bot.send_message(
            chat_id=order_info.tg_id,
            text=LEXICON['user_order_status_changed'].format(
                order_id=order_id,
                status=ORDER_STATUSES.get(new_status, new_status)
            )
        )
    except Exception as e:
        print(f"Не удалось отправить уведомление пользователю {order_info.tg_id}: {e}")
    
    await callback.answer(LEXICON['admin_status_updated'])
    
    # Обновляем сообщение у админа
    await view_order_detail(callback, ViewOrder(order_id=order_id), session)