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
    if not chunks:
        return []

    is_list_of_strings = isinstance(chunks[0], str)
    if is_list_of_strings:
        original_texts = list(chunks)
        chunks = [{"chunk_content": s} for s in chunks]
    
    texts_to_embed = [f"{prefix}{chunk['chunk_content']}" for chunk in chunks]
    
    # model.encode-ը վերադարձնում է NumPy զանգված
    embeddings_array = model.encode(
        texts_to_embed,
        batch_size=batch_size,
        show_progress_bar=True,
        normalize_embeddings=True
    )

    # Եթե save_mode-ը "update" է, պահպանում ենք բազայում
    if save_mode == "update":
        # Օգտագործում ենք 'with'՝ ավելի հուսալի սեսիայի կառավարման համար
        with SessionLocal() as session:
            try:
                for i, chunk in enumerate(chunks):
                    db_obj = session.query(Embedding).filter(Embedding.id == chunk["id"]).first()
                    if db_obj:
                        # Փոխակերպում ենք embedding-ը list-ի փոխարեն bytes-ի
                        db_obj.embedding = embeddings_array[i].tobytes()
                
                session.commit()
            except Exception as e:
                print(f"❌ Սխալ տեղի ունեցավ embedding-ները պահպանելիս: {e}")
                session.rollback()

    # Bulk ռեժիմի կամ վերադարձվող արժեքի համար պատրաստում ենք արդյունքները
    results = []
    for i, chunk in enumerate(chunks):
        result = dict(chunk)
        # Վերադարձվող արժեքը կարող է լինել list
        result["embedding"] = embeddings_array[i].tolist()
        results.append(result)

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
    from collector.chunker import chunk_articles

    # Load test articles (provide your own test file)
    with open("test_articles.json", "r", encoding="utf-8") as f:
        articles = json.load(f)
    chunks = chunk_articles(articles)
    embeddings = embed_chunks(chunks, save_mode="bulk")
    print("Chunk embeddings computed.")

    avg_embs = compute_article_average_embeddings(embeddings)
    print("Average article embeddings computed.")
