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

def get_category_by_name(mat_name):
    lower_name = str(mat_name).lower()
    if 'ткань' in lower_name: return 'Ткань'
    if 'поролон' in lower_name or bool(re.match(r'^[a-z]{2}\d*', lower_name)): return 'Поролон'
    if 'дсп' in lower_name: return 'ДСП'
    if 'мдф' in lower_name: return 'МДФ'
    if 'фанер' in lower_name: return 'Фанера'
    return 'Неизвестно'

def main():
    st.set_page_config(page_title="Калькулятор материалов", layout="wide")
    st.title("🧮 Калькулятор стоимости материалов")
    st.markdown("Загрузите выгрузки из SketchUp и выберите точные материалы из базы.")
    
    cwd = os.path.dirname(os.path.abspath(__file__))
    db_file = os.path.join(cwd, "master_materials_db.json")
    
    if not os.path.exists(db_file):
        st.error(f"База данных `master_materials_db.json` не найдена! Убедитесь, что вы запустили скрипт сборки базы.")
        return
        
    with open(db_file, 'r', encoding='utf-8') as f:
        db = json.load(f)
        
    uploaded_files = st.file_uploader("📂 Загрузите файлы SketchUp (.csv)", type=['csv'], accept_multiple_files=True)
    
    if not uploaded_files:
        return

    # Extract all unique materials and process file data
    files_data = [] # {filename, grouped_items: {(name, thick): area}}
    unique_items = set()
    
    for file in uploaded_files:
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
            unique_items.add(key)
            
        files_data.append({"name": file.name, "data": grouped_materials})

    # UI for mapping
    st.header("⚙️ Настройка материалов для проекта")
    
    # Track final mapped DB items
    mapped_db_items = {} # key: (mat_name, mat_thick), value: db_item_dict
    
    for (mat_name, mat_thick) in sorted(list(unique_items)):
        cat = get_category_by_name(mat_name)
        st.subheader(f"► Из файла: {mat_name} (Толщина: {mat_thick}мм)")
        
        # Filtering DB
        if cat == 'Ткань':
            fabric_vendors = sorted(list(set([i['Производитель'] for i in db if 'ткань' in str(i.get('Категория','')).lower()])))
            col1, col2 = st.columns(2)
            with col1:
                vendor_key = f"vendor_{mat_name}_{mat_thick}"
                if vendor_key not in st.session_state:
                    st.session_state[vendor_key] = fabric_vendors[0] if fabric_vendors else "Неизвестно"
                selected_vendor = st.selectbox("Производитель:", fabric_vendors, key=vendor_key)
                
            with col2:
                filtered_fabrics = [i for i in db if 'ткань' in str(i.get('Категория','')).lower() and i['Производитель'] == selected_vendor]
                fabric_options = {f"{i['Название/Сорт']} - {i['Цена (с НДС)']} €": i for i in filtered_fabrics}
                if fabric_options:
                    selected_fab_label = st.selectbox("Название ткани:", list(fabric_options.keys()), key=f"mat_{mat_name}_{mat_thick}")
                    mapped_db_items[(mat_name, mat_thick)] = fabric_options[selected_fab_label]
                else:
                    st.warning("Нет тканей у этого производителя.")
        else:
            # Plates & Foam
            target_thick = parse_thickness(mat_thick)
            
            exact_matches = []
            all_cat_matches = []
            
            for item in db:
                db_cat = str(item.get('Категория', '')).lower()
                db_subcat = str(item.get('Подкатегория', '')).lower()
                db_name = str(item.get('Название/Сорт', '')).lower()
                
                is_correct_cat = False
                if cat == 'Поролон' and 'поролон' in db_cat: is_correct_cat = True
                elif cat == 'ДСП' and ('дсп' in db_cat or 'дсп' in db_subcat or 'дсп' in db_name): is_correct_cat = True
                elif cat == 'МДФ' and ('мдф' in db_cat or 'мдф' in db_subcat or 'мдф' in db_name): is_correct_cat = True
                elif cat == 'Фанера' and 'фанера' in db_cat: is_correct_cat = True
                
                if is_correct_cat:
                    all_cat_matches.append(item)
                    if parse_thickness(item.get('Толщина', '-')) == target_thick:
                        exact_matches.append(item)
                        
            # If no exact thickness matches, show warning and show all category matches
            if exact_matches:
                options_list = exact_matches
            else:
                if all_cat_matches:
                    st.warning(f"Толщина {mat_thick}мм не найдена в базе для категории '{cat}'. Пожалуйста, выберите аналог для замены.")
                    options_list = all_cat_matches
                else:
                    st.error(f"В базе вообще нет материалов категории '{cat}'.")
                    options_list = []
                    
            if options_list:
                options_dict = {f"{i['Название/Сорт']} [Размер: {i.get('Размер', '-')}, Толщина: {i.get('Толщина', '-')}мм] - {i['Цена (с НДС)']} €": i for i in options_list}
                
                default_idx = 0
                if cat == 'Поролон':
                    for idx, label in enumerate(options_dict.keys()):
                        if mat_name.lower() in label.lower():
                            default_idx = idx
                            break

                selected_plate_label = st.selectbox("Выберите материал из базы:", list(options_dict.keys()), index=default_idx, key=f"mat_{mat_name}_{mat_thick}")
                mapped_db_items[(mat_name, mat_thick)] = options_dict[selected_plate_label]
                
    st.write("---")
    if st.button("🚀 ВЫПОЛНИТЬ РАСЧЕТ", type="primary", use_container_width=True):
        st.session_state.calculated = True
        
    if getattr(st.session_state, 'calculated', False):
        st.header("📊 Результаты расчета")
        global_total = 0.0
        project_summaries = []
        
        for file_info in files_data:
            st.subheader(f"📄 Проект: {file_info['name']}")
            
            results = []
            file_cost = 0.0
            
            for (mat_name, mat_thick), total_area in file_info['data'].items():
                db_match = mapped_db_items.get((mat_name, mat_thick))
                if db_match:
                    db_name = db_match['Название/Сорт']
                    db_price = db_match['Цена (с НДС)']
                    is_fabric_cat = 'ткань' in str(db_match.get('Категория', '')).lower()
                    
                    if is_fabric_cat:
                        try: width_mm = float(db_match.get('Ширина материала', 1400))
                        except: width_mm = 1400.0
                        width_m = width_mm / 1000.0
                        linear_meters = total_area / width_m
                        item_cost = linear_meters * db_price
                        file_cost += item_cost
                        
                        results.append({
                            "Материал из файла": mat_name,
                            "Выбрано из базы": db_name,
                            "Потребность": f"{linear_meters:.2f} пог.м",
                            "Цена за ед.": f"{db_price} €",
                            "Итого (€)": round(item_cost, 2)
                        })
                    else:
                        sheet_area = parse_dimensions(db_match.get('Размер', '-'))
                        if not sheet_area:
                            if 'фанера' in str(db_match.get('Категория', '')).lower(): sheet_area = 1.525 * 1.525
                            else: sheet_area = 1.0
                        sheets_needed = total_area / sheet_area
                        item_cost = sheets_needed * db_price
                        file_cost += item_cost
                        
                        results.append({
                            "Материал из файла": f"{mat_name} (Толщ: {mat_thick}мм)",
                            "Выбрано из базы": db_name,
                            "Потребность": f"{sheets_needed:.2f} шт.",
                            "Цена за ед.": f"{db_price} €",
                            "Итого (€)": round(item_cost, 2)
                        })
                else:
                    results.append({
                        "Материал из файла": f"{mat_name} (Толщ: {mat_thick}мм)",
                        "Выбрано из базы": "❌ НЕ ВЫБРАНО",
                        "Потребность": f"{total_area:.3f} м2",
                        "Цена за ед.": "0 €",
                        "Итого (€)": 0.0
                    })
            
            if results:
                df_res = pd.DataFrame(results)
                st.dataframe(df_res, use_container_width=True)
            
            st.markdown(f"**Стоимость проекта [{file_info['name']}]:** `{file_cost:.2f} €`")
            st.write("---")
            
            global_total += file_cost
            project_summaries.append((file_info['name'], file_cost))
            
        st.header("📋 Сводная информация по всем проектам")
        for name, cost in project_summaries:
            st.write(f"- **{name}**: `{cost:.2f} €`")
            
        st.markdown(f'''
        <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; border-left: 5px solid #ff4b4b; margin-top: 20px;">
            <h2 style="color: #31333F; margin:0;">ОБЩАЯ СТОИМОСТЬ ВСЕХ ПРОЕКТОВ: <span style="color: #ff4b4b;">{global_total:.2f} €</span></h2>
        </div>
        ''', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
