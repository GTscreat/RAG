from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Union
import numpy as np
import os
import json

MODEL_PATH = os.getenv(
    "ARMENIAN_EMBEDDING_MODEL_PATH",
    "Metric-AI/armenian-text-embeddings-1"
)

model = SentenceTransformer(MODEL_PATH)

def embed_chunks(
    chunks: Union[List[Dict[str, Any]], List[str]],
    batch_size: int = 32,
    prefix: str = "passage: ",
    save_path: str = None,
    save_mode: str = "bulk"  # "bulk" կամ "append"
) -> List[Dict[str, Any]]:
    """
    Armenian chunk embedding with correct prefix.
    Accepts both list of dicts (with 'chunk_content') or list of strings.
    If save_path is provided, saves embeddings either in 'bulk' or 'append' mode.
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
        # --- 2. Immediate (append) save mode
        if save_path and save_mode == "append":
            append_embedding_to_file(result, save_path)

    # --- 3. Bulk save mode
    if save_path and save_mode == "bulk":
        save_embeddings_to_file(results, save_path)

    return results

def append_embedding_to_file(embedding: Dict[str, Any], filepath="data/embeddings.json"):
    """
    Append a single embedding to the file.
    """
    try:
        with open(filepath, 'r+', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except Exception:
                data = []
            data.append(embedding)
            f.seek(0)
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.truncate()
    except FileNotFoundError:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump([embedding], f, ensure_ascii=False, indent=2)

def save_embeddings_to_file(embeddings: List[Dict[str, Any]], filepath="data/embeddings.json"):
    """
    Bulk save: Replace or append the whole embeddings list to the file.
    """
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except Exception:
                data = []
    else:
        data = []
    data.extend(embeddings)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def embed_query(query: str) -> np.ndarray:
    return model.encode([f"query: {query}"], normalize_embeddings=True)[0]

def compute_article_average_embeddings(
    chunk_embeddings: List[Dict[str, Any]],
    output_path: str = "data/id_embeddings.json"
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
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(avg_results, f, ensure_ascii=False, indent=2)
    return avg_results

if __name__ == "__main__":
    import sys
    from chunker import chunk_articles
    with open("test_articles.json", "r", encoding="utf-8") as f:
        articles = json.load(f)
    chunks = chunk_articles(articles)
    # bulk save
    embeddings = embed_chunks(chunks, save_path="data/embeddings.json", save_mode="bulk")
    print("Chunk embeddings saved to data/embeddings.json.")
    compute_article_average_embeddings(embeddings, output_path="data/id_embeddings.json")
    print("Average article embeddings saved to data/id_embeddings.json.")