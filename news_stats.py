import sqlite3
from datetime import datetime, timedelta

DB_PATH = "news.db"


def get_stats():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    stats = {}

    # 1. 总新闻数
    cur.execute("SELECT COUNT(*) FROM news")
    stats["total_news"] = cur.fetchone()[0]

    # 2. 今日新增
    today = datetime.now().strftime("%Y-%m-%d")
    cur.execute("""
        SELECT COUNT(*) FROM news
        WHERE fetched_at LIKE ?
    """, (today + "%",))
    stats["today_new"] = cur.fetchone()[0]

    # 3. 最近 24 小时新增
    since = (datetime.now() - timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
    cur.execute("""
        SELECT COUNT(*) FROM news
        WHERE fetched_at >= ?
    """, (since,))
    stats["last_24h_new"] = cur.fetchone()[0]

    # 4. 按来源统计
    cur.execute("""
        SELECT source, COUNT(*) FROM news
        GROUP BY source
        ORDER BY COUNT(*) DESC
    """)
    stats["by_source"] = cur.fetchall()

    # 5. 按地区统计
    cur.execute("""
        SELECT region, COUNT(*) FROM news
        GROUP BY region
    """)
    stats["by_region"] = cur.fetchall()

    # 6. 最近抓取时间
    cur.execute("SELECT MAX(fetched_at) FROM news")
    stats["last_fetch_time"] = cur.fetchone()[0]

    conn.close()
    return stats


def print_stats(stats):
    print("\n📊 News System Stats")
    print("=" * 40)
    print(f"📰 Total news        : {stats['total_news']}")
    print(f"🆕 Today new         : {stats['today_new']}")
    print(f"⏱ Last 24h new      : {stats['last_24h_new']}")
    print(f"🕒 Last fetch time  : {stats['last_fetch_time']}")
    print("\n📌 By Source")
    for s, c in stats["by_source"]:
        print(f"  - {s}: {c}")

    print("\n🌍 By Region")
    for r, c in stats["by_region"]:
        print(f"  - {r}: {c}")


if __name__ == "__main__":
    stats = get_stats()
    print_stats(stats)
