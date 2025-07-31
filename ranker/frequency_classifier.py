import numpy as np
from collections import defaultdict
from db import SessionLocal, Embedding, Parameter

# cosine_similarity և average_pooling ֆունկցիաները մնում են նույնը
def cosine_similarity(a, b):
    # ... (անփոփոխ)
    a = np.array(a)
    b = np.array(b)
    if np.linalg.norm(a) == 0 or np.linalg.norm(b) == 0:
        return 0.0
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

def average_pooling(embeddings):
    # ... (անփոփոխ)
    arr = np.array(embeddings)
    return arr.mean(axis=0) # Վերադարձնում ենք NumPy array, ոչ թե list


# ԹԱՐՄԱՑՎԱԾ ՖՈՒՆԿՑԻԱ
def update_aver_embeddings():
    print("Parameters աղյուսակի aver_embedding սյունակի թարմացում...")
    with SessionLocal() as session:
        try:
            # Բեռնում ենք միայն անհրաժեշտ սյուները՝ արդյունավետության համար
            all_embeddings_data = session.query(Embedding.article_id, Embedding.embedding).filter(Embedding.embedding != None).all()
            
            id_to_chunks = defaultdict(list)
            for article_id, emb_bytes in all_embeddings_data:
                # Կարդալիս bytes -> numpy array
                numpy_emb = np.frombuffer(emb_bytes, dtype=np.float32)
                id_to_chunks[article_id].append(numpy_emb)

            params_to_update = []
            for article_id, embeddings in id_to_chunks.items():
                if embeddings:
                    # average_pooling-ը վերադարձնում է numpy array
                    avg_embedding_arr = average_pooling(embeddings)
                    params_to_update.append({
                        'id': article_id,
                        # Գրելիս numpy array -> bytes
                        'aver_embedding': avg_embedding_arr.tobytes() 
                    })
            
            # Թարմացնում ենք բոլորը միասին՝ օգտագործելով session.merge
            for param_data in params_to_update:
                 session.merge(Parameter(
                     id=param_data['id'], 
                     aver_embedding=param_data['aver_embedding']
                 ))

            session.commit()
            print(f"✅ {len(params_to_update)} պարամետր թարմացվեց/ավելացվեց։")

        except Exception as e:
            print(f"❌ Սխալ՝ aver_embedding-ի թարմացման ժամանակ: {e}")
            session.rollback()


# ԹԱՐՄԱՑՎԱԾ ՖՈՒՆԿՑԻԱ
def run_frequency_classifier():
    print("Հաճախականության դասակարգչի գործարկում...")
    with SessionLocal() as session:
        try:
            # Նախազգուշացում. սա կարող է շատ ռեսուրսատար լինել մեծ բազաների դեպքում
            all_embeddings_data = session.query(Embedding.article_id, Embedding.embedding).filter(Embedding.embedding != None).all()
            param_objs = session.query(Parameter).all()
            
            param_map = {p.id: p for p in param_objs}
            id_to_chunks = defaultdict(list)

            for article_id, emb_bytes in all_embeddings_data:
                # Կարդալիս bytes -> numpy array
                numpy_emb = np.frombuffer(emb_bytes, dtype=np.float32)
                id_to_chunks[article_id].append(numpy_emb)
            
            all_article_ids = [emb[0] for emb in all_embeddings_data]
            seen = set()
            last_ids = []
            for id_ in reversed(all_article_ids):
                if id_ not in seen:
                    last_ids.append(id_)
                    seen.add(id_)
                if len(last_ids) == 100:
                    break
            base_ids = set(last_ids)

            # Հիմնական տրամաբանությունը մնում է նույնը, քանի որ այժմ աշխատում ենք numpy array-ների հետ
            for new_id in id_to_chunks.keys():
                new_chunks = id_to_chunks[new_id]
                for base_id in base_ids:
                    if base_id == new_id:
                        continue
                    
                    base_chunks = id_to_chunks.get(base_id, [])
                    if not base_chunks:
                        continue

                    max_sim = 0.0
                    for emb1 in new_chunks:
                        for emb2 in base_chunks:
                            sim = cosine_similarity(emb1, emb2)
                            if sim > max_sim:
                                max_sim = sim
                    
                    if max_sim >= 0.75:
                        if base_id in param_map:
                            obj = param_map[base_id]
                            if obj.similarity is None:
                                obj.similarity = []
                            
                            # Թարմացում JSON դաշտի համար
                            current_sims = obj.similarity
                            if not any(x["id"] == new_id for x in current_sims):
                                new_sim_entry = {"id": new_id, "similarity_index": max_sim}
                                obj.similarity = current_sims + [new_sim_entry]
            
            session.commit()
            print("✅ Հաճախականության դասակարգումն ավարտվեց։")

        except Exception as e:
            print(f"❌ Սխալ՝ հաճախականության դասակարգման ժամանակ: {e}")
            session.rollback()