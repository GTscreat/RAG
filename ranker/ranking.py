import json
import os
from db import SessionLocal, Content, Parameter, Embedding, NERResult, NERRating, Rank
from ranker.calculate_ner_importance import calculate_ner_importance
import math

THEMATIC_PATH = "data/tamplates/thematic_corpus.json"
MEDIA_RATING_PATH = "data/tamplates/media_rating.json"
CONTENT_DB_PATH = "data/database.db"   # Բազա, որտեղ գտնվում է ner_results աղյուսակը
NER_DB_PATH = "data/nerdatabase.db"     # Օպտիմիզացված NER բազան

# --- Նորմալիզացիայի պարամետրեր ---
# TODO: Այս արժեքները պետք է որոշվեն էմպիրիկ կերպով՝ վերլուծելով ստացվող արդյունքները
NER_SUM_MIN = 0.0      # Նոր հաշվարկի min արժեքը նորմալիզացիայի համար
NER_SUM_MAX = 500.0    # Նոր հաշվարկի max պայմանական արժեքը (պետք է ճշգրտվի)

MIN_FREQ = 0.0         # Similarity գումարի min, նորմալիզացիայի համար
MAX_FREQ = 3.0         # Similarity գումարի max, նորմալիզացիայի համար

# --- Կշիռներ (պետական կարևորության scoring) ---
THEMATIC_W = 0.3
NER_W = 0.3
FREQ_W = 0.3
SOURCE_W = 0.15


# ==============================================================================
# === ՕԺԱՆԴԱԿ ՖՈՒՆԿՑԻԱՆԵՐ ===
# ==============================================================================

def load_score_dict(path, key="category"):
    """Բեռնում է JSON ֆայլը և վերածում բառարանի։"""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {entry[key]: entry["score"] for entry in data}

def normalize(val, min_val, max_val, scale_min=1, scale_max=5):
    """Բերում է val-ը min_val-max_val միջակայքից դեպի scale_min-scale_max։"""
    if max_val - min_val == 0:
        return float(scale_min)
    
    normalized_val = (val - min_val) / (max_val - min_val)
    scaled_val = normalized_val * (scale_max - scale_min) + scale_min
    
    # Համոզվում ենք, որ արդյունքը չի անցնում սահմանները
    return max(scale_min, min(scaled_val, scale_max))

import math

def normalize_log(val, scale_min=1, scale_max=5):
    """
    Նորմալիզացնում է արժեքը՝ օգտագործելով լոգարիթմական սանդղակ։
    Լավ է աշխատում մեծ տարածվածություն ունեցող տվյալների հետ։
    """
    if val <= 0:
        return float(scale_min)
    
    # math.log1p(x) հաշվում է log(1+x), ինչն ավելի կայուն է 0-ին մոտ արժեքների համար։
    # Սա կանխում է log(0)-ի սխալը և ապահովում է, որ 0-ն դառնա 0։
    log_val = math.log1p(val)

    # Այստեղ պետք է սահմանենք լոգարիթմների ենթադրյալ մաքսիմումը։
    # Օրինակ, եթե ձեր max արժեքը մոտ 2000 է, log1p(2000) ≈ 7.6
    # Եթե max արժեքը մոտ 10000 է, log1p(10000) ≈ 9.2
    # Եկեք վերցնենք պայմանական MAX_LOG_VAL = 8.0
    MAX_LOG_VAL = 8.0 
    
    # Նորմալիզացնում ենք լոգարիթմական արժեքը 0-1 միջակայքում
    normalized = min(log_val / MAX_LOG_VAL, 1.0)
    
    # Ձգում ենք մինչև 1-5 միջակայք
    scaled_val = normalized * (scale_max - scale_min) + scale_min
    return scaled_val

def calc_total_score(thematic, ner, freq, source):
    """Հաշվում է կշռված ընդհանուր միավորը։"""
    return (
        THEMATIC_W * thematic +
        NER_W * ner +
        FREQ_W * freq +
        SOURCE_W * source
    )


# ==============================================================================
# === ՀԻՄՆԱԿԱՆ ՌԱՆԺԱՎՈՐՄԱՆ ՖՈՒՆԿՑԻԱ ===
# ==============================================================================

def rank_news():
    """
    Կատարում է բոլոր նորությունների ռանժավորում՝ հիմնվելով 4 հիմնական պարամետրի վրա։
    """
    session = SessionLocal()
    
    # Բեռնում ենք անհրաժեշտ տվյալները
    contents = session.query(Content).all()
    params = {p.id: p for p in session.query(Parameter).all()}
    media_rating = load_score_dict(MEDIA_RATING_PATH, key="url")
    thematic_rating = load_score_dict(THEMATIC_PATH, key="category")

    count_new, count_updated = 0, 0
    print(f"Սկսում ենք սանդղակավորումը {len(contents)} նյութի համար...")

    for article in contents:
        id_ = article.id

        # 1. Թեմատիկ կարևորություն (category) - ԹԱՐՄԱՑՎԱԾ ՏՐԱՄԱԲԱՆՈՒԹՅՈՒՆ
        param = params.get(id_)
        thematic_score = 1.0  # Սկզբնական լռելյայն միավոր

        if param and param.category:
            sub_categories = param.category.split('-')
            scores_found = []
            for sub_cat in sub_categories:
                score = thematic_rating.get(sub_cat.strip(), 1.0)
                scores_found.append(score)
            
            if scores_found:
                thematic_score = sum(scores_found) / len(scores_found)

        # 2. NER կարևորություն (հիմնված նոր տրամաբանության վրա)
        ner_sum_of_products = calculate_ner_importance(id_, CONTENT_DB_PATH, NER_DB_PATH)
        ner_score = normalize_log(ner_sum_of_products, 1, 5) # Օգտագործում ենք լոգարիթմական նորմալիզացիան

        # 3. Frequency (similarity գումար)
        freq_score = 1.0 # Default score
        if param and param.similarity:
            sim_sum = sum(float(s.get("similarity_index", 0)) for s in param.similarity)
            freq_score = normalize(sim_sum, MIN_FREQ, MAX_FREQ, 1, 5)

        # 4. Source (media rating)
        website = article.website
        source_score = media_rating.get(website, 1.0) # Default score

        # 5. Ընդհանուր կարևորություն
        total_score = calc_total_score(thematic_score, ner_score, freq_score, source_score)

        # 6. Արդյունքի պահպանում Rank աղյուսակում
        rank_obj = session.query(Rank).filter_by(id=id_).first()
        if not rank_obj:
            rank_obj = Rank(
                id=id_,
                topic_importance=thematic_score,
                ner_content_importance=ner_score,
                frequency_importance=freq_score,
                source_importance=source_score,
                total_score=total_score
            )
            session.add(rank_obj)
            count_new += 1
        else:
            rank_obj.topic_importance = thematic_score
            rank_obj.ner_content_importance = ner_score
            rank_obj.frequency_importance = freq_score
            rank_obj.source_importance = source_score
            rank_obj.total_score = total_score
            count_updated += 1

    session.commit()
    session.close()
    print(f"Ռանժավորումն ավարտված է։ Գրանցվեց {count_new} նոր նյութ, թարմացվեց {count_updated} նյութ։")


# ==============================================================================
# === ՍԿՐԻՊՏԻ ԳՈՐԾԱՐԿՈՒՄ ===
# ==============================================================================

if __name__ == "__main__":
    # Համոզվում ենք, որ բոլոր ֆայլերը տեղում են
    required_files = [THEMATIC_PATH, MEDIA_RATING_PATH, CONTENT_DB_PATH, NER_DB_PATH]
    for f_path in required_files:
        if not os.path.exists(f_path):
            print(f"!!! ԽՆԴԻՐ։ Պահանջվող ֆայլը գոյություն չունի՝ {f_path}")
            exit() # Դադարեցնում ենք սկրիպտի աշխատանքը
            
    rank_news()