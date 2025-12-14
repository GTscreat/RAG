from db import SessionLocal, Embedding  # Քո db.py-ից ներմուծում

def chunk_articles_and_store(articles, max_chunk_size=512, overlap_size=256):
    """
    articles: list of SQLAlchemy Content objects
    Չանկերը անմիջապես ավելացնում է տվյալների բազայի Embedding աղյուսակում։
    """
    with SessionLocal() as session:
        chunk_count = 0
        try:
            for article in articles:
                # ՈՒՂՂՈՒՄ. article.get("content", "") -> article.content
                content = article.content or ""
                if not content:
                    continue

                start = 0
                while start < len(content):
                    end = min(start + max_chunk_size, len(content))
                    chunk_text = content[start:end]
                    
                    chunk = Embedding(
                        # ՈՒՂՂՈՒՄ. article.get("id") -> article.id
                        article_id=article.id,
                        chunk_content=chunk_text,
                        chunk_start=start,
                        chunk_end=end,
                        embedding=None
                    )
                    session.add(chunk)
                    chunk_count += 1

                    if end == len(content):
                        break
                    
                    new_start = end - overlap_size
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
