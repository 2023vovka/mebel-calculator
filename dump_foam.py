import pandas as pd
import os

cwd = r"f:\Антигравити ии\калькулятор материалов"
file_path = os.path.join(cwd, "ЦЕНЫ ПОРОЛОН ДЛЯ НЕТБУК ЛМ.xlsx")

try:
    # Читаем все листы
    xls = pd.ExcelFile(file_path)
    with open(os.path.join(cwd, "foam_full_debug.txt"), "w", encoding="utf-8") as f:
        f.write(f"Листы в файле: {xls.sheet_names}\n\n")
        
        for sheet in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet, header=None)
            f.write(f"--- Лист: {sheet} ---\n")
            # Выводим первые 50 строк, убирая пустые
            df_clean = df.dropna(how='all')
            f.write(df_clean.head(40).to_string())
            f.write("\n\n")
            
    print("Файл foam_full_debug.txt успешно создан!")
except Exception as e:
    print(f"Ошибка: {e}")
