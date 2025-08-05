# ranking.py
import json
import math
from db import SessionLocal, Content, Parameter, Rank
from ranker.ner_importance import calculate_ner_importance

# --- Կոնֆիգուրացիոն ֆայլերի ճանապարհները ---
THEMATIC_PATH = "data/tamplates/thematic_corpus.json"
MEDIA_RATING_PATH = "data/tamplates/media_rating.json"

# --- Նորմալիզացիայի և կշիռների պարամետրերը ---
MIN_FREQ = 0.0
MAX_FREQ = 3.0
THEMATIC_W = 0.25
NER_W = 0.32
FREQ_W = 0.28
SOURCE_W = 0.15

# --- ID-ների և կայքերի համապատասխանեցման բառարան ---
# Համոզվեք, որ այստեղ ավելացրել եք Ձեր բոլոր կայքերի ID-ները և URL-ները
WEBSITE_ID_MAP = {
    1: "news.am",
    2: "armenpress.am",
    3: "armtimes.com",
    4: "hraparak.am",
    5: "1lurer.am",
    6: "arm.sputniknews.ru",
    9: "t.me/s/rian_ru",
    # Ավելացրեք մյուսները ըստ անհրաժեշտության...
}

# ==============================================================================
# === ՕԺԱՆԴԱԿ ՖՈՒՆԿՑԻԱՆԵՐ ===
# ==============================================================================

def load_score_dict(path, key="category"):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {entry[key]: entry["score"] for entry in data}

def normalize(val, min_val, max_val, scale_min=1, scale_max=5):
    if max_val - min_val == 0: return float(scale_min)
    normalized_val = (val - min_val) / (max_val - min_val)
    scaled_val = normalized_val * (scale_max - scale_min) + scale_min
    return max(scale_min, min(scaled_val, scale_max))

def normalize_log(val, scale_min=1, scale_max=5):
    if val <= 0: return float(scale_min)
    log_val = math.log1p(val)
    MAX_LOG_VAL = 8.0 
    normalized = min(log_val / MAX_LOG_VAL, 1.0)
    scaled_val = normalized * (scale_max - scale_min) + scale_min
    return scaled_val

def calc_total_score(thematic, ner, freq, source):
    return (THEMATIC_W * thematic + NER_W * ner + FREQ_W * freq + SOURCE_W * source)

# ==============================================================================
# === ՀԻՄՆԱԿԱՆ ՌԱՆԺԱՎՈՐՄԱՆ ՖՈՒՆԿՑԻԱ ===
# ==============================================================================

def rank_news():
    """
    Կատարում է բոլոր նորությունների ռանժավորում՝ արդյունավետ կերպով, 
    մշակելով տվյալները մաս-մաս (batches)՝ հիշողությունը չծանրաբեռնելու համար։
    """
    with SessionLocal() as session:
        try:
            media_rating = load_score_dict(MEDIA_RATING_PATH, key="url")
            thematic_rating = load_score_dict(THEMATIC_PATH, key="category")
            
            count_processed = 0
            
            query = session.query(Content, Parameter).outerjoin(Parameter, Content.id == Parameter.id).yield_per(100)
            
            # query.count()-ը կարող է դանդաղ լինել մեծ աղյուսակների դեպքում, սակայն այս պահին ընդունելի է
            total_articles = session.query(Content).count() 
            print(f"Սկսում ենք սանդղակավորումը {total_articles} նյութի համար...")

            for article, param in query:
                id_ = article.id

                # 1. Թեմատիկ կարևորություն
                thematic_score = 1.0
                if param and param.category:
                    sub_categories = param.category.split('-')
                    scores_found = [thematic_rating.get(sub_cat.strip(), 1.0) for sub_cat in sub_categories]
                    if scores_found:
                        thematic_score = sum(scores_found) / len(scores_found)

                # 2. NER կարևորություն
                ner_sum_of_products = calculate_ner_importance(id_)
                ner_score = normalize_log(ner_sum_of_products)

                # 3. Հաճախականություն
                freq_score = 1.0
                if param and param.similarity:
                    sim_sum = sum(float(s.get("similarity_index", 0)) for s in param.similarity)
                    freq_score = normalize(sim_sum, MIN_FREQ, MAX_FREQ)

                # 4. Աղբյուր (Օգտագործում ենք մեր ստեղծած բառարանը)
                source_score = 1.0
                website_url = WEBSITE_ID_MAP.get(article.website_id)
                if website_url and website_url in media_rating:
                     source_score = media_rating[website_url]

                # 5. Ընդհանուր միավոր
                total_score = calc_total_score(thematic_score, ner_score, freq_score, source_score)

                # 6. Արդյունքի պահպանում
                session.merge(Rank(
                    id=id_,
                    topic_importance=thematic_score,
                    ner_content_importance=ner_score,
                    frequency_importance=freq_score,
                    source_importance=source_score,
                    total_score=total_score
                ))
                count_processed += 1
            
            session.commit()
            print(f"Ռանժավորումն ավարտված է։ Մշակվեց {count_processed} նյութ։")
        
        except Exception as e:
            print(f"❌ Սխալ՝ ռանժավորման ընթացքում: {e}")
            session.rollback()

if __name__ == "__main__":
    rank_news()