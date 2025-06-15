from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData

from app.lexicon.lexicon_ru import LEXICON, ORDER_STATUSES
from app.database.models import Product
from app.config import config


# --- Фабрики Callback-данных (CallbackData) ---
# Используются для создания структурированных callback-ов для кнопок

# Для просмотра деталей заказа админом
class ViewOrder(CallbackData, prefix="view_order"):
    order_id: int

# Для запроса на смену статуса заказа (показывает клавиатуру со статусами)
class PromptStatus(CallbackData, prefix="prompt_status"):
    order_id: int

# Для смены статуса заказа
class ChangeStatus(CallbackData, prefix="change_status"):
    order_id: int
    new_status: str
    action: str | None = None  # Дополнительное действие (например, запросить трек-номер)

# Для просмотра деталей товара
class ViewProduct(CallbackData, prefix="view_prod"):
    product_id: int

# Для навигации по страницам каталога
class CatalogPage(CallbackData, prefix="catalog_page"):
    page: int

# Для добавления товара в корзину
class AddToCart(CallbackData, prefix="add_cart"):
    product_id: int

# Для отмены процесса оформления заказа
class CancelCheckout(CallbackData, prefix="cancel_checkout"):
    order_id: int | None = None  # ID заказа, если он уже был создан

# Для отмены любого FSM-состояния (например, добавления товара админом)
class CancelFSM(CallbackData, prefix="cancel_fsm"):
    pass

# Для просмотра чека админом
class ViewReceipt(CallbackData, prefix="view_receipt"):
    order_id: int

# Для просмотра деталей заказа пользователем
class UserViewOrder(CallbackData, prefix="user_view_order"):
    order_id: int

# Для подтверждения получения заказа пользователем
class ConfirmReceipt(CallbackData, prefix="confirm_receipt"):
    order_id: int

# Для управления конкретным товаром (админка)
class ManageProduct(CallbackData, prefix="mng_prod"):
    product_id: int

# Для редактирования товара (админка)
class EditProduct(CallbackData, prefix="edit_prod"):
    product_id: int
    action: str  # Какое поле редактируем ('price', 'name', 'description')

# Для удаления товара (админка)
class DeleteProduct(CallbackData, prefix="del_prod"):
    product_id: int
    confirm: bool  # Флаг подтверждения удаления


# --- Функции для сборки клавиатур (Keyboard Builders) ---

def main_menu_keyboard(is_admin: bool = False):
    """Создает клавиатуру главного меню."""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=LEXICON['catalog_button'], callback_data='catalog'))
    builder.row(InlineKeyboardButton(text=LEXICON['cart_button'], callback_data='my_cart'))
    builder.row(InlineKeyboardButton(text=LEXICON['orders_button'], callback_data='my_orders'))
    builder.row(InlineKeyboardButton(
        text=LEXICON['feedback_button'],
        url=f't.me/{config.support_username}'  # Кнопка-ссылка
    ))
    if is_admin:
        # Добавляем кнопку админ-панели, если пользователь является админом
        builder.row(InlineKeyboardButton(text=LEXICON['admin_panel_button'], callback_data='admin_panel'))
    return builder.as_markup()

def admin_panel_keyboard():
    """Создает клавиатуру админ-панели."""
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
    """Создает клавиатуру с одной кнопкой "Отмена" для прерывания FSM-состояний."""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text=LEXICON['cancel_action_button'],
        callback_data=CancelFSM().pack()
    ))
    return builder.as_markup()

def catalog_keyboard(products: list[Product], page: int, total_pages: int):
    """Создает клавиатуру для каталога с товарами и кнопками навигации."""
    builder = InlineKeyboardBuilder()
    # Добавляем кнопки для каждого товара
    for product in products:
        builder.row(InlineKeyboardButton(
            text=f'{product.name} - {int(product.price)} руб.',
            callback_data=ViewProduct(product_id=product.id).pack()
        ))
    
    # Добавляем кнопки навигации "Вперед" / "Назад"
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
        builder.row(*nav_buttons)  # Добавляем кнопки навигации в один ряд

    builder.row(InlineKeyboardButton(text=LEXICON['back_to_main_menu'], callback_data='to_main_menu'))
    return builder.as_markup()

def product_detail_keyboard(product_id: int, back_callback: str = 'catalog'):
    """Создает клавиатуру для страницы с деталями товара."""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text='➕ Добавить в корзину',
        callback_data=AddToCart(product_id=product_id).pack()
    ))
    # Логика для кнопки "Назад", чтобы вернуться на правильную страницу каталога
    if back_callback == 'catalog_page_1':
        builder.row(InlineKeyboardButton(text=LEXICON['back_button'], callback_data=CatalogPage(page=1).pack()))
    else:
        builder.row(InlineKeyboardButton(text=LEXICON['back_button'], callback_data=back_callback))
    return builder.as_markup()

def product_added_to_cart_keyboard(product_id: int, back_callback: str = 'catalog'):
    """Клавиатура, которая показывается после добавления товара в корзину."""
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
    """Создает клавиатуру для корзины."""
    builder = InlineKeyboardBuilder()
    if items: # Если корзина не пуста
        builder.row(InlineKeyboardButton(text=LEXICON['checkout_button'], callback_data='checkout'))
        builder.row(InlineKeyboardButton(text=LEXICON['clear_cart_button'], callback_data='clear_cart'))
    builder.row(InlineKeyboardButton(text=LEXICON['back_to_main_menu'], callback_data='to_main_menu'))
    return builder.as_markup()

def back_to_main_menu_keyboard():
    """Создает клавиатуру с одной кнопкой "Назад в главное меню"."""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=LEXICON['back_to_main_menu'], callback_data='to_main_menu'))
    return builder.as_markup()

def cancel_checkout_keyboard(order_id: int | None = None):
    """Создает клавиатуру для отмены оформления заказа."""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text=LEXICON['cancel_checkout_button'],
        callback_data=CancelCheckout(order_id=order_id).pack()
    ))
    return builder.as_markup()

def pickup_point_keyboard():
    """Клавиатура для шага ввода пункта выдачи СДЭК."""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text=LEXICON['checkout_cdek_offices_button'],
        url="https://www.cdek.ru/ru/offices"  # Кнопка-ссылка на карту офисов СДЭК
    ))
    builder.row(InlineKeyboardButton(
        text=LEXICON['cancel_checkout_button'],
        callback_data=CancelCheckout().pack()
    ))
    return builder.as_markup()

def user_orders_keyboard(orders: list):
    """Создает клавиатуру со списком заказов пользователя."""
    builder = InlineKeyboardBuilder()
    for order in orders:
        status_text = ORDER_STATUSES.get(order.status, order.status) # Получаем текстовое представление статуса
        builder.row(InlineKeyboardButton(
            text=f'Заказ #{order.id} (Статус: {status_text})',
            callback_data=UserViewOrder(order_id=order.id).pack()
        ))
    builder.row(InlineKeyboardButton(text=LEXICON['back_to_main_menu'], callback_data='to_main_menu'))
    return builder.as_markup()

def user_order_detail_keyboard(order_id: int, status: str, track_number: str | None):
    """Клавиатура для страницы с деталями заказа пользователя."""
    builder = InlineKeyboardBuilder()
    if track_number:
        # Если есть трек-номер, добавляем кнопку для отслеживания
        builder.row(InlineKeyboardButton(
            text=LEXICON['track_order_button'],
            url=f"https://www.cdek.ru/ru/tracking/?order_id={track_number}"
        ))
    if status == 'shipped':
        # Если заказ отправлен, добавляем кнопку подтверждения получения
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
    """Создает клавиатуру со списком всех заказов для админа."""
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
    """Клавиатура для управления конкретным заказом в админ-панели."""
    builder = InlineKeyboardBuilder()

    if has_receipt:
        # Кнопка для просмотра прикрепленного чека
        builder.row(
            InlineKeyboardButton(
                text=LEXICON['view_receipt_button'],
                callback_data=ViewReceipt(order_id=order_id).pack()
            )
        )
    
    if track_number:
        # Кнопка для отслеживания заказа на сайте СДЭК
        builder.row(InlineKeyboardButton(
            text=LEXICON['track_order_button'],
            url=f"https://www.cdek.ru/ru/tracking/?order_id={track_number}"
        ))

    # Кнопка для смены статуса, если заказ еще не завершен или не отменен
    if status not in ['completed', 'canceled']:
        builder.row(
            InlineKeyboardButton(
                text=LEXICON['change_status_button'],
                callback_data=PromptStatus(order_id=order_id).pack()
            )
        )
    
    builder.row(InlineKeyboardButton(text=LEXICON['back_to_orders_button'], callback_data='admin_list_orders'))
    return builder.as_markup()

def change_status_keyboard(order_id: int):
    """Клавиатура для выбора нового статуса заказа админом."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=LEXICON['status_processing_button'],
            callback_data=ChangeStatus(order_id=order_id, new_status='processing').pack()
        ),
        InlineKeyboardButton(
            text=LEXICON['status_shipped_button'],
            # При смене на "Отправлен" требуется доп. действие - запросить трек-номер
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
            # При смене на "Отменен" требуется доп. действие - запросить причину
            callback_data=ChangeStatus(order_id=order_id, new_status='canceled', action='prompt_reason').pack()
        )
    )
    builder.row(InlineKeyboardButton(
        text=LEXICON['back_to_order_details_button'],
        callback_data=ViewOrder(order_id=order_id).pack()
    ))
    return builder.as_markup()

def manage_products_keyboard(products: list[Product]):
    """Создает клавиатуру со списком товаров для управления в админ-панели."""
    builder = InlineKeyboardBuilder()
    for product in products:
        builder.row(InlineKeyboardButton(
            text=product.name,
            callback_data=ManageProduct(product_id=product.id).pack()
        ))
    builder.row(InlineKeyboardButton(text=LEXICON['back_button'], callback_data='admin_panel'))
    return builder.as_markup()

def product_edit_actions_keyboard(product_id: int):
    """Клавиатура для выбора поля товара, которое нужно отредактировать."""
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
    """Клавиатура с действиями над конкретным товаром: редактировать или удалить."""
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
    """Клавиатура для подтверждения удаления товара."""
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
    """Универсальная клавиатура отмены с возвратом на указанный 'back_to' callback."""
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