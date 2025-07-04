import numpy as np
from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification
from db import SessionLocal, NERResult, NERRating

def load_ner_pipeline():
    model_name = "daviddallakyan2005/armenian-ner"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForTokenClassification.from_pretrained(model_name)
    ner_pipeline = pipeline("ner", model=model, tokenizer=tokenizer, aggregation_strategy="simple")
    return ner_pipeline

def merge_entities(entities, group_key="entity_group", word_key="word", start_key="start", end_key="end", score_key="score"):
    if not entities:
        return []
    merged = []
    entities = sorted(entities, key=lambda x: x[start_key])
    buffer = entities[0].copy()
    for ent in entities[1:]:
        if ent[group_key] == buffer[group_key] and ent[start_key] == buffer[end_key]:
            buffer[word_key] += ent[word_key]
            buffer[end_key] = ent[end_key]
            buffer[score_key] = max(buffer[score_key], ent[score_key])
        else:
            merged.append(buffer)
            buffer = ent.copy()
    merged.append(buffer)
    return merged

def run_ner_on_articles(articles, ner_pipeline):
    results = []
    for article in articles:
        text = article.get("title", "") + "\n" + article.get("content", "")
        entities = ner_pipeline(text)
        entities = merge_entities(entities)
        results.append({
            "id": article["id"],
            "entities": entities
        })
    return results

def to_python_type(obj):
    if isinstance(obj, dict):
        return {k: to_python_type(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [to_python_type(x) for x in obj]
    elif isinstance(obj, np.generic):
        return obj.item()
    else:
        return obj

def save_ner_results_to_db(results):
    """
    results: List[Dict], յուր․ նյութի id-ի հետ entities
    Յուրաքանչյուր նյութի արդյունքը ավելացնում է կամ թարմացնում է NERResult աղյուսակում,
    և անմիջապես հետո թարմացնում է NERRating աղյուսակը նոր entities-ով։
    """
    session = SessionLocal()
    count_new, count_update = 0, 0
    for item in results:
        article_id = item["id"]
        entities = to_python_type(item["entities"])
        exists = session.query(NERResult).filter_by(id=article_id).first()
        if exists:
            exists.entities = entities
            count_update += 1
        else:
            session.add(NERResult(id=article_id, entities=entities))
            count_new += 1
    session.commit()

    # ---- NER Rating Update (ner_update logic) ----
    existing_words = {row.word for row in session.query(NERRating.word).all()}
    # Collect all unique words in the just-updated results
    new_words = set()
    for item in results:
        for ent in item.get("entities", []):
            word = ent.get("word", "")
            if word and word not in existing_words:
                new_words.add(word)
    # Add missing words to NERRating table
    added = 0
    for word in new_words:
        session.add(NERRating(word=word, score=None))  # score=None, can be changed to 0.0 or ""
        added += 1
    session.commit()
    session.close()
    print(f"Նոր NER արդյունքներ: {count_new} | Թարմացված: {count_update}")
    print(f"{added} նոր NER բառ ավելացվեց ner_rating աղյուսակում։")

# Օրինակ օգտագործման համար
if __name__ == "__main__":
    import json
    with open("test_articles.json", "r", encoding="utf-8") as f:
        articles = json.load(f)
    ner_pipeline = load_ner_pipeline()
    ner_results = run_ner_on_articles(articles, ner_pipeline)
    save_ner_results_to_db(ner_results)
