from sqlalchemy import BigInteger, String, Float, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs


class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id = mapped_column(BigInteger)
    username: Mapped[str] = mapped_column(String(100), nullable=True)


class Product(Base):
    __tablename__ = 'products'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(255), nullable=True)
    price: Mapped[float] = mapped_column(Float(asdecimal=True))
    photo_id: Mapped[str] = mapped_column(String)


class CartItem(Base):
    __tablename__ = 'cart_items'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id'))


class Order(Base):
    __tablename__ = 'orders'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    status: Mapped[str] = mapped_column(String(50), default='new')
    
    delivery_pickup_point: Mapped[str] = mapped_column(String(255), nullable=True)
    recipient_full_name: Mapped[str] = mapped_column(String(150), nullable=True)
    recipient_phone_number: Mapped[str] = mapped_column(String(20), nullable=True)
    receipt_file_id: Mapped[str] = mapped_column(String, nullable=True)
    cdek_track_number: Mapped[str] = mapped_column(String, nullable=True) # <-- ДОБАВЛЕНО ПОЛЕ


class OrderItem(Base):
    __tablename__ = 'order_items'
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey('orders.id'))
    product_name: Mapped[str] = mapped_column(String(100))
    product_price: Mapped[float] = mapped_column(Float(asdecimal=True))