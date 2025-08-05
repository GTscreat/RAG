# collector/article_selector.py

from datetime import datetime, timedelta, timezone
from db import SessionLocal, News, Embedding

def select_new_articles(time_window_hours: int = 1):
    """
    Ընտրում է այն բոլոր հոդվածները, որոնք հրապարակվել են նշված ժամանակային
    միջակայքում ԵՎ դեռևս չունեն գրառում `embeddings` աղյուսակում։
    
    Args:
        time_window_hours (int): Ժամանակային միջակայքը (ժամերով), որի համար պետք է փնտրել նոր հոդվածներ։
                               Լռելյայն՝ 24 ժամ (մեկ օր)։
    """
    print(f"----- Փնտրում ենք վերջին {time_window_hours} ժամվա չմշակված հոդվածները -----")

    with SessionLocal() as session:
        try:
            # 1. Հաշվարկում ենք ժամանակային սահմանը
            from_time = datetime.now(timezone.utc) - timedelta(hours=time_window_hours)
            
            # 2. Կատարում ենք համակցված հարցում
            new_articles = session.query(News).outerjoin(
                Embedding, News.id == Embedding.article_id
            ).filter(
                # Պայման 1. Հոդվածը դեռ չպետք է ունենա embedding
                Embedding.id.is_(None),
                
                # Պայման 2. Հոդվածը պետք է հրապարակված լինի նշված ժամանակահատվածում
                News.published_at >= from_time
            ).all()

            if new_articles:
                print(f"{len(new_articles)} նոր (չէմբեդավորված) հոդված հայտնաբերվեց նշված ժամանակահատվածում։")
            else:
                print("Նշված ժամանակահատվածում չմշակված նոր հոդվածներ չկան։")

            return new_articles

        except Exception as e:
            print(f"❌ Սխալ՝ բազայից նոր հոդվածներ ստանալիս: {e}")
            return []