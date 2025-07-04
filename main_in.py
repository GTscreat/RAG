import time
from app.get_api import fetch_articles, insert_articles_to_db
from app.chunker import chunk_articles_and_store
from app.embedding import embed_chunks
from app.utils import filter_new_articles
from app.ner import load_ner_pipeline, run_ner_on_articles, save_ner_results_to_db
from db import SessionLocal, Embedding

def main_loop():
    # Նախապես բեռնենք NER pipeline-ը, որ ամեն անգամ չլիցքավորվի
    ner_pipeline = load_ner_pipeline()

    while True:
        print("----- Կատարվում է API հարցում -----")
        data = fetch_articles()
        if data is None:
            print("Հոդվածներ ստանալը ձախողվեց։ Սպասում ենք 1 րոպե...")
            time.sleep(60)
            continue

        articles = data.get('data', [])
        if not articles:
            print("Հոդվածների ցանկը դատարկ է։ Սպասում ենք 1 րոպե...")
            time.sleep(60)
            continue

        # --- Ֆիլտրում ենք արդեն բազայում եղած հոդվածները
        new_articles = filter_new_articles(articles)
        if not new_articles:
            print("Նոր հոդվածներ չկան։ Սպասում ենք 1 րոպե...")
            time.sleep(60)
            continue

        print(f"{len(new_articles)} նոր հոդված հայտնաբերվեց։")
        print("----- Ավելացնում ենք նոր հոդվածները բազայում -----")
        insert_articles_to_db(new_articles)  # Նոր հոդվածները Content աղյուսակում

        print("----- Կատարվում է չանկավորում և պահում -----")
        chunk_articles_and_store(new_articles)  # Չանկերը Embedding աղյուսակում (embedding=None)

        print("----- Կատարվում է embedding-ի հաշվարկ և պահում -----")
        # Վերցնում ենք բոլոր embedding=None չանկերը Embedding աղյուսակից
        session = SessionLocal()
        chunks_to_embed = session.query(Embedding).filter(Embedding.embedding == None).all()
        chunk_dicts = [{
            "id": ch.id,
            "website": ch.website,
            "title": ch.title,
            "published_at": ch.published_at,
            "url": ch.url,
            "meta": ch.meta,
            "chunk_content": ch.chunk_content,
            "chunk_start": ch.chunk_start,
            "chunk_end": ch.chunk_end,
        } for ch in chunks_to_embed]
        session.close()

        if chunk_dicts:
            # Ստեղծում ենք embedding-ները և անմիջապես թարմացնում Embedding աղյուսակում
            embed_chunks(chunk_dicts, save_mode="update")
            print(f"{len(chunk_dicts)} embedding computed and saved.")
        else:
            print("Embedding-ը արդեն հաշվարկված է բոլոր չանկերի համար։")

        print("----- Կատարվում է Named Entity Recognition (NER) և պահում -----")
        ner_results = run_ner_on_articles(new_articles, ner_pipeline)
        save_ner_results_to_db(ner_results)  # NER արդյունքները NERResult աղյուսակում
        print(f"NER արդյունքները պահված են բազայում։")

        print("----- Սպասում ենք 1 րոպե -----")
        time.sleep(60)

if __name__ == "__main__":
    main_loop()
