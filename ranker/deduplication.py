import numpy as np

def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)
    if np.linalg.norm(a) == 0 or np.linalg.norm(b) == 0:
        return 0.0
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def deduplicate(articles, embeddings, threshold=0.93):
    """
    articles: list of dicts, յուրաքանչյուրն ունի 'id'
    embeddings: dict, {'id': embedding}
    threshold: similarity շեմ
    Վերադարձնում է ոչ կրկնվող id-ների ցուցակ
    """
    selected = []
    used_ids = set()
    for article in articles:
        a_id = article['id']
        a_emb = embeddings[a_id]
        is_duplicate = False
        for s_id in used_ids:
            s_emb = embeddings[s_id]
            if cosine_similarity(a_emb, s_emb) > threshold:
                is_duplicate = True
                break
        if not is_duplicate:
            selected.append(article)
            used_ids.add(a_id)
    return selected