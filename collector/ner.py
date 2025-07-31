import numpy as np
from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification
from db import SessionLocal, NERResult, Entity # Փոխվել է ներմուծումը

def load_ner_pipeline():
    # ... (Այս ֆունկցիան մնում է անփոփոխ)
    model_name = "daviddallakyan2005/armenian-ner"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForTokenClassification.from_pretrained(model_name)
    ner_pipeline = pipeline("ner", model=model, tokenizer=tokenizer, aggregation_strategy="simple")
    return ner_pipeline

def merge_entities(entities, group_key="entity_group", word_key="word", start_key="start", end_key="end", score_key="score"):
    # ... (Այս ֆունկցիան մնում է անփոփոխ)
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
    # ... (Այս ֆունկցիան մնում է անփոփոխ)
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
    # ... (Այս ֆունկցիան մնում է անփոփոխ)
    if isinstance(obj, dict):
        return {k: to_python_type(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [to_python_type(x) for x in obj]
    elif isinstance(obj, np.generic):
        return obj.item()
    else:
        return obj

# =============================================================
# === ԱՄԲՈՂՋՈՒԹՅԱՄԲ ԹԱՐՄԱՑՎԱԾ ՖՈՒՆԿՑԻԱ ===
# =============================================================
def save_ner_results_to_db(results):
    """
    Պահպանում է NER արդյունքները և ավելացնում է նոր, եզակի էնթիթիները։
    """
    if not results:
        return

    with SessionLocal() as session:
        try:
            # ... (Մաս 1-ը մնում է նույնը) ...
            count_new_results, count_updated_results = 0, 0
            for item in results:
                article_id = item["id"]
                entities_json = to_python_type(item["entities"])
                exists = session.query(NERResult).filter(NERResult.id == article_id).first()
                if exists:
                    exists.entities = entities_json
                    count_updated_results += 1
                else:
                    session.add(NERResult(id=article_id, entities=entities_json))
                    count_new_results += 1
            print(f"✅ NER արդյունքներ: Նոր՝ {count_new_results} | Թարմացված՝ {count_updated_results}")

            # --- Մաս 2: Նոր էնթիթիների ավելացում Entities աղյուսակում ---
            word_to_entity_data = {}
            for item in results:
                for ent in item.get("entities", []):
                    word = ent.get("word")
                    if word and word not in word_to_entity_data:
                        # ՀԻՄՆԱԿԱՆ ՈՒՂՂՈՒՄԸ. Ամբողջ entity dict-ը մշակում ենք to_python_type-ով
                        word_to_entity_data[word] = to_python_type(ent)

            all_words_from_ner = set(word_to_entity_data.keys())
            if not all_words_from_ner:
                session.commit()
                return

            existing_words_query = session.query(Entity.word).filter(Entity.word.in_(all_words_from_ner))
            existing_words = {row[0] for row in existing_words_query.all()}
            
            new_words_to_add = all_words_from_ner - existing_words
            
            for word in new_words_to_add:
                entity_data = word_to_entity_data[word]
                new_entity = Entity(
                    word=word,
                    entity_group=entity_data.get('entity_group'),
                    score=entity_data.get('score'), # Այժմ սա սովորական float է
                    ner_score=None,
                    category_id=None
                )
                session.add(new_entity)
            
            session.commit()
            print(f"✅ {len(new_words_to_add)} նոր էնթիթի ավելացվեց entities աղյուսակում։")

        except Exception as e:
            print(f"❌ Սխալ տեղի ունեցավ NER արդյունքները պահպանելիս: {e}")
            session.rollback()


# Օրինակ օգտագործման համար
if __name__ == "__main__":
    # ... (Այս հատվածը մնում է անփոփոխ)
    import json
    with open("test_articles.json", "r", encoding="utf-8") as f:
        articles = json.load(f)
    ner_pipeline = load_ner_pipeline()
    ner_results = run_ner_on_articles(articles, ner_pipeline)
    save_ner_results_to_db(ner_results)