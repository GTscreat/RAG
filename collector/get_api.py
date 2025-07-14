import os
import hashlib
import requests
<<<<<<< HEAD
from datetime import datetime, timezone
=======
from datetime import datetime, timedelta, timezone
>>>>>>> af9f7c1306457baccdb18a196f05e72add56f907
from dotenv import load_dotenv
from db import SessionLocal, Content

load_dotenv()

# Ֆայլային պահոց էջի համարի համար
def get_last_page(filename="last_page.txt"):
    try:
        with open(filename, "r") as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return 1  # Եթե ֆայլը չկա կամ վնասված է, սկսում ենք 1-ից

def save_last_page(page, filename="last_page.txt"):
    with open(filename, "w") as f:
        f.write(str(page))

def fetch_articles():
    secret = os.getenv("TOKEN_APP_KEY")
<<<<<<< HEAD
    expected_token = hashlib.sha256(f"{secret}{datetime.now(timezone.utc).strftime('%Y-%m-%d')}".encode()).hexdigest()
    # yesterday = datetime.now() - timedelta(days=1)
    # expected_token = hashlib.sha256(f"{secret}{yesterday.strftime('%Y-%m-%d')}".encode()).hexdigest()
    print(expected_token)
    url = (
        "http://185.133.248.60/api/v1/articles"
        "?per_page=10&page=2"
        "&websites=azatutyun.am,1lurer.am"
        "&from=2025-07-11&to=2025-07-11"
=======
    expected_token = hashlib.sha256(f"{secret}{datetime.now().strftime('%Y-%m-%d')}".encode()).hexdigest()
    yesterday = datetime.now() - timedelta(days=1)
    # expected_token = hashlib.sha256(f"{secret}{yesterday.strftime('%Y-%m-%d')}".encode()).hexdigest()
    
    # Ստանում ենք նախորդ էջը
    current_page = get_last_page()
    
    url = (
        "http://185.133.248.60/api/v1/articles"
        f"?per_page=30&page={current_page}"
        "&websites=news.am,1lurer.am,armenpress.am"
        f"&from={yesterday.strftime('%Y-%m-%d')}"
        f"&to={yesterday.strftime('%Y-%m-%d')}"
>>>>>>> af9f7c1306457baccdb18a196f05e72add56f907
        f"&token={expected_token}"
    )

    response = requests.get(url)
    if response.status_code != 200:
        print("❌ Սխալ հարցման ժամանակ:", response.status_code, response.text)
        return None

    # Հաջող հարցման դեպքում պահում ենք հաջորդ էջը
    save_last_page(current_page + 1)

    data = response.json()
    return data

def insert_articles_to_db(new_articles):
    session = SessionLocal()
    count_new, count_existing = 0, 0

    # Եթե նոր հոդվածները dict են՝ ստանում ենք data դաշտը
    if isinstance(new_articles, dict):
        articles_to_add = new_articles.get('data', new_articles)
    else:
        articles_to_add = new_articles

    for art in articles_to_add:
        # Ստուգում ենք՝ արդեն կա՞ նույն id-ով հոդված
        exists = session.query(Content).filter_by(id=art.get("id")).first()
        if not exists:
            c = Content(
                id=art.get("id"),
                website=art.get("website"),
                title=art.get("title"),
                content=art.get("content"),
                url=art.get("url"),
                meta=art.get("meta"),
                published_at=art.get("published_at"),
            )
            session.add(c)
            count_new += 1
        else:
            count_existing += 1
    session.commit()
    session.close()
    print(f"✅ Նոր հոդվածներ ավելացվեց: {count_new} | 🔁 Կրկնվող հոդվածներ չավելացվեցին: {count_existing}")

if __name__ == "__main__":
    articles = fetch_articles()
    if articles:
        insert_articles_to_db(articles)




# import os
# import hashlib
# import requests
# from datetime import datetime, timedelta, timezone
# from dotenv import load_dotenv
# from db import SessionLocal, Content

# load_dotenv()

# def fetch_articles():
#     secret = os.getenv("TOKEN_APP_KEY")
#     # expected_token = hashlib.sha256(f"{secret}{datetime.now().strftime('%Y-%m-%d')}".encode()).hexdigest()
#     yesterday = datetime.now() - timedelta(days=1)
#     expected_token = hashlib.sha256(f"{secret}{yesterday.strftime('%Y-%m-%d')}".encode()).hexdigest()
#     url = (
#         "http://185.133.248.60/api/v1/articles"
#         "?per_page=30&page=1"
#         "&websites=news.am,1lurer.am,armenpress.am,"
#         "&from=2025-07-12&to=2025-07-12"
#         f"&token={expected_token}"
#     )
#     response = requests.get(url)
#     if response.status_code != 200:
#         print("Սխալ հարցման ժամանակ:", response.status_code, response.text)
#         return None
#     data = response.json()
#     return data

# def insert_articles_to_db(new_articles):
#     session = SessionLocal()
#     count_new, count_existing = 0, 0

#     # Եթե նոր հոդվածները dict է՝ ստանում ենք data դաշտը
#     if isinstance(new_articles, dict):
#         articles_to_add = new_articles.get('data', new_articles)
#     else:
#         articles_to_add = new_articles

#     for art in articles_to_add:
#         # Ստուգում ենք՝ արդեն կա՞ նույն id-ով հոդված
#         exists = session.query(Content).filter_by(id=art.get("id")).first()
#         if not exists:
#             c = Content(
#                 id=art.get("id"),
#                 website=art.get("website"),
#                 title=art.get("title"),
#                 content=art.get("content"),
#                 url=art.get("url"),
#                 meta=art.get("meta"),
#                 published_at=art.get("published_at"),
#             )
#             session.add(c)
#             count_new += 1
#         else:
#             count_existing += 1
#     session.commit()
#     session.close()
#     print(f"Նոր հոդվածներ ավելացվեց: {count_new} | Կրկնվող հոդվածներ չավելացվեցին: {count_existing}")

# if __name__ == "__main__":
#     articles = fetch_articles()
#     print(articles)
#     if articles:
#         insert_articles_to_db(articles)