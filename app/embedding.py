from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Union
import numpy as np
import os

from db import SessionLocal, Embedding

MODEL_PATH = os.getenv(
    "ARMENIAN_EMBEDDING_MODEL_PATH",
    "Metric-AI/armenian-text-embeddings-1"
)

model = SentenceTransformer(MODEL_PATH)

def embed_chunks(
    chunks: Union[List[Dict[str, Any]], List[str]],
    batch_size: int = 32,
    prefix: str = "passage: ",
    save_mode: str = "bulk"  # "bulk" կամ "update"
) -> List[Dict[str, Any]]:
    """
    Armenian chunk embedding with correct prefix.
    Accepts both list of dicts (with 'chunk_content') or list of strings.
    If save_mode == "bulk", returns embeddings as list (for external save).
    If save_mode == "update", embeddings are written directly to DB.
    """
    # --- 1. Input normalization
    if not chunks:
        return []

    # If input is list of strings, convert to list of dicts with 'chunk_content'
    if isinstance(chunks[0], str):
        chunks = [{"chunk_content": s} for s in chunks]

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

    if save_mode == "update":
        session = SessionLocal()
        for chunk, emb in zip(chunks, embeddings):
            db_obj = session.query(Embedding).filter_by(id=chunk["id"]).first()
            if db_obj:
                db_obj.embedding = emb
        session.commit()
        session.close()
    # bulk mode just returns the results (you can save them elsewhere)
    return results

def embed_query(query: str) -> np.ndarray:
    return model.encode([f"query: {query}"], normalize_embeddings=True)[0]

def compute_article_average_embeddings(
    chunk_embeddings: List[Dict[str, Any]],
):
    from collections import defaultdict
    id_to_embs = defaultdict(list)
    for item in chunk_embeddings:
        id_to_embs[item["id"]].append(item["embedding"])
    avg_results = []
    for article_id, embs in id_to_embs.items():
        embs_arr = np.array(embs)
        avg_emb = np.mean(embs_arr, axis=0)
        avg_results.append({
            "id": article_id,
            "embedding": avg_emb.tolist()
        })
    return avg_results

if __name__ == "__main__":
    # For manual test/debug
    import json
    from app.chunker import chunk_articles

    # Load test articles (provide your own test file)
    with open("test_articles.json", "r", encoding="utf-8") as f:
        articles = json.load(f)
    chunks = chunk_articles(articles)
    embeddings = embed_chunks(chunks, save_mode="bulk")
    print("Chunk embeddings computed.")

    avg_embs = compute_article_average_embeddings(embeddings)
    print("Average article embeddings computed.")
