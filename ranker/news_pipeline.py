import json
from ranker.scoring import compute_score
from ranker.top_selection import select_top_n
from ranker.deduplication import deduplicate


with open("data/content.json", "r", encoding="utf-8") as f:
    articles = json.load(f)

with open("data/embeddings.json", "r", encoding="utf-8") as f:
    embeddings = json.load(f)

with open("data/ner_results.json", "r", encoding="utf-8") as f:
    ner_results = json.load(f)

with open("data/thematic_results.json", "r", encoding="utf-8") as f:
    thematic_results = json.load(f)

# scoring
scored = []
for art in articles:
    thematic_cat, thematic_score = ... # thematic classification արդյունք
    ner = ... # NER արդյունք
    meta = art.get("meta", {})
    result = compute_score(art, thematic_cat, thematic_score, ner, meta)
    scored.append(result)

# TOP-N
top_scored = select_top_n(scored, N=30)

# Ընդհանուր embedding-ը dict-ով
embeddings_dict = {emb['id']: emb['embedding'] for emb in embeddings}

# Deduplication
final_selection = deduplicate(top_scored, embeddings_dict)