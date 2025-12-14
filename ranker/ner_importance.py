# ranker/ner_importance.py
from db import SessionLocal, Parameter, Entity, EntityCategory

def calculate_ner_importance(content_id: int) -> float:
    """
    Հաշվում է կոնտենտի NER-երի կարևորությունը՝ տվյալները վերցնելով Parameter աղյուսակից։
    """
    with SessionLocal() as session:
        try:
            # ՓՈՓՈԽՈՒԹՅՈՒՆ. Կարդում ենք Parameter աղյուսակից, ոչ թե NERResult-ից
            param_obj = session.query(Parameter.entities).filter(Parameter.id == content_id).first()
            
            if not param_obj or not param_obj.entities:
                return 0.0

            ner_entities = param_obj.entities
            words_to_check = {entity.get("word") for entity in ner_entities if entity.get("word")}

            if not words_to_check:
                return 0.0

            # ... (ֆունկցիայի մնացած տրամաբանությունը մնում է նույնը) ...
            word_scores_query = session.query(
                Entity.word,
                Entity.ner_score,
                EntityCategory.ner_category_index
            ).join(
                EntityCategory, Entity.category_id == EntityCategory.id
            ).filter(
                Entity.word.in_(words_to_check)
            )
            
            word_data = {word: (score, index) for word, score, index in word_scores_query.all()}

            total_score_sum = 0.0
            for word in words_to_check:
                if word in word_data:
                    ner_score, ner_category_index = word_data[word]
                    ner_score = float(ner_score or 0)
                    ner_category_index = float(ner_category_index or 0)
                    total_score_sum += (ner_score * ner_category_index)
            
            return total_score_sum

        except Exception as e:
            print(f"Սխալ՝ NER-ի կարևորությունը հաշվելիս (content_id {content_id}): {e}")
            return 0.0

# Օրինակ օգտագործման համար
if __name__ == "__main__":
    # Այս հատվածը նույնպես պետք է թարմացվի, քանի որ այլևս երկու բազա չկա
    # Սա պարզապես ցուցադրական օրինակ է
    
    # Ենթադրենք՝ մենք ուզում ենք ստուգել 1-ին ID-ով կոնտենտը
    content_id_to_test = 1 
    
    print(f"Հաշվարկում ենք NER կարևորությունը ID={content_id_to_test}-ի համար...")
    importance_score = calculate_ner_importance(content_id_to_test)
    print(f"ID={content_id_to_test}-ի NER կարևորության գործակիցը՝ {importance_score}")