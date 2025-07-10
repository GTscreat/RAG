
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
    Update the 'top' table with ai_score and final_score for each id from OpenAI response.
    """
    db = SessionLocal()
    try:
        for _id, vals in scores_dict.items():
            top_row = db.query(Top).filter(Top.id == _id).first()
            if top_row:
                if not hasattr(top_row, "ai_score"):
                    raise Exception("ai_score column not found in Top table.")
                top_row.ai_score = vals.get("ai_score")
                top_row.urgency = vals.get("urgency")
                top_row.sentiment = vals.get("sentiment")
                top_row.geopolitical = vals.get("geopolitical")

        db.commit()

        # Now calculate and update final_score for each row
        for top_row in db.query(Top).all():
            if getattr(top_row, "ai_score", None) is None or top_row.total_score is None:
                continue
            final_score = (
                total_score_weight * top_row.total_score +
                ai_score_weight * top_row.ai_score
            ) / (total_score_weight + ai_score_weight)
            if not hasattr(top_row, "final_score"):
                raise Exception("final_score column not found in Top table.")
            top_row.final_score = final_score

        db.commit()
    finally:
        db.close()

def set_score_weights(total_weight, ai_weight):
    """
    Update global weights for score calculation.
    """
    global TOTAL_SCORE_WEIGHT, AI_SCORE_WEIGHT
    TOTAL_SCORE_WEIGHT = total_weight
    AI_SCORE_WEIGHT = ai_weight