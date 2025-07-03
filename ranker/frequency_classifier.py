import json
import numpy as np
from collections import defaultdict

PARAM_PATH = "data/parameters.json"
EMB_PATH = "data/embeddings.json"

def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_json(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)
    if np.linalg.norm(a) == 0 or np.linalg.norm(b) == 0:
        return 0.0
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

def run_frequency_classifier():
    embeddings = load_json(EMB_PATH)
    parameters = load_json(PARAM_PATH)
    if not isinstance(parameters, list):
        parameters = []

    # id -> parameter dict
    param_map = {str(item["id"]): item for item in parameters if "id" in item}

    # Group embeddings by id
    id_to_chunks = defaultdict(list)
    for emb in embeddings:
        id_to_chunks[str(emb["id"])].append(emb["embedding"])

    # Find last 50 unique ids (base ids)
    all_ids = [str(emb["id"]) for emb in embeddings]
    seen = set()
    last_ids = []
    for id_ in reversed(all_ids):
        if id_ not in seen:
            last_ids.append(id_)
            seen.add(id_)
        if len(last_ids) == 50:
            break
    base_ids = set(last_ids)

    # For each id, compare to all base_ids (including new ones)
    for new_id in id_to_chunks.keys():
        new_chunks = id_to_chunks[new_id]
        for base_id in base_ids:
            if base_id == new_id:
                continue
            base_chunks = id_to_chunks[base_id]
            # Compare all pairs, keep max similarity
            max_sim = 0.0
            for emb1 in new_chunks:
                for emb2 in base_chunks:
                    sim = cosine_similarity(emb1, emb2)
                    if sim > max_sim:
                        max_sim = sim
            if max_sim >= 0.75:
                if base_id in param_map:
                    if "similarity" not in param_map[base_id]:
                        param_map[base_id]["similarity"] = []
                    # Avoid duplicates
                    if not any(x["id"] == int(new_id) for x in param_map[base_id]["similarity"]):
                        param_map[base_id]["similarity"].append({
                            "id": int(new_id),
                            "similarity_index": max_sim
                        })

    # Save back as list
    save_json(list(param_map.values()), PARAM_PATH)

if __name__ == "__main__":
    run_frequency_classifier()