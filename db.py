import sqlite3, os

def init_db():
    if not os.path.exists("database"):
        os.makedirs("database")
    conn = sqlite3.connect("database/members.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS members (
        user_id TEXT PRIMARY KEY,
        name TEXT,
        last_checkin TEXT
    )""")
    conn.commit()
    conn.close()
