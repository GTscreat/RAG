import re
import json

def extract_id_content_from_sql(sql_path, output_json="news_id_content.json"):
    results = []

    insert_pattern = r"INSERT INTO public\.news VALUES\s*(.*?);"
    tuple_pattern = r"\((.*?)\)"
    value_pattern = r"""('(?:[^']|'')*'|NULL|[^\s,()]+)"""

    with open(sql_path, "r", encoding="utf-8") as f:
        data = f.read()

    inserts = re.findall(insert_pattern, data, re.DOTALL)
    total_tuples = sum(len(re.findall(tuple_pattern, block, re.DOTALL)) for block in inserts)
    processed = 0

    for insert_block in inserts:
        tuples = re.findall(tuple_pattern, insert_block, re.DOTALL)
        for tup in tuples:
            processed += 1
            if processed % 100 == 0 or processed == total_tuples:
                print(f"Մշակված տողեր՝ {processed}/{total_tuples}")
            values = re.findall(value_pattern, tup)
            if len(values) >= 5:
                try:
                    id_raw = values[0]
                    # Հեռացնում ենք գծիկները, եթե id-ն տեքստային է
                    if id_raw.startswith("'") and id_raw.endswith("'"):
                        id_raw = id_raw[1:-1]
                    # Ստուգում ենք՝ id-ն ամբողջությամբ թիվ է
                    if not id_raw.isdigit():
                        continue
                    id_ = int(id_raw)
                    content = values[4]
                    if content.startswith("'") and content.endswith("'"):
                        content = content[1:-1].replace("''", "'")
                    if not content or len(content.strip()) < 10:
                        continue
                    results.append({"id": id_, "content": content})
                except Exception as ex:
                    print(f"Չհաջողվեց վերծանել՝ {ex}")

    with open(output_json, "w", encoding="utf-8") as out:
        json.dump(results, out, ensure_ascii=False, indent=2)

    print(f"Պահպանված հոդվածներ՝ {len(results)}")
    return results

if __name__ == "__main__":
    extract_id_content_from_sql("scrapper.sql")





# import numpy as np
# import json
# from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification
# from db import SessionLocal, NERResult

# def load_ner_pipeline():
#     model_name = "daviddallakyan2005/armenian-ner"
#     tokenizer = AutoTokenizer.from_pretrained(model_name)
#     model = AutoModelForTokenClassification.from_pretrained(model_name)
#     ner_pipeline = pipeline("ner", model=model, tokenizer=tokenizer, aggregation_strategy="simple")
#     return ner_pipeline

# def merge_entities(entities, group_key="entity_group", word_key="word", start_key="start", end_key="end", score_key="score"):
#     if not entities:
#         return []
#     merged = []
#     entities = sorted(entities, key=lambda x: x[start_key])
#     buffer = entities[0].copy()
#     for ent in entities[1:]:
#         if ent[group_key] == buffer[group_key] and ent[start_key] == buffer[end_key]:
#             buffer[word_key] += ent[word_key]
#             buffer[end_key] = ent[end_key]
#             buffer[score_key] = max(buffer[score_key], ent[score_key])
#         else:
#             merged.append(buffer)
#             buffer = ent.copy()
#     merged.append(buffer)
#     return merged

# def run_ner_on_articles(articles, ner_pipeline):
#     results = []
#     total = len(articles)
#     for idx, article in enumerate(articles, 1):
#         text = article.get("content", "")
#         entities = ner_pipeline(text)
#         entities = merge_entities(entities)
#         results.append({
#             "id": article["id"],
#             "entities": entities
#         })
#         if idx % 100 == 0 or idx == total:
#             print(f"NER պրոգրես՝ {idx}/{total}")
#     return results

# def to_python_type(obj):
#     if isinstance(obj, dict):
#         return {k: to_python_type(v) for k, v in obj.items()}
#     elif isinstance(obj, list):
#         return [to_python_type(x) for x in obj]
#     elif isinstance(obj, np.generic):
#         return obj.item()
#     else:
#         return obj

# def save_ner_results_to_db(results):
#     session = SessionLocal()
#     count_new, count_update = 0, 0
#     for item in results:
#         article_id = item["id"]
#         entities = to_python_type(item["entities"])
#         exists = session.query(NERResult).filter_by(id=article_id).first()
#         if exists:
#             exists.entities = entities
#             count_update += 1
#         else:
#             session.add(NERResult(id=article_id, entities=entities))
#             count_new += 1
#     session.commit()
#     session.close()
#     print(f"Նոր NER արդյունքներ: {count_new} | Թարմացված: {count_update}")

# if __name__ == "__main__":
#     # 1. Կարդա JSON-ը, օրինակ՝ "news_id_content.json"
#     with open("news_id_content.json", "r", encoding="utf-8") as f:
#         articles = json.load(f)
#     print(f"Կարդացվեց {len(articles)} հոդված")

#     # 2. Ներբեռնիր NER pipeline-ը
#     ner_pipeline = load_ner_pipeline()

#     # 3. Հաշվիր entitie-ները
#     ner_results = run_ner_on_articles(articles, ner_pipeline)

#     # 4. Պահիր արդյունքը sqlite բազայում
#     save_ner_results_to_db(ner_results)
