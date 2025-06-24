from app.embedding import model
import json
import numpy as np
from retriever.llm_client import generate_sql_answer

def embed_query(text):
    return model.encode([f"query: {text}"], normalize_embeddings=True)[0]

def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def get_top_k(query_emb, embedded_chunks, k=5):
    scored = [
        (cosine_similarity(query_emb, chunk["embedding"]), chunk)
        for chunk in embedded_chunks
    ]
    scored.sort(reverse=True, key=lambda x: x[0])
    return [chunk for sim, chunk in scored[:k]]

if __name__ == "__main__":
    user_question = input("Ի՞նչ հարց ունեք։\n> ")
    # Հարմարեցնում ենք embeddings ֆայլի անունը
    EMBEDDINGS_PATH = "data/embeddings.json"
    try:
        with open(EMBEDDINGS_PATH, "r", encoding="utf-8") as f:
            embedded_chunks = json.load(f)
    except FileNotFoundError:
        print(f"{EMBEDDINGS_PATH} ֆայլը գոյություն չունի։")
        exit(1)
    query_emb = embed_query(user_question)
    top_chunks = get_top_k(query_emb, embedded_chunks, k=5)
    result = generate_sql_answer(user_question, top_chunks)
    print(result["answer"])
