import numpy as np
from collections import defaultdict
from db import SessionLocal, Embedding, Parameter

def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)
    if np.linalg.norm(a) == 0 or np.linalg.norm(b) == 0:
        return 0.0
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

def average_pooling(embeddings):
    arr = np.array(embeddings)
    return arr.mean(axis=0).tolist()

def update_aver_embeddings():
    session = SessionLocal()

    # article_id -> embeddings list
    id_to_chunks = defaultdict(list)
    all_embeddings = session.query(Embedding).filter(Embedding.embedding != None).all()
    for emb in all_embeddings:
        id_to_chunks[emb.article_id].append(emb.embedding)

    # Հաշվարկում ենք միջին embedding-ը յուրաքանչյուր article_id-ի համար
    for article_id, embeddings in id_to_chunks.items():
        if embeddings:
            avg_embedding = average_pooling(embeddings)
            param = session.query(Parameter).filter_by(id=article_id).first()
            if param:
                param.aver_embedding = avg_embedding
            else:
                # Եթե Parameter աղյուսակում չկա, ավելացնում ենք նոր
                session.add(Parameter(id=article_id, aver_embedding=avg_embedding, category=None, similarity=None))

    session.commit()
    session.close()
    print("Parameters աղյուսակի aver_embedding սյունակը թարմացվեց։")

def run_frequency_classifier():
    session = SessionLocal()

    # Բեռնում ենք բոլոր embeddings-ները
    all_embeddings = session.query(Embedding).filter(Embedding.embedding != None).all()
    # Բեռնում ենք բոլոր parameters-ները
    param_objs = session.query(Parameter).all()
    param_map = {str(p.id): p for p in param_objs}

    # article_id -> embeddings list
    id_to_chunks = defaultdict(list)
    for emb in all_embeddings:
        id_to_chunks[str(emb.article_id)].append(emb.embedding)

    # Վերջին 50 unique article_id
    all_article_ids = [str(emb.article_id) for emb in all_embeddings]
    seen = set()
    last_ids = []
    for id_ in reversed(all_article_ids):
        if id_ not in seen:
            last_ids.append(id_)
            seen.add(id_)
        if len(last_ids) == 100:
            break
    base_ids = set(last_ids)

    # For each article_id, compare to all base_ids
    for new_id in id_to_chunks.keys():
        new_chunks = id_to_chunks[new_id]
        for base_id in base_ids:
            if base_id == new_id:
                continue
            base_chunks = id_to_chunks[base_id]
            max_sim = 0.0
            for emb1 in new_chunks:
                for emb2 in base_chunks:
                    sim = cosine_similarity(emb1, emb2)
                    if sim > max_sim:
                        max_sim = sim
            if max_sim >= 0.75:
                if base_id in param_map:
                    obj = param_map[base_id]
                    if obj.similarity is None:
                        obj.similarity = []
                    # Avoid duplicates
                    if not any(x["id"] == int(new_id) for x in obj.similarity):
                        obj.similarity.append({
                            "id": int(new_id),
                            "similarity_index": max_sim
                        })

    session.commit()
    session.close()