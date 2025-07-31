import os
import hashlib
import requests
from datetime import datetime, timezone
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from db import SessionLocal, Content

load_dotenv()

def fetch_articles():
    secret = os.getenv("TOKEN_APP_KEY")
    expected_token = hashlib.sha256(f"{secret}{datetime.now(timezone.utc).strftime('%Y-%m-%d')}".encode()).hexdigest()
    # current_page = get_last_page()
    
    TIME_FORMAT = "%Y-%m-%d %H:%M"
    now = datetime.now(timezone.utc)
    to_time = now.strftime(TIME_FORMAT)
    from_time = (now - timedelta(minutes=15)).strftime(TIME_FORMAT)

    url = (
        "http://185.133.248.60/api/v1/articles"
        "?per_page=10&page=1"
        "&websites=news.am,1lurer.am,armenpress.am,armtimes.com,hraparak.am,arm.sputniknews.ru"
        f"&from={from_time}&to={to_time}"
        f"&token={expected_token}"
    )
    
    response = requests.get(url)
    if response.status_code != 200:
        print("❌ Սխալ հարցման ժամանակ:", response.status_code, response.text)
        return None

    # # Հաջող հարցման դեպքում պահում ենք հաջորդ էջը
    # save_last_page(current_page + 1)

    data = response.json()
    return data

def insert_articles_to_db(new_articles):
    # Ստեղծում ենք նոր ցուցակ՝ իրականում ավելացված հոդվածները պահելու համար
    successfully_inserted_articles = []
    
    with SessionLocal() as session:
        try:
            count_new, count_existing, count_skipped = 0, 0, 0

            # ... (կոդի մնացած մասը մնում է նույնը) ...
            articles_to_add = new_articles.get('data', new_articles) if isinstance(new_articles, dict) else new_articles

            for art in articles_to_add:
                content_text = art.get("content")
                if not content_text or str(content_text).strip() == "":
                    count_skipped += 1
                    continue
                
                exists = session.query(Content).filter(Content.id == art.get("id")).first()
                if not exists:
                    c = Content(
                        id=art.get("id"),
                        website=art.get("website"),
                        title=art.get("title"),
                        content=content_text,
                        url=art.get("url"),
                        meta=art.get("meta"),
                        published_at=art.get("published_at"),
                    )
                    session.add(c)
                    count_new += 1
                    # Ավելացնում ենք հոդվածը հաջողվածների ցուցակին
                    successfully_inserted_articles.append(art)
                else:
                    count_existing += 1
            
            session.commit()
            print(f"✅ Նոր հոդվածներ ավելացվեց: {count_new} | 🔁 Կրկնվող հոդվածներ չավելացվեցին: {count_existing} | ⏭️ Դատարկ հոդվածներ բաց թողնվեցին: {count_skipped}")

        except Exception as e:
            print(f"❌ Սխալ տեղի ունեցավ տվյալներն ավելացնելիս: {e}")
            session.rollback()

    # Վերադարձնում ենք միայն այն հոդվածները, որոնք իրականում ավելացվել են
    return successfully_inserted_articles

if __name__ == "__main__":
    articles = fetch_articles()
    if articles:
        insert_articles_to_db(articles)