import json
import numpy as np
from ranker.thematic_classifier import load_thematic_embeddings, classify_topic_article
from ranker.frequency_classifier import run_frequency_classifier

def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_json(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def average_pooling(embeddings):
    arr = np.array(embeddings)
    return arr.mean(axis=0).tolist()

def main():
    content = load_json("data/content.json")
    parameters = load_json("data/parameters.json")
    embeddings = load_json("data/embeddings.json")

    # 1. Գտնել բոլոր id-ները content.json-ից
    content_ids = {item["id"] for item in content if "id" in item}

    # 2. Գտնել արդեն մշակված id-ները parameters.json-ից
    processed_ids = {item["id"] for item in parameters if "id" in item}

    # 3. Գտնել նոր id-ները
    new_ids = content_ids - processed_ids
    if not new_ids:
        print("No new content found.")
        return

    # 4. Յուրաքանչյուր նոր id-ի համար վերցնել embeddings-ները
    id_to_embeddings = {}
    for emb in embeddings:
        if emb.get("id") in new_ids:
            id_to_embeddings.setdefault(emb["id"], []).append(emb["embedding"])

    # thematic embeddings
    thematic_embeddings = load_thematic_embeddings()

    # 5. Յուրաքանչյուր նոր id-ի համար հաշվել միջին embedding և թեման
    for id_ in new_ids:
        chunk_embs = id_to_embeddings.get(id_, [])
        if not chunk_embs:
            continue
        avg_emb = average_pooling(chunk_embs)
        category = classify_topic_article(chunk_embs, thematic_embeddings)
        parameters.append({
            "id": id_,
            "category": category,
            "aver_embedding": avg_emb
        })

    # 6. Պահպանել parameters.json-ը
    save_json(parameters, "data/parameters.json")

    # 7. Frequency classifier step
    run_frequency_classifier()

if __name__ == "__main__":
    main()