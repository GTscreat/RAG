import psycopg2
import os 

PG_SETTINGS = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432")
}

def get_db_connection():
    """
    Հաստատում և վերադարձնում է միացում PostgreSQL տվյալների բազայի հետ։
    """
    try:
        conn = psycopg2.connect(**PG_SETTINGS)
        return conn
    except psycopg2.OperationalError as e:
        print(f"ՍԽԱԼ։ Չհաջողվեց միանալ PostgreSQL բազային։ {e}")
        return None