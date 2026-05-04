import pandas as pd
import json
import os

cwd = r"f:\Антигравити ии\калькулятор материалов"
json_file = os.path.join(cwd, "master_materials_db.json")

if os.path.exists(json_file):
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    found = [item for item in data if '25090' in str(item.get('Название/Сорт', ''))]
    if found:
        print(f"Найдено в сводной таблице ({len(found)} записей):")
        for item in found:
            print(f"- {item['Название/Сорт']}: размер {item['Толщина/Размер']}, цена {item['Цена (с НДС)']} EUR")
    else:
        print("В сводной таблице марка RP25090 НЕ найдена. Возможно, вы еще не запустили build_materials_db.py или формат данных не совпадает.")
else:
    print("Сводная таблица еще не создана.")

print("\nПрямая проверка нового Excel файла поролона...")
excel_path = os.path.join(cwd, "цены поролон (новые) Moncor.xlsx")
try:
    df = pd.read_excel(excel_path, header=None)
    found_in_excel = False
    for index, row in df.iterrows():
        if '25090' in str(row[0]):
            found_in_excel = True
            print(f"Найдено в Excel строке {index + 1}: {list(row)}")
    if not found_in_excel:
        print("Марка RP25090 не найдена в самом Excel-файле!")
except Exception as e:
    print(f"Ошибка при чтении Excel: {e}")
