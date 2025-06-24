import os
import hashlib
import requests
from datetime import datetime

def fetch_articles():
    secret = os.getenv('TOKEN_APP_KEY')
    expected_token = hashlib.sha256(f"{secret}{datetime.now().strftime('%Y-%m-%d')}".encode()).hexdigest()
    url = (
        "http://185.133.248.60/api/v1/articles"
        "?per_page=10&page=1"
        "&websites=azatutyun.am,news.am"
        "&from=2025-06-24&to=2025-06-24"
        f"&token={expected_token}"
    )
    response = requests.get(url)
    if response.status_code != 200:
        print("Սխալ հարցման ժամանակ:", response.status_code, response.text)
        return None
    data = response.json()
    return data

if __name__ == "__main__":
    articles = fetch_articles()
    print(articles)
