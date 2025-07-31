
import re
from sqlalchemy.orm import Session
from db import SessionLocal, Top

# Default weights for total_score and ai_score (can be changed as needed)
TOTAL_SCORE_WEIGHT = 0.6
AI_SCORE_WEIGHT = 0.4

def parse_openai_scores(openai_response):
    """
    Parse OpenAI response to dict: {id: ai_score}
    Each line is of the form: "id": "<story_id>" - "openai_score": "<importance_score>"
    """
    id_score = {}
    pattern = r'"id":\s*"(\d+)"\s*-\s*"openai_score":\s*"([1-5])"'
    for line in openai_response.splitlines():
        match = re.match(pattern, line.strip())
        if match:
            _id, score = match.groups()
            id_score[int(_id)] = float(score)
    return id_score

def update_top_with_ai_score(scores_dict, total_score_weight=TOTAL_SCORE_WEIGHT, ai_score_weight=AI_SCORE_WEIGHT):
    """
    Թարմացնում է 'top' աղյուսակը AI գնահատականներով և հաշվարկում է final_score-ը
    մեկ անվտանգ գործարքի շրջանակում։
    """
    if not scores_dict:
        return

    # 'with' բլոկ՝ սեսիայի անվտանգ կառավարման համար
    with SessionLocal() as db:
        try:
            # Ստանում ենք բոլոր անհրաժեշտ տողերը մեկ հարցումով՝ արդյունավետության համար
            ids_to_update = list(scores_dict.keys())
            top_rows = db.query(Top).filter(Top.id.in_(ids_to_update)).all()
            
            # Ստեղծում ենք բառարան՝ տողերին արագ հասանելիության համար
            top_map = {row.id: row for row in top_rows}

            for id_, vals in scores_dict.items():
                top_row = top_map.get(id_)
                if top_row:
                    # Թարմացնում ենք AI-ի տված տվյալները
                    top_row.ai_score = vals.get("ai_score")
                    top_row.urgency = vals.get("urgency")
                    top_row.sentiment = vals.get("sentiment")
                    top_row.geopolitical = vals.get("geopolitical")

                    # Միանգամից հաշվարկում և թարմացնում ենք նաև final_score-ը
                    if top_row.total_score is not None and top_row.ai_score is not None:
                        weight_sum = total_score_weight + ai_score_weight
                        if weight_sum > 0:
                            final_score = (
                                total_score_weight * top_row.total_score +
                                ai_score_weight * top_row.ai_score
                            ) / weight_sum
                            top_row.final_score = final_score

            # Կատարում ենք մեկ commit՝ բոլոր փոփոխությունները պահպանելու համար
            db.commit()
            print(f"✅ Top աղյուսակը թարմացվեց {len(scores_dict)} գրառման համար։")

        except Exception as e:
            print(f"❌ Սխալ՝ Top աղյուսակը թարմացնելիս: {e}")
            db.rollback()

def set_score_weights(total_weight, ai_weight):
    """
    Update global weights for score calculation.
    """
    global TOTAL_SCORE_WEIGHT, AI_SCORE_WEIGHT
    TOTAL_SCORE_WEIGHT = total_weight
    AI_SCORE_WEIGHT = ai_weight