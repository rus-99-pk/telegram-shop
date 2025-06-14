from sqlalchemy import select, func, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import User, Product, CartItem, Order, OrderItem


async def get_user(session: AsyncSession, tg_id: int, username: str | None = None):
    user = await session.scalar(select(User).where(User.tg_id == tg_id))
    if not user:
        user = User(tg_id=tg_id, username=username)
        session.add(user)
        await session.commit()
    elif user.username != username:
        user.username = username
        await session.commit()
    return user


async def get_products(session: AsyncSession, page: int = 1, page_size: int = 5):
    offset = (page - 1) * page_size
    query = select(Product).offset(offset).limit(page_size)
    return await session.scalars(query)


async def count_products(session: AsyncSession):
    return await session.scalar(select(func.count(Product.id)))


async def add_to_cart(session: AsyncSession, user_id: int, product_id: int):
    cart_item = CartItem(user_id=user_id, product_id=product_id)
    session.add(cart_item)
    await session.commit()


async def get_cart_items(session: AsyncSession, user_id: int):
    query = select(Product.name, Product.price, func.count(CartItem.product_id).label('quantity')) \
        .join(CartItem, Product.id == CartItem.product_id) \
        .where(CartItem.user_id == user_id) \
        .group_by(Product.name, Product.price)
    return await session.execute(query)


async def get_cart_items_for_order(session: AsyncSession, user_id: int):
    query = select(Product.name, Product.price) \
        .join(CartItem, Product.id == CartItem.product_id) \
        .where(CartItem.user_id == user_id)
    return await session.execute(query)


async def clear_cart(session: AsyncSession, user_id: int):
    await session.execute(delete(CartItem).where(CartItem.user_id == user_id))
    await session.commit()


async def place_order(session: AsyncSession, user_id: int, delivery_details: dict):
    cart_products = await get_cart_items_for_order(session, user_id)
    products_list = cart_products.all()

    if not products_list:
        return None

    new_order = Order(
        user_id=user_id,
        status='new',
        delivery_pickup_point=delivery_details.get('pickup_point'),
        recipient_full_name=delivery_details.get('full_name'),
        recipient_phone_number=delivery_details.get('phone')
    )
    session.add(new_order)
    await session.flush()

    for product in products_list:
        order_item = OrderItem(
            order_id=new_order.id,
            product_name=product.name,
            product_price=product.price
        )
        session.add(order_item)

    await session.commit()
    return new_order.id


async def get_user_orders(session: AsyncSession, user_id: int):
    query = select(Order.id, Order.status).where(Order.user_id == user_id).order_by(Order.id.desc())
    return await session.execute(query)


async def get_all_orders(session: AsyncSession):
    query = select(Order.id, Order.status, User.tg_id).join(User, Order.user_id == User.id).order_by(Order.id.desc())
    return await session.execute(query)


async def get_order_details(session: AsyncSession, order_id: int):
    query = select(
        Order.id, Order.status, Order.delivery_pickup_point,
        Order.recipient_full_name, Order.recipient_phone_number,
        Order.receipt_file_id, Order.cdek_track_number, # <-- ДОБАВЛЕНО
        User.tg_id, User.username
    ).join(User, Order.user_id == User.id).where(Order.id == order_id)
    
    order_info = await session.execute(query)
    
    query_items = select(OrderItem.product_name, OrderItem.product_price) \
        .where(OrderItem.order_id == order_id)
    order_items = await session.execute(query_items)
    
    return order_info.one_or_none(), order_items.all()


async def get_user_order_details(session: AsyncSession, order_id: int, user_id: int):
    query = select(Order).where(Order.id == order_id, Order.user_id == user_id)
    order = await session.scalar(query)
    
    if not order:
        return None, None
        
    query_items = select(OrderItem.product_name, OrderItem.product_price).where(OrderItem.order_id == order_id)
    order_items = await session.execute(query_items)
    
    return order, order_items.all()


async def update_order_status(session: AsyncSession, order_id: int, status: str):
    query = update(Order).where(Order.id == order_id).values(status=status)
    await session.execute(query)
    await session.commit()


async def attach_receipt_to_order(session: AsyncSession, order_id: int, file_id: str):
    query = update(Order).where(Order.id == order_id).values(receipt_file_id=file_id)
    await session.execute(query)
    await session.commit()

# --- НОВАЯ ФУНКЦИЯ ---
async def set_cdek_track_number(session: AsyncSession, order_id: int, track_number: str):
    """Устанавливает трек-номер для заказа."""
    query = update(Order).where(Order.id == order_id).values(cdek_track_number=track_number)
    await session.execute(query)
    await session.commit()
# ---------------------

async def add_product(session: AsyncSession, name: str, price: float, photo_id: str, description: str | None):
    product = Product(name=name, price=price, photo_id=photo_id, description=description)
    session.add(product)
    await session.commit()


async def get_all_products(session: AsyncSession):
    return await session.scalars(select(Product))


async def update_product_price(session: AsyncSession, product_id: int, new_price: float):
    await session.execute(update(Product).where(Product.id == product_id).values(price=new_price))
    await session.commit()


async def update_product_name(session: AsyncSession, product_id: int, new_name: str):
    await session.execute(update(Product).where(Product.id == product_id).values(name=new_name))
    await session.commit()

async def update_product_description(session: AsyncSession, product_id: int, new_description: str | None):
    await session.execute(update(Product).where(Product.id == product_id).values(description=new_description))
    await session.commit()

async def delete_product(session: AsyncSession, product_id: int):
    await session.execute(delete(Product).where(Product.id == product_id))
    await session.commit()


async def get_stats(session: AsyncSession):
    total_users = await session.scalar(select(func.count(User.id)))
    
    orders_by_status = await session.execute(
        select(Order.status, func.count(Order.id)).group_by(Order.status)
    )
    
    total_revenue = await session.scalar(
        select(func.sum(OrderItem.product_price))
        .join(Order, OrderItem.order_id == Order.id)
        .where(Order.status == 'completed')
    )

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

    for status, count in orders_by_status:
        stats_key = f'{status}_orders'
        if stats_key in stats:
            stats[stats_key] = count
            stats['total_orders'] += count
        
    return stats


async def get_all_user_ids(session: AsyncSession):
    return await session.scalars(select(User.tg_id))