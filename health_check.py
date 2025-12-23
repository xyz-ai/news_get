import sqlite3
from datetime import datetime, timedelta

DB_PATH = "news.db"
MAX_IDLE_HOURS = 6

def parse_time(ts: str):
    try:
        return datetime.fromisoformat(ts)
    except ValueError:
        return datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")

def check_health():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT MAX(fetched_at) FROM news")
    last = cur.fetchone()[0]
    conn.close()

    if not last:
        print("❌ No data in database")
        return False

    last_time = parse_time(last)

    idle_hours = (datetime.now() - last_time).total_seconds() / 3600

    if idle_hours > MAX_IDLE_HOURS:
        print(f"⚠️ WARNING: No new data for {idle_hours:.1f} hours")
        return False
    else:
        print(f"✅ Healthy: last update {idle_hours:.1f} hours ago")
        return True


if __name__ == "__main__":
    check_health()
