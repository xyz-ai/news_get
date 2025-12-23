import sqlite3
from datetime import datetime, timedelta

DB_PATH = "news.db"
KEEP_DAYS = 30


def cleanup_by_days():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cutoff = (datetime.now() - timedelta(days=KEEP_DAYS)).isoformat()

    cur.execute("""
        DELETE FROM news
        WHERE fetched_at < ?
    """, (cutoff,))

    deleted = cur.rowcount
    conn.commit()

    # 真正释放磁盘空间
    cur.execute("VACUUM")
    conn.close()

    print(f"🧹 Cleaned {deleted} records older than {KEEP_DAYS} days")


MAX_RECORDS = 5000


def cleanup_by_max_records():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM news")
    total = cur.fetchone()[0]

    if total <= MAX_RECORDS:
        print("📦 Record count within limit, no cleanup needed")
        conn.close()
        return

    to_delete = total - MAX_RECORDS

    cur.execute("""
        DELETE FROM news
        WHERE id IN (
            SELECT id FROM news
            ORDER BY fetched_at ASC
            LIMIT ?
        )
    """, (to_delete,))

    conn.commit()
    cur.execute("VACUUM")
    conn.close()

    print(f"📦 Trimmed {to_delete} old records (max {MAX_RECORDS})")


if __name__ == "__main__":
    cleanup_by_days()
    cleanup_by_max_records()