import sqlite3
import json
import sys
import time
import os

# --- ԿԱՐԳԱՎՈՐՈՒՄՆԵՐ ---

# Տվյալների բազայի ֆայլի անունը
DB_FILE = 'data/ner_class.db'
# Աղյուսակի անունը
TABLE_NAME = 'classifications'
# Մեկ խմբաքանակում ուղարկվող տողերի քանակը
BATCH_SIZE = 50
# Gemini API Key. Խորհուրդ է տրվում սահմանել որպես միջավայրի փոփոխական։
# Եթե թողնեք դատարկ, կփորձի կարդալ 'GEMINI_API_KEY' միջավայրի փոփոխականը։
API_KEY = "" 

# --- ՍԿՐԻՊՏԻ ՏՐԱՄԱԲԱՆՈՒԹՅՈՒՆ ---

def get_api_key():
    """Gets the API key from the script variable or environment variable."""
    key = API_KEY
    if not key:
        key = os.environ.get("GEMINI_API_KEY")
    if not key:
        print("Սխալ: API բանալին նշված չէ։")
        print("Խնդրում ենք սահմանել այն API_KEY փոփոխականում կամ որպես 'GEMINI_API_KEY' միջավայրի փոփոխական։")
        sys.exit(1)
    return key

def prepare_database():
    """
    Նախապատրաստում է տվյալների բազան՝ ավելացնելով գնահատականի սյունակը, եթե այն գոյություն չունի։
    """
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute(f"ALTER TABLE {TABLE_NAME} ADD COLUMN ner_class_index INTEGER")
            print(f"'{DB_FILE}' բազայում հաջողությամբ ավելացվեց 'ner_class_index' սյունակը։")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            # Սա սպասելի սխալ է, եթե սյունակն արդեն գոյություն ունի։ Ուղղակի անտեսում ենք։
            pass
        else:
            # Այլ սխալի դեպքում ցուցադրում ենք այն։
            print(f"Տվյալների բազան նախապատրաստելիս սխալ առաջացավ: {e}")
            sys.exit(1)

def get_rows_to_process():
    """
    Վերցնում է աղյուսակի բոլոր տողերը՝ անկախ դրանց գնահատված լինելուց։
    """
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        # Ընտրում ենք աղյուսակի բոլոր տողերը
        cursor.execute(f"SELECT index_code, hierarchical_path FROM {TABLE_NAME}")
        rows = cursor.fetchall()
        return rows

def build_prompt(batch):
    """
    Կառուցում է հարցումը (prompt) Gemini-ի համար՝ հստակ հրահանգներով։
    """
    prompt_header = """

**Դեր:** Դու Հայաստանի հասարակական-քաղաքական կյանքին, տնտեսությանը և մշակույթին չափազանց ծանոթ ու տեղեկացված գլխավոր խմբագիր ես։

**Առաջադրանք:** Ես կտրամադրեմ քեզ օբյեկտների` անձանց, կազմակերպությունների և հասկացությունների խմբերի ցանկ՝ իրենց ունիկալ կոդերով։ Քո խնդիրն է յուրաքանչյուրի համար գնահատել դրա կարևորությունն ու հանրային հետաքրքրությունը Հայաստանի լրատվական դաշտի համար՝ 0-ից 10 սանդղակով, որտեղ 0-ն ամենացածրն է, իսկ 10-ը՝ ամենաբարձրը։

Օրինակ՝ «Քաղաքականություն > Իշխանական քաղաքական գործիչներ > Վարչապետ»-ը կարող է ունենալ 10 գնահատական, մինչդեռ «Մշակույթ > Նկարիչներ, քանդակագործներ > Դեկորատորներ»-ը՝ ավելի ցածր՝ 2-3։ Գնահատումը պետք է կատարել խիստ ոճով՝ օբյեկտների խմբերի միջև տարբերակվածությունը հստակ արտացոլելու նպատակով

Պատասխանը վերադարձրու **բացառապես JSON ձևաչափով**։ Այն պետք է լինի օբյեկտների զանգված (array), որտեղ յուրաքանչյուր օբյեկտ պարունակում է երկու դաշտ՝ `index_code` (որը ես կտրամադրեմ) և քո կողմից տրված `score` (0-10 միջակայքի ամբողջ թիվ)։

Ահա գնահատման ենթակա ցանկը.
"""
    items_to_evaluate = []
    for index_code, path in batch:
        items_to_evaluate.append(f"- index_code: {index_code}, path: \"{path}\"")
    
    prompt_footer = "\nԽնդրում եմ տրամադրել միայն JSON զանգվածը, առանց որևէ այլ տեքստի կամ մեկնաբանության։"
    
    return prompt_header + "\n".join(items_to_evaluate) + prompt_footer

async def call_gemini_api(prompt, api_key):
    """
    Ուղարկում է հարցումը Gemini API-ին և վերադարձնում է պատասխանը։
    """
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent?key={api_key}"
    
    # Հարցում ենք JSON պատասխան՝ համապատասխան սխեմայով
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
        # Using fetch API which is available in the environment
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
        
        # Քանի որ մենք պահանջել ենք կոնկրետ JSON schema, պատասխանը պետք է լինի ուղիղ տեքստի մեջ
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
    """
    Թարմացնում է տվյալների բազայի տողերը՝ ստացված գնահատականներով։
    """
    updates = []
    for item in results:
        # Ստուգում ենք, որ score-ը թիվ է և 0-10 միջակայքում
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

    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.executemany(f"UPDATE {TABLE_NAME} SET ner_class_index = ? WHERE index_code = ?", updates)
        conn.commit()
        print(f"Հաջողությամբ թարմացվեց {len(updates)} տող։")

async def main():
    """
    Գլխավոր ֆունկցիա, որը կառավարում է ամբողջ գործընթացը։
    """
    api_key = get_api_key()
    prepare_database()
    
    rows = get_rows_to_process()
    if not rows:
        print("✅ Աղյուսակը դատարկ է։")
        return
        
    print(f"Ընդհանուր մշակման ենթակա է {len(rows)} տող։")
    
    # Ստեղծում ենք խմբաքանակները
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
            
        # Դադար՝ API-ի հնարավոր սահմանափակումները չխախտելու համար
        if i < len(batches) - 1:
            print("Սպասում ենք 5 վայրկյան մինչև հաջորդ խմբաքանակը...")
            time.sleep(2)
            
    print("\n✅ Աշխատանքն ավարտված է։")
# Սկրիպտի մեկնարկը կատարվում է async միջավայրում
# To run this, you would typically use: asyncio.run(main())
# In this environment, we can just call main() if it's async.
import asyncio

asyncio.run(main())
