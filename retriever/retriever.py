import numpy as np
from app.embedding import model
import os
import json

def embed_query(text):
    return model.encode([f"query: {text}"], normalize_embeddings=True)[0]

def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def get_top_k(query_emb, embedded_chunks, k=20):
    scored = [
        (cosine_similarity(query_emb, chunk["embedding"]), chunk)
        for chunk in embedded_chunks
    ]
    scored.sort(reverse=True, key=lambda x: x[0])
    return [chunk for sim, chunk in scored[:k]]

def get_full_articles_by_top_chunks(top_chunks, content_path="data/content.json"):
    """
    Returns full articles (dict) for the unique ids in top_chunks from content.json.
    Each dict includes all fields (id, website_url, news_url, title, published_at, meta, content, etc).
    """
    if not os.path.exists(content_path):
        print(f"{content_path} ֆայլը գոյություն չունի։")
        exit(1)
    with open(content_path, "r", encoding="utf-8") as f:
        all_articles = json.load(f)
    # Collect unique ids from top_chunks
    top_ids = {str(chunk["id"]) for chunk in top_chunks}
    # Filter articles by these ids (no duplicates)
    id_to_article = {str(article["id"]): article for article in all_articles}
    full_articles = []
    for id_ in top_ids:
        if id_ in id_to_article:
            full_articles.append(id_to_article[id_])
    return full_articles