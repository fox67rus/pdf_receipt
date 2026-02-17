#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF-чек-мейкер: генератор чеков из CSV в PDF
Версия: с использованием ReportLab
"""

import csv
import os
import platform
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Настройка кодировки для Windows
if platform.system() == 'Windows':
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8')
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def read_csv_data(csv_path):
    """Читает данные из CSV файла"""
    items = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            items.append({
                'product': row['product'],
                'price': float(row['price']),
                'qty': int(row['qty']),
                'total': float(row['price']) * int(row['qty'])
            })
    return items

def register_cyrillic_fonts():
    """Регистрирует шрифты с поддержкой кириллицы"""
    system = platform.system()
    
    if system == 'Windows':
        # Используем системные шрифты Windows
        fonts_dir = os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts')
        arial_path = os.path.join(fonts_dir, 'arial.ttf')
        arial_bd_path = os.path.join(fonts_dir, 'arialbd.ttf')
        
        if os.path.exists(arial_path):
            pdfmetrics.registerFont(TTFont('Arial', arial_path))
        if os.path.exists(arial_bd_path):
            pdfmetrics.registerFont(TTFont('Arial-Bold', arial_bd_path))
        return 'Arial', 'Arial-Bold'
    elif system == 'Darwin':  # macOS
        # Попробуем найти Arial в стандартных местах macOS
        arial_paths = [
            '/Library/Fonts/Arial.ttf',
            '/System/Library/Fonts/Supplemental/Arial.ttf',
        ]
        for path in arial_paths:
            if os.path.exists(path):
                pdfmetrics.registerFont(TTFont('Arial', path))
                return 'Arial', 'Arial-Bold'
    else:  # Linux
        # Попробуем найти DejaVu Sans или Arial
        arial_paths = [
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
            '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
        ]
        for path in arial_paths:
            if os.path.exists(path):
                pdfmetrics.registerFont(TTFont('Arial', path))
                return 'Arial', 'Arial-Bold'
    
    # Если ничего не найдено, используем стандартные шрифты
    return 'Helvetica', 'Helvetica-Bold'

def generate_pdf_reportlab(items, output_path):
    """Генерирует PDF из данных используя ReportLab"""
    # Регистрируем шрифты с поддержкой кириллицы
    font_name, font_bold = register_cyrillic_fonts()
    
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    # Элементы документа
    elements = []
    styles = getSampleStyleSheet()
    
    # Заголовок
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=30,
        alignment=1,  # Центрирование
        fontName=font_bold
    )
    elements.append(Paragraph("ЧЕК ПОКУПКИ", title_style))
    
    # Дата
    date_style = ParagraphStyle(
        'Date',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.grey,
        alignment=1,
        fontName=font_name
    )
    current_date = datetime.now().strftime('%d.%m.%Y %H:%M')
    elements.append(Paragraph(f"Дата: {current_date}", date_style))
    elements.append(Spacer(1, 1*cm))
    
    # Подготовка данных для таблицы
    table_data = [['Товар', 'Цена', 'Кол-во', 'Сумма']]
    grand_total = 0
    
    for item in items:
        table_data.append([
            item['product'],
            f"{item['price']:,.0f} ₽".replace(',', ' '),
            str(item['qty']),
            f"{item['total']:,.0f} ₽".replace(',', ' ')
        ])
        grand_total += item['total']
    
    # Создание таблицы
    table = Table(table_data, colWidths=[8*cm, 3*cm, 2*cm, 3*cm])
    table.setStyle(TableStyle([
        # Заголовок
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), font_bold),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        
        # Тело таблицы
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('FONTNAME', (0, 1), (-1, -1), font_name),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        
        # Границы
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('LINEABOVE', (0, 0), (-1, 0), 2, colors.HexColor('#34495e')),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 0.5*cm))
    
    # Итого
    total_style = ParagraphStyle(
        'Total',
        parent=styles['Normal'],
        fontSize=16,
        textColor=colors.HexColor('#2c3e50'),
        alignment=2,  # Выравнивание вправо
        fontName=font_bold
    )
    total_text = f"ИТОГО: {grand_total:,.0f} ₽".replace(',', ' ')
    elements.append(Paragraph(total_text, total_style))
    
    # Генерация PDF
    doc.build(elements)

def open_file(filepath):
    """Автоматически открывает файл в системе"""
    system = platform.system()
    try:
        if system == 'Darwin':  # macOS
            subprocess.run(['open', filepath])
        elif system == 'Windows':
            os.startfile(filepath)
        else:  # Linux
            subprocess.run(['xdg-open', filepath])
        print(f"✅ PDF открыт автоматически")
    except Exception as e:
        print(f"⚠️ Не удалось открыть PDF автоматически: {e}")
        print(f"   Файл сохранён по пути: {filepath}")

def main():
    """Основная функция скрипта"""
    # Пути к файлам
    csv_path = 'products.csv'
    output_dir = Path('output')
    
    # Создаём папку output, если её нет
    output_dir.mkdir(exist_ok=True)
    
    # Читаем данные
    print("📖 Читаю данные из CSV...")
    items = read_csv_data(csv_path)
    print(f"   Найдено товаров: {len(items)}")
    
    # Генерируем PDF
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    pdf_path = output_dir / f'check_{timestamp}.pdf'
    
    print(f"📄 Создаю PDF: {pdf_path}...")
    generate_pdf_reportlab(items, pdf_path)
    
    print(f"✨ Готово! PDF сохранён: {pdf_path}")
    
    # Открываем PDF
    open_file(str(pdf_path))

if __name__ == '__main__':
    main()
