# composing.py
from db import SessionLocal, Content, Parameter, Top, Processed
import json
from composer.llm_prompts import (
    ROLE2, OPERATIONAL_BALANCED, FORMAT_DETAILED, LANGUAGE_RUSSIAN,
    OBJECTIVITY_OPPOSITION, STYLE_DIRECT,
    OBJECTIVITY_TOPIC_ADJUSTED, STYLE_REPHRASED, TITLE_TELEGRAM_CHANNEL,
    TELEGRAM_OUTPUT_FORMAT
)
from openai import OpenAI

MAX_CONTEXT_LEN = 2000  # Խորհուրդ է տրվում՝ չափազանց երկար տեքստերը կրճատել

def format_back_context_ru(text, source=None):
    if not text:
        return None
    text = text.strip()
    if not text.endswith(('.', '։', '!', '?')):
        text += '։'
    # source-ը չօգտագործել, եթե չկա
    if len(text) > MAX_CONTEXT_LEN:
        text = text[:MAX_CONTEXT_LEN].rsplit(' ', 1)[0] + '…'
    return text

def prompt_gen_request_ru(base_id):
    session = SessionLocal()
    try:
        # Վերցնել հիմնական կոնտենտը
        main_news = session.query(Content.content).filter(Content.id == base_id).scalar()

        # Վերցնել similarity id-ները
        param = session.query(Parameter.similarity).filter(Parameter.id == base_id).scalar()
        back_contexts = []
        if param:
            try:
                if isinstance(param, str):
                    sim_list = json.loads(param)
                elif isinstance(param, list):
                    sim_list = param
                else:
                    raise ValueError("Unexpected type for param")

                for sim in sim_list:
                    cid = sim.get("id")
                    if cid:
                        ctx_content = session.query(Content.content).filter(Content.id == cid).scalar()
                        if ctx_content:
                            formatted_ctx = format_back_context_ru(ctx_content)  # աղբյուր չկա
                            if formatted_ctx:
                                back_contexts.append(formatted_ctx)

            except Exception as e:
                print(f"[ERROR] Failed to process similarity data: {e}")

        # Վերցնել geopolitical
        geopolitical = session.query(Top.geopolitical).filter(Top.id == base_id).scalar()

        # Կառուցել պրոմպտ
        prompt = ROLE2 + OPERATIONAL_BALANCED + FORMAT_DETAILED + LANGUAGE_RUSSIAN + TITLE_TELEGRAM_CHANNEL + TELEGRAM_OUTPUT_FORMAT
        if geopolitical == "antiarmenian":
            prompt += OBJECTIVITY_TOPIC_ADJUSTED + STYLE_REPHRASED
        else:
            prompt += OBJECTIVITY_OPPOSITION + STYLE_DIRECT

        # Ամբողջ բովանդակությունը
        content = {
            "main_news": main_news,
            "back_contexts": back_contexts
        }
        return prompt, content

        # Եթե ցանկանաս content-ը դարձնել մաքուր տեքստ պրոմպտի համար, փոխարինիր հետևյալով՝
        # prompt_input = f"Main news: {main_news}\n\nContext:\n" + "\n".join([f"- {ctx}" for ctx in back_contexts])
        # return prompt, prompt_input

    finally:
        session.close()

def generate_content_with_openai_ru(prompt, content):
    client = OpenAI()
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": json.dumps(content, ensure_ascii=False)}
        # Եթե content-ը փոխես string-ի, ապա գրիր՝ {"role": "user", "content": content}
    ]
    completion = client.chat.completions.create(
        model="gpt-4.1",
        messages=messages
    )
    return completion.choices[0].message.content

def save_processed_ru(base_id, openai_response):
    import re
    session = SessionLocal()
    try:
        title = ""
        content = ""
        # Փորձում ենք մեկ տողում գտնել
        match = re.search(r'title:\s*"([^"]+)",\s*content:\s*"([^"]+)"', openai_response)
        if match:
            title = match.group(1)
            content = match.group(2)
        else:
            # Փորձում ենք առանձին տողերով գտնել
            title_match = re.search(r'title:\s*"([^"]+)"', openai_response)
            content_match = re.search(r'content:\s*"([^"]+)"', openai_response)
            if title_match:
                title = title_match.group(1)
            if content_match:
                content = content_match.group(1)
            if not title and not content:
                print("[ERROR] Failed to parse OpenAI response for title/content")
                content = openai_response  # fallback: save raw response

        # Փնտրում ենք արդեն առկա row-ը և թարմացնում տվյալները
        existing = session.query(Processed).filter(Processed.base_id == base_id).first()
        if existing:
            existing.title_r = title
            existing.generated_content_r = content
        else:
            processed = Processed(base_id=base_id, title_r=title, generated_content_r=content)
            session.add(processed)
        session.commit()
    finally:
        session.close()