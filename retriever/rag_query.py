import json
import os
from retriever.retriever import embed_query, get_top_k, get_full_articles_by_top_chunks
from retriever.llm_client import generate_sql_answer

if __name__ == "__main__":
    user_question = input("Ի՞նչ հարց ունեք։\n> ")
    EMBEDDINGS_PATH = "data/embeddings.json"
    CONTENT_PATH = "data/content.json"

    if not os.path.exists(EMBEDDINGS_PATH):
        print(f"{EMBEDDINGS_PATH} ֆայլը գոյություն չունի։")
        exit(1)
    if not os.path.exists(CONTENT_PATH):
        print(f"{CONTENT_PATH} ֆայլը գոյություն չունի։")
        exit(1)

    with open(EMBEDDINGS_PATH, "r", encoding="utf-8") as f:
        embedded_chunks = json.load(f)

    query_emb = embed_query(user_question)
    top_chunks = get_top_k(query_emb, embedded_chunks, k=20)

    # Ստանալ թոփ չանկերին համապատասխանող ամբողջական հոդվածները՝ առանց կրկնության
    full_articles = get_full_articles_by_top_chunks(top_chunks, content_path=CONTENT_PATH)

    result = generate_sql_answer(user_question, full_articles)
    print(result["answer"])