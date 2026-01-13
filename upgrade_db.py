import sqlite3

conn = sqlite3.connect("news.db")
cur = conn.cursor()

def add_column(sql):
    try:
        cur.execute(sql)
        print("OK:", sql)
    except sqlite3.OperationalError as e:
        print("SKIP:", e)

add_column("ALTER TABLE news ADD COLUMN content_en TEXT")
add_column("ALTER TABLE news ADD COLUMN content_zh TEXT")
add_column("ALTER TABLE news ADD COLUMN content_fetched INTEGER DEFAULT 0")
add_column("ALTER TABLE news ADD COLUMN content_updated_at TEXT")

conn.commit()
conn.close()
