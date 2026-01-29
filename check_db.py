import sqlite3

conn = sqlite3.connect("news.db")
cur = conn.cursor()

rows = cur.execute(
    "SELECT name, sql FROM sqlite_master WHERE type='table'"
).fetchall()

for name, sql in rows:
    print("TABLE:", name)
    print(sql)
    print("-" * 60)

conn.close()
