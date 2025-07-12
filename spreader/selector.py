import os
import pickle
from db import SessionLocal, Processed, Top, Content
from sqlalchemy import and_, or_, func

def save_urgent_value(value, path='spreader/selector_urgent_value.txt'):
    with open(path, 'w') as f:
        f.write(str(value))

def select_to_publish():
    db = SessionLocal()
    try:
        not_published = db.query(Processed).filter(
            or_(
                Processed.published != "published",
                Processed.published.is_(None)
            )
        ).all()
        not_published_ids = [row.base_id for row in not_published]
        print(f"[SELECTOR] Not published count: {len(not_published_ids)}")

        if not not_published_ids:
            save_urgent_value(0)
            print("[SELECTOR] No candidates for publishing.")
            return

        
        # 2. Find base_ids with urgency==3 in top table
        urgent_ids = db.query(Top.id).filter(and_(Top.urgency==3, Top.id.in_(not_published_ids))).all()
        urgent_ids = [row[0] for row in urgent_ids]

        urgent_count = len(urgent_ids)
        save_urgent_value(urgent_count)

        # Priority 1: If any urgent
        if urgent_ids:
            if len(urgent_ids) == 1:
                chosen_id = urgent_ids[0]
            else:
                # Compare final_score
                scores = db.query(Top.id, Top.final_score).filter(Top.id.in_(urgent_ids)).all()
                vals = [s.final_score for s in scores if s.final_score is not None]
                avg_score = sum(vals) / len(vals) if vals else 0
                high_score = [(s.id, s.final_score) for s in scores if s.final_score is not None and s.final_score >= avg_score + 1]
                if high_score:
                    # Pick first with high score
                    chosen_id = high_score[0][0]
                else:
                    # Choose the one with earliest published_at
                    content_times = db.query(Content.id, Content.published_at).filter(Content.id.in_(urgent_ids)).all()
                    content_times = [c for c in content_times if c.published_at is not None]
                    if content_times:
                        chosen_id = min(content_times, key=lambda x: x.published_at)[0]
                    else:
                        chosen_id = urgent_ids[0]
        else:
            # Priority 2: No urgent, use all not published
            scores = db.query(Top.id, Top.final_score).filter(Top.id.in_(not_published_ids)).all()
            vals = [s.final_score for s in scores if s.final_score is not None]
            avg_score = sum(vals) / len(vals) if vals else 0
            high_score = [(s.id, s.final_score) for s in scores if s.final_score is not None and s.final_score >= avg_score + 1]
            if high_score:
                chosen_id = high_score[0][0]
            else:
                # Choose earliest published_at
                content_times = db.query(Content.id, Content.published_at).filter(Content.id.in_(not_published_ids)).all()
                content_times = [c for c in content_times if c.published_at is not None]
                if content_times:
                    chosen_id = min(content_times, key=lambda x: x.published_at)[0]
                else:
                    chosen_id = not_published_ids[0]

        # Mark chosen_id as "publish" in processed

        if chosen_id:
            print(f"[DEBUG] Chosen ID for publishing: {chosen_id}")
            db.query(Processed).filter(
                Processed.base_id == chosen_id
            ).update({'published': 'publish'})
            db.commit()
        else:
            print("[ERROR] No chosen ID for publishing.")
    finally:
        db.close()

if __name__ == "__main__":
    select_to_publish()