import streamlit as st
import pandas as pd
import json
import os
import re

def parse_dimensions(dim_string):
    """Пытается извлечь размеры листа (ШхВ) из строки для расчета площади"""
    if not dim_string or str(dim_string).lower() in ['nan', '-']:
        return None
        
    match = re.search(r'(\d+)\s*[xх]\s*(\d+)', str(dim_string), re.IGNORECASE)
    if match:
        w, h = float(match.group(1)), float(match.group(2))
        return (w * h) / 1000000.0  # в квадратные метры
    return None

def parse_thickness(t_str):
    if not t_str or str(t_str).lower() == 'nan' or str(t_str).strip() == '-':
        return -1.0
    s = str(t_str).replace(',', '.').strip()
    try:
        return float(s)
    except:
        return -1.0

def match_material(mat_name, mat_thick, db):
    """Ищет материал в базе данных по имени и толщине, используя новую структуру БД"""
    mat_name_lower = str(mat_name).lower()
    mat_thick_val = parse_thickness(mat_thick)
    
    # Эвристика для поролона
    is_foam = bool(re.match(r'^[a-z]{2}\d*', mat_name_lower)) or 'поролон' in mat_name_lower
    # Эвристика для ДСП/МДФ/Фанеры
    is_dsp = 'дсп' in mat_name_lower
    is_mdf = 'мдф' in mat_name_lower
    is_plywood = 'фанер' in mat_name_lower
    is_fabric = 'ткань' in mat_name_lower
    
    for item in db:
        db_name = str(item.get('Название/Сорт', '')).lower()
        db_cat = str(item.get('Категория', '')).lower()
        db_subcat = str(item.get('Подкатегория', '')).lower()
        
        # Получаем толщину напрямую из новой колонки 'Толщина'
        db_thick_val = parse_thickness(item.get('Толщина', '-'))
        
        # 0. Поиск ткани
        if is_fabric and 'ткань' in db_cat:
            clean_name = mat_name_lower.replace('ткань', '').strip()
            if clean_name and clean_name in db_name:
                return item
            elif mat_name_lower in db_name:
                return item
                
        # 1. Поиск поролона
        if is_foam and 'поролон' in db_cat:
            if mat_name_lower in db_name and db_thick_val == mat_thick_val:
                return item
                
        # 2. Строгий поиск Плитных материалов (ДСП, МДФ, Фанера)
        if is_dsp or is_mdf or is_plywood:
            if db_thick_val == mat_thick_val:
                if is_dsp and ('дсп' in db_subcat or 'дсп' in db_name or 'дсп' in db_cat):
                    return item
                if is_mdf and ('мдф' in db_subcat or 'мдф' in db_name or 'мдф' in db_cat):
                    return item
                if is_plywood and 'фанера' in db_cat:
                    return item
                
    return None

def process_file(file, db):
    df = pd.read_csv(file, sep=';', dtype=str)
    grouped_materials = {}
    
    for _, row in df.iterrows():
        raw_name = str(row.get('Имя материала', '')).strip()
        if raw_name == 'nan' or not raw_name:
            continue
            
        qty = float(row.get('Количество', 1))
        length = float(row.get('Длина - пильная', 0))
        width = float(row.get('Ширина - пильная', 0))
        raw_thick = str(row.get('Толщина', '')).strip()
        
        # Обработка ситуаций, когда толщина в имени, например "HR25070 10"
        match = re.match(r'(.+?)\s+(\d+)$', raw_name)
        if match:
            mat_name = match.group(1).strip()
            mat_thick = match.group(2)
        else:
            mat_name = raw_name
            mat_thick = raw_thick
            
        area_m2 = (length * width) / 1_000_000.0 * qty
        
        key = (mat_name, mat_thick)
        if key not in grouped_materials:
            grouped_materials[key] = 0.0
        grouped_materials[key] += area_m2
        
    results = []
    total_cost = 0.0
    
    for (mat_name, mat_thick), total_area in grouped_materials.items():
        db_match = match_material(mat_name, mat_thick, db)
        
        if db_match:
            db_name = db_match['Название/Сорт']
            db_price = db_match['Цена (с НДС)']
            is_fabric_cat = 'ткань' in str(db_match.get('Категория', '')).lower()
            
            if is_fabric_cat:
                try:
                    width_mm = float(db_match.get('Ширина материала', 1400))
                except:
                    width_mm = 1400.0
                    
                width_m = width_mm / 1000.0
                linear_meters = total_area / width_m
                item_cost = linear_meters * db_price
                total_cost += item_cost
                
                results.append({
                    "Материал из файла": mat_name,
                    "Найдено в БД": db_name,
                    "Потребность": f"{linear_meters:.2f} пог.м",
                    "Цена за ед.": f"{db_price} €",
                    "Итого (€)": round(item_cost, 2)
                })
            else:
                # Поиск площади листа из БД по новой колонке 'Размер'
                sheet_area = parse_dimensions(db_match.get('Размер', '-'))
                
                if not sheet_area:
                    if 'фанера' in str(db_match.get('Категория', '')).lower():
                        sheet_area = 1.525 * 1.525
                    else:
                        sheet_area = 1.0
                        
                sheets_needed = total_area / sheet_area
                item_cost = sheets_needed * db_price
                total_cost += item_cost
                
                results.append({
                    "Материал из файла": f"{mat_name} (Толщ: {mat_thick}мм)",
                    "Найдено в БД": db_name,
                    "Потребность": f"{sheets_needed:.2f} шт.",
                    "Цена за ед.": f"{db_price} €",
                    "Итого (€)": round(item_cost, 2)
                })
        else:
            results.append({
                "Материал из файла": f"{mat_name} (Толщ: {mat_thick}мм)",
                "Найдено в БД": "❌ НЕ НАЙДЕНО",
                "Потребность": f"{total_area:.3f} м2",
                "Цена за ед.": "0 €",
                "Итого (€)": 0.0
            })
            
    return results, total_cost

def main():
    st.set_page_config(page_title="Калькулятор материалов", layout="wide")
    st.title("🧮 Калькулятор стоимости материалов")
    st.markdown("Загрузите выгрузки из SketchUp в формате `.csv` для мгновенного расчета стоимости проекта.")
    
    cwd = os.path.dirname(os.path.abspath(__file__))
    db_file = os.path.join(cwd, "master_materials_db.json")
    
    if not os.path.exists(db_file):
        st.error(f"База данных `master_materials_db.json` не найдена! Убедитесь, что вы запустили скрипт сборки базы.")
        return
        
    with open(db_file, 'r', encoding='utf-8') as f:
        db = json.load(f)
        
    uploaded_files = st.file_uploader("📂 Загрузите файлы SketchUp (.csv)", type=['csv'], accept_multiple_files=True)
    
    if uploaded_files:
        global_total = 0.0
        project_summaries = []
        
        st.write("---")
        for file in uploaded_files:
            st.subheader(f"📄 Проект: {file.name}")
            
            results, file_cost = process_file(file, db)
            
            if results:
                df_res = pd.DataFrame(results)
                # Выводим таблицу
                st.dataframe(df_res, use_container_width=True)
            
            st.markdown(f"**Стоимость проекта [{file.name}]:** `{file_cost:.2f} €`")
            st.write("---")
            
            global_total += file_cost
            project_summaries.append((file.name, file_cost))
            
        # Итоговая сводка
        st.header("📋 Сводная информация по всем проектам")
        
        for name, cost in project_summaries:
            st.write(f"- **{name}**: `{cost:.2f} €`")
            
        st.markdown(f"""
        <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; border-left: 5px solid #ff4b4b; margin-top: 20px;">
            <h2 style='color: #31333F; margin:0;'>ОБЩАЯ СТОИМОСТЬ ВСЕХ ПРОЕКТОВ: <span style='color: #ff4b4b;'>{global_total:.2f} €</span></h2>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
