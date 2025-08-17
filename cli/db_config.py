import os

DB_PATH = os.getenv("DB_PATH", "glow_nest.db")

def get_db_path() -> str:
    return DB_PATH
