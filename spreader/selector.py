# selector.py
import os
import pickle
from db import SessionLocal, Processed, Top, News
from sqlalchemy import and_, or_, func

def save_urgent_value(value, path='spreader/selector_urgent_value.txt'):
    # Այս ֆունկցիան փոփոխության կարիք չունի
    with open(path, 'w') as f:
        f.write(str(value))

# ԹԱՐՄԱՑՎԱԾ ՖՈՒՆԿՑԻԱ
def select_to_publish():
    # 'with' բլոկ՝ ամբողջ գործողությունը մեկ սեսիայի և տրանզակցիայի մեջ պահելու համար
    with SessionLocal() as db:
        try:
            # 1. Արդյունավետ կերպով ստանում ենք միայն չհրապարակվածների ID-ները
            not_published_ids_query = db.query(Processed.base_id).filter(
                or_(
                    Processed.published != "published",
                    Processed.published.is_(None)
                )
            )
            not_published_ids = {row[0] for row in not_published_ids_query.all()}
            print(f"[SELECTOR] Not published count: {len(not_published_ids)}")

            if not not_published_ids:
                save_urgent_value(0)
                print("[SELECTOR] No candidates for publishing.")
                return

            # 2. Գտնում ենք "շտապ" ID-ները
            urgent_ids_query = db.query(Top.id).filter(and_(Top.urgency == 3, Top.id.in_(not_published_ids)))
            urgent_ids = {row[0] for row in urgent_ids_query.all()}
            save_urgent_value(len(urgent_ids))

            chosen_id = None
            
            # 3. Ընտրության տրամաբանություն (մնում է գրեթե նույնը)
            candidate_pool = urgent_ids if urgent_ids else not_published_ids

            if len(candidate_pool) == 1:
                chosen_id = list(candidate_pool)[0]
            else:
                scores_query = db.query(Top.id, Top.final_score).filter(Top.id.in_(candidate_pool))
                scores = [s for s in scores_query.all() if s.final_score is not None]

                if not scores:
                     chosen_id = list(candidate_pool)[0] if candidate_pool else None
                else:
                    vals = [s.final_score for s in scores]
                    avg_score = sum(vals) / len(vals)
                    high_score_candidates = [s.id for s in scores if s.final_score >= avg_score + 1]
                    
                    if high_score_candidates:
                        chosen_id = high_score_candidates[0]
                    else:
                        # Ընտրում ենք ամենահին հոդվածը
                        content_times_query = db.query(News.id, News.published_at).filter(News.id.in_(candidate_pool))
                        content_times = [c for c in content_times_query.all() if c.published_at is not None]
                        
                        if content_times:
                            chosen_id = min(content_times, key=lambda x: x.published_at)[0]
                        else:
                            chosen_id = list(candidate_pool)[0]

            # 4. Նշում ենք ընտրված ID-ն որպես "publish"
            if chosen_id:
                print(f"[SELECTOR] Chosen ID for publishing: {chosen_id}")
                db.query(Processed).filter(
                    Processed.base_id == chosen_id
                ).update({'published': 'publish', 'published_r': 'publish'})
                
                # Կատարում ենք մեկ commit՝ գործողության ավարտին
                db.commit()
            else:
                print("[SELECTOR] No chosen ID for publishing.")

        except Exception as e:
            print(f"❌ Սխալ՝ հրապարակման թեկնածու ընտրելիս: {e}")
            db.rollback()

if __name__ == "__main__":
    select_to_publish()