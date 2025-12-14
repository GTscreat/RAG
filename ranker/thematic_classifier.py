import numpy as np
from collections import defaultdict
from db import SessionLocal, Embedding, Parameter

def load_thematic_embeddings(path="data/tamplates/thematic_corpus_embeddings.json"):
    import json
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)
    if np.linalg.norm(a) == 0 or np.linalg.norm(b) == 0:
        return 0.0
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def classify_topic_article(chunks_embeddings, thematic_embeddings, threshold=0.75, min_secondary_threshold=0.5):
    category_sims = {entry["category"]: [] for entry in thematic_embeddings}
    for emb in chunks_embeddings:
        for entry in thematic_embeddings:
            category = entry["category"]
            corpus_embeds = entry["embeddings"]
            similarities = [cosine_similarity(emb, corpus_embeds[i]) for i in range(len(corpus_embeds))]
            if similarities:
                category_sims[category].append(max(similarities))
    avg_category_sims = []
    for category, sims in category_sims.items():
        if sims:
            avg_sim = sum(sims) / len(sims)
            avg_category_sims.append((category, avg_sim))
    avg_category_sims.sort(key=lambda x: x[1], reverse=True)
    if not avg_category_sims:
        return "այլ"
    if avg_category_sims[0][1] >= threshold:
        return avg_category_sims[0][0]
    elif len(avg_category_sims) > 1 and avg_category_sims[0][1] >= min_secondary_threshold and avg_category_sims[1][1] >= min_secondary_threshold:
        return f"{avg_category_sims[0][0]}-{avg_category_sims[1][0]}"
    elif avg_category_sims[0][1] >= min_secondary_threshold:
        return avg_category_sims[0][0]
    else:
        return "այլ"

def run_thematic_classifier():
    print("Թեմատիկ դասակարգչի գործարկում...")
    thematic_embeddings = load_thematic_embeddings()

    # 'with' բլոկ՝ սեսիայի անվտանգ և ավտոմատ կառավարման համար
    with SessionLocal() as session:
        try:
            # Զգուշացում. մեծ բազաների դեպքում սա դանդաղ է աշխատելու
            # Բեռնում ենք միայն անհրաժեშտ դաշտերը՝ արդյունավետության համար
            all_embeddings_data = session.query(Embedding.article_id, Embedding.embedding).filter(Embedding.embedding != None).all()
            
            article_embeddings_map = defaultdict(list)
            for article_id, emb_bytes in all_embeddings_data:
                # ՀԻՄՆԱԿԱՆ ՈՒՂՂՈՒՄԸ. bytes -> numpy array փոխակերպում
                numpy_emb = np.frombuffer(emb_bytes, dtype=np.float32)
                article_embeddings_map[article_id].append(numpy_emb)

            updated_count, new_count = 0, 0
            
            # Հավաքում ենք բոլոր թարմացումները՝ մեկ հարցումով դրանք կատարելու համար
            updates_to_process = []
            for art_id, chunk_embs in article_embeddings_map.items():
                # Այժմ այս ֆունկցիան ստանում է NumPy զանգվածների ցուցակ, ինչպես որ պետք է
                topic = classify_topic_article(chunk_embs, thematic_embeddings)
                updates_to_process.append({'id': art_id, 'category': topic})

            # Արդյունավետ կերպով թարմացնում ենք բոլոր պարամետրները
            for update_data in updates_to_process:
                # session.merge()-ը կթարմացնի օբյեկտը, եթե այն գոյություն ունի,
                # կամ կստեղծի նորը, եթե այն ավելացվի սեսիայի մեջ։
                param = session.query(Parameter).filter(Parameter.id == update_data['id']).first()
                if param:
                    param.category = update_data['category']
                    updated_count += 1
                else:
                    # Եթե չկա, ստեղծում ենք նորը
                    session.add(Parameter(id=update_data['id'], category=update_data['category']))
                    new_count += 1
            
            session.commit()
            print(f"✅ Թեմատիկ դասակարգում. Թարմացվեց {updated_count} | Նոր ավելացվեց {new_count}")

        except Exception as e:
            print(f"❌ Սխալ՝ թեմատիկ դասակարգման ժամանակ: {e}")
            session.rollback()