def chunk_articles(articles, max_chunk_size=384, overlap_size=256):
    """
    articles: list of dicts (այս json-ով)
    max_chunk_size: չանկի առավելագույն չափ (տոկենին համարժեք)
    overlap_size: չանկերի միջև overlap (տոկենին համարժեք)
    """
    result = []
    for article in articles:
        content = article.get("content", "")
        # Որոշում ենք որտեղից որտեղ են չանկերը
        start = 0
        while start < len(content):
            # Եթե ավարտին ենք մոտենում, վերցնենք մնացածը
            end = min(start + max_chunk_size, len(content))
            chunk_text = content[start:end]
            # Ձևավորում ենք տվյալ չանկի dict-ը
            chunk = {
                "id": article.get("id"),
                "website": article.get("website"),
                "title": article.get("title"),
                "published_at": article.get("published_at"),
                "url": article.get("url"),
                "meta": {
                    "image": article.get("meta", {}).get("image"),
                    "iframe": article.get("meta", {}).get("iframe")
                },
                "chunk_content": chunk_text,
                "chunk_start": start,
                "chunk_end": end,
                # կարող եք ավելացնել նույնականացուցիչ, օրինակ՝ չանկի համար
            }
            result.append(chunk)
            # Հաշվում ենք հաջորդ չանկի սկիզբը՝ overlap-ով
            if end == len(content):
                break  # վերջ
            start = end - overlap_size if (end - overlap_size) > start else end
    return result

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
        },
        "published_at": "2025-06-11 01:17:58"
    }]
    chunks = chunk_articles(sample_article)
    for c in chunks:
        print(c)
