from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.exceptions import TelegramBadRequest

from app.lexicon.lexicon_ru import LEXICON, ORDER_STATUSES
from app.keyboards import builders as kb
from app.keyboards.builders import ViewProduct, AddToCart
from app.database import requests as rq
from app.config import config

router = Router()

@router.message(F.text == '/start')
async def cmd_start(message: Message, session: AsyncSession):
    # --- ПЕРЕДАЕМ username ---
    await rq.get_user(session, message.from_user.id, message.from_user.username)
    is_admin = message.from_user.id in config.admin_ids
    await message.answer(
        LEXICON['start_message'],
        reply_markup=kb.main_menu_keyboard(is_admin)
    )

@router.callback_query(F.data == 'to_main_menu')
async def to_main_menu(callback: CallbackQuery):
    is_admin = callback.from_user.id in config.admin_ids
    await callback.message.delete()
    await callback.message.answer(
        text=LEXICON['start_message'],
        reply_markup=kb.main_menu_keyboard(is_admin)
    )
    await callback.answer()

@router.callback_query(F.data == 'catalog')
async def catalog(callback: CallbackQuery, session: AsyncSession):
    await callback.message.delete()
    products = await rq.get_products(session)
    await callback.message.answer(
        text=LEXICON['catalog_title'],
        reply_markup=kb.catalog_keyboard(products.all())
    )
    await callback.answer()

@router.callback_query(ViewProduct.filter())
async def product_detail(callback: CallbackQuery, callback_data: ViewProduct, session: AsyncSession):
    product_id = callback_data.product_id
    product = await session.get(rq.Product, product_id)
    if product:
        await callback.message.delete()
        await callback.message.answer_photo(
            photo=product.photo_id,
            caption=f"{product.name}\n\nЦена: {int(product.price)} руб.",
            reply_markup=kb.product_detail_keyboard(product.id)
        )

@router.callback_query(AddToCart.filter())
async def add_to_cart(callback: CallbackQuery, callback_data: AddToCart, session: AsyncSession):
    product_id = callback_data.product_id
    # --- ПЕРЕДАЕМ username ---
    user = await rq.get_user(session, callback.from_user.id, callback.from_user.username)
    await rq.add_to_cart(session, user.id, product_id)
    await callback.answer(LEXICON['item_added_to_cart'])

@router.callback_query(F.data == 'my_cart')
async def my_cart(callback: CallbackQuery, session: AsyncSession):
    # --- ПЕРЕДАЕМ username ---
    user = await rq.get_user(session, callback.from_user.id, callback.from_user.username)
    cart_items = await rq.get_cart_items(session, user.id)
    items = cart_items.all()
    try:
        if not items:
            await callback.message.edit_text(LEXICON['empty_cart'], reply_markup=kb.back_to_main_menu_keyboard())
            return
        cart_text = f"{LEXICON['cart_title']}\n\n"
        total_price = 0
        for item in items:
            cart_text += f"▪️ {item.name} x{item.quantity} - {int(item.price * item.quantity)} руб.\n"
            total_price += item.price * item.quantity
        cart_text += f"\nИтого: {int(total_price)} руб."
        await callback.message.edit_text(cart_text, reply_markup=kb.cart_keyboard(items))
    except TelegramBadRequest:
        await callback.answer()

@router.callback_query(F.data == 'clear_cart')
async def clear_cart(callback: CallbackQuery, session: AsyncSession):
    # --- ПЕРЕДАЕМ username ---
    user = await rq.get_user(session, callback.from_user.id, callback.from_user.username)
    await rq.clear_cart(session, user.id)
    try:
        await callback.message.edit_text(LEXICON['empty_cart'], reply_markup=kb.back_to_main_menu_keyboard())
    except TelegramBadRequest:
        await callback.answer()

@router.callback_query(F.data == 'checkout')
async def checkout(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    # --- ПЕРЕДАЕМ username ---
    user = await rq.get_user(session, callback.from_user.id, callback.from_user.username)
    cart_items_for_order = await rq.get_cart_items_for_order(session, user.id)
    products_for_notification = ""
    for item in cart_items_for_order.all():
         products_for_notification += f"- {item.name} ({int(item.price)} руб.)\n"
    order_id = await rq.place_order(session, user.id)
    try:
        if order_id:
            await callback.message.edit_text(LEXICON['order_placed'].format(order_id=order_id))
            for admin_id in config.admin_ids:
                try:
                    await bot.send_message(
                        admin_id,
                        LEXICON['admin_new_order_notification'].format(
                            order_id=order_id,
                            products=products_for_notification,
                            username=callback.from_user.username or 'N/A',
                            user_id=callback.from_user.id
                        )
                    )
                except Exception as e:
                    print(f"Не удалось отправить уведомление админу {admin_id}: {e}")
        else:
            await callback.message.edit_text(LEXICON['empty_cart'])
    except TelegramBadRequest:
        await callback.answer()

@router.callback_query(F.data == 'my_orders')
async def my_orders(callback: CallbackQuery, session: AsyncSession):
    # --- ПЕРЕДАЕМ username ---
    user = await rq.get_user(session, callback.from_user.id, callback.from_user.username)
    orders = await rq.get_user_orders(session, user.id)
    orders_list = orders.all()
    try:
        if not orders_list:
            await callback.message.edit_text(LEXICON['no_orders'], reply_markup=kb.back_to_main_menu_keyboard())
            return
        orders_text = f"{LEXICON['order_history_title']}\n\n"
        for order in orders_list:
            status_text = ORDER_STATUSES.get(order.status, order.status)
            orders_text += f"▪️ Заказ #{order.id} - Статус: {status_text}\n"
        await callback.message.edit_text(orders_text, reply_markup=kb.back_to_main_menu_keyboard())
    except TelegramBadRequest:
        await callback.answer()