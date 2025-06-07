from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData

from app.lexicon.lexicon_ru import LEXICON, ORDER_STATUSES
from app.database.models import Product

# --- CallbackData FACTORIES ---
# Для заказов
class ViewOrder(CallbackData, prefix="view_order"):
    order_id: int

class ChangeStatus(CallbackData, prefix="change_status"):
    order_id: int
    new_status: str
    action: str | None = None

# Для каталога и корзины
class ViewProduct(CallbackData, prefix="view_prod"):
    product_id: int

class AddToCart(CallbackData, prefix="add_cart"):
    product_id: int
# ---


def main_menu_keyboard(is_admin: bool = False):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=LEXICON['catalog_button'], callback_data='catalog'))
    builder.row(InlineKeyboardButton(text=LEXICON['cart_button'], callback_data='my_cart'))
    builder.row(InlineKeyboardButton(text=LEXICON['orders_button'], callback_data='my_orders'))
    builder.row(InlineKeyboardButton(text=LEXICON['feedback_button'], url='t.me/your_support_username'))
    if is_admin:
        builder.row(InlineKeyboardButton(text=LEXICON['admin_panel_button'], callback_data='admin_panel'))
    return builder.as_markup()

def admin_panel_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=LEXICON['add_item_button'], callback_data='admin_add_product'))
    builder.row(InlineKeyboardButton(text=LEXICON['list_orders_button'], callback_data='admin_list_orders'))
    builder.row(InlineKeyboardButton(text=LEXICON['back_to_main_menu'], callback_data='to_main_menu'))
    return builder.as_markup()

def catalog_keyboard(products: list[Product]):
    builder = InlineKeyboardBuilder()
    for product in products:
        builder.row(InlineKeyboardButton(
            text=f'{product.name} - {int(product.price)} руб.',
            callback_data=ViewProduct(product_id=product.id).pack()
        ))
    builder.row(InlineKeyboardButton(text=LEXICON['back_to_main_menu'], callback_data='to_main_menu'))
    return builder.as_markup()

def product_detail_keyboard(product_id: int):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text='➕ Добавить в корзину',
        callback_data=AddToCart(product_id=product_id).pack()
    ))
    builder.row(InlineKeyboardButton(text=LEXICON['back_button'], callback_data='catalog'))
    return builder.as_markup()

def cart_keyboard(items: list):
    builder = InlineKeyboardBuilder()
    if items:
        builder.row(InlineKeyboardButton(text=LEXICON['checkout_button'], callback_data='checkout'))
        builder.row(InlineKeyboardButton(text=LEXICON['clear_cart_button'], callback_data='clear_cart'))
    builder.row(InlineKeyboardButton(text=LEXICON['back_to_main_menu'], callback_data='to_main_menu'))
    return builder.as_markup()

def back_to_main_menu_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=LEXICON['back_to_main_menu'], callback_data='to_main_menu'))
    return builder.as_markup()


def admin_list_orders_keyboard(orders: list):
    builder = InlineKeyboardBuilder()
    for order in orders:
        status_text = ORDER_STATUSES.get(order.status, order.status)
        builder.row(InlineKeyboardButton(
            text=f'Заказ #{order.id} (Статус: {status_text})',
            callback_data=ViewOrder(order_id=order.id).pack()
        ))
    builder.row(InlineKeyboardButton(text=LEXICON['back_button'], callback_data='admin_panel'))
    return builder.as_markup()


def manage_order_keyboard(order_id: int):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=LEXICON['status_processing_button'],
            callback_data=ChangeStatus(order_id=order_id, new_status='processing').pack()
        ),
        InlineKeyboardButton(
            text=LEXICON['status_shipped_button'],
            callback_data=ChangeStatus(order_id=order_id, new_status='shipped').pack()
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=LEXICON['status_completed_button'],
            callback_data=ChangeStatus(order_id=order_id, new_status='completed').pack()
        ),
        InlineKeyboardButton(
            text=LEXICON['status_canceled_button'],
            # --- ИЗМЕНЕНА callback_data ---
            callback_data=ChangeStatus(order_id=order_id, new_status='canceled', action='prompt_reason').pack()
        )
    )
    builder.row(InlineKeyboardButton(text=LEXICON['back_to_orders_button'], callback_data='admin_list_orders'))
    return builder.as_markup()