import json
from app.embedding import embed_chunks  # օգտագործիր նույն embedding ֆունկցիան, ինչ հոդվածների համար

def load_thematic_corpus(path="data/tamplates/thematic_corpus.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_thematic_embeddings(data, path="data/tamplates/thematic_corpus_embeddings.json"):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def build_thematic_embeddings():
    corpus = load_thematic_corpus()
    thematic_embeddings = []
    for entry in corpus:
        category = entry["category"]
        examples = entry["examples"]
        embeddings = embed_chunks([{"content": ex} for ex in examples])
        # embed_chunks կարող է վերադարձնել [{"embedding": ...}, ...] կամ ուղիղ list[list[float]]
        # Հարմարեցրու ըստ քո embedding ֆունկցիայի արդյունքի
        if isinstance(embeddings[0], dict):
            embeddings = [e["embedding"] for e in embeddings]
        thematic_embeddings.append({
            "category": category,
            "embeddings": embeddings
        })
    save_thematic_embeddings(thematic_embeddings)

if __name__ == "__main__":
    build_thematic_embeddings()