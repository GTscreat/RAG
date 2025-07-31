from db import SessionLocal, Content

def filter_new_articles(articles):
    """
    Արդյունավետ կերպով ֆիլտրում է հոդվածների ցանկը՝ գտնելու համար
    նրանք, որոնք դեռ գոյություն չունեն տվյալների բազայում։
    """
    if not articles:
        return []

    # Ստանում ենք API-ից եկած բոլոր հոդվածների ID-ների բազմությունը (set)
    incoming_ids = {a.get("id") for a in articles if a.get("id") is not None}
    
    # Եթե ID-ներ չկան, վերադարձնում ենք դատարկ ցուցակ
    if not incoming_ids:
        return []

    # 'with' բլոկ՝ սեսիայի անվտանգ կառավարման համար
    with SessionLocal() as session:
        # Հարցում ենք կատարում բազային՝ ստուգելու համար, թե մեր ստացած ID-ներից
        # որոնք արդեն գոյություն ունեն։ Սա շատ ավելի արդյունավետ է։
        existing_ids = {
            result[0] for result in session.query(Content.id).filter(Content.id.in_(incoming_ids))
        }

    # Գտնում ենք նոր ID-ները՝ հանելով գոյություն ունեցողները եկածներից
    new_ids = incoming_ids - existing_ids

    # Վերադարձնում ենք միայն այն հոդվածների ամբողջական օբյեկտները, որոնց ID-ները նոր են
    new_articles = [a for a in articles if a.get("id") in new_ids]
    
    return new_articles