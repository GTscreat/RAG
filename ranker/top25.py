import os
from sqlalchemy.orm import Session
from db import SessionLocal, Rank, Parameter, Content, Top
from retriever.prompt_templates import TOP_REQUEST_ROLE, TOP_REQUEST
from openai import OpenAI
import re

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

# Context buffer for last 5 prompts/responses
class ContextMemory:
    def __init__(self, size=5):
        self.size = size
        self.buffer = []

    def add(self, user_message, assistant_message):
        self.buffer.append({"role": "user", "content": user_message})
        self.buffer.append({"role": "assistant", "content": assistant_message})
        # Պահպանել միայն վերջին 5 user/assistant զույգերը (10 մեսիջ)
        if len(self.buffer) > 10:
            self.buffer = self.buffer[-10:]

    def get(self):
        return self.buffer

context_memory = ContextMemory(size=5)

def get_top_ids_with_scores(db: Session, top_n=25, similarity_threshold=0.9):
    # Get all ranks sorted by total_score desc
    all_ranks = db.query(Rank).order_by(Rank.total_score.desc()).all()
    top_ids = []
    top_scores = []

    # Load all similarity links from Parameter.similarity (assume all rows)
    param_map = {p.id: p.similarity for p in db.query(Parameter).all() if p.similarity}

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

    for rank in all_ranks:
        if any(is_similar(rank.id, tid) for tid in top_ids):
            continue
        top_ids.append(rank.id)
        top_scores.append(rank.total_score)
        if len(top_ids) == top_n:
            break

    return list(zip(top_ids, top_scores))

def update_top_table(db: Session, top_n=25):
    top = get_top_ids_with_scores(db, top_n=top_n)
    db.query(Top).delete()  # Clear existing
    for id_, score in top:
        db.add(Top(id=id_, total_score=score))
    db.commit()

def get_top_contents(db: Session):
    # Return [(id, content)] for all in Top
    top_rows = db.query(Top).all()
    ids = [row.id for row in top_rows]
    contents = db.query(Content).filter(Content.id.in_(ids)).all()
    id_to_content = {c.id: c.content for c in contents}
    return [(id_, id_to_content.get(id_, "")) for id_ in ids]

def openai_score_stories(top_contents):
    # Վերցնել վերջին 5 մեսիջները context_memory-ից
    previous_messages = [{"role": "system", "content": TOP_REQUEST_ROLE}] + context_memory.get()

    # Կառուցել user prompt
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
    """
    Վերլուծում է OpenAI-ից ստացված տեքստը և վերադարձնում dict՝ id-ների համար գնահատականներով։
    """
    results = {}
    # Օրինակային տող՝
    # "id": "123", "importance": "5", "urgency": "3", "domestic_sentiment": "pro", "geopolitical": "proarmenian"
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
                # final_score հաշվարկեք ըստ ձեր տրամաբանության, օրինակ՝
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