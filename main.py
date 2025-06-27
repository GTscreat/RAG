import time
from app.get_api import fetch_articles
from app.chunker import chunk_articles
from app.embedding import embed_chunks, save_embeddings_to_file
from app.utils import filter_new_articles
from app.ner import load_ner_pipeline, run_ner_on_articles, save_ner_results  # ← Ավելացրու սա

# Նախապես բեռնենք NER pipeline-ը, որ ամեն անգամ չլիցքավորվի
ner_pipeline = load_ner_pipeline()

while True:
    print("----- Կատարվում է API հարցում -----")
    data = fetch_articles()
    if data is None:
        print("Հոդվածներ ստանալը ձախողվեց։ Սպասում ենք 3 րոպե...")
        time.sleep(180)
        continue

    articles = data.get('data', [])
    if not articles:
        print("Հոդվածների ցանկը դատարկ է։ Սպասում ենք 3 րոպե...")
        time.sleep(180)
        continue

    # --- Ֆիլտրում ենք նոր հոդվածները և ավելացնում content.json-ում
    new_articles = filter_new_articles(articles, filepath="data/content.json")
    if not new_articles:
        print("Նոր հոդվածներ չկան։ Սպասում ենք 3 րոպե...")
        time.sleep(180)
        continue

    print(f"{len(new_articles)} նոր հոդված հայտնաբերվեց։")
    print("----- Կատարվում է չանկինգ -----")
    chunks = chunk_articles(new_articles)
    print(f"{len(chunks)} chunks generated.")

    print("----- Կատարվում է embedding -----")
    embeddings = embed_chunks(chunks)
    save_embeddings_to_file(embeddings, filepath="data/embeddings.json")
    print(f"{len(embeddings)} embeddings added to file.")

    print("----- Կատարվում է Named Entity Recognition (NER) -----")
    ner_results = run_ner_on_articles(new_articles, ner_pipeline)
    save_ner_results(ner_results, filepath="data/ner_results.json")
    print(f"NER արդյունքները պահպանվել են data/ner_results.json-ում։")

    print("----- Սպասում ենք 1 րոպե -----")
    time.sleep(60)