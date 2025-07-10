# composing.py
from db import SessionLocal, Content, Parameter, Top, Processed
import json
from composer.llm_prompts import (
    OPERATIONAL_HIGH, FORMAT_BRIEF, LANGUAGE_ARMENIAN,
    OBJECTIVITY_NEUTRAL, STYLE_DIRECT,
    OBJECTIVITY_TOPIC_ADJUSTED, STYLE_REPHRASED, TELEGRAM_POST, TITLE_TELEGRAM_CHANNEL
)
from openai import OpenAI

def prompt_gen_request(base_id):
    session = SessionLocal()
    try:
        # Վերցնել հիմնական կոնտենտը
        main_news = session.query(Content.content).filter(Content.id == base_id).scalar()
        # Վերցնել similarity id-ները
        param = session.query(Parameter.similarity).filter(Parameter.id == base_id).scalar()
        back_contexts = []
        if param:
            try:
                sim_list = json.loads(param)
                for sim in sim_list:
                    cid = sim.get("id")
                    if cid:
                        ctx = session.query(Content.content).filter(Content.id == cid).scalar()
                        if ctx:
                            back_contexts.append(ctx)
            except Exception:
                pass
        # Վերցնել geopolitical
        geopolitical = session.query(Top.geopolitical).filter(Top.id == base_id).scalar()
        # Կառուցել պրոմպտ
        prompt = OPERATIONAL_HIGH + FORMAT_BRIEF + LANGUAGE_ARMENIAN + TITLE_TELEGRAM_CHANNEL + TELEGRAM_POST
        if geopolitical == "antiarmenian":
            prompt += OBJECTIVITY_TOPIC_ADJUSTED + STYLE_REPHRASED
        else:
            prompt += OBJECTIVITY_NEUTRAL + STYLE_DIRECT
        # Ամբողջ բովանդակությունը
        content = {
            "main_news": main_news,
            "back_context": back_contexts
        }
        return prompt, content
        
    finally:
        session.close()

def generate_content_with_openai(prompt, content):
    client = OpenAI()
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": json.dumps(content, ensure_ascii=False)}
    ]
    print(messages)
    completion = client.chat.completions.create(
        model="gpt-4.1",
        messages=messages
    )
    return completion.choices[0].message.content

def save_processed(base_id, generated_content):
    session = SessionLocal()
    try:
        processed = Processed(base_id=base_id, generated_content=generated_content)
        session.add(processed)
        session.commit()
    finally:
        session.close()