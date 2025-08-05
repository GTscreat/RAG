# composing.py
from db import SessionLocal, News, Parameter, Top, Processed
import json
import re
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
    """
    Արդյունավետ կերպով ստեղծում է ռուսերեն պրոմպտ՝ օգտագործելով նվազագույն քանակի բազային հարցումներ։
    """
    with SessionLocal() as session:
        try:
            # 1. ԱՌԱՋԻՆ ՀԱՐՑՈՒՄ. JOIN-ի միջոցով ստանում ենք հիմնական տվյալները
            main_data = session.query(
                News.content,
                Parameter.similarity,
                Top.geopolitical
            ).select_from(News) \
             .outerjoin(Parameter, News.id == Parameter.id) \
             .outerjoin(Top, News.id == Top.id) \
             .filter(News.id == base_id).first()

            if not main_data:
                print(f"[ERROR] Δεν βρέθηκαν δεδομένα για το base_id: {base_id}")
                return None, None

            main_news, similarity_data, geopolitical = main_data
            
            back_contexts = []
            if similarity_data:
                sim_ids = [sim.get("id") for sim in similarity_data if sim.get("id")]
                if sim_ids:
                    # 2. ԵՐԿՐՈՐԴ ՀԱՐՑՈՒՄ. Ստանում ենք բոլոր նմանատիպ հոդվածների կոնտենտը մեկ հարցումով
                    back_context_results = session.query(News.content).filter(News.id.in_(sim_ids)).all()
                    for row in back_context_results:
                        formatted_ctx = format_back_context_ru(row[0])
                        if formatted_ctx:
                            back_contexts.append(formatted_ctx)
            
            # Պրոմպտի կառուցման տրամաբանությունը մնում է նույնը
            prompt = ROLE2 + OPERATIONAL_BALANCED + FORMAT_DETAILED + LANGUAGE_RUSSIAN + TITLE_TELEGRAM_CHANNEL + TELEGRAM_OUTPUT_FORMAT
            if geopolitical == "antiarmenian":
                prompt += OBJECTIVITY_TOPIC_ADJUSTED + STYLE_REPHRASED
            else:
                prompt += OBJECTIVITY_OPPOSITION + STYLE_DIRECT
            
            content = {
                "main_news": main_news,
                "back_contexts": back_contexts
            }
            return prompt, content

        except Exception as e:
            print(f"[ERROR] Սխալ՝ ռուսերեն պրոմպտ ստեղծելիս (base_id {base_id}): {e}")
            return None, None


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
    """
    Թարմացնում է Processed աղյուսակի ռուսերեն դաշտերը։
    """
    with SessionLocal() as session:
        try:
            title_r = ""
            content_r = ""
            
            # ՆՈՒՅՆ ՃԿՈՒՆ REGEX-Ը
            pattern = r'title:\s*"(.*?)"\s*content:\s*"(.*?)"'
            match = re.search(pattern, openai_response, re.DOTALL)
            
            if match:
                title_r = match.group(1).strip()
                content_r = match.group(2).strip()
            else:
                print(f"[WARNING] OpenAI-ի ռուսերեն պատասխանը չհաջողվեց մասնատել base_id={base_id}-ի համար։")
                content_r = openai_response.strip()

            existing_processed = session.query(Processed).filter(Processed.base_id == base_id).first()
            
            if existing_processed:
                existing_processed.title_r = title_r
                existing_processed.generated_content_r = content_r
            else:
                print(f"[WARNING] Δεν βρέθηκε εγγραφή επεξεργασμένου για το base_id={base_id}. Δημιουργείται νέα.")
                new_processed = Processed(
                    base_id=base_id, 
                    title_r=title_r, 
                    generated_content_r=content_r
                )
                session.add(new_processed)

            session.commit()
        except Exception as e:
            print(f"❌ Սխալ՝ ռուսերեն մշակված կոնտենտը պահպանելիս: {e}")
            session.rollback()