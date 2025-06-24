import os
import json

def load_json(filepath):
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except Exception:
                return []
    return []

def save_json(data, filepath):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def filter_new_articles(articles, filepath="data/content.json"):
    existing_articles = load_json(filepath)
    existing_ids = set([a.get("id") for a in existing_articles])
    new_articles = [a for a in articles if a.get("id") not in existing_ids]
    if new_articles:
        updated_articles = existing_articles + new_articles
        save_json(updated_articles, filepath)
    return new_articles