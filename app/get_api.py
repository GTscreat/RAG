import os
import hashlib
import requests
from datetime import datetime
import json

def fetch_articles():
    secret = os.getenv('TOKEN_APP_KEY')
    expected_token = hashlib.sha256(f"{secret}{datetime.now().strftime('%Y-%m-%d')}".encode()).hexdigest()
    url = (
        "http://185.133.248.60/api/v1/articles"
        "?per_page=3&page=1"
        "&websites=azatutyun.am,news.am"
        "&from=2025-06-27&to=2025-06-27"
        f"&token={expected_token}"
    )
    response = requests.get(url)
    if response.status_code != 200:
        print("Սխալ հարցման ժամանակ:", response.status_code, response.text)
        return None
    data = response.json()
    return data

def append_articles_to_file(new_articles, filepath="data/content.json"):
    # Կարդում ենք արդեն եղած հոդվածները (եթե կա)
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            try:
                existing = json.load(f)
            except Exception:
                existing = []
    else:
        existing = []

    # Եթե նոր հոդվածները dict է՝ ստանում ենք data դաշտը
    if isinstance(new_articles, dict):
        # Եթե ունի 'data' դաշտ՝ վերցնում ենք դա, եթե ոչ՝ ամբողջ dict
        articles_to_add = new_articles.get('data', new_articles)
    else:
        articles_to_add = new_articles

    # Ավելացնում ենք նորերը
    existing.extend(articles_to_add)

    # Գրում ենք ամբողջությամբ նորից (ավելացնում ենք վերջից)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    articles = fetch_articles()
    print(articles)
    if articles:
        append_articles_to_file(articles)
