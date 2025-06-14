# Определяем статусы, чтобы использовать их консистентно по всему проекту
ORDER_STATUSES = {
    'new': 'Ожидает оплаты',
    'paid': 'Оплачен, ожидает подтверждения',
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
    'main_menu_button': '☰ Меню',
    'catalog_title': '👇 Наши товары:',
    'cart_title': '🛒 Ваша корзина',
    'empty_cart': 'Ваша корзина пуста.',
    'checkout_enter_pickup_point': '📍 <b>Шаг 1/3:</b> Введите <b>адрес пункта выдачи СДЭК</b>, где вам будет удобно забрать заказ.\n\n<b>Пример:</b> Москва, пер. Благовещенский, 5',
    'checkout_cdek_offices_button': 'Посмотреть пункты СДЭК на карте',
    'checkout_enter_full_name': '👤 <b>Шаг 2/3:</b> Введите ваши <b>Фамилию, Имя и Отчество</b> полностью. Эти данные нужны для получения посылки.',
    'checkout_enter_phone_number': '📞 <b>Шаг 3/3:</b> Введите ваш <b>номер телефона</b> для связи. Пример: +79123456789',
    'checkout_invalid_phone': '❌ Неверный формат номера. Пожалуйста, введите номер в формате +7xxxxxxxxxx или 8xxxxxxxxxx.',
    'checkout_final_prompt': (
        '✅ <b>Заказ почти готов!</b>\n\n'
        '<b>Ваши данные:</b>\n'
        'Пункт выдачи: <code>{pickup_point}</code>\n'
        'Получатель: <code>{full_name}</code>\n'
        'Телефон: <code>{phone}</code>\n\n'
        '<b>Состав заказа:</b>\n{products}\n'
        '<b>К оплате: {total_price} руб.</b>\n\n'
        '1. Пожалуйста, переведите указанную сумму на карту:\n'
        '<code>{card_number}</code> (копируется по нажатию)\n\n'
        '2. После оплаты <b>сразу отправьте сюда чек в формате PDF</b> для подтверждения заказа.'
    ),
    'receipt_received': '📄 Чек получен!',
    'not_a_pdf': '❌ Пожалуйста, прикрепите чек именно в формате <b>PDF</b>.',
    'order_finalized': '✅ <b>Спасибо! Ваш заказ #{order_id} принят в обработку.</b>\n\nМы проверим поступление средств и возьмем заказ в работу. Отслеживать статус заказа можно в разделе «Мои заказы».',
    'cancel_checkout_button': '❌ Отменить заказ',
    'checkout_canceled': 'Вы отменили оформление заказа.',
    'order_history_title': '📦 <b>Ваши заказы</b>\n\nНажмите на заказ для просмотра деталей.',
    'no_orders': 'У вас еще нет заказов.',
    'item_added_to_cart': '✅ Товар добавлен в корзину!',
    'checkout_button': '✅ Оформить заказ',
    'clear_cart_button': '🗑️ Очистить корзину',
    'back_to_main_menu': '⬅️ Назад в главное меню',
    'user_order_status_changed': '🔔 Статус вашего заказа <b>#{order_id}</b> изменен на: <b>{status}</b>',
    'user_order_canceled_with_reason': '🔔 К сожалению, ваш заказ <b>#{order_id}</b> был отменен.\n\n<b>Причина:</b> {reason}',
    'user_order_details': (
        '<b>Детали заказа #{order_id}</b>\n\n'
        '<b>Статус:</b> {status}\n'
        '<b>Получатель:</b> {full_name}\n'
        '<b>Телефон:</b> {phone}\n'
        '<b>Пункт выдачи:</b> {pickup_point}\n\n'
        '<b>Состав заказа:</b>\n{products}'
    ),
    'confirm_receipt_button': '✅ Я получил(а) заказ',
    'order_receipt_confirmed_user': '🎉 Спасибо за подтверждение! Надеемся, вам все понравилось.',
    'back_to_orders_list_button': '⬅️ К списку заказов',
    'user_order_processing_notification': 'Благодарим за заказ! Ваш заказ собирается (срок сборки от 1 до 5 рабочих дней). После сборки Вам придет номер для его отслеживания в СДЭК.',
    'user_order_shipped_notification': '🚚 Ваш заказ #{order_id} отправлен!\n\nТрек-номер для отслеживания: <code>{track_number}</code>.\n\nЛибо воспользуйтесь кнопкой ниже 👇\nТакже вы можете ее найти в разделе "Мои заказы"',
    'track_order_button': '🚚 Отследить заказ',

    # Admin part
    'admin_start_message': '👋 Привет, админ! Что будем делать?',
    'admin_panel_button': '⚙️ Админ-панель',
    'add_item_button': '➕ Добавить товар',
    'list_orders_button': '📋 Список заказов',
    'manage_products_button': '🛍️ Управление товарами',
    'statistics_button': '📊 Статистика',
    'mailing_button': '📢 Рассылка',
    'admin_manage_products_title': '👇 Выберите товар для управления:',
    'edit_product_button': '✏️ Редактировать',
    'delete_product_button': '🗑️ Удалить',
    'confirm_delete_button': '✅ Да, удалить',
    'cancel_delete_button': '❌ Отмена',
    'product_deleted_message': '✅ Товар удален!',
    'confirm_delete_product': 'Вы уверены, что хотите удалить товар "{name}"?',
    'choose_edit_action': 'Что вы хотите отредактировать?',
    'edit_price_button': 'Изменить цену',
    'edit_name_button': 'Изменить название',
    'enter_new_price': 'Введите новую цену для товара "{name}":',
    'enter_new_name': 'Введите новое название для товара "{name}":',
    'price_updated': '✅ Цена обновлена!',
    'name_updated': '✅ Название обновлено!',
    'stats_message': (
        '<b>📊 Статистика магазина</b>\n\n'
        'Всего пользователей: {total_users}\n'
        'Всего заказов: {total_orders}\n'
        '   - Ожидают оплаты: {new_orders}\n'
        '   - Оплачены: {paid_orders}\n'
        '   - В работе: {processing_orders}\n'
        '   - Отправлено: {shipped_orders}\n'
        '   - Завершено: {completed_orders}\n'
        '   - Отменено: {canceled_orders}\n\n'
        'Общая сумма завершенных заказов: {total_revenue} руб.'
    ),
    'enter_mailing_text': 'Введите текст для рассылки. Пользователи получат это сообщение от имени бота. Вы можете использовать <b>HTML</b>-разметку.',
    'mailing_started': '✅ Рассылка запущена. Это может занять некоторое время.',
    'mailing_completed': '✅ Рассылка завершена! Отправлено {count} сообщений.',
    'mailing_canceled': 'Рассылка отменена.',
    'cancel_mailing_button': '❌ Отменить',
    'admin_order_canceled_notification': '❌ Заказ #{order_id} был отменен пользователем @{username} (ID: {user_id}) на этапе оформления.',
    'admin_receipt_notification': '📄 Пользователь @{username} (ID: {user_id}) прикрепил чек к заказу #{order_id}. Нажмите «Список заказов», чтобы посмотреть детали.',
    'admin_receipt_confirmed_notification': '✅ Пользователь @{username} подтвердил получение заказа #{order_id}. Заказ завершен.',
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
        '<b><u>Данные для доставки (копируются по нажатию):</u></b>\n'
        '<b>ПВЗ СДЭК:</b> <code>{pickup_point}</code>\n'
        '<b>ФИО получателя:</b> <code>{full_name}</code>\n'
        '<b>Телефон:</b> <code>{phone}</code>\n\n'
        '<b>Состав:</b>\n{products}'
    ),
    'admin_status_updated': '✅ Статус заказа обновлен!',
    'back_to_orders_button': '⬅️ К списку заказов',
    'admin_enter_cancellation_reason': '📝 Введите причину отмены заказа #{order_id}:',
    'admin_enter_cdek_track_number': '🚚 Введите трек-номер СДЭК для заказа #{order_id}:', # <-- ДОБАВЛЕНО
    'admin_add_product_description': 'Введите краткое описание товара (например, "бесплатная доставка").\n\nОтправьте `-` (дефис), чтобы пропустить.',
    'description_updated': '✅ Описание обновлено!',
    'edit_description_button': 'Изменить описание',
    'enter_new_description': 'Введите новое описание для товара "{name}".\n\nОтправьте `-` (дефис), чтобы удалить описание.',
    'cancel_action_button': '❌ Отмена',
    'action_canceled': 'Действие отменено.',
    'view_receipt_button': '📄 Посмотреть чек',

    # Common
    'back_button': '⬅️ Назад',
    'error_message': 'Что-то пошло не так. Попробуйте снова.',
    
    # Order Statuses Buttons
    'status_processing_button': f'➡️ {ORDER_STATUSES["processing"]}',
    'status_shipped_button': f'🚚 {ORDER_STATUSES["shipped"]}',
    'status_completed_button': f'✅ {ORDER_STATUSES["completed"]}',
    'status_canceled_button': f'❌ {ORDER_STATUSES["canceled"]}',
}