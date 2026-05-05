import pandas as pd
import datetime
import re

def clean_price(price_str):
    if pd.isna(price_str) or price_str is None: 
        return None
    if isinstance(price_str, (datetime.datetime, pd.Timestamp)):
        try:
            return float(f"{price_str.month}.{price_str.day:02d}")
        except:
            pass
    s = str(price_str).lower().replace('€', '').replace('eur', '').replace(' ', '').replace('\xa0', '')
    s = s.replace(',', '.')
    match = re.search(r'\d+\.?\d*', s)
    if match:
        try:
            return float(match.group())
        except:
            return None
    return None

def test_firenze():
    df = pd.read_excel("БД ткани для ноутбук ЛМ.xlsx")
    name_cols = [c for c in df.columns if 'назван' in str(c).lower() or 'name' in str(c).lower() or 'артикул' in str(c).lower() or 'коллекц' in str(c).lower() or 'ткань' in str(c).lower()]
    price_cols = [c for c in df.columns if 'цен' in str(c).lower() or 'price' in str(c).lower()]

    if not name_cols or not price_cols:
        print("Не найдены колонки с именами или ценами!")
        return

    found = False
    for _, row in df.iterrows():
        name = row[name_cols[0]]
        if pd.notna(name) and 'firenze' in str(name).lower():
            found = True
            raw_price = row[price_cols[0]]
            cleaned = clean_price(raw_price)
            print(f"[{name}] Оригинал: {raw_price} (Тип: {type(raw_price).__name__}) ---> Очищено: {cleaned}")
            
    if not found:
        print("Ткань со словом 'firenze' вообще не найдена в Excel-файле.")

if __name__ == "__main__":
    test_firenze()
