import sqlite3

DB_NAME = "commandes.db"

def get_db():
    return sqlite3.connect(DB_NAME)

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS commandes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero TEXT UNIQUE,
        client TEXT,
        telephone TEXT,
        adresse TEXT,
        recap TEXT,
        total INTEGER,
        statut TEXT,
        chat_id INTEGER
    )
    """)

    conn.commit()
    conn.close()
