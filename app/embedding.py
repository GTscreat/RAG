from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
import numpy as np
import os
import json

MODEL_PATH = os.getenv(
    "ARMENIAN_EMBEDDING_MODEL_PATH",
    "Metric-AI/armenian-text-embeddings-1"
)

model = SentenceTransformer(MODEL_PATH)

def embed_chunks(
    chunks: List[Dict[str, Any]],
    batch_size: int = 32,
    prefix: str = "passage: "
) -> List[Dict[str, Any]]:
    """
    Armenian chunk embedding with correct prefix.
    """
    # texts = [f"{prefix}{chunk['text']}" for chunk in chunks]    # OLD
    texts = [f"{prefix}{chunk['chunk_content']}" for chunk in chunks]  # NEW (fits chunker.py output)
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

def save_embeddings_to_file(embeddings: List[Dict[str, Any]], filepath="data/embeddings.json"):
    """
    Append new embeddings to the existing file. If file does not exist, create it.
    """
    # Ստուգում ենք՝ կա՞ արդյոք ֆայլը, եթե այո՝ կարդում ենք հները
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except Exception:
                data = []
    else:
        data = []

    # Ավելացնում ենք նոր embedding-ները
    data.extend(embeddings)

    # Գրում ենք ամբողջությամբ նորից (ավելացնել վերջից)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def embed_query(query: str) -> np.ndarray:
    return model.encode([f"query: {query}"], normalize_embeddings=True)[0]

def compute_article_average_embeddings(
    chunk_embeddings: List[Dict[str, Any]],
    output_path: str = "data/id_embeddings.json"
):
    """
    Computes average (mean) embedding per article id based on chunk embeddings.
    Saves results as a list of dicts: [{"id": id, "embedding": [...]}, ...]
    """
    from collections import defaultdict

    # Group embeddings by id
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

    # Save to file
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(avg_results, f, ensure_ascii=False, indent=2)

    return avg_results

if __name__ == "__main__":
    # Օրինակ, եթե run անես embedding.py-ն առանձին
    import sys
    from chunker import chunk_articles

    # Ենթադրում ենք՝ test_articles.json ֆայլ կա
    with open("test_articles.json", "r", encoding="utf-8") as f:
        articles = json.load(f)
    chunks = chunk_articles(articles)
    embeddings = embed_chunks(chunks)
    save_embeddings_to_file(embeddings)
    print("Chunk embeddings saved to data/embeddings.json.")

    # Հաշվել և պահել յուրաքանչյուր նյութի միջին embedding-ը
    compute_article_average_embeddings(embeddings, output_path="data/id_embeddings.json")
    print("Average article embeddings saved to data/id_embeddings.json.")