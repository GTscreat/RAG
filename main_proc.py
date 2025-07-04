import numpy as np
from db import SessionLocal, Content, Embedding, Parameter
from ranking.thematic_classifier import load_thematic_embeddings, classify_topic_article
from ranking.frequency_classifier import run_frequency_classifier

def average_pooling(embeddings):
    arr = np.array(embeddings)
    return arr.mean(axis=0).tolist()

def main():
    session = SessionLocal()

    # 1. Բոլոր content id-ները
    content_ids = {c.id for c in session.query(Content.id).all()}

    # 2. Արդեն մշակված id-ները parameters-ում
    processed_ids = {p.id for p in session.query(Parameter.id).all()}

    # 3. Նոր id-ները
    new_ids = content_ids - processed_ids
    if not new_ids:
        print("No new content found.")
        session.close()
        return

    # 4. Յուրաքանչյուր նոր id-ի համար embeddings-ները
    id_to_embeddings = {}
    all_embeddings = session.query(Embedding).filter(
        Embedding.article_id.in_(list(new_ids)),
        Embedding.embedding != None
    ).all()
    for emb in all_embeddings:
        id_to_embeddings.setdefault(emb.article_id, []).append(emb.embedding)

    # thematic embeddings
    thematic_embeddings = load_thematic_embeddings()

    # 5. Յուրաքանչյուր նոր id-ի համար՝ միջին embedding և թեմա
    added = 0
    for id_ in new_ids:
        chunk_embs = id_to_embeddings.get(id_, [])
        if not chunk_embs:
            continue
        avg_emb = average_pooling(chunk_embs)
        category = classify_topic_article(chunk_embs, thematic_embeddings)
        param = Parameter(id=id_, category=category, aver_embedding=avg_emb, similarity=None)
        session.add(param)
        added += 1

    session.commit()
    session.close()
    print(f"{added} նոր պարամետր ավելացվեց։")

    # 7. Frequency classifier step (արդեն բազայով տարբերակն ես օգտագործում)
    run_frequency_classifier()

if __name__ == "__main__":
    main()
