import pandas as pd
import json

df = pd.read_excel("master_materials_db.xlsx")
firenze_rows = df[df.astype(str).apply(lambda x: x.str.contains('FIRENZE', case=False, na=False)).any(axis=1)]

with open("firenze_check.txt", "w", encoding="utf-8") as f:
    if len(firenze_rows) > 0:
        f.write("Найдены строки с FIRENZE в master_materials_db.xlsx:\n")
        f.write(firenze_rows.to_string())
    else:
        f.write("FIRENZE НЕТ в master_materials_db.xlsx\n")

with open("master_materials_db.json", "r", encoding="utf-8") as jf:
    data = json.load(jf)

found_in_json = [item for item in data if "firenze" in str(item).lower()]
with open("firenze_check.txt", "a", encoding="utf-8") as f:
    if found_in_json:
        f.write("\n\nНайдены строки с FIRENZE в master_materials_db.json:\n")
        for x in found_in_json:
            f.write(str(x) + "\n")
    else:
        f.write("\n\nFIRENZE НЕТ в master_materials_db.json\n")
