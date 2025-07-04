import numpy as np
from db import SessionLocal, Embedding, Parameter

def load_thematic_embeddings(path="data/tamplates/thematic_corpus_embeddings.json"):
    import json
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)
    if np.linalg.norm(a) == 0 or np.linalg.norm(b) == 0:
        return 0.0
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def classify_topic_article(chunks_embeddings, thematic_embeddings, threshold=0.75, min_secondary_threshold=0.5):
    category_sims = {entry["category"]: [] for entry in thematic_embeddings}
    for emb in chunks_embeddings:
        for entry in thematic_embeddings:
            category = entry["category"]
            corpus_embeds = entry["embeddings"]
            similarities = [cosine_similarity(emb, corpus_embeds[i]) for i in range(len(corpus_embeds))]
            if similarities:
                category_sims[category].append(max(similarities))
    avg_category_sims = []
    for category, sims in category_sims.items():
        if sims:
            avg_sim = sum(sims) / len(sims)
            avg_category_sims.append((category, avg_sim))
    avg_category_sims.sort(key=lambda x: x[1], reverse=True)
    if not avg_category_sims:
        return "այլ"
    if avg_category_sims[0][1] >= threshold:
        return avg_category_sims[0][0]
    elif len(avg_category_sims) > 1 and avg_category_sims[0][1] >= min_secondary_threshold and avg_category_sims[1][1] >= min_secondary_threshold:
        return f"{avg_category_sims[0][0]}-{avg_category_sims[1][0]}"
    elif avg_category_sims[0][1] >= min_secondary_threshold:
        return avg_category_sims[0][0]
    else:
        return "այլ"

def run_thematic_classifier():
    thematic_embeddings = load_thematic_embeddings()
    session = SessionLocal()
    # Բեռնում ենք բոլոր embeddings-ը՝ id-ով խմբավորած
    from collections import defaultdict
    all_embeddings = session.query(Embedding).all()
    article_embeddings_map = defaultdict(list)
    for chunk in all_embeddings:
        article_embeddings_map[chunk.id].append(chunk.embedding)
    # Յուրաքանչյուր հոդվածի համար դասակարգում ենք թեման
    updated, missed = 0, 0
    for art_id, chunk_embs in article_embeddings_map.items():
        topic = classify_topic_article(chunk_embs, thematic_embeddings)
        # Թարմացնում ենք Parameter աղյուսակում տվյալ հոդվածի category դաշտը
        param = session.query(Parameter).filter_by(id=art_id).first()
        if param:
            param.category = topic
            updated += 1
        else:
            # Եթե չկա, կարող ես ավելացնել, կամ բաց թողնել
            session.add(Parameter(id=art_id, category=topic, aver_embedding=None, similarity=None))
            missed += 1
    session.commit()
    session.close()
    print(f"Թեմատիկ դասակարգում. Թարմացվեց {updated} | Նոր ավելացվեց {missed}")

if __name__ == "__main__":
    run_thematic_classifier()
