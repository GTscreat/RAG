import json
from embedding import embed_chunks

def load_thematic_corpus(path="data/tamplates/thematic_corpus.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_thematic_embeddings(data, path="data/tamplates/thematic_corpus_embeddings.json"):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def build_thematic_embeddings(
    embeddings_save_path=None,  # օրինակ՝ "data/embeddings.json"
    embeddings_save_mode="bulk"  # կամ "append"
):
    corpus = load_thematic_corpus()
    thematic_embeddings = []
    for entry in corpus:
        category = entry.get("category")
        examples = entry.get("examples", [])
        # embed_chunks արդեն կհոգա input-ի տիպի ստուգումը և dict-ի դարձնելը
        if not examples:
            continue  # skip empty categories
        embeddings = embed_chunks(
            examples,
            prefix="passage: ",
            save_path=embeddings_save_path,
            save_mode=embeddings_save_mode
        )
        # Եթե embeddings-ը dict-երի list է, վերցնում ենք embedding դաշտը
        if embeddings and isinstance(embeddings[0], dict):
            embeddings = [e["embedding"] for e in embeddings]
        thematic_embeddings.append({
            "category": category,
            "embeddings": embeddings
        })
    save_thematic_embeddings(thematic_embeddings)

if __name__ == "__main__":
    # Կարող ես փոխանցել ճանապարհը, եթե thematic embedding-ները ուզում ես անմիջապես ավելացնել ընդհանուր բազայում
    # build_thematic_embeddings(embeddings_save_path="data/embeddings.json", embeddings_save_mode="append")
    build_thematic_embeddings()