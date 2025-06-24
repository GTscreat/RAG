import time
from app.get_api import fetch_articles
from app.chunker import chunk_articles
from app.embedding import embed_chunks, save_embeddings_to_file

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

    print("----- Կատարվում է չանկինգ -----")
    chunks = chunk_articles(articles)
    print(f"{len(chunks)} chunks generated.")

    print("----- Կատարվում է embedding -----")
    embeddings = embed_chunks(chunks)
    save_embeddings_to_file(embeddings, filepath="data/embeddings.json")
    print(f"{len(embeddings)} embeddings added to file.")

    print("----- Սպասում ենք 3 րոպե -----")
    time.sleep(180)
