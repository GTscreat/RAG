import json
import os
from db import SessionLocal, Content, Parameter, Embedding, NERResult, NERRating, Rank

# === CONFIG ===

THEMATIC_PATH = "data/tamplates/thematic_corpus.json"
MEDIA_RATING_PATH = "data/tamplates/media_rating.json"
MAX_NER_WORDS = 8     # առավելագույն NER հաշվողի համար նորմալիզացիայի սահման
MIN_FREQ = 0.0        # similarity գումարի min, նորմալիզացիայի համար
MAX_FREQ = 3.0        # similarity գումարի max, նորմալիզացիայի համար

# Կշիռներ (պետական կարեւորության scoring)
THEMATIC_W = 0.3
NER_W = 0.3
FREQ_W = 0.3
SOURCE_W = 0.15

# === Բեռնում ենք բալային աղյուսակները ===

def load_score_dict(path, key="category"):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {entry[key]: entry["score"] for entry in data}

thematic_scores = load_score_dict(THEMATIC_PATH, key="category")
media_scores = load_score_dict(MEDIA_RATING_PATH, key="url")

def normalize(val, min_val, max_val, scale_min=1, scale_max=5):
    # Բերում է val-ը min_val-max_val միջակայքից դեպի scale_min-scale_max
    if max_val - min_val == 0:
        return scale_min
    return min(max((val - min_val) / (max_val - min_val) * (scale_max - scale_min) + scale_min, scale_min), scale_max)

def calc_total_score(thematic, ner, freq, source):
    return (
        THEMATIC_W * thematic +
        NER_W * ner +
        FREQ_W * freq +
        SOURCE_W * source
    )

def rank_news():
    session = SessionLocal()
    contents = session.query(Content).all()
    params = {p.id: p for p in session.query(Parameter).all()}
    nerratings = {n.word: n.score or 0 for n in session.query(NERRating).all()}
    media_rating = media_scores
    thematic_rating = thematic_scores

    count_new, count_updated = 0, 0

    for article in contents:
        id_ = article.id

        # 1. Թեմատիկ կարևորություն (category)
        param = params.get(id_)
        thematic_score = 1
        if param and param.category and param.category in thematic_rating:
            thematic_score = thematic_rating.get(param.category, 1)

        # 2. NER կարևորություն (NER բառերի գումար)
        ner_result = session.query(NERResult).filter_by(id=id_).first()
        ner_sum = 0
        ner_count = 0
        if ner_result and ner_result.entities:
            for ent in ner_result.entities:
                word = ent.get("word", "")
                score = nerratings.get(word, 0)
                if score:
                    ner_sum += float(score)
                    ner_count += 1
        # Նորմալացում՝ եթե մեկ նյութում շատ NER է, cap=MAX_NER_WORDS, բերում ենք 1-5 սանդղակի
        ner_score = normalize(ner_sum, 0, MAX_NER_WORDS * 5, 1, 5)

        # 3. Frequency (similarity գումար)
        freq_score = 0
        if param and param.similarity:
            sim_sum = sum(float(s.get("similarity_index", 0)) for s in param.similarity)
            freq_score = normalize(sim_sum, MIN_FREQ, MAX_FREQ, 1, 5)  # կամ թողնես 0-1, եթե ուզում ես

        # 4. Source (media rating)
        website = article.website
        source_score = media_rating.get(website, 1)

        # 5. Ընդհանուր կարևորություն
        total_score = calc_total_score(thematic_score, ner_score, freq_score, source_score)

        # Արդյունքը Rank աղյուսակ
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
    print(f"Գրանցվեց {count_new} նոր նյութ, թարմացվեց {count_updated} նյութ։")

if __name__ == "__main__":
    rank_news()
