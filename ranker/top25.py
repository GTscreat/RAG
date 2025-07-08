import os
from sqlalchemy.orm import Session
from db import SessionLocal, Rank, Parameter, Content, Top
from retriever.prompt_templates import TOP_REQUEST_ROLE, TOP_REQUEST
from openai import OpenAI

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

# Context buffer for last 5 prompts/responses
class ContextMemory:
    def __init__(self, size=5):
        self.size = size
        self.memory = []

    def add(self, user_message, assistant_message):
        self.memory.append((user_message, assistant_message))
        if len(self.memory) > self.size:
            self.memory.pop(0)

    def get(self):
        messages = []
        for user_msg, assistant_msg in self.memory:
            messages.append({"role": "user", "content": user_msg})
            messages.append({"role": "assistant", "content": assistant_msg})
        return messages

context_memory = ContextMemory(size=5)

def get_top_ids_with_scores(db: Session, top_n=25, similarity_threshold=0.9):
    # Get all ranks sorted by total_score desc
    all_ranks = db.query(Rank).order_by(Rank.total_score.desc()).all()
    top_ids = []
    top_scores = []

    # Load all similarity links from Parameter.similarity (assume one row, first one)
    param = db.query(Parameter).first()
    similarity_list = param.similarity if param and param.similarity else []

    def is_similar(id1, id2):
        # similarity_list = [{"id": ..., "similarity_index": ...}]
        for sim in similarity_list:
            if (sim["id"][0] == id1 and sim["id"][1] == id2) or (sim["id"][0] == id2 and sim["id"][1] == id1):
                if sim["similarity_index"] >= similarity_threshold:
                    return True
        return False

    for rank in all_ranks:
        # Skip if this id is similar to any already in top_ids
        if any(is_similar(rank.id, tid) for tid in top_ids):
            continue
        top_ids.append(rank.id)
        top_scores.append(rank.total_score)
        if len(top_ids) >= top_n:
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
    top_entries = db.query(Top).order_by(Top.total_score.desc()).all()
    contents = []
    for top in top_entries:
        content_row = db.query(Content).filter(Content.id == top.id).first()
        if content_row:
            contents.append((top.id, content_row.content))
    return contents

def openai_score_stories(top_contents):
    # Build the input for one call
    stories = []
    for id_, content in top_contents:
        stories.append(f'"id": "{id_}" - "content": "{content}"')
    stories_str = "\n".join(stories)

    messages = [
        {"role": "system", "content": TOP_REQUEST_ROLE.strip()},
        {"role": "user", "content": TOP_REQUEST.strip() + "\n\n" + stories_str}
    ]
    # Add previous context
    messages = context_memory.get() + messages

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.2,
        max_completion_tokens=512,
        n=1
    )
    result = response.choices[0].message.content
    context_memory.add(messages[-1]["content"], result)
    return result

def refresh_top_and_score():
    db = SessionLocal()
    try:
        update_top_table(db)
        top_contents = get_top_contents(db)
        if top_contents:
            scores = openai_score_stories(top_contents)
            return scores
        return None
    finally:
        db.close()