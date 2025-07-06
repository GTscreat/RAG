import os
import hashlib
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from db import SessionLocal, Content

load_dotenv()

def fetch_articles():
    secret = os.getenv("TOKEN_APP_KEY")
    expected_token = hashlib.sha256(f"{secret}{datetime.now().strftime('%Y-%m-%d')}".encode()).hexdigest()
    # yesterday = datetime.now() - timedelta(days=1)
    # expected_token = hashlib.sha256(f"{secret}{yesterday.strftime('%Y-%m-%d')}".encode()).hexdigest()
    url = (
        "http://185.133.248.60/api/v1/articles"
        "?per_page=10&page=1"
        "&websites=azatutyun.am,news.am"
        "&from=2025-06-05&to=2025-06-09"
        f"&token={expected_token}"
    )
    response = requests.get(url)
    if response.status_code != 200:
        print("Սխալ հարցման ժամանակ:", response.status_code, response.text)
        return None
    data = response.json()
    return data

def insert_articles_to_db(new_articles):
    session = SessionLocal()
    count_new, count_existing = 0, 0

    # Եթե նոր հոդվածները dict է՝ ստանում ենք data դաշտը
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
    print(f"Նոր հոդվածներ ավելացվեց: {count_new} | Կրկնվող հոդվածներ չավելացվեցին: {count_existing}")

if __name__ == "__main__":
    articles = fetch_articles()
    print(articles)
    if articles:
        insert_articles_to_db(articles)
