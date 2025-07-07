import os
from sqlalchemy import desc
from db import SessionLocal, Rank, Parameter, Content, Top
from openai import OpenAI
from retriever.prompt_templates import TOP_REQUEST_ROLE

OPENAI_API_KEY=os.getenv("OPENAI_API_KEY")
print(OPENAI_API_KEY)
TOP_N = 25
SIMILARITY_THRESHOLD = 0.9

from sqlalchemy import Column, Integer, Float

def get_top_ids():
    session = SessionLocal()
    # Վերցնել բոլոր id-ները և total_score-ները
    all_ranks = session.query(Rank).order_by(desc(Rank.total_score)).all()
    all_ids_scores = [(r.id, r.total_score) for r in all_ranks]

    # Վերցնել similarity dict-ը parameters աղյուսակից
    param_map = {p.id: p.similarity for p in session.query(Parameter).all() if p.similarity}

    top_ids = []
    for id_, score in all_ids_scores:
        # Ստուգել՝ արդյոք արդեն կա նման id top_ids-ում
        is_similar = False
        for top_id in top_ids:
            sim_list = param_map.get(top_id, [])
            if any(sim['id'] == id_ and sim['similarity_index'] >= SIMILARITY_THRESHOLD for sim in sim_list):
                is_similar = True
                break
            sim_list_rev = param_map.get(id_, [])
            if any(sim['id'] == top_id and sim['similarity_index'] >= SIMILARITY_THRESHOLD for sim in sim_list_rev):
                is_similar = True
                break
        if not is_similar:
            top_ids.append(id_)
        if len(top_ids) == TOP_N:
            break

    # Թարմացնել TOP աղյուսակը՝ ORM-ով
    session.query(Top).delete()
    for id_ in top_ids:
        score = next(s for i, s in all_ids_scores if i == id_)
        session.add(Top(id=id_, total_score=score))
    session.commit()
    session.close()
    return top_ids

def get_top_contents(top_ids):
    session = SessionLocal()
    contents = session.query(Content).filter(Content.id.in_(top_ids)).all()
    id_to_content = {c.id: c.content for c in contents}
    session.close()
    return id_to_content

def ask_openai_for_top(top_ids, id_to_content, previous_messages=None, api_key=OPENAI_API_KEY):
    client = OpenAI(api_key=api_key)
    results = {}

    # Եթե նախորդ մեսիջներ չկան, օգտագործել միայն system մեսիջը
    if previous_messages is None:
        previous_messages = [{"role": "system", "content": TOP_REQUEST_ROLE}]
    else:
        # Պահպանել միայն վերջին 5 մեսիջները (բացի system-ից)
        sys_msgs = [msg for msg in previous_messages if msg["role"] == "system"]
        other_msgs = [msg for msg in previous_messages if msg["role"] != "system"]
        previous_messages = sys_msgs + other_msgs[-5:]

    # Վերցնել նոր լուրերի տեքստերը ըստ top_ids
    latest_news_batch = [id_to_content.get(id_, "") for id_ in top_ids]

    # Կառուցել user prompt
    user_prompt = "\n\nԼուրերի ցուցակ՝\n"
    user_prompt += "\n".join([f"{i+1}. {news}" for i, news in enumerate(latest_news_batch)])

    # Messages array
    messages = previous_messages + [
        {"role": "user", "content": user_prompt}
    ]

    print(messages)

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.2,
            max_tokens=512,
            n=1
        )
        answer = response.choices[0].message.content.strip()
    except Exception as e:
        answer = f"Error: {e}"

    results["top25"] = answer
    return results