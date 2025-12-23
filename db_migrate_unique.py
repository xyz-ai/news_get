import sqlite3

DB_PATH = "news.db"

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# 1. 创建新表（带 UNIQUE 约束）
cur.execute("""
CREATE TABLE IF NOT EXISTS news_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT,
    region TEXT,
    title TEXT,
    link TEXT UNIQUE,
    published TEXT,
    fetched_at TEXT
)
""")

# 2. 迁移旧数据（自动去重）
cur.execute("""
INSERT OR IGNORE INTO news_new (source, region, title, link, published, fetched_at)
SELECT source, region, title, link, published, fetched_at FROM news
""")

# 3. 删除旧表
cur.execute("DROP TABLE news")

# 4. 重命名
cur.execute("ALTER TABLE news_new RENAME TO news")

conn.commit()
conn.close()

print("✅ 数据库迁移完成，link 已唯一")
