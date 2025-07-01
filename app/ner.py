import json
import numpy as np
from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification

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
        # Եթե նույն խմբի է և անմիջապես հաջորդում է
        if ent[group_key] == buffer[group_key] and ent[start_key] == buffer[end_key]:
            buffer[word_key] += ent[word_key]
            buffer[end_key] = ent[end_key]
            buffer[score_key] = max(buffer[score_key], ent[score_key])
        else:
            merged.append(buffer)
            buffer = ent.copy()
    merged.append(buffer)
    return merged

def merge_any_adjacent_entities(entities, word_key="word", start_key="start", end_key="end", score_key="score"):
    if not entities:
        return []
    merged = []
    entities = sorted(entities, key=lambda x: x[start_key])
    buffer = entities[0].copy()
    buffer_groups = [buffer["entity_group"]]
    for ent in entities[1:]:
        # Եթե անմիջապես հաջորդում է (կամ ընդամենը մեկ բացատ է)
        if ent[start_key] <= buffer[end_key] + 1:
            buffer[word_key] += ent[word_key]
            buffer[end_key] = ent[end_key]
            buffer[score_key] = max(buffer[score_key], ent[score_key])
            buffer_groups.append(ent["entity_group"])
        else:
            buffer["entity_group"] = list(set(buffer_groups))
            merged.append(buffer)
            buffer = ent.copy()
            buffer_groups = [buffer["entity_group"]]
    buffer["entity_group"] = list(set(buffer_groups))
    merged.append(buffer)
    return merged

def run_ner_on_articles(articles, ner_pipeline):
    """
    articles: List[Dict], ամեն հոդված dict:
        {
            "id": ...,
            "title": ...,
            "content": ...
        }
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

def save_ner_results(results, filepath="data/ner_results.json"):
    results = to_python_type(results)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)