# selector.py
from db import SessionLocal, Top, Processed

def get_next_unprocessed_top_id():
    session = SessionLocal()
    try:
        top_ids = [row.id for row in session.query(Top.id).order_by(Top.total_score.desc()).all()]
        processed_base_ids = set(row.base_id for row in session.query(Processed.base_id).all())
        for tid in top_ids:
            if tid not in processed_base_ids:
                return tid
        return None
    finally:
        session.close()