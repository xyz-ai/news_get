import sqlite3
from datetime import datetime, timedelta

DB_PATH = "news.db"


def get_latest_news(limit=20):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        """
        SELECT source, region, title, link, published, fetched_at
        FROM news
        ORDER BY fetched_at DESC
        LIMIT ?
        """,
        (limit,),
    )

    rows = cur.fetchall()
    conn.close()
    return rows


def get_news_by_region(region, days=1, limit=50):
    since = (datetime.utcnow() - timedelta(days=days)).isoformat()

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        """
        SELECT source, region, title, link, published
        FROM news
        WHERE region = ?
          AND fetched_at >= ?
        ORDER BY fetched_at DESC
        LIMIT ?
        """,
        (region, since, limit),
    )

    rows = cur.fetchall()
    conn.close()
    return rows


def print_news(rows, title):
    print(f"\n📰 {title}")
    print("=" * 60)
    for source, region, title, link, published, *rest in rows:
        print(f"[{source} | {region}]")
        print(f"{title}")
        if published:
            print(f"🕒 {published}")
        print(f"🔗 {link}")
        print("-" * 60)


def main():
    # 1️⃣ 最新新闻
    latest = get_latest_news(limit=20)
    print_news(latest, "Latest News")

    # 2️⃣ 中国相关新闻（最近 2 天）
    china_news = get_news_by_region("China", days=2, limit=20)
    print_news(china_news, "China News (Last 2 Days)")

    # 3️⃣ 美国相关新闻（最近 1 天）
    us_news = get_news_by_region("US", days=1, limit=20)
    print_news(us_news, "US News (Last 24 Hours)")


if __name__ == "__main__":
    main()
