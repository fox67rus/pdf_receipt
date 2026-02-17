#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF-чек-мейкер: генератор чеков из CSV в PDF
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
from jinja2 import Template
from weasyprint import HTML

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

def render_html(template_path, data):
    """Подставляет данные в HTML-шаблон"""
    with open(template_path, 'r', encoding='utf-8') as f:
        template_content = f.read()
    
    template = Template(template_content)
    return template.render(**data)

def generate_pdf(html_content, output_path):
    """Генерирует PDF из HTML"""
    HTML(string=html_content).write_pdf(output_path)

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

def main():
    """Основная функция скрипта"""
    # Пути к файлам
    csv_path = 'products.csv'
    template_path = 'template.html'
    output_dir = Path('output')
    
    # Создаём папку output, если её нет
    output_dir.mkdir(exist_ok=True)
    
    # Читаем данные
    print("📖 Читаю данные из CSV...")
    items = read_csv_data(csv_path)
    
    # Подготавливаем данные для шаблона
    grand_total = sum(item['total'] for item in items)
    data = {
        'items': items,
        'date': datetime.now().strftime('%d.%m.%Y %H:%M'),
        'grand_total': f"{grand_total:,.0f}".replace(',', ' ')
    }
    
    # Рендерим HTML
    print("🎨 Генерирую HTML...")
    html_content = render_html(template_path, data)
    
    # Генерируем PDF
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    pdf_path = output_dir / f'check_{timestamp}.pdf'
    
    print(f"📄 Создаю PDF: {pdf_path}...")
    generate_pdf(html_content, str(pdf_path))
    
    print(f"✨ Готово! PDF сохранён: {pdf_path}")
    
    # Открываем PDF
    open_file(str(pdf_path))

if __name__ == '__main__':
    main()
