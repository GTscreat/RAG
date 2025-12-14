import sqlite3
import psycopg2
import sys
from datetime import datetime # Ավելացնում ենք datetime գրադարանը

# --- ԿՈՆՖԻԳՈՒՐԱՑԻԱ ---
# Փոխարինեք այս տվյալները ձեր սեփական տվյալներով

# 1. SQLite բազայի ֆայլի ճանապարհը
sqlite_db_path = 'RAG_old_version/data/database.db'

# 2. PostgreSQL բազայի միացման տվյալները
pg_config = {
    'dbname': 'Dpir_database',
    'user': 'postgres',
    'password': 'Aylabanutyun1991',
    'host': 'localhost',
    'port': '5432'
}

# 3. Աղյուսակի և սյունակի անունները
table_name = 'content'
table_name_postgres = 'news'
datetime_column_name = 'published_at'

# 4. SQLite-ի ամսաթվի ֆորմատը
SQLITE_DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'

# 5. Սյունակներ, որոնք պետք է բաց թողնել տեղափոխման ժամանակ
EXCLUDED_COLUMNS = ['website'] 

# 6. (ՆՈՐ) Սյունակներ, որոնք պետք է ավելացվեն ֆիքսված արժեքով
# Օգտակար է, երբ Postgres-ի աղյուսակն ունի NOT NULL սյունակ, որը չկա SQLite-ում
DEFAULT_VALUES = {
    'website_id': 1
}


# --- ՍԿՐԻՊՏԻ ՏՐԱՄԱԲԱՆՈՒԹՅՈՒՆԸ ---

def migrate_data():
    sqlite_conn = None
    postgres_conn = None
    
    try:
        # Միացումներ բազաներին
        print("Connecting to databases...")
        sqlite_conn = sqlite3.connect(sqlite_db_path)
        sqlite_cursor = sqlite_conn.cursor()
        postgres_conn = psycopg2.connect(**pg_config)
        postgres_cursor = postgres_conn.cursor()
        
        # 1. Ստանալ տվյալները SQLite-ից
        print(f"Fetching data from SQLite table '{table_name}'...")
        sqlite_cursor.execute(f"SELECT * FROM {table_name}")
        
        source_column_names = [description[0] for description in sqlite_cursor.description]
        all_rows = sqlite_cursor.fetchall()

        if not all_rows:
            print("No data found in the source table. Exiting.")
            return

        print(f"Fetched {len(all_rows)} rows from SQLite.")
        
        # 2. Ֆիլտրում և պատրաստում ենք սյունակների ցանկը
        print(f"Excluding columns: {', '.join(EXCLUDED_COLUMNS)}")
        target_column_names = [col for col in source_column_names if col not in EXCLUDED_COLUMNS]
        indices_to_keep = [source_column_names.index(col) for col in target_column_names]
        
        # Ավելացնում ենք ֆիքսված արժեքով սյունակների անունները
        if DEFAULT_VALUES:
            target_column_names.extend(DEFAULT_VALUES.keys())

        print(f"Final columns for insertion: {', '.join(target_column_names)}")

        # 3. Մշակում ենք յուրաքանչյուր տողը
        processed_rows = []
        
        dt_column_index_in_target = -1
        if datetime_column_name in target_column_names:
            dt_column_index_in_target = target_column_names.index(datetime_column_name)

        for row in all_rows:
            # Ստեղծում ենք նոր տող՝ միայն պահպանվող սյունակների տվյալներով
            filtered_row_list = [row[i] for i in indices_to_keep]
            
            # Մշակում ենք ամսաթիվը, եթե այն առկա է
            if dt_column_index_in_target != -1:
                date_string = filtered_row_list[dt_column_index_in_target]
                
                if date_string and isinstance(date_string, str):
                    try:
                        datetime_object = datetime.strptime(date_string, SQLITE_DATETIME_FORMAT)
                        filtered_row_list[dt_column_index_in_target] = datetime_object
                    except ValueError:
                        filtered_row_list[dt_column_index_in_target] = None
                else:
                    filtered_row_list[dt_column_index_in_target] = None
            
            # Ավելացնում ենք ֆիքսված արժեքները տողի վերջում
            if DEFAULT_VALUES:
                filtered_row_list.extend(DEFAULT_VALUES.values())

            processed_rows.append(tuple(filtered_row_list))

        # 4. Ներմուծել տվյալները PostgreSQL
        print(f"Inserting data into PostgreSQL table '{table_name_postgres}'...")
        
        cols_string = ", ".join(target_column_names)
        vals_string = ", ".join(["%s"] * len(target_column_names))
        insert_query = f"INSERT INTO {table_name_postgres} ({cols_string}) VALUES ({vals_string})"
        
        postgres_cursor.executemany(insert_query, processed_rows)
        postgres_conn.commit()
        
        print("\nMigration successful!")
        print(f"{postgres_cursor.rowcount} rows were inserted into PostgreSQL.")

    except (Exception, psycopg2.Error, sqlite3.Error) as error:
        print(f"\nError during migration: {error}", file=sys.stderr)
        if postgres_conn:
            postgres_conn.rollback()
            print("PostgreSQL transaction has been rolled back.", file=sys.stderr)

    finally:
        if sqlite_conn:
            sqlite_conn.close()
        if postgres_conn:
            postgres_conn.close()
        print("Database connections closed.")

if __name__ == '__main__':
    migrate_data()