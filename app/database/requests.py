from sqlalchemy import select, func, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import User, Product, CartItem, Order, OrderItem


# --- ИЗМЕНЕНА ФУНКЦИЯ get_user ---
async def get_user(session: AsyncSession, tg_id: int, username: str | None = None):
    user = await session.scalar(select(User).where(User.tg_id == tg_id))
    if not user:
        user = User(tg_id=tg_id, username=username)
        session.add(user)
        await session.commit()
    # Обновляем username, если он изменился или был null
    elif user.username != username:
        user.username = username
        await session.commit()
    return user


async def get_products(session: AsyncSession):
    return await session.scalars(select(Product))


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


async def place_order(session: AsyncSession, user_id: int):
    cart_products = await get_cart_items_for_order(session, user_id)
    products_list = cart_products.all()

    if not products_list:
        return None

    new_order = Order(user_id=user_id, status='new')
    session.add(new_order)
    await session.flush()

    for product in products_list:
        order_item = OrderItem(
            order_id=new_order.id,
            product_name=product.name,
            product_price=product.price
        )
        session.add(order_item)

    await session.execute(delete(CartItem).where(CartItem.user_id == user_id))
    await session.commit()
    return new_order.id


async def get_user_orders(session: AsyncSession, user_id: int):
    query = select(Order.id, Order.status).where(Order.user_id == user_id).order_by(Order.id.desc())
    return await session.execute(query)


async def get_all_orders(session: AsyncSession):
    query = select(Order.id, Order.status, User.tg_id).join(User, Order.user_id == User.id).order_by(Order.id.desc())
    return await session.execute(query)

async def get_order_details(session: AsyncSession, order_id: int):
    query = select(Order.id, Order.status, User.tg_id, User.username) \
        .join(User, Order.user_id == User.id) \
        .where(Order.id == order_id)
    order_info = await session.execute(query)
    
    query_items = select(OrderItem.product_name, OrderItem.product_price) \
        .where(OrderItem.order_id == order_id)
    order_items = await session.execute(query_items)
    
    return order_info.one_or_none(), order_items.all()


async def update_order_status(session: AsyncSession, order_id: int, status: str):
    query = update(Order).where(Order.id == order_id).values(status=status)
    await session.execute(query)
    await session.commit()

async def add_product(session: AsyncSession, name: str, price: float, photo_id: str):
    product = Product(name=name, price=price, photo_id=photo_id)
    session.add(product)
    await session.commit()