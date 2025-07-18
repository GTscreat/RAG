import sqlite3
import json
import sys
import time
import os

DB_FILE = 'data/ner_class.db'
DB_FILE2 = "data/nerdatabase.db"
TABLE_NAME = 'classifications'
TABLE_NAME2 = "categories"
BATCH_SIZE = 40
API_KEY = ""

def get_api_key():
    key = API_KEY
    if not key:
        key = os.environ.get("GEMINI_API_KEY")
    if not key:
        print("Սխալ: API բանալին նշված չէ։")
        sys.exit(1)
    return key

def prepare_database():
    try:
        with sqlite3.connect(DB_FILE2) as conn:
            cursor = conn.cursor()
            cursor.execute(f"ALTER TABLE {TABLE_NAME2} ADD COLUMN ner_class_opposite INTEGER")
            print(f"'{DB_FILE}' բազայում հաջողությամբ ավելացվեց 'ner_class_opposite' սյունակը։")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            pass
        else:
            print(f"Տվյալների բազան նախապատրաստելիս սխալ առաջացավ: {e}")
            sys.exit(1)

def get_rows_to_process():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT index_code, hierarchical_path FROM {TABLE_NAME}")
        rows = cursor.fetchall()
        return rows

def build_prompt(batch):
    prompt_header = """

**Դեր:** Դու Հայաստանի հասարակական-քաղաքական կյանքին, տնտեսությանը և մշակույթին չափազանց ծանոթ ու տեղեկացված, **իշխանությանը խիստ ընդդիմադիր** հայացքներ ունեցող գլխավոր խմբագիր ես։

**Առաջադրանք:** Ես կտրամադրեմ քեզ օբյեկտների` անձանց, կազմակերպությունների և հասկացությունների խմբերի ցանկ՝ իրենց ունիկալ կոդերով։ Քո խնդիրն է յուրաքանչյուրի համար ընդդիմադիր տեսանկյունից գնահատել դրա կարևորությունն ու հանրային հետաքրքրությունը Հայաստանի լրատվական դաշտի համար՝ 0-ից 10 սանդղակով, որտեղ 0-ն ամենացածրն է, իսկ 10-ը՝ ամենաբարձրը։

Օրինակ՝ «Քաղաքականություն > Ընդդիմադիր քաղաքական գործիչներ»-ը կարող է ունենալ 10 գնահատական, մինչդեռ «Մշակույթ > Նկարիչներ, քանդակագործներ > Դեկորատորներ»-ը՝ ավելի ցածր՝ 2-3։ Գնահատումը պետք է կատարել խիստ ոճով՝ օբյեկտների խմբերի միջև տարբերակվածությունը հստակ արտացոլելու նպատակով

Պատասխանը վերադարձրու **բացառապես JSON ձևաչափով**։ Այն պետք է լինի օբյեկտների զանգված (array), որտեղ յուրաքանչյուր օբյեկտ պարունակում է երկու դաշտ՝ `index_code` (որը ես կտրամադրեմ) և քո կողմից տրված `score` (0-10 միջակայքի ամբողջ թիվ)։

Ահա գնահատման ենթակա ցանկը.
"""
    items_to_evaluate = []
    for index_code, path in batch:
        items_to_evaluate.append(f"- index_code: {index_code}, path: \"{path}\"")
    prompt_footer = "\nԽնդրում եմ տրամադրել միայն JSON զանգվածը, առանց որևէ այլ տեքստի կամ մեկնաբանության։"
    return prompt_header + "\n".join(items_to_evaluate) + prompt_footer

async def call_gemini_api(prompt, api_key):
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent?key={api_key}"
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "index_code": {"type": "STRING"},
                        "score": {"type": "INTEGER"}
                    },
                    "required": ["index_code", "score"]
                }
            }
        }
    }
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, json=payload, headers={'Content-Type': 'application/json'}) as response:
                if response.status != 200:
                    print(f"API-ից սխալ ստացվեց (կոդ {response.status}): {await response.text()}")
                    return None
                result = await response.json()
        if response.status != 200:
            print(f"API-ից սխալ ստացվեց (կոդ {response.status}): {await response.text()}")
            return None
        result = await response.json()
        if result.get('candidates') and result['candidates'][0].get('content'):
            response_text = result['candidates'][0]['content']['parts'][0]['text']
            return json.loads(response_text)
        else:
            print("API-ի պատասխանը չի պարունակում սպասվող տվյալները։")
            print("Ստացված պատասխան:", result)
            return None
    except Exception as e:
        print(f"API հարցում կատարելիս սխալ առաջացավ: {e}")
        return None

def update_batch_in_db(results):
    updates = []
    for item in results:
        try:
            score = int(item['score'])
            if 0 <= score <= 10:
                updates.append((score, item['index_code']))
            else:
                print(f"Ուշադրություն: Ստացվել է միջակայքից դուրս գնահատական ({score}) '{item['index_code']}' համար։ Այս տողը բաց կթողնվի։")
        except (ValueError, TypeError):
            print(f"Ուշադրություն: Ստացվել է անվավեր գնահատական ('{item.get('score')}') '{item['index_code']}' համար։ Այս տողը բաց կթողնվի։")
    if not updates:
        return
    with sqlite3.connect(DB_FILE2) as conn:
        cursor = conn.cursor()
        cursor.executemany(f"UPDATE {TABLE_NAME2} SET ner_class_opposite = ? WHERE code = ?", updates)
        conn.commit()
        print(f"Հաջողությամբ թարմացվեց {len(updates)} տող։")

async def main():
    api_key = get_api_key()
    prepare_database()
    rows = get_rows_to_process()
    if not rows:
        print("✅ Աղյուսակը դատարկ է։")
        return
    print(f"Ընդհանուր մշակման ենթակա է {len(rows)} տող։")
    batches = [rows[i:i + BATCH_SIZE] for i in range(0, len(rows), BATCH_SIZE)]
    for i, batch in enumerate(batches):
        print(f"\n--- Մշակվում է խմբաքանակ {i + 1}/{len(batches)} ({len(batch)} տող) ---")
        prompt = build_prompt(batch)
        results = await call_gemini_api(prompt, api_key)
        if results:
            print(f"API-ից ստացվել է {len(results)} գնահատական։")
            update_batch_in_db(results)
        else:
            print("Չհաջողվեց ստանալ գնահատականներ այս խմբաքանակի համար։")
        if i < len(batches) - 1:
            print("Սպասում ենք 5 վայրկյան մինչև հաջորդ խմբաքանակը...")
            time.sleep(2)
    print("\n✅ Աշխատանքն ավարտված է։")

import asyncio
asyncio.run(main())