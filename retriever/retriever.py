import numpy as np
from db import SessionLocal, Embedding, Content
from app.embedding import model
from retriever.prompt_templates import TOP_ID

def embed_query(text):
    return model.encode([f"query: {text}"], normalize_embeddings=True)[0]

def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def get_top_k_unique_articles(query_emb, top_id=TOP_ID):
    """
    Վերադարձնում է similarity-ով սորտավորված ամենամոտ չանկերի համապատասխանող տարբեր հոդվածների ամբողջական dict-երը։
    """
    session = SessionLocal()
    # Վերցնում ենք բոլոր embeddings-ը
    embedded_chunks = session.query(Embedding).all()
    # id-ով հավաքում ենք հոդվածները
    all_articles = session.query(Content).all()
    id_to_article = {str(article.id): article for article in all_articles}

    # Համարենք similarity
    scored = [
        (cosine_similarity(query_emb, chunk.embedding), chunk)
        for chunk in embedded_chunks
    ]
    scored.sort(reverse=True, key=lambda x: x[0])

    selected_ids = set()
    selected_articles = []
    for sim, chunk in scored:
        chunk_id = str(chunk.id)
        if chunk_id not in selected_ids and chunk_id in id_to_article:
            # ORM-ից dict դարձնել
            article = id_to_article[chunk_id]
            article_dict = {
                "id": article.id,
                "website": article.website,
                "title": article.title,
                "content": article.content,
                "url": article.url,
                "meta": article.meta,
                "published_at": article.published_at
            }
            selected_articles.append(article_dict)
            selected_ids.add(chunk_id)
        if len(selected_articles) >= top_id:
            break
    session.close()
    return selected_articles
