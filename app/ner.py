import numpy as np
from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification
from db import SessionLocal, NERResult

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
    """
    articles: List[Dict], յուր. նյութի dict՝ "id", "title", "content"
    ner_pipeline: transformers.pipeline object
    Returns: List[Dict], յուր. նյութի id-ի հետ
    """
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
    """
    Recursively convert numpy types to python native types for JSON serialization.
    """
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
    Յուրաքանչյուր նյութի արդյունքը ավելացնում է կամ թարմացնում է NERResult աղյուսակում
    """
    session = SessionLocal()
    count_new, count_update = 0, 0
    for item in results:
        article_id = item["id"]
        entities = to_python_type(item["entities"])  # <--- ԱՅՍՏԵՂ
        exists = session.query(NERResult).filter_by(id=article_id).first()
        if exists:
            exists.entities = entities
            count_update += 1
        else:
            session.add(NERResult(id=article_id, entities=entities))
            count_new += 1
    session.commit()
    session.close()
    print(f"Նոր NER արդյունքներ: {count_new} | Թարմացված: {count_update}")

# Օրինակ օգտագործման համար
if __name__ == "__main__":
    import json
    # articles = [{"id": ..., "title": ..., "content": ...}, ...]
    with open("test_articles.json", "r", encoding="utf-8") as f:
        articles = json.load(f)
    ner_pipeline = load_ner_pipeline()
    ner_results = run_ner_on_articles(articles, ner_pipeline)
    save_ner_results_to_db(ner_results)
