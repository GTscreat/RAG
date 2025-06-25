import os
import json
from typing import List, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer

# === Կոնֆիգուրացիա ===
NEWS_PATH = "data/news.json"
EMBEDDINGS_PATH = "data/embeddings.json"
MODEL_PATH = os.getenv("ARMENIAN_EMBEDDING_MODEL_PATH", "Metric-AI/armenian-text-embeddings-1")

# === Չանկավորում ===
def chunk_articles(articles: List[Dict[str, Any]], max_chunk_size=512, overlap_size=256) -> List[Dict[str, Any]]:
    result = []
    for article in articles:
        content = article.get("content", "")
        start = 0
        while start < len(content):
            end = min(start + max_chunk_size, len(content))
            chunk_text = content[start:end]
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
            }
            result.append(chunk)
            if end == len(content):
                break
            start = end - overlap_size if (end - overlap_size) > start else end
    return result

# === Էմբեդինգ ===
def embed_chunks(
    chunks: List[Dict[str, Any]],
    batch_size: int = 32,
    prefix: str = "passage: "
) -> List[Dict[str, Any]]:
    model = SentenceTransformer(MODEL_PATH)
    texts = [f"{prefix}{chunk['chunk_content']}" for chunk in chunks]
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=True,
        normalize_embeddings=True
    )
    if isinstance(embeddings, np.ndarray):
        embeddings = embeddings.tolist()
    results = []
    for chunk, emb in zip(chunks, embeddings):
        result = dict(chunk)
        result["embedding"] = emb
        results.append(result)
    return results

# === Ֆայլերի օգնիչ ֆունկցիաներ ===
def load_json(filepath):
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except Exception:
                return []
    return []

def save_json(data, filepath):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# === Հիմնական սկրիպտ ===
if __name__ == "__main__":
    # NEWS ֆայլից հոդվածները բեռնում ենք
    articles = load_json(NEWS_PATH)
    if not articles:
        print(f"Հոդվածներ չգտնվեց {NEWS_PATH} ֆայլում։")
        exit(1)
    print(f"{len(articles)} հոդված ընթերցված է {NEWS_PATH} ֆայլից։")

    # Չանկավորում
    chunks = chunk_articles(articles)
    print(f"{len(chunks)} չանկեր ստացվեցին։")

    # Էմբեդինգ
    embeddings = embed_chunks(chunks)
    print(f"{len(embeddings)} embedding ստացվեցին։")

    # Պահպանում ենք embeddings.json-ում
    save_json(embeddings, EMBEDDINGS_PATH)
    print(f"Embedding-ները պահպանված են {EMBEDDINGS_PATH}-ում։")