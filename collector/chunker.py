from db import SessionLocal, Embedding  # Քո db.py-ից ներմուծում

def chunk_articles_and_store(articles, max_chunk_size=512, overlap_size=256):
    """
    articles: list of dicts (content աղյուսակի օրինակով)
    Չանկերը անմիջապես ավելացնում է տվյալների բազայի Embedding աղյուսակում։
    """
    # Օգտագործում ենք 'with'՝ սեսիայի ավտոմատ և անվտանգ փակման համար
    with SessionLocal() as session:
        chunk_count = 0
        try:
            for article in articles:
                content = article.get("content", "")
                # Բաց թողնում ենք դատարկ կոնտենտով հոդվածները
                if not content:
                    continue

                start = 0
                while start < len(content):
                    end = min(start + max_chunk_size, len(content))
                    chunk_text = content[start:end]
                    
                    # Ձեր տրամաբանությունն այստեղ արդեն ճիշտ է
                    chunk = Embedding(
                        # id-ն բաց է թողնված, PostgreSQL-ը կգեներացնի այն
                        article_id=article.get("id"),
                        website=article.get("website"),
                        title=article.get("title"),
                        published_at=article.get("published_at"),
                        url=article.get("url"),
                        meta=article.get("meta"),
                        chunk_content=chunk_text,
                        chunk_start=start,
                        chunk_end=end,
                        embedding=None
                    )
                    session.add(chunk)
                    chunk_count += 1

                    # Եթե հասել ենք տեքստի վերջին, դադարեցնում ենք ցիկլը
                    if end == len(content):
                        break
                    
                    # Հաշվարկում ենք հաջորդ մեկնարկային կետը՝ համընկնումը (overlap) հաշվի առնելով
                    new_start = end - overlap_size
                    # Երաշխավորում ենք, որ ցիկլը անվերջ չի լինի
                    start = new_start if new_start > start else end

            session.commit()
            print(f"✅ Ընդհանուր ավելացված չանկեր: {chunk_count}")
        
        except Exception as e:
            print(f"❌ Սխալ տեղի ունեցավ չանկերը պահպանելիս: {e}")
            session.rollback()

# Օրինակ օգտագործման համար
if __name__ == "__main__":
    sample_article = [{
        "id": 1,
        "website": "news.am",
        "title": "Օրինակի հոդվածի վերնագիր",
        "published_at": "2025-06-24 13:30:12",
        "content": "Սա շատ երկար օրինակ տեքստ է, որը մենք կօգտագործենք հայերեն չանկերի փորձարկման համար։ " * 50,
        "url": "https://news.am/arm/news/1.html",
        "meta": {
            "image": "img/news/1.jpg",
            "iframe": None
        }
    }]
    chunk_articles_and_store(sample_article)
