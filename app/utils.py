from db import SessionLocal, Content

def filter_new_articles(articles):
    """
    articles: list of dicts (յուրաքանչյուրում 'id' դաշտ)
    Ստուգում է՝ որոնք դեռ չկան Content աղյուսակում։
    Վերադարձնում է նորերը (որոնք չկային բազայում)։
    """
    session = SessionLocal()
    existing_ids = set(r[0] for r in session.query(Content.id).all())
    new_articles = [a for a in articles if a.get("id") not in existing_ids]
    session.close()
    return new_articles
