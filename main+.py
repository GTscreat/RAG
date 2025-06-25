import os
import json
from retriever.retriever import embed_query, get_top_k, get_full_articles_by_top_chunks
from retriever.llm_client import generate_answer

def main():
    user_question = input("Ի՞նչ հարց ունեք։\n> ")
    EMBEDDINGS_PATH = "data/embeddings.json"
    if not os.path.exists(EMBEDDINGS_PATH):
        print(f"{EMBEDDINGS_PATH} ֆայլը գոյություն չունի։")
        exit(1)
    with open(EMBEDDINGS_PATH, "r", encoding="utf-8") as f:
        embedded_chunks = json.load(f)
    query_emb = embed_query(user_question)
    top_chunks = get_top_k(query_emb, embedded_chunks, k=5)

    # Ստանալ թոփ չանկերին համապատասխանող հոդվածները՝ առանց կրկնության, ամբողջությամբ
    full_articles = get_full_articles_by_top_chunks(top_chunks, content_path="data/content.json")

    result = generate_answer(user_question, full_articles)
    print("\n=== Պատասխան ===\n")
    print(result["answer"])

if __name__ == "__main__":
    main()