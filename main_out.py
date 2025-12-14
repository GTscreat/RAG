from retriever.retriever import embed_query, get_top_k_unique_articles
from retriever.llm_client import generate_answer
from retriever.prompt_templates import TOP_ID

def main():
    user_question = input("Ի՞նչ հարց ունեք։\n> ")
    # Ստեղծում ենք հարցի embedding
    query_emb = embed_query(user_question)

    # Վերցնում ենք similarity-ով ամենամոտ չանկերի տարբեր հոդվածներ՝ անմիջապես բազայից
    full_articles = get_top_k_unique_articles(query_emb, top_id=TOP_ID)

    if not full_articles:
        print("Հարցմանը համապատասխան հոդվածներ չեն գտնվել։")
        return

    result = generate_answer(user_question, full_articles)
    print("\n=== Պատասխան ===\n")
    print(result["answer"])

if __name__ == "__main__":
    main()