import pandas as pd
import json

with open("truth.txt", "w", encoding="utf-8") as out:
    # 1. Проверяем XLSX
    try:
        df = pd.read_excel("master_materials_db.xlsx")
        out.write("--- В EXCEL ---\n")
        
        # Ищем litena или firenze
        mask = df.astype(str).apply(lambda x: x.str.contains('firenze|litena|9\.03', case=False, na=False)).any(axis=1)
        found_df = df[mask]
        out.write(f"Найдено совпадений: {len(found_df)}\n")
        out.write(found_df.to_string() + "\n\n")
    except Exception as e:
        out.write(f"Ошибка чтения EXCEL: {e}\n\n")

    # 2. Проверяем JSON
    try:
        with open("master_materials_db.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        out.write("--- В JSON ---\n")
        found_json = [item for item in data if 'firenze' in str(item).lower() or 'litena' in str(item).lower() or '9.03' in str(item).lower() or isinstance(item.get('Цена (с НДС)'), str) and ('202' in item.get('Цена (с НДС)') or '16' in item.get('Цена (с НДС)'))]
        out.write(f"Найдено совпадений: {len(found_json)}\n")
        for x in found_json[:20]:
            out.write(str(x) + "\n")
    except Exception as e:
        out.write(f"Ошибка чтения JSON: {e}\n\n")
