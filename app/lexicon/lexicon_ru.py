# Определяем статусы, чтобы использовать их консистентно по всему проекту
ORDER_STATUSES = {
    'new': 'Новый',
    'processing': 'В работе',
    'shipped': 'Отправлен',
    'completed': 'Завершен',
    'canceled': 'Отменен'
}

LEXICON: dict[str, str] = {
    # User part
    'start_message': '👋 Привет! Я бот-магазин.\n\nИспользуй меню для навигации.',
    'catalog_button': '🛍️ Каталог',
    'cart_button': '🛒 Корзина',
    'orders_button': '📦 Мои заказы',
    'feedback_button': '👨‍💻 Поддержка',
    'catalog_title': '👇 Наши товары:',
    'cart_title': '🛒 Ваша корзина',
    'empty_cart': 'Ваша корзина пуста.',
    'order_placed': '✅ Ваш заказ успешно оформлен! Номер заказа: {order_id}.\n\nСкоро мы с вами свяжемся.',
    'order_history_title': '📦 Ваши заказы:',
    'no_orders': 'У вас еще нет заказов.',
    'item_added_to_cart': '✅ Товар добавлен в корзину!',
    'checkout_button': '✅ Оформить заказ',
    'clear_cart_button': '🗑️ Очистить корзину',
    'back_to_main_menu': '⬅️ Назад в главное меню',
    'user_order_status_changed': '🔔 Статус вашего заказа <b>#{order_id}</b> изменен на: <b>{status}</b>',
    # --- НОВЫЙ ТЕКСТ ---
    'user_order_canceled_with_reason': '🔔 К сожалению, ваш заказ <b>#{order_id}</b> был отменен.\n\n<b>Причина:</b> {reason}',

    # Admin part
    'admin_start_message': '👋 Привет, админ! Что будем делать?',
    'admin_panel_button': '⚙️ Админ-панель',
    'add_item_button': '➕ Добавить товар',
    'list_orders_button': '📋 Список заказов',
    'admin_new_order_notification': '🔔 Новый заказ #{order_id}!\n\nСостав:\n{products}\n\nПользователь: @{username} (ID: {user_id})',
    'admin_add_product_name': 'Введите название товара:',
    'admin_add_product_photo': 'Отправьте фото товара:',
    'admin_add_product_price': 'Введите цену товара (только число):',
    'admin_product_added': '✅ Товар "{name}" успешно добавлен!',
    'admin_no_orders': 'Пока нет ни одного заказа.',
    'admin_list_orders_title': '📋 Нажмите на заказ для управления:',
    'admin_order_details': (
        '<b>Детали заказа #{order_id}</b>\n\n'
        '<b>Пользователь:</b> @{username} (ID: {user_id})\n'
        '<b>Статус:</b> {status}\n\n'
        '<b>Состав:</b>\n{products}'
    ),
    'admin_status_updated': '✅ Статус заказа обновлен!',
    'back_to_orders_button': '⬅️ К списку заказов',
    # --- НОВЫЙ ТЕКСТ ---
    'admin_enter_cancellation_reason': '📝 Введите причину отмены заказа #{order_id}:',

    # Common
    'back_button': '⬅️ Назад',
    'error_message': 'Что-то пошло не так. Попробуйте снова.',
    
    # Order Statuses Buttons
    'status_processing_button': f'➡️ {ORDER_STATUSES["processing"]}',
    'status_shipped_button': f'🚚 {ORDER_STATUSES["shipped"]}',
    'status_completed_button': f'✅ {ORDER_STATUSES["completed"]}',
    'status_canceled_button': f'❌ {ORDER_STATUSES["canceled"]}',
}