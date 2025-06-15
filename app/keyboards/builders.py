from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData

from app.lexicon.lexicon_ru import LEXICON, ORDER_STATUSES
from app.database.models import Product
from app.config import config


class ViewOrder(CallbackData, prefix="view_order"):
    order_id: int

# <-- НОВАЯ CALLBACKDATA -->
class PromptStatus(CallbackData, prefix="prompt_status"):
    order_id: int
# -------------------------

class ChangeStatus(CallbackData, prefix="change_status"):
    order_id: int
    new_status: str
    action: str | None = None

class ViewProduct(CallbackData, prefix="view_prod"):
    product_id: int

class CatalogPage(CallbackData, prefix="catalog_page"):
    page: int

class AddToCart(CallbackData, prefix="add_cart"):
    product_id: int

class CancelCheckout(CallbackData, prefix="cancel_checkout"):
    order_id: int | None = None

class CancelFSM(CallbackData, prefix="cancel_fsm"):
    pass

class ViewReceipt(CallbackData, prefix="view_receipt"):
    order_id: int

class UserViewOrder(CallbackData, prefix="user_view_order"):
    order_id: int

class ConfirmReceipt(CallbackData, prefix="confirm_receipt"):
    order_id: int

class ManageProduct(CallbackData, prefix="mng_prod"):
    product_id: int

class EditProduct(CallbackData, prefix="edit_prod"):
    product_id: int
    action: str

class DeleteProduct(CallbackData, prefix="del_prod"):
    product_id: int
    confirm: bool


def main_menu_keyboard(is_admin: bool = False):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=LEXICON['catalog_button'], callback_data='catalog'))
    builder.row(InlineKeyboardButton(text=LEXICON['cart_button'], callback_data='my_cart'))
    builder.row(InlineKeyboardButton(text=LEXICON['orders_button'], callback_data='my_orders'))
    builder.row(InlineKeyboardButton(
        text=LEXICON['feedback_button'],
        url=f't.me/{config.support_username}'
    ))
    if is_admin:
        builder.row(InlineKeyboardButton(text=LEXICON['admin_panel_button'], callback_data='admin_panel'))
    return builder.as_markup()

def admin_panel_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=LEXICON['add_item_button'], callback_data='admin_add_product'))
    builder.row(InlineKeyboardButton(text=LEXICON['manage_products_button'], callback_data='admin_manage_products'))
    builder.row(InlineKeyboardButton(text=LEXICON['list_orders_button'], callback_data='admin_list_orders'))
    builder.row(
        InlineKeyboardButton(text=LEXICON['statistics_button'], callback_data='admin_stats'),
        InlineKeyboardButton(text=LEXICON['report_button'], callback_data='admin_report')
    )
    builder.row(InlineKeyboardButton(text=LEXICON['mailing_button'], callback_data='admin_mailing'))
    builder.row(InlineKeyboardButton(text=LEXICON['back_to_main_menu'], callback_data='to_main_menu'))
    return builder.as_markup()

def cancel_fsm_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text=LEXICON['cancel_action_button'],
        callback_data=CancelFSM().pack()
    ))
    return builder.as_markup()

def catalog_keyboard(products: list[Product], page: int, total_pages: int):
    builder = InlineKeyboardBuilder()
    for product in products:
        builder.row(InlineKeyboardButton(
            text=f'{product.name} - {int(product.price)} руб.',
            callback_data=ViewProduct(product_id=product.id).pack()
        ))
    
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(
            text="◀️ Назад",
            callback_data=CatalogPage(page=page - 1).pack()
        ))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton(
            text="Вперед ▶️",
            callback_data=CatalogPage(page=page + 1).pack()
        ))
    
    if nav_buttons:
        builder.row(*nav_buttons)

    builder.row(InlineKeyboardButton(text=LEXICON['back_to_main_menu'], callback_data='to_main_menu'))
    return builder.as_markup()

def product_detail_keyboard(product_id: int, back_callback: str = 'catalog'):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text='➕ Добавить в корзину',
        callback_data=AddToCart(product_id=product_id).pack()
    ))
    if back_callback == 'catalog_page_1':
        builder.row(InlineKeyboardButton(text=LEXICON['back_button'], callback_data=CatalogPage(page=1).pack()))
    else:
        builder.row(InlineKeyboardButton(text=LEXICON['back_button'], callback_data=back_callback))
    return builder.as_markup()

def product_added_to_cart_keyboard(product_id: int, back_callback: str = 'catalog'):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text='➕ Добавить еще',
        callback_data=AddToCart(product_id=product_id).pack()
    ))
    builder.row(InlineKeyboardButton(
        text=LEXICON['cart_button'],
        callback_data='my_cart'
    ))
    if back_callback == 'catalog_page_1':
        builder.row(InlineKeyboardButton(text=LEXICON['back_button'], callback_data=CatalogPage(page=1).pack()))
    else:
        builder.row(InlineKeyboardButton(text=LEXICON['back_button'], callback_data=back_callback))
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

def cancel_checkout_keyboard(order_id: int | None = None):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text=LEXICON['cancel_checkout_button'],
        callback_data=CancelCheckout(order_id=order_id).pack()
    ))
    return builder.as_markup()

def pickup_point_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text=LEXICON['checkout_cdek_offices_button'],
        url="https://www.cdek.ru/ru/offices"
    ))
    builder.row(InlineKeyboardButton(
        text=LEXICON['cancel_checkout_button'],
        callback_data=CancelCheckout().pack()
    ))
    return builder.as_markup()

def user_orders_keyboard(orders: list):
    builder = InlineKeyboardBuilder()
    for order in orders:
        status_text = ORDER_STATUSES.get(order.status, order.status)
        builder.row(InlineKeyboardButton(
            text=f'Заказ #{order.id} (Статус: {status_text})',
            callback_data=UserViewOrder(order_id=order.id).pack()
        ))
    builder.row(InlineKeyboardButton(text=LEXICON['back_to_main_menu'], callback_data='to_main_menu'))
    return builder.as_markup()

def user_order_detail_keyboard(order_id: int, status: str, track_number: str | None):
    builder = InlineKeyboardBuilder()
    if track_number:
        builder.row(InlineKeyboardButton(
            text=LEXICON['track_order_button'],
            url=f"https://www.cdek.ru/ru/tracking/?order_id={track_number}"
        ))
    if status == 'shipped':
        builder.row(InlineKeyboardButton(
            text=LEXICON['confirm_receipt_button'],
            callback_data=ConfirmReceipt(order_id=order_id).pack()
        ))
    builder.row(InlineKeyboardButton(
        text=LEXICON['back_to_orders_list_button'],
        callback_data='my_orders'
    ))
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

def manage_order_keyboard(order_id: int, has_receipt: bool, status: str, track_number: str | None):
    builder = InlineKeyboardBuilder()

    if has_receipt:
        builder.row(
            InlineKeyboardButton(
                text=LEXICON['view_receipt_button'],
                callback_data=ViewReceipt(order_id=order_id).pack()
            )
        )
    
    if track_number:
        builder.row(InlineKeyboardButton(
            text=LEXICON['track_order_button'],
            url=f"https://www.cdek.ru/ru/tracking/?order_id={track_number}"
        ))

    # <-- ИЗМЕНЕНИЕ: Отдельная кнопка для смены статуса -->
    if status not in ['completed', 'canceled']:
        builder.row(
            InlineKeyboardButton(
                text=LEXICON['change_status_button'],
                callback_data=PromptStatus(order_id=order_id).pack()
            )
        )
    # ---------------------------------------------------
    
    builder.row(InlineKeyboardButton(text=LEXICON['back_to_orders_button'], callback_data='admin_list_orders'))
    return builder.as_markup()

# <-- НОВАЯ КЛАВИАТУРА ДЛЯ ВЫБОРА СТАТУСА -->
def change_status_keyboard(order_id: int):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=LEXICON['status_processing_button'],
            callback_data=ChangeStatus(order_id=order_id, new_status='processing').pack()
        ),
        InlineKeyboardButton(
            text=LEXICON['status_shipped_button'],
            callback_data=ChangeStatus(order_id=order_id, new_status='shipped', action='prompt_track_number').pack()
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=LEXICON['status_completed_button'],
            callback_data=ChangeStatus(order_id=order_id, new_status='completed').pack()
        ),
        InlineKeyboardButton(
            text=LEXICON['status_canceled_button'],
            callback_data=ChangeStatus(order_id=order_id, new_status='canceled', action='prompt_reason').pack()
        )
    )
    builder.row(InlineKeyboardButton(
        text=LEXICON['back_to_order_details_button'],
        callback_data=ViewOrder(order_id=order_id).pack()
    ))
    return builder.as_markup()
# ----------------------------------------------

def manage_products_keyboard(products: list[Product]):
    builder = InlineKeyboardBuilder()
    for product in products:
        builder.row(InlineKeyboardButton(
            text=product.name,
            callback_data=ManageProduct(product_id=product.id).pack()
        ))
    builder.row(InlineKeyboardButton(text=LEXICON['back_button'], callback_data='admin_panel'))
    return builder.as_markup()

def product_edit_actions_keyboard(product_id: int):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=LEXICON['edit_price_button'],
            callback_data=EditProduct(product_id=product_id, action='price').pack()
        ),
        InlineKeyboardButton(
            text=LEXICON['edit_name_button'],
            callback_data=EditProduct(product_id=product_id, action='name').pack()
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=LEXICON['edit_description_button'],
            callback_data=EditProduct(product_id=product_id, action='description').pack()
        )
    )
    builder.row(InlineKeyboardButton(text=LEXICON['back_button'], callback_data='admin_manage_products'))
    return builder.as_markup()

def product_management_keyboard(product_id: int):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=LEXICON['edit_product_button'],
            callback_data=EditProduct(product_id=product_id, action='choose').pack()
        ),
        InlineKeyboardButton(
            text=LEXICON['delete_product_button'],
            callback_data=DeleteProduct(product_id=product_id, confirm=False).pack()
        )
    )
    builder.row(InlineKeyboardButton(text=LEXICON['back_button'], callback_data='admin_manage_products'))
    return builder.as_markup()

def confirm_delete_keyboard(product_id: int):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=LEXICON['confirm_delete_button'],
            callback_data=DeleteProduct(product_id=product_id, confirm=True).pack()
        ),
        InlineKeyboardButton(
            text=LEXICON['cancel_delete_button'],
            callback_data=ManageProduct(product_id=product_id).pack()
        )
    )
    return builder.as_markup()

def cancel_keyboard(back_to: str):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=LEXICON['cancel_mailing_button'], callback_data=back_to))
    return builder.as_markup()

def shipped_order_notification_keyboard(track_number: str):
    """
    Клавиатура с одной кнопкой "Отследить заказ" для уведомления пользователя.
    """
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text=LEXICON['track_order_button'],
        url=f"https://www.cdek.ru/ru/tracking/?order_id={track_number}"
    ))
    return builder.as_markup()

def admin_receipt_notification_keyboard():
    """
    Клавиатура для уведомления админа о новом чеке.
    Кнопка ведет в список заказов.
    """
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text=LEXICON['list_orders_button'],
        callback_data='admin_list_orders'
    ))
    return builder.as_markup()