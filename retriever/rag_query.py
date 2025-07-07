from retriever.retriever import embed_query, get_top_k_unique_articles
from retriever.llm_client import generate_answer
from retriever.prompt_templates import TOP_ID

if __name__ == "__main__":
    user_question = input("Ի՞նչ հարց ունեք։\n> ")

    # 1․ Ստանում ենք հարցի embedding-ը
    query_emb = embed_query(user_question)
    print(f"Query embedding: {query_emb}")
    # 2․ Վերցնում similarity-ով ամենամոտ չանկերի հոդվածները՝ արդեն տվյալների բազայից
    # get_top_k_unique_articles-ը պարտադիր պետք է վերափոխված լինի՝ տվյալները բազայից բերելու համար։
    full_articles = get_top_k_unique_articles(query_emb, top_id=TOP_ID)

    # 3․ Ուղարկում ենք LLM-ին
    result = generate_answer(user_question, full_articles)
    print(result["answer"])
