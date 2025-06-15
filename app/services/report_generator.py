from io import BytesIO
from datetime import datetime
from collections import defaultdict

import openpyxl
from openpyxl.styles import Font, Alignment

from app.database.models import Order, User, OrderItem
from app.lexicon.lexicon_ru import ORDER_STATUSES

def create_orders_excel_report(orders_with_users: list[tuple[Order, User]], all_items: list[OrderItem]) -> BytesIO:
    """
    Создает Excel-отчет по заказам и возвращает его как объект BytesIO.
    
    :param orders_with_users: Список кортежей (Order, User).
    :param all_items: Список всех OrderItem.
    """
    
    items_by_order_id = defaultdict(list)
    for item in all_items:
        items_by_order_id[item.order_id].append(item)

    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Отчет по заказам"

    headers = [
        "ID Заказа", "Статус", "TG ID", "Username", "ФИО Получателя",
        "Телефон", "ПВЗ СДЭК", "Трек-номер СДЭК", "Состав заказа", "Сумма заказа (руб.)"
    ]
    sheet.append(headers)

    header_font = Font(bold=True)
    for cell in sheet[1]:
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center')

    for order, user in orders_with_users:
        order_items = items_by_order_id.get(order.id, [])
        
        items_str_list = [f"{item.product_name} ({int(item.product_price)} руб.)" for item in order_items]
        items_str = "\n".join(items_str_list)
        
        total_price = sum(item.product_price for item in order_items)

        row_data = [
            order.id,
            ORDER_STATUSES.get(order.status, order.status),
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

    for column_cells in sheet.columns:
        length = max(len(str(cell.value).split('\n')[0]) for cell in column_cells)
        sheet.column_dimensions[column_cells[0].column_letter].width = length + 4

    file_in_memory = BytesIO()
    workbook.save(file_in_memory)
    file_in_memory.seek(0)
    
    return file_in_memory