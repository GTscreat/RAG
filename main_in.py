import time
from collector.get_api import fetch_articles, insert_articles_to_db
from collector.chunker import chunk_articles_and_store
from collector.embedding import embed_chunks
from collector.utils import filter_new_articles
from collector.ner import load_ner_pipeline, run_ner_on_articles, save_ner_results_to_db
from ranker.frequency_classifier import update_aver_embeddings, run_frequency_classifier
from ranker.thematic_classifier import run_thematic_classifier
from ranker.ranking import rank_news
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

        print("----- Կատարվում է aver_embedding-ի թարմացում -----")
        update_aver_embeddings()

        print("----- Կատարվում է թեմատիկ դասակարգում -----")
        run_thematic_classifier()

        print("----- Կատարվում է հաճախականության դասակարգում -----")
        run_frequency_classifier()

        print("----- Կատարվում է նյութերի վարկանիշավորում -----")
        rank_news()

        print("----- Սպասում ենք 1 րոպե -----")
        time.sleep(60)

if __name__ == "__main__":
    main_loop()