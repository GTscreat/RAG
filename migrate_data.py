import sqlite3
import psycopg2
from dotenv import load_dotenv
import os
import json

# --- ԿԱՐԳԱՎՈՐՈՒՄՆԵՐ ---
# Փոխարինեք ձեր տվյալներով
SQLITE_DB_PATH = 'data/database.db'

load_dotenv()
password = os.getenv("POSTGRES_PASSWORD")

PG_SETTINGS = {
    "dbname": "Dpir_database",  # Ձեր ստեղծած PostgreSQL բազայի անունը
    "user": "postgres",
    "password": password, # Ձեր սահմանած գաղտնաբառը
    "host": "localhost",
    "port": "5432"
}

def migrate_data():
    """Հիմնական ֆունկցիան, որը կառավարում է միգրացիայի ամբողջ գործընթացը։"""
    
    sqlite_conn = None
    pg_conn = None
    
    try:
        # Միանում ենք բազաներին
        sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)
        pg_conn = psycopg2.connect(**PG_SETTINGS)

        sqlite_cursor = sqlite_conn.cursor()
        pg_cursor = pg_conn.cursor()
        
        print("Միգրացիան սկսված է... Սա կարող է տևել որոշ ժամանակ։")

        # ID-ների համապատասխանեցման բառարաններ
        content_id_map = {}  # {հին_sqlite_id: նոր_pg_id}
        category_id_map = {} # {հին_sqlite_id: նոր_pg_id}

        # Քայլ 1: Տեղափոխել "մայր" աղյուսակները և ստեղծել ID քարտեզներ (maps)
        # ---------------------------------------------------------------------
        print("\n[1/10] 'content' աղյուսակի միգրացիա...")
        sqlite_cursor.execute("SELECT id, website, title, content, url, meta, published_at FROM content")
        for row in sqlite_cursor.fetchall():
            old_id = row[0]
            # INSERT-ը վերադարձնում է նոր ստեղծված ID-ն
            pg_cursor.execute(
                "INSERT INTO content (website, title, content, url, meta, published_at) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
                (row[1], row[2], row[3], row[4], row[5], row[6])
            )
            new_id = pg_cursor.fetchone()[0]
            content_id_map[old_id] = new_id
        print(f"-> 'content' ավարտված է։ {len(content_id_map)} տող մշակված է։")


        print("\n[2/10] 'categories' աղյուսակի միգրացիա...")
        sqlite_cursor.execute("SELECT id, code, path, ner_class_index, ner_class_opposite FROM categories")
        for row in sqlite_cursor.fetchall():
            old_id = row[0]
            pg_cursor.execute(
                "INSERT INTO entity_categories (code, path, ner_category_index, ner_category_opp_index) VALUES (%s, %s, %s, %s) RETURNING id",
                (row[1], row[2], row[3], row[4])
            )
            new_id = pg_cursor.fetchone()[0]
            category_id_map[old_id] = new_id
        print(f"-> 'categories' ավարտված է։ {len(category_id_map)} տող մշակված է։")


        # Քայլ 2: Տեղափոխել "երեխա" աղյուսակները՝ օգտագործելով ID քարտեզները
        # ---------------------------------------------------------------------
        print("\n[3/10] 'embeddings' աղյուսակի միգրացիա...")
        sqlite_cursor.execute("SELECT article_id, website, title, published_at, url, meta, chunk_content, chunk_start, chunk_end, embedding FROM embeddings")
        for row in sqlite_cursor.fetchall():
            old_article_id = row[0]
            new_article_id = content_id_map.get(old_article_id)
            if new_article_id:
                pg_cursor.execute(
                    "INSERT INTO embeddings (article_id, website, title, published_at, url, meta, chunk_content, chunk_start, chunk_end, embedding) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (new_article_id, row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9])
                )
        print("-> 'embeddings' ավարտված է։")


        print("\n[4/10] 'ner_results' աղյուսակի միգրացիա...")
        sqlite_cursor.execute("SELECT id, entities FROM ner_results")
        for row in sqlite_cursor.fetchall():
            old_id = row[0]
            new_id = content_id_map.get(old_id)
            if new_id:
                pg_cursor.execute("INSERT INTO ner_results (id, entities) VALUES (%s, %s)", (new_id, row[1]))
        print("-> 'ner_results' ավարտված է։")


        print("\n[5/10] 'parameters' աղյուսակի միգրացիա...")
        sqlite_cursor.execute("SELECT id, category, aver_embedding, similarity FROM parameters")
        for row in sqlite_cursor.fetchall():
            old_id = row[0]
            new_id = content_id_map.get(old_id)
            if new_id:
                pg_cursor.execute("INSERT INTO parameters (id, category, aver_embedding, similarity) VALUES (%s, %s, %s, %s)", (new_id, row[1], row[2], row[3]))
        print("-> 'parameters' ավարտված է։")


        print("\n[6/10] 'ranks' աղյուսակի միգրացիա...")
        sqlite_cursor.execute("SELECT id, topic_importance, ner_content_importance, frequency_importance, source_importance, total_score FROM ranks")
        for row in sqlite_cursor.fetchall():
            old_id = row[0]
            new_id = content_id_map.get(old_id)
            if new_id:
                pg_cursor.execute("INSERT INTO ranks (id, topic_importance, ner_content_importance, frequency_importance, source_importance, total_score) VALUES (%s, %s, %s, %s, %s, %s)", (new_id, *row[1:]))
        print("-> 'ranks' ավարտված է։")
        

        print("\n[7/10] 'top' աղյուսակի միգրացիա...")
        sqlite_cursor.execute("SELECT id, total_score, ai_score, urgency, sentiment, geopolitical, final_score FROM top")
        for row in sqlite_cursor.fetchall():
            old_id = row[0]
            new_id = content_id_map.get(old_id)
            if new_id:
                pg_cursor.execute("INSERT INTO top (id, total_score, ai_score, urgency, sentiment, geopolitical, final_score) VALUES (%s, %s, %s, %s, %s, %s, %s)", (new_id, *row[1:]))
        print("-> 'top' ավարտված է։")


        print("\n[8/10] 'processed' աղյուսակի միգրացիա...")
        sqlite_cursor.execute("SELECT base_id, title, generated_content, published, title_r, generated_content_r, published_r FROM processed")
        for row in sqlite_cursor.fetchall():
            old_base_id = row[0]
            new_base_id = content_id_map.get(old_base_id)
            if new_base_id:
                pg_cursor.execute("INSERT INTO processed (base_id, title, generated_content, published, title_r, generated_content_r, published_r) VALUES (%s, %s, %s, %s, %s, %s, %s)", (new_base_id, *row[1:]))
        print("-> 'processed' ավարտված է։")


        print("\n[9/10] 'entities' աղյուսակի միգրացիա...")
        sqlite_cursor.execute("SELECT entity_group, score, word, ner_score, category_id FROM entities")
        for row in sqlite_cursor.fetchall():
            old_category_id = row[4]
            new_category_id = category_id_map.get(old_category_id)
            # new_category_id-ն կարող է լինել None, եթե կապ չկա, դա նորմալ է
            pg_cursor.execute("INSERT INTO entities (entity_group, score, word, ner_score, category_id) VALUES (%s, %s, %s, %s, %s)", (row[0], row[1], row[2], row[3], new_category_id))
        print("-> 'entities' ավարտված է։")
        

        # Քայլ 3: Տեղափոխել անկախ աղյուսակները
        # -------------------------------------------------
        print("\n[10/10] 'ner_rating' աղյուսակի միգրացիա...")
        sqlite_cursor.execute("SELECT word, score FROM ner_rating")
        for row in sqlite_cursor.fetchall():
            pg_cursor.execute("INSERT INTO ner_rating (word, score) VALUES (%s, %s)", row)
        print("-> 'ner_rating' ավարտված է։")


        # Եթե ամեն ինչ բարեհաջող է, հաստատում ենք բոլոր փոփոխությունները
        pg_conn.commit()
        print("\n✅ Միգրացիան հաջողությամբ ավարտվեց։ Բոլոր փոփոխությունները պահպանվեցին։")

    except (Exception, psycopg2.Error) as error:
        print(f"\n❌ ՍԽԱԼ։ Միգրացիայի ընթացքում սխալ տեղի ունեցավ. {error}")
        if pg_conn:
            # Սխալի դեպքում հետ ենք կանգնում բոլոր փոփոխություններից
            pg_conn.rollback()
            print("Բոլոր փոփոխությունները հետ կանչվեցին (rollback)։")
    
    finally:
        # Անկախ ամեն ինչից, փակում ենք միացումները
        if pg_conn:
            pg_cursor.close()
            pg_conn.close()
            print("\nPostgreSQL միացումը փակված է։")
        if sqlite_conn:
            sqlite_cursor.close()
            sqlite_conn.close()
            print("SQLite միացումը փակված է։")


if __name__ == '__main__':
    migrate_data()