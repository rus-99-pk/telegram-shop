from io import BytesIO
from datetime import datetime
from collections import defaultdict

import openpyxl
from openpyxl.styles import Font, Alignment

from app.database.models import Order, User, OrderItem
from app.lexicon.lexicon_ru import ORDER_STATUSES

def create_orders_excel_report(orders_with_users: list[tuple[Order, User]], all_items: list[OrderItem]) -> BytesIO:
    """
    Создает Excel-отчет по заказам и возвращает его как объект BytesIO (файл в памяти).
    
    :param orders_with_users: Список кортежей (Order, User), результат запроса из БД.
    :param all_items: Список всех заказанных товаров (OrderItem) для всех заказов.
    :return: Объект BytesIO с готовым Excel-файлом.
    """
    
    # Группируем товары по ID заказа для быстрого доступа
    items_by_order_id = defaultdict(list)
    for item in all_items:
        items_by_order_id[item.order_id].append(item)

    # Создаем новую книгу Excel
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Отчет по заказам"

    # Определяем заголовки столбцов
    headers = [
        "ID Заказа", "Статус", "TG ID", "Username", "ФИО Получателя",
        "Телефон", "ПВЗ СДЭК", "Трек-номер СДЭК", "Состав заказа", "Сумма заказа (руб.)"
    ]
    sheet.append(headers)

    # Применяем стили к заголовкам (жирный шрифт, выравнивание по центру)
    header_font = Font(bold=True)
    for cell in sheet[1]:
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center')

    # Заполняем строки данными по каждому заказу
    for order, user in orders_with_users:
        # Получаем товары для текущего заказа
        order_items = items_by_order_id.get(order.id, [])
        
        # Формируем строку с составом заказа (каждый товар с новой строки)
        items_str_list = [f"{item.product_name} ({int(item.product_price)} руб.)" for item in order_items]
        items_str = "\n".join(items_str_list)
        
        # Считаем общую сумму заказа
        total_price = sum(item.product_price for item in order_items)

        # Формируем строку для записи в Excel
        row_data = [
            order.id,
            ORDER_STATUSES.get(order.status, order.status), # Текстовый статус
            user.tg_id,
            user.username or "N/A",
            order.recipient_full_name or "N/A",
            order.recipient_phone_number or "N/A",
            order.delivery_pickup_point or "N/A",
            order.cdek_track_number or "N/A",
            items_str,
            int(total_price)
        ]
        sheet.append(row_data)

    # Автоматически подбираем ширину столбцов по самому длинному значению
    for column_cells in sheet.columns:
        # Берем длину первой строки в ячейке (актуально для состава заказа)
        length = max(len(str(cell.value).split('\n')[0]) for cell in column_cells)
        # Устанавливаем ширину с небольшим запасом
        sheet.column_dimensions[column_cells[0].column_letter].width = length + 4

    # Сохраняем книгу Excel в объект BytesIO в памяти
    file_in_memory = BytesIO()
    workbook.save(file_in_memory)
    file_in_memory.seek(0)  # Перемещаем "курсор" в начало файла
    
    return file_in_memory