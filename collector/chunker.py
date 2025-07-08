from db import SessionLocal, Embedding  # Քո models/db.py-ից ներմուծում

def chunk_articles_and_store(articles, max_chunk_size=512, overlap_size=256):
    """
    articles: list of dicts (content աղյուսակի օրինակով)
    Չանկերը անմիջապես ավելացնում է SQLite Embedding աղյուսակում։
    """
    session = SessionLocal()
    chunk_count = 0

    for article in articles:
        content = article.get("content", "")
        start = 0
        while start < len(content):
            end = min(start + max_chunk_size, len(content))
            chunk_text = content[start:end]
            chunk = Embedding(
                id=None, 
                article_id=article.get("id"), # Եթե ունես չանկի նույնականացուցիչ, այստեղ դնի, եթե ոչ՝ թող լինի ավտո
                website=article.get("website"),
                title=article.get("title"),
                published_at=article.get("published_at"),
                url=article.get("url"),
                meta=article.get("meta"),
                chunk_content=chunk_text,
                chunk_start=start,
                chunk_end=end,
                embedding=None  # Սկզբնական փուլում embedding դեռ չունես, ավելացրու հետո
            )
            session.add(chunk)
            chunk_count += 1

            if end == len(content):
                break
            start = end - overlap_size if (end - overlap_size) > start else end

    session.commit()
    session.close()
    print(f"Total chunks added: {chunk_count}")

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
