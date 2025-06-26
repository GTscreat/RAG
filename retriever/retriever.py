import numpy as np
import os
import json
from app.embedding import model
from retriever.prompt_templates import TOP_ID

def embed_query(text):
    return model.encode([f"query: {text}"], normalize_embeddings=True)[0]

def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def get_top_k_unique_articles(query_emb, embedded_chunks, content_path="data/content.json", top_id=TOP_ID):
    """
    Վերադարձնում է similarity-ով սորտավորված ամենամոտ չանկերին համապատասխանող տարբեր հոդվածների ամբողջական dict-երը։
    Հոդվածն ավելացվում է միայն մեկ անգամ, եթե նրա id-ն դեռ չկա արդյունքներում։
    top_id-ը սահմանում է, թե քանի տարբեր հոդված է անհրաժեշտ վերադարձնել։
    """
    # Բեռնենք բոլոր հոդվածները
    if not os.path.exists(content_path):
        print(f"{content_path} ֆայլը գոյություն չունի։")
        exit(1)
    with open(content_path, "r", encoding="utf-8") as f:
        all_articles = json.load(f)
    # id->article dict
    id_to_article = {str(article["id"]): article for article in all_articles}

    # Համարենք similarity
    scored = [
        (cosine_similarity(query_emb, chunk["embedding"]), chunk)
        for chunk in embedded_chunks
    ]
    scored.sort(reverse=True, key=lambda x: x[0])

    selected_ids = set()
    selected_articles = []
    for sim, chunk in scored:
        chunk_id = str(chunk["id"])
        if chunk_id not in selected_ids and chunk_id in id_to_article:
            selected_articles.append(id_to_article[chunk_id])
            selected_ids.add(chunk_id)
        if len(selected_articles) >= top_id:
            break
    return selected_articles