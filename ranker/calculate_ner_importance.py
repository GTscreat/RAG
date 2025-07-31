# ranker/ner_importance.py
import json
from db import SessionLocal, NERResult, Entity, EntityCategory

def calculate_ner_importance(content_id: int) -> float:
    """
    Հաշվում է կոնտենտի NER-երի կարևորությունը՝ օգտագործելով 
    միասնական PostgreSQL տվյալների բազան։

    Args:
        content_id: Կոնտենտի ID-ն, որի համար պետք է հաշվարկ կատարել։

    Returns:
        NER բառերի գործակիցների արտադրյալների ընդհանուր գումարը։
    """
    # Օգտագործում ենք 'with' բլոկը՝ սեսիայի անվտանգ կառավարման համար
    with SessionLocal() as session:
        try:
            # 1. Վերցնում ենք կոնտենտի NER բառերը `ner_results` աղյուսակից
            ner_result_obj = session.query(NERResult.entities).filter(NERResult.id == content_id).first()
            
            if not ner_result_obj or not ner_result_obj.entities:
                return 0.0  # Եթե NER-եր չկան, վերադարձնում ենք 0

            # SQLAlchemy-ն JSONB դաշտը ավտոմատ վերադարձնում է որպես Python dict/list
            ner_entities = ner_result_obj.entities
            words_to_check = {entity.get("word") for entity in ner_entities if entity.get("word")}

            if not words_to_check:
                return 0.0

            # 2. Կատարում ենք ՄԵԿ արդյունավետ հարցում՝ բոլոր բառերի տվյալները ստանալու համար
            # Սա փոխարինում է հին կոդի ցիկլի մեջ կատարվող բազմաթիվ հարցումներին
            word_scores_query = session.query(
                Entity.word,
                Entity.ner_score,
                EntityCategory.ner_category_index  # Օգտագործում ենք ճիշտ սյան անունը
            ).join(
                EntityCategory, Entity.category_id == EntityCategory.id
            ).filter(
                Entity.word.in_(words_to_check)
            )
            
            word_data = {word: (score, index) for word, score, index in word_scores_query.all()}

            # 3. Հաշվարկում ենք ընդհանուր գումարը Python-ում
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
            return 0.0 # Սխալի դեպքում վերադարձնում ենք 0

# Օրինակ օգտագործման համար
if __name__ == "__main__":
    # Այս հատվածը նույնպես պետք է թարմացվի, քանի որ այլևս երկու բազա չկա
    # Սա պարզապես ցուցադրական օրինակ է
    
    # Ենթադրենք՝ մենք ուզում ենք ստուգել 1-ին ID-ով կոնտենտը
    content_id_to_test = 1 
    
    print(f"Հաշվարկում ենք NER կարևորությունը ID={content_id_to_test}-ի համար...")
    importance_score = calculate_ner_importance(content_id_to_test)
    print(f"ID={content_id_to_test}-ի NER կարևորության գործակիցը՝ {importance_score}")