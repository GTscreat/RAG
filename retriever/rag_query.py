import json
import os
from retriever.retriever import embed_query, get_top_k_unique_articles
from retriever.llm_client import generate_answer
from retriever.prompt_templates import TOP_ID

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
    # Վերցնում ենք similarity-ով ամենամոտ չանկերին համապատասխանող տարբեր հոդվածներ
    full_articles = get_top_k_unique_articles(query_emb, embedded_chunks, content_path=CONTENT_PATH, top_id=TOP_ID)

    result = generate_answer(user_question, full_articles)
    print(result["answer"])