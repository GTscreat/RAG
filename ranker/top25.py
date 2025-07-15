import os
import numpy as np
from sqlalchemy.orm import Session
from db import SessionLocal, Rank, Parameter, Content, Top, Processed
from retriever.prompt_templates import TOP_REQUEST_ROLE, TOP_REQUEST
from openai import OpenAI
import re
import json

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

class ContextMemory:
    def __init__(self, size=5):
        self.size = size
        self.buffer = []

    def add(self, user_message, assistant_message):
        self.buffer.append({"role": "user", "content": user_message})
        self.buffer.append({"role": "assistant", "content": assistant_message})
        if len(self.buffer) > 10:
            self.buffer = self.buffer[-10:]

    def get(self):
        return self.buffer

context_memory = ContextMemory(size=5)

def cosine_similarity(vec1, vec2):
    if vec1 is None or vec2 is None:
        return 0.0
    v1 = np.array(vec1)
    v2 = np.array(vec2)
    if v1.shape != v2.shape or np.linalg.norm(v1) == 0 or np.linalg.norm(v2) == 0:
        return 0.0
    return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))

def get_top_ids_with_scores(db: Session, top_n=25, similarity_threshold=0.85):
    all_ranks = db.query(Rank).order_by(Rank.total_score.desc()).all()
    top_ids = []
    top_scores = []

    # Load similarity links from Parameter.similarity
    param_map = {p.id: p.similarity for p in db.query(Parameter).all() if p.similarity}
    embedding_map = {p.id: p.aver_embedding for p in db.query(Parameter).all() if p.aver_embedding}

    # Get last 100 processed base_ids and their embeddings
    processed_rows = db.query(Processed).order_by(Processed.id.desc()).limit(100).all()
    processed_base_ids = [row.base_id for row in processed_rows if row.base_id is not None]
    processed_embeddings = [embedding_map.get(bid) for bid in processed_base_ids]

    def is_similar(id1, id2):
        sim_list = param_map.get(id1, [])
        for sim in sim_list:
            if sim["id"] == id2 and sim["similarity_index"] >= similarity_threshold:
                return True
        sim_list_rev = param_map.get(id2, [])
        for sim in sim_list_rev:
            if sim["id"] == id1 and sim["similarity_index"] >= similarity_threshold:
                return True
        return False

    def is_embedding_similar(id1_embedding, other_embeddings):
        if id1_embedding is None:
            return False
        for emb in other_embeddings:
            if emb is not None and cosine_similarity(id1_embedding, emb) >= similarity_threshold:
                return True
        return False

    for rank in all_ranks:
        # Skip if similar to any already selected top id
        if any(is_similar(rank.id, tid) for tid in top_ids):
            continue
        # Skip if similar to any processed base_id (by similarity links)
        if any(is_similar(rank.id, pid) for pid in processed_base_ids):
            continue
        # Skip if embedding is similar to any processed embedding
        rank_embedding = embedding_map.get(rank.id)
        if is_embedding_similar(rank_embedding, processed_embeddings):
            continue
        top_ids.append(rank.id)
        top_scores.append(rank.total_score)
        if len(top_ids) == top_n:
            break

    print(f"Top candidates after filtering: {len(top_ids)}")
    return list(zip(top_ids, top_scores))

def update_top_table(db: Session, top_n=25):
    top = get_top_ids_with_scores(db, top_n=top_n)
    db.query(Top).delete()
    for id_, score in top:
        db.add(Top(id=id_, total_score=score))
    db.commit()

def get_top_contents(db: Session):
    top_rows = db.query(Top).all()
    ids = [row.id for row in top_rows]
    contents = db.query(Content).filter(Content.id.in_(ids)).all()
    id_to_content = {c.id: c.content for c in contents}
    return [(id_, id_to_content.get(id_, "")) for id_ in ids]

def openai_score_stories(top_contents):
    previous_messages = [{"role": "system", "content": TOP_REQUEST_ROLE}] + context_memory.get()
    user_prompt = TOP_REQUEST + "\n\nԼուրերի ցուցակ՝\n"
    user_prompt += "\n".join([f'{id_}. {news}' for id_, news in top_contents])
    messages = previous_messages + [
        {"role": "user", "content": user_prompt}
    ]
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.2,
        max_tokens=1024,
        n=1
    )
    result = response.choices[0].message.content
    context_memory.add(messages[-1]["content"], result)
    return result

def parse_openai_response(response_text):
    results = {}
    pattern = r'"id":\s*"(\d+)",\s*"importance":\s*"(\d+)",\s*"urgency":\s*"(\d+)",\s*"domestic_sentiment":\s*"(\w+)",\s*"geopolitical":\s*"(\w+)"'
    for match in re.finditer(pattern, response_text):
        id_, importance, urgency, sentiment, geopolitical = match.groups()
        results[int(id_)] = {
            "ai_score": int(importance),
            "urgency": int(urgency),
            "sentiment": sentiment,
            "geopolitical": geopolitical
        }
    return results

def update_top_with_ai_score(scores_dict):
    db = SessionLocal()
    try:
        for id_, vals in scores_dict.items():
            top_row = db.query(Top).filter(Top.id == id_).first()
            if top_row:
                top_row.ai_score = vals.get("ai_score")
                top_row.urgency = vals.get("urgency")
                top_row.sentiment = vals.get("sentiment")
                top_row.geopolitical = vals.get("geopolitical")
                if top_row.total_score and top_row.ai_score:
                    top_row.final_score = 0.5 * top_row.total_score + 0.5 * top_row.ai_score
        db.commit()
    finally:
        db.close()

def refresh_top_and_score():
    db = SessionLocal()
    try:
        update_top_table(db)
        top_contents = get_top_contents(db)
        if top_contents:
            response_text = openai_score_stories(top_contents)
            scores_dict = parse_openai_response(response_text)
            update_top_with_ai_score(scores_dict)
            return scores_dict
        return None
    finally:
        db.close()