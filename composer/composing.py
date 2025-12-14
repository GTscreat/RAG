# composing.py
from db import SessionLocal, News, Parameter, Top, Processed
import json
import re
from composer.llm_prompts import (
    ROLE1, OPERATIONAL_HIGH, FORMAT_BRIEF, LANGUAGE_ARMENIAN,
    OBJECTIVITY_NEUTRAL, STYLE_DIRECT,
    OBJECTIVITY_TOPIC_ADJUSTED, STYLE_REPHRASED, TITLE_TELEGRAM_CHANNEL,
    TELEGRAM_OUTPUT_FORMAT
)
from openai import OpenAI

MAX_CONTEXT_LEN = 2000  # Խորհուրդ է տրվում՝ չափազանց երկար տեքստերը կրճատել

def format_back_context(text, source=None):
    if not text:
        return None
    text = text.strip()
    if not text.endswith(('.', '։', '!', '?')):
        text += '։'
    # source-ը չօգտագործել, եթե չկա
    if len(text) > MAX_CONTEXT_LEN:
        text = text[:MAX_CONTEXT_LEN].rsplit(' ', 1)[0] + '…'
    return text

def prompt_gen_request(base_id):
    """
    Արդյունավետ կերպով ստեղծում է պրոմպտ՝ օգտագործելով նվազագույն քանակի բազային հարցումներ։
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
                        # row-ն tuple է, որի առաջին անդամը content-ն է
                        formatted_ctx = format_back_context(row[0])
                        if formatted_ctx:
                            back_contexts.append(formatted_ctx)
            
            # Պրոմպտի կառուցման տրամաբանությունը մնում է նույնը
            prompt = ROLE1 + OPERATIONAL_HIGH + LANGUAGE_ARMENIAN + TITLE_TELEGRAM_CHANNEL + FORMAT_BRIEF + TELEGRAM_OUTPUT_FORMAT
            if geopolitical == "antiarmenian":
                prompt += OBJECTIVITY_TOPIC_ADJUSTED + STYLE_REPHRASED
            else:
                prompt += OBJECTIVITY_NEUTRAL + STYLE_DIRECT
            
            content = {
                "main_news": main_news,
                "back_contexts": back_contexts
            }
            return prompt, content

        except Exception as e:
            print(f"[ERROR] Սխալ՝ պրոմպտ ստեղծելիս (base_id {base_id}): {e}")
            return None, None
        
def generate_content_with_openai(prompt, content):
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

def save_processed(base_id, openai_response):
    """
    Պահպանում է մշակված կոնտենտը՝ օգտագործելով "upsert" (update or insert) տրամաբանությունը։
    """
    with SessionLocal() as session:
        try:
            title = ""
            content = ""
            
            # ՀԻՄՆԱԿԱՆ ՈՒՂՂՈՒՄԸ. Ավելի ճկուն regex՝ re.DOTALL դրոշակով
            # (.*?) - նշանակում է գտնել ցանկացած սիմվոլ (ներառյալ նոր տողեր) չակերտների միջև
            pattern = r'title:\s*"(.*?)"\s*content:\s*"(.*?)"'
            match = re.search(pattern, openai_response, re.DOTALL)
            
            if match:
                # Եթե համընկնումը գտնված է, առանձնացնում ենք վերնագիրը և կոնտենտը
                title = match.group(1).strip()
                content = match.group(2).strip()
            else:
                # Եթե համընկնում չկա, որպես պահեստային տարբերակ՝
                # ամբողջ պատասխանը պահում ենք կոնտենտի մեջ
                print(f"[WARNING] OpenAI-ի պատասխանը չհաջողվեց մասնատել base_id={base_id}-ի համար։ Պահպանվում է ամբողջական տեքստը։")
                content = openai_response.strip()

            # session.merge()-ը ավտոմատ կթարմացնի տողը, եթե այն գոյություն ունի
            # (ըստ primary key-ի՝ base_id), կամ կստեղծի նորը, եթե չկա։
            processed_obj = Processed(
                base_id=base_id,
                title=title,
                generated_content=content
            )
            session.merge(processed_obj)
            session.commit()
            
        except Exception as e:
            print(f"❌ Սխալ՝ մշակված կոնտենտը պահպանելիս: {e}")
            session.rollback()