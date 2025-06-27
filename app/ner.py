import json
import numpy as np
from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification

def load_ner_pipeline():
    model_name = "daviddallakyan2005/armenian-ner"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForTokenClassification.from_pretrained(model_name)
    ner_pipeline = pipeline("ner", model=model, tokenizer=tokenizer, aggregation_strategy="simple")
    return ner_pipeline

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
        results.append({
            "id": article["id"],
            "entities": entities
        })
    return results

def save_ner_results(results, filepath="data/ner_results.json"):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

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