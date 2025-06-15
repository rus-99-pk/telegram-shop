from sqlalchemy import BigInteger, String, Float, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs

# Базовый класс для всех моделей SQLAlchemy, с поддержкой асинхронных операций
class Base(AsyncAttrs, DeclarativeBase):
    pass


# Модель пользователя
class User(Base):
    __tablename__ = 'users'  # Название таблицы в базе данных
    
    # Поля таблицы
    id: Mapped[int] = mapped_column(primary_key=True)  # Уникальный идентификатор пользователя в нашей БД (первичный ключ)
    tg_id = mapped_column(BigInteger)  # Уникальный идентификатор пользователя в Telegram
    username: Mapped[str] = mapped_column(String(100), nullable=True)  # Имя пользователя в Telegram (может отсутствовать)


# Модель товара
class Product(Base):
    __tablename__ = 'products'
    
    id: Mapped[int] = mapped_column(primary_key=True)  # Уникальный ID товара
    name: Mapped[str] = mapped_column(String(100))  # Название товара
    description: Mapped[str] = mapped_column(String(255), nullable=True)  # Описание товара (может отсутствовать)
    price: Mapped[float] = mapped_column(Float(asdecimal=True))  # Цена товара, хранится как Decimal для точности
    photo_id: Mapped[str] = mapped_column(String)  # File ID фотографии товара в Telegram


# Модель товара в корзине пользователя
class CartItem(Base):
    __tablename__ = 'cart_items'
    
    id: Mapped[int] = mapped_column(primary_key=True)  # Уникальный ID записи в корзине
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))  # ID пользователя, которому принадлежит корзина (внешний ключ)
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id'))  # ID добавленного товара (внешний ключ)


# Модель заказа
class Order(Base):
    __tablename__ = 'orders'
    
    id: Mapped[int] = mapped_column(primary_key=True)  # Уникальный ID заказа
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))  # ID пользователя, сделавшего заказ
    status: Mapped[str] = mapped_column(String(50), default='new')  # Статус заказа (например, 'new', 'paid', 'shipped')
    
    # Детали доставки
    delivery_pickup_point: Mapped[str] = mapped_column(String(255), nullable=True)  # Адрес пункта выдачи
    recipient_full_name: Mapped[str] = mapped_column(String(150), nullable=True)  # ФИО получателя
    recipient_phone_number: Mapped[str] = mapped_column(String(20), nullable=True)  # Номер телефона получателя
    receipt_file_id: Mapped[str] = mapped_column(String, nullable=True)  # File ID чека об оплате
    cdek_track_number: Mapped[str] = mapped_column(String, nullable=True)  # Трек-номер СДЭК для отслеживания


# Модель отдельного товара в составе заказа
# Используется для хранения "снимка" товара на момент заказа (название, цена)
class OrderItem(Base):
    __tablename__ = 'order_items'
    
    id: Mapped[int] = mapped_column(primary_key=True)  # Уникальный ID
    order_id: Mapped[int] = mapped_column(ForeignKey('orders.id'))  # ID заказа, к которому относится товар
    product_name: Mapped[str] = mapped_column(String(100))  # Название товара на момент заказа
    product_price: Mapped[float] = mapped_column(Float(asdecimal=True))  # Цена товара на момент заказа