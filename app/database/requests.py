from sqlalchemy import select, func, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import User, Product, CartItem, Order, OrderItem


# --- Функции для работы с пользователями ---

async def get_user(session: AsyncSession, tg_id: int, username: str | None = None):
    """
    Находит пользователя по tg_id. Если пользователь не найден, создает нового.
    Если найден, но изменился username, обновляет его.
    """
    # Ищем пользователя в БД по его Telegram ID
    user = await session.scalar(select(User).where(User.tg_id == tg_id))
    if not user:
        # Если пользователь не найден, создаем новую запись
        user = User(tg_id=tg_id, username=username)
        session.add(user)
        await session.commit()
    elif user.username != username:
        # Если пользователь найден, но его username изменился, обновляем его
        user.username = username
        await session.commit()
    return user


# --- Функции для работы с товарами (Каталог) ---

async def get_products(session: AsyncSession, page: int = 1, page_size: int = 5):
    """Получает список товаров для определенной страницы (пагинация)."""
    offset = (page - 1) * page_size  # Рассчитываем смещение
    query = select(Product).offset(offset).limit(page_size)  # Запрос на выборку товаров с учетом смещения и лимита
    return await session.scalars(query)


async def count_products(session: AsyncSession):
    """Подсчитывает общее количество товаров в базе данных."""
    return await session.scalar(select(func.count(Product.id)))


# --- Функции для работы с корзиной ---

async def add_to_cart(session: AsyncSession, user_id: int, product_id: int):
    """Добавляет товар в корзину пользователя."""
    cart_item = CartItem(user_id=user_id, product_id=product_id)
    session.add(cart_item)
    await session.commit()


async def get_cart_items(session: AsyncSession, user_id: int):
    """
    Получает сгруппированный список товаров в корзине пользователя.
    Для каждого товара возвращает название, цену и количество.
    """
    query = select(Product.name, Product.price, func.count(CartItem.product_id).label('quantity')) \
        .join(CartItem, Product.id == CartItem.product_id) \
        .where(CartItem.user_id == user_id) \
        .group_by(Product.name, Product.price)  # Группируем, чтобы посчитать одинаковые товары
    return await session.execute(query)


async def get_cart_items_for_order(session: AsyncSession, user_id: int):
    """Получает полный (несгруппированный) список товаров из корзины для создания заказа."""
    query = select(Product.name, Product.price) \
        .join(CartItem, Product.id == CartItem.product_id) \
        .where(CartItem.user_id == user_id)
    return await session.execute(query)


async def clear_cart(session: AsyncSession, user_id: int):
    """Очищает корзину пользователя."""
    await session.execute(delete(CartItem).where(CartItem.user_id == user_id))
    await session.commit()


# --- Функции для работы с заказами ---

async def place_order(session: AsyncSession, user_id: int, delivery_details: dict):
    """
    Создает новый заказ на основе товаров в корзине и данных о доставке.
    """
    # Получаем товары из корзины
    cart_products = await get_cart_items_for_order(session, user_id)
    products_list = cart_products.all()

    if not products_list:
        return None  # Нельзя создать заказ из пустой корзины

    # Создаем основную запись о заказе
    new_order = Order(
        user_id=user_id,
        status='new',  # Начальный статус
        delivery_pickup_point=delivery_details.get('pickup_point'),
        recipient_full_name=delivery_details.get('full_name'),
        recipient_phone_number=delivery_details.get('phone')
    )
    session.add(new_order)
    await session.flush()  # Получаем ID нового заказа до коммита

    # Добавляем каждый товар из корзины в детали заказа (OrderItem)
    for product in products_list:
        order_item = OrderItem(
            order_id=new_order.id,
            product_name=product.name,
            product_price=product.price
        )
        session.add(order_item)

    await session.commit()
    return new_order.id  # Возвращаем ID созданного заказа


async def get_user_orders(session: AsyncSession, user_id: int):
    """Получает историю заказов конкретного пользователя."""
    query = select(Order.id, Order.status).where(Order.user_id == user_id).order_by(Order.id.desc())
    return await session.execute(query)


async def get_all_orders(session: AsyncSession):
    """Получает все заказы для админ-панели."""
    query = select(Order.id, Order.status, User.tg_id).join(User, Order.user_id == User.id).order_by(Order.id.desc())
    return await session.execute(query)


async def get_order_details(session: AsyncSession, order_id: int):
    """Получает полную информацию о заказе, включая данные пользователя."""
    # Запрос на получение основной информации о заказе и пользователе
    query = select(
        Order.id, Order.status, Order.delivery_pickup_point,
        Order.recipient_full_name, Order.recipient_phone_number,
        Order.receipt_file_id, Order.cdek_track_number,
        User.tg_id, User.username
    ).join(User, Order.user_id == User.id).where(Order.id == order_id)
    
    order_info = await session.execute(query)
    
    # Запрос на получение списка товаров в этом заказе
    query_items = select(OrderItem.product_name, OrderItem.product_price) \
        .where(OrderItem.order_id == order_id)
    order_items = await session.execute(query_items)
    
    # Возвращаем кортеж: (информация о заказе, список товаров)
    return order_info.one_or_none(), order_items.all()


async def get_user_order_details(session: AsyncSession, order_id: int, user_id: int):
    """Получает детали заказа для конкретного пользователя (для безопасности)."""
    query = select(Order).where(Order.id == order_id, Order.user_id == user_id)
    order = await session.scalar(query)
    
    if not order:
        return None, None
        
    query_items = select(OrderItem.product_name, OrderItem.product_price).where(OrderItem.order_id == order_id)
    order_items = await session.execute(query_items)
    
    return order, order_items.all()


async def update_order_status(session: AsyncSession, order_id: int, status: str):
    """Обновляет статус заказа."""
    query = update(Order).where(Order.id == order_id).values(status=status)
    await session.execute(query)
    await session.commit()


async def attach_receipt_to_order(session: AsyncSession, order_id: int, file_id: str):
    """Прикрепляет ID файла с чеком к заказу."""
    query = update(Order).where(Order.id == order_id).values(receipt_file_id=file_id)
    await session.execute(query)
    await session.commit()


async def set_cdek_track_number(session: AsyncSession, order_id: int, track_number: str):
    """Устанавливает трек-номер для заказа."""
    query = update(Order).where(Order.id == order_id).values(cdek_track_number=track_number)
    await session.execute(query)
    await session.commit()

# --- Функции для отчета и статистики ---

async def get_all_orders_with_user_info(session: AsyncSession):
    """Получает все заказы с информацией о пользователе для Excel-отчета."""
    query = select(Order, User).join(User, Order.user_id == User.id).order_by(Order.id.asc())
    result = await session.execute(query)
    return result.all()


async def get_all_order_items(session: AsyncSession):
    """Получает все заказанные товары для отчета."""
    query = select(OrderItem)
    result = await session.scalars(query)
    return result.all()


async def get_stats(session: AsyncSession):
    """Собирает статистику по магазину."""
    # Общее количество пользователей
    total_users = await session.scalar(select(func.count(User.id)))
    
    # Количество заказов по каждому статусу
    orders_by_status = await session.execute(
        select(Order.status, func.count(Order.id)).group_by(Order.status)
    )
    
    # Общая выручка по завершенным заказам
    total_revenue = await session.scalar(
        select(func.sum(OrderItem.product_price))
        .join(Order, OrderItem.order_id == Order.id)
        .where(Order.status == 'completed')
    )

    # Формируем словарь со статистикой
    stats = {
        'total_users': total_users or 0,
        'total_orders': 0,
        'new_orders': 0,
        'paid_orders': 0,
        'processing_orders': 0,
        'shipped_orders': 0,
        'completed_orders': 0,
        'canceled_orders': 0,
        'total_revenue': int(total_revenue) if total_revenue else 0
    }

    # Заполняем статистику по статусам
    for status, count in orders_by_status:
        stats_key = f'{status}_orders'
        if stats_key in stats:
            stats[stats_key] = count
            stats['total_orders'] += count
        
    return stats


# --- Функции для администрирования (товары, рассылка) ---

async def add_product(session: AsyncSession, name: str, price: float, photo_id: str, description: str | None):
    """Добавляет новый товар в базу данных."""
    product = Product(name=name, price=price, photo_id=photo_id, description=description)
    session.add(product)
    await session.commit()


async def get_all_products(session: AsyncSession):
    """Получает все товары (для управления ими в админ-панели)."""
    return await session.scalars(select(Product))


async def update_product_price(session: AsyncSession, product_id: int, new_price: float):
    """Обновляет цену товара."""
    await session.execute(update(Product).where(Product.id == product_id).values(price=new_price))
    await session.commit()


async def update_product_name(session: AsyncSession, product_id: int, new_name: str):
    """Обновляет название товара."""
    await session.execute(update(Product).where(Product.id == product_id).values(name=new_name))
    await session.commit()

async def update_product_description(session: AsyncSession, product_id: int, new_description: str | None):
    """Обновляет описание товара."""
    await session.execute(update(Product).where(Product.id == product_id).values(description=new_description))
    await session.commit()

async def delete_product(session: AsyncSession, product_id: int):
    """Удаляет товар из базы данных."""
    await session.execute(delete(Product).where(Product.id == product_id))
    await session.commit()


async def get_all_user_ids(session: AsyncSession):
    """Получает Telegram ID всех пользователей для рассылки."""
    return await session.scalars(select(User.tg_id))