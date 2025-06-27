def compute_score(article, thematic_category, thematic_score, ner_entities, meta):
    """
    article: dict, բուն հոդվածի ինֆո (title, content, id, ...),
    thematic_category: str, թեմատիկ դասակարգում,
    thematic_score: float, թեմատիկ նմանության score,
    ner_entities: list, NER արդյունք,
    meta: dict, լրացուցիչ մետադատա (աղբյուր, հրապարակման ժամ, ...)
    
    Վերադարձնում է scoring dict:
    """
    # Օրինակ՝ scoring՝ ըստ թեմատիկ score + NER-ի քանակ (անուններ, տեղանուններ) + աղբյուրի կշիռ
    # Կարող ես ավելացնել քո scoring տրամաբանությունը
    score = 0
    # Թեմատիկ score-ին ավելացնենք կշիռ
    score += 0.6 * thematic_score
    # NER-ում անձանց կամ տեղանունների քանակը կարող է կարևոր լինել
    per_count = sum(1 for e in ner_entities if e['entity_group'] == 'PER')
    loc_count = sum(1 for e in ner_entities if e['entity_group'] == 'LOC')
    score += 0.2 * min(per_count, 3)  # մինչև 3 անձ առավելագույն միավոր
    score += 0.1 * min(loc_count, 2)  # մինչև 2 տեղ առավելագույն միավոր
    # Աղբյուրի վստահելիություն, օրինակ՝ եթե ունես աղբյուրի վստահելիության ցուցակ
    source_weight = 0.1
    trusted_sources = ["azatutyun.am", "news.am", ...]  # լրացրու ինքդ
    if article.get("website") in trusted_sources:
        score += source_weight
    return {
        "id": article["id"],
        "score": score,
        "thematic_category": thematic_category,
        "thematic_score": thematic_score,
        "per_count": per_count,
        "loc_count": loc_count,
        "source": article.get("website")
    }