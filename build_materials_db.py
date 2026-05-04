import pandas as pd
import docx
import os
import json
import re
import traceback

def clean_price(price_str):
    if pd.isna(price_str) or price_str is None: 
        return None
    s = str(price_str).lower().replace('€', '').replace('eur', '').replace(' ', '').replace('\xa0', '')
    s = s.replace(',', '.')
    match = re.search(r'\d+\.?\d*', s)
    if match:
        try:
            return float(match.group())
        except:
            return None
    return None

def extract_size(text):
    text = str(text)
    match = re.search(r'(\d+[\.,]?\d*\s*(мм|mm|см|cm|м|m))|(\d+\s*[xх]\s*\d+)', text, re.IGNORECASE)
    if match:
        return match.group(0)
    return "-"

def determine_plywood_subcategory(name):
    n = name.lower()
    if 'обрезки' in n or 'rumbula' in n or 'stock' in n or 'спецпредлож' in n:
        return "Спецпредложения: Обрезки (Rumbula Stock)"
    if 'f/w' in n or 'tex' in n or 'сетч' in n:
        return "Фанера с сетчатым покрытием (Riga Tex / F/W)"
    if 'f/f' in n or 'ламин' in n or 'riga wood' in n:
        return "Ламинированная фанера (Riga Wood / F/F)"
    if 'bb' in n or 'wg' in n or 'шлиф' in n:
        return "Шлифованная березовая фанера (Сорт BB/WG)"
    return "Стандартная фанера"

def process_fabric(filepath):
    print(f"Читаем файл: {os.path.basename(filepath)}")
    df = pd.read_excel(filepath)
    records = []
    
    price_cols = [c for c in df.columns if 'цен' in str(c).lower() or 'price' in str(c).lower()]
    name_cols = [c for c in df.columns if 'назван' in str(c).lower() or 'name' in str(c).lower() or 'артикул' in str(c).lower() or 'коллекц' in str(c).lower() or 'ткань' in str(c).lower()]
    vendor_cols = [c for c in df.columns if 'производ' in str(c).lower() or 'поставщ' in str(c).lower() or 'бренд' in str(c).lower() or 'vendor' in str(c).lower()]
    
    if not price_cols: price_cols = [df.columns[-1]] 
    if not name_cols: name_cols = [df.columns[0]] 

    for _, row in df.iterrows():
        name = row[name_cols[0]]
        price = clean_price(row[price_cols[0]])
        vendor = row[vendor_cols[0]] if vendor_cols else "Неизвестно"
        
        if pd.notna(name) and str(name).strip() and price is not None:
            records.append({
                "Категория": "Ткань",
                "Подкатегория": "-",
                "Производитель": str(vendor).strip() if pd.notna(vendor) and str(vendor).strip() else "Неизвестно",
                "Название/Сорт": str(name).strip(),
                "Толщина": "-",
                "Размер": "-",
                "Ширина материала": "1400",
                "Единица измерения": "пог. м",
                "Цена (с НДС)": price
            })
    return records

def process_foam(filepath):
    print(f"Читаем файл: {os.path.basename(filepath)}")
    df = pd.read_excel(filepath, header=None)
    records = []
    
    is_moncor_format = False
    for _, row in df.iterrows():
        col0 = str(row[0]).strip()
        if len(row) >= 7 and re.match(r'^[a-zA-Z]{2,3}\d*', col0):
            size1 = clean_price(row[1])
            size2 = clean_price(row[2])
            thick = clean_price(row[3])
            price = clean_price(row[6])
            
            if size1 and size2 and thick and price is not None and price > 0:
                is_moncor_format = True
                
                records.append({
                    "Категория": "Поролон",
                    "Подкатегория": "-",
                    "Производитель": "SIA Moncor",
                    "Название/Сорт": col0,
                    "Толщина": str(int(thick)),
                    "Размер": f"{int(size1)}x{int(size2)}",
                    "Ширина материала": str(min(int(size1), int(size2))),
                    "Единица измерения": "лист",
                    "Цена (с НДС)": price
                })

    if is_moncor_format:
        return records

    df = pd.read_excel(filepath)
    price_cols = [c for c in df.columns if 'цен' in str(c).lower() or 'price' in str(c).lower()]
    name_cols = [c for c in df.columns if 'марка' in str(c).lower() or 'назван' in str(c).lower() or 'тип' in str(c).lower() or 'поролон' in str(c).lower()]
    thick_cols = [c for c in df.columns if 'толщин' in str(c).lower() or 'мм' in str(c).lower() or 'h' == str(c).lower().strip()]
    size_cols = [c for c in df.columns if 'размер' in str(c).lower() or 'габарит' in str(c).lower() or 'лист' in str(c).lower()]
    vendor_cols = [c for c in df.columns if 'производ' in str(c).lower() or 'поставщ' in str(c).lower()]

    if not price_cols: price_cols = [df.columns[-1]]
    if not name_cols: name_cols = [df.columns[0]]

    for _, row in df.iterrows():
        name = row[name_cols[0]]
        price = clean_price(row[price_cols[0]])
        vendor = row[vendor_cols[0]] if vendor_cols else "SIA Moncor"
        
        thickness = row[thick_cols[0]] if thick_cols else "-"
        size = row[size_cols[0]] if size_cols else "-"
        
        if pd.notna(name) and str(name).strip() and price is not None:
            sz = str(size).strip() if str(size).strip() != "nan" else "-"
            
            w_match = re.search(r'(\d+)\s*[xхX]\s*(\d+)', sz)
            w_val = str(min(int(w_match.group(1)), int(w_match.group(2)))) if w_match else "-"
            
            records.append({
                "Категория": "Поролон",
                "Подкатегория": "-",
                "Производитель": str(vendor).strip() if pd.notna(vendor) else "SIA Moncor",
                "Название/Сорт": str(name).strip(),
                "Толщина": str(thickness).strip() if str(thickness).strip() != "nan" else "-",
                "Размер": sz,
                "Ширина материала": w_val,
                "Единица измерения": "лист",
                "Цена (с НДС)": price
            })
    return records

def extract_docx_tables(filepath, default_category):
    print(f"Читаем файл: {os.path.basename(filepath)}")
    doc = docx.Document(filepath)
    records = []
    
    vendor = "Неизвестно"
    if "фанер" in filepath.lower() or "латвия" in filepath.lower():
        vendor = "Latvijas Finieris / Riga Wood"
    
    for table in doc.tables:
        for row in table.rows:
            cells = [cell.text.strip().replace('\n', ' ') for cell in row.cells]
            clean_cells = []
            for c in cells:
                if c and (not clean_cells or clean_cells[-1] != c):
                    clean_cells.append(c)
            
            if len(clean_cells) < 2:
                continue
                
            prices = []
            price_indices = []
            for i, c in enumerate(clean_cells):
                cp = clean_price(c)
                if cp is not None and cp > 0:
                    prices.append(cp)
                    price_indices.append(i)
            
            if prices:
                price = prices[-1] 
                price_idx = price_indices[-1]
                
                name_parts = clean_cells[:price_idx]
                name = " ".join(name_parts).strip()
                if not name:
                    name = "Неизвестно"
                
                parsed_size = "-"
                size_match = re.search(r'(\d+\s*[xхX]\s*\d+)', name)
                if size_match:
                    parsed_size = size_match.group(1).replace(' ', '')
                
                parsed_thick = "-"
                thick_match_mm = re.search(r'(\d+[\.,]?\d*)\s*(?:мм|mm)', name, re.IGNORECASE)
                if thick_match_mm:
                    parsed_thick = thick_match_mm.group(1)
                else:
                    name_without_size = name.replace(size_match.group(1), '') if size_match else name
                    thick_match_first = re.search(r'(?<!\d)(\d+[\.,]?\d*)(?!\d)', name_without_size)
                    if thick_match_first:
                        parsed_thick = thick_match_first.group(1)

                category = default_category
                subcategory = "-"
                
                name_lower = name.lower()
                if 'дсп' in name_lower: 
                    category = 'ДСП'
                elif 'мдф' in name_lower: 
                    category = 'МДФ'
                elif 'фанера' in name_lower or default_category == 'Фанера': 
                    category = 'Фанера'
                    subcategory = determine_plywood_subcategory(name)
                    name = "Стандартная фанера"
                
                unit = "лист"
                if "обрезки" in name_lower or "спецпредлож" in name_lower: 
                    unit = "шт" 

                w_match = re.search(r'(\d+)\s*[xхX]\s*(\d+)', parsed_size)
                w_val = str(min(int(w_match.group(1)), int(w_match.group(2)))) if w_match else "-"

                records.append({
                    "Категория": category,
                    "Подкатегория": subcategory,
                    "Производитель": vendor,
                    "Название/Сорт": name,
                    "Толщина": parsed_thick,
                    "Размер": parsed_size,
                    "Ширина материала": w_val,
                    "Единица измерения": unit,
                    "Цена (с НДС)": price
                })
    return records

def get_mdf_dsp_records():
    records = []
    
    # МДФ
    mdf_data = [
        ("3мм", 17.88),
        ("6мм", 31.52),
        ("8мм", 33.39),
        ("10мм", 40.14)
    ]
    for thick, price in mdf_data:
        num_thick = thick.replace('мм', '')
        records.append({
            "Категория": "Плитные материалы",
            "Подкатегория": "МДФ",
            "Производитель": "Неизвестно",
            "Название/Сорт": f"МДФ {thick}",
            "Толщина": num_thick,
            "Размер": "2800х2070",
            "Ширина материала": "2070",
            "Единица измерения": "лист",
            "Цена (с НДС)": price
        })
        
    # ДСП
    dsp_data = [
        ("12мм", 29.62),
        ("15мм", 30.97),
        ("16мм", 36.19),
        ("18мм", 41.25)
    ]
    for thick, price in dsp_data:
        num_thick = thick.replace('мм', '')
        records.append({
            "Категория": "Плитные материалы",
            "Подкатегория": "ДСП",
            "Производитель": "Неизвестно",
            "Название/Сорт": f"ДСП {thick}",
            "Толщина": num_thick,
            "Размер": "2800х2070",
            "Ширина материала": "2070",
            "Единица измерения": "лист",
            "Цена (с НДС)": price
        })
        
    return records

def main():
    cwd = r"f:\Антигравити ии\калькулятор материалов"
    all_records = []
    
    try:
        all_records.extend(process_fabric(os.path.join(cwd, "БД ткани для ноутбук ЛМ.xlsx")))
    except Exception as e:
        print(f"Ошибка при обработке ткани: {e}")
        traceback.print_exc()
        
    try:
        all_records.extend(process_foam(os.path.join(cwd, "цены поролон (новые) Moncor.xlsx")))
    except Exception as e:
        print(f"Ошибка при обработке поролона: {e}")
        traceback.print_exc()
        
    try:
        all_records.extend(extract_docx_tables(os.path.join(cwd, "Прайс-лист на фанеру (Латвия).docx"), "Фанера"))
    except Exception as e:
        print(f"Ошибка при обработке фанеры: {e}")
        traceback.print_exc()
        
    try:
        print("Добавляем новые цены на МДФ и ДСП...")
        all_records.extend(get_mdf_dsp_records())
    except Exception as e:
        print(f"Ошибка при добавлении МДФ/ДСП: {e}")
        traceback.print_exc()

    if not all_records:
        print("Не удалось извлечь данные из файлов. Проверьте форматы файлов.")
        return

    df = pd.DataFrame(all_records)
    
    # Расставляем колонки в удобном порядке
    cols = ["Категория", "Подкатегория", "Производитель", "Название/Сорт", "Толщина", "Размер", "Ширина материала", "Единица измерения", "Цена (с НДС)"]
    df = df[cols]
    
    df = df.drop_duplicates()
    
    print(f"\nСобрано записей: {len(df)}")
    
    excel_path = os.path.join(cwd, "master_materials_db.xlsx")
    df.to_excel(excel_path, index=False)
    
    json_path = os.path.join(cwd, "master_materials_db.json")
    df.to_json(json_path, orient='records', force_ascii=False, indent=4)
    
    print("\nСводная база успешно создана!")
    print(f"Excel: {excel_path}")
    print(f"JSON:  {json_path}")

if __name__ == "__main__":
    main()
