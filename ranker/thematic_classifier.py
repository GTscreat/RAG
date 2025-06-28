import json
import numpy as np

def load_thematic_embeddings(path="data/tamplates/thematic_corpus_embeddings.json"):
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

def save_thematic_results(results, path="data/thematic_results.json"):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    # Բեռնում ենք thematic embeddings
    thematic_embeddings = load_thematic_embeddings()
    # Բեռնում ենք հոդվածների embeddings
    with open("data/embeddings.json", "r", encoding="utf-8") as f:
        all_embeddings = json.load(f)

    # id-ով խմբավորում ենք embeddings-ը
    from collections import defaultdict
    article_embeddings_map = defaultdict(list)
    for chunk in all_embeddings:
        article_embeddings_map[chunk["id"]].append(chunk["embedding"])

    # Յուրաքանչյուր հոդվածի համար դասակարգում ենք թեման
    thematic_results = []
    for art_id, chunk_embs in article_embeddings_map.items():
        topic = classify_topic_article(chunk_embs, thematic_embeddings)
        thematic_results.append({
            "id": art_id,
            "topic": topic
        })

    # Պահպանում ենք thematic_results.json-ում
    save_thematic_results(thematic_results)