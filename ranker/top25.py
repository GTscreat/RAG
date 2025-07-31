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
    """
    Ընտրում է top N թեկնածուներին՝ խուսափելով նմանատիպ և արդեն մշակված հոդվածներից։
    """
    all_ranks = db.query(Rank).order_by(Rank.total_score.desc()).all()
    
    # Բեռնում ենք անհրաժեշտ տվյալները մեկ անգամ՝ արդյունավետության համար
    all_params = db.query(Parameter).all()
    param_map = {p.id: p.similarity for p in all_params if p.similarity}
    
    # ՀԻՄՆԱԿԱՆ ՈՒՂՂՈՒՄԸ. bytes -> numpy array փոխակերպում
    embedding_map = {
        p.id: np.frombuffer(p.aver_embedding, dtype=np.float32) 
        for p in all_params if p.aver_embedding
    }

    processed_rows = db.query(Processed.base_id).order_by(Processed.base_id.desc()).limit(100).all()
    processed_base_ids = {row.base_id for row in processed_rows if row.base_id is not None}
    processed_embeddings = [embedding_map.get(bid) for bid in processed_base_ids if embedding_map.get(bid) is not None]

    # ... (is_similar և is_embedding_similar օժանդակ ֆունկցիաները մնում են նույնը) ...
    def is_similar(id1, id2):
        # ... (անփոփոխ)
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
        # ... (անփոփոխ)
        if id1_embedding is None:
            return False
        for emb in other_embeddings:
            if emb is not None and cosine_similarity(id1_embedding, emb) >= similarity_threshold:
                return True
        return False

    top_ids = []
    top_scores = []
    
    for rank in all_ranks:
        if rank.id in processed_base_ids:
            continue
        if any(is_similar(rank.id, tid) for tid in top_ids):
            continue
        if any(is_similar(rank.id, pid) for pid in processed_base_ids):
            continue
            
        rank_embedding = embedding_map.get(rank.id)
        if is_embedding_similar(rank_embedding, processed_embeddings):
            continue

        top_ids.append(rank.id)
        top_scores.append(rank.total_score)
        if len(top_ids) == top_n:
            break

    print(f"Top թեկնածուներ ֆիլտրումից հետո: {len(top_ids)}")
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
    """
    Թարմացնում է Top աղյուսակը AI-ի կողմից տրված գնահատականներով։
    Օգտագործում է 'with' բլոկ՝ սեսիայի ավտոմատ կառավարման համար։
    """
    if not scores_dict:
        return
        
    with SessionLocal() as db:
        try:
            for id_, vals in scores_dict.items():
                top_row = db.query(Top).filter(Top.id == id_).first()
                if top_row:
                    top_row.ai_score = vals.get("ai_score")
                    top_row.urgency = vals.get("urgency")
                    top_row.sentiment = vals.get("sentiment")
                    top_row.geopolitical = vals.get("geopolitical")
                    if top_row.total_score is not None and top_row.ai_score is not None:
                        top_row.final_score = 0.5 * top_row.total_score + 0.5 * top_row.ai_score
            db.commit()
        except Exception as e:
            print(f"❌ Սխալ՝ Top աղյուսակը AI գնահատականներով թարմացնելիս: {e}")
            db.rollback()


def refresh_top_and_score():
    """
    Հիմնական ֆունկցիա, որը համակարգում է ամբողջ գործընթացը՝ 
    top ընտրելուց մինչև AI-ով գնահատելը։
    """
    with SessionLocal() as db:
        try:
            # Թարմացնում ենք Top աղյուսակը top թեկնածուներով
            top_candidates = get_top_ids_with_scores(db)
            db.query(Top).delete()
            db.flush() # Համոզվում ենք, որ delete-ը կատարվել է commit-ից առաջ
            for id_, score in top_candidates:
                db.add(Top(id=id_, total_score=score))
            
            # Ստանում ենք նոր top-ի կոնտենտը OpenAI-ին ուղարկելու համար
            top_contents = get_top_contents(db)
            
            if top_contents:
                response_text = openai_score_stories(top_contents)
                scores_dict = parse_openai_response(response_text)
                
                # Թարմացնում ենք նույն սեսիայի մեջ AI գնահատականները
                for id_, vals in scores_dict.items():
                    top_row = db.query(Top).filter(Top.id == id_).first()
                    if top_row:
                        top_row.ai_score = vals.get("ai_score")
                        top_row.urgency = vals.get("urgency")
                        top_row.sentiment = vals.get("sentiment")
                        top_row.geopolitical = vals.get("geopolitical")
                        if top_row.total_score is not None and top_row.ai_score is not None:
                            top_row.final_score = 0.5 * top_row.total_score + 0.5 * top_row.ai_score
                
                db.commit() # Ամբողջ գործարքը հաստատում ենք մեկ անգամ
                return scores_dict
            
            db.commit() # Հաստատում ենք, եթե նույնիսկ top_contents չկար
            return None
            
        except Exception as e:
            print(f"❌ Սխալ՝ refresh_top_and_score-ի ընթացքում: {e}")
            db.rollback()
            return None