import json
import sqlite3

def calculate_ner_importance(content_id: int, content_db_path: str, ner_db_path: str) -> float:
    """
    Հաշվում է կոնտենտի NER-երի կարևորությունը՝ հիմնվելով նոր տրամաբանության վրա։

    Args:
        content_id: Կոնտենտի ID-ն, որի համար պետք է հաշվարկ կատարել։
        content_db_path: Ճանապարհ դեպի հիմնական բազա (ner_results աղյուսակով)։
        ner_db_path: Ճանապարհ դեպի NER-երի բազան (entities և categories աղյուսակներով)։

    Returns:
        NER բառերի գործակիցների արտադրյալների ընդհանուր գումարը։
    """
    total_score_sum = 0.0
    
    # Ստեղծում ենք միացումներ երկու բազաներին
    content_conn = sqlite3.connect(content_db_path)
    ner_conn = sqlite3.connect(ner_db_path)
    
    try:
        content_cursor = content_conn.cursor()
        ner_cursor = ner_conn.cursor()

        # 1. Վերցնում ենք կոնտենտի NER բառերը `ner_results` աղյուսակից
        content_cursor.execute("SELECT entities FROM ner_results WHERE id = ?", (content_id,))
        result = content_cursor.fetchone()
        
        if not result or not result[0]:
            return 0.0  # Եթե NER-եր չկան, վերադարձնում ենք 0

        ner_entities_json = json.loads(result[0])
        words_to_check = [entity.get("word") for entity in ner_entities_json if entity.get("word")]

        # 2. Յուրաքանչյուր բառի համար փնտրում ենք գործակիցները nerdatabase.db-ում
        for word in words_to_check:
            # SQL հարցում, որը միացնում է entities և categories աղյուսակները
            sql_query = """
                SELECT
                    e.ner_score,
                    c.ner_class_index
                FROM entities AS e
                JOIN categories AS c ON e.category_id = c.id
                WHERE e.word = ?
            """
            ner_cursor.execute(sql_query, (word,))
            ner_data = ner_cursor.fetchone()

            if ner_data:
                ner_score = float(ner_data[0] or 0)
                ner_class_index = float(ner_data[1] or 0)
                
                # 3. Բազմապատկում ենք գործակիցները և գումարում ընդհանուրին
                product = ner_score * ner_class_index
                total_score_sum += product

    except Exception as e:
        print(f"Error calculating NER importance for content_id {content_id}: {e}")
        return 0.0 # Սխալի դեպքում վերադարձնում ենք 0
    finally:
        # Անպայման փակում ենք միացումները
        content_conn.close()
        ner_conn.close()
        
    return total_score_sum