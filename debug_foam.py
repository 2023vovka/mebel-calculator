import pandas as pd
import os

cwd = r"f:\Антигравити ии\калькулятор материалов"
file_path = os.path.join(cwd, "ЦЕНЫ ПОРОЛОН ДЛЯ НЕТБУК ЛМ.xlsx")

try:
    df = pd.read_excel(file_path)
    with open(os.path.join(cwd, "foam_debug.txt"), "w", encoding="utf-8") as f:
        f.write("Колонки:\n")
        f.write(str(df.columns.tolist()) + "\n\n")
        f.write("Первые 10 строк:\n")
        f.write(df.head(10).to_string())
    print("Файл foam_debug.txt успешно создан. Можешь открыть его и скопировать мне содержимое.")
except Exception as e:
    print(f"Ошибка: {e}")
