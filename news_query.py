import sqlite3
import argparse
from datetime import datetime, timedelta
from deep_translator import GoogleTranslator

DB_PATH = "news.db"

translator = GoogleTranslator(source="en", target="zh-CN")


def translate_text(text):
    try:
        return translator.translate(text)
    except Exception:
        return "[Translation failed]"


def build_query(args):
    conditions = []
    params = []

    if args.region:
        conditions.append("region = ?")
        params.append(args.region)

    if args.source:
        conditions.append("source LIKE ?")
        params.append(f"%{args.source}%")

    if args.days is not None:
        since = (datetime.utcnow() - timedelta(days=args.days)).isoformat()
        conditions.append("fetched_at >= ?")
        params.append(since)

    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    query = f"""
        SELECT source, region, title, link, published
        FROM news
        {where_clause}
        ORDER BY fetched_at DESC
        LIMIT ?
    """

    params.append(args.limit)
    return query, params


def fetch_news(args):
    query, params = build_query(args)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return rows


def print_news(rows, args):
    if not rows:
        print("⚠️ No results found.")
        return

    for source, region, title, link, published in rows:
        print(f"[{source} | {region}]")

        if args.translate or args.bilingual:
            zh_title = translate_text(title)

            if args.bilingual:
                print(f"EN: {title}")
                print(f"ZH: {zh_title}")
            else:
                print(zh_title)
        else:
            print(title)

        if published:
            print(f"🕒 {published}")
        print(f"🔗 {link}")
        print("-" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Query & translate news from local SQLite database"
    )

    parser.add_argument("--region", help="Region filter (China / US / World)")
    parser.add_argument("--source", help="Source keyword (BBC / Guardian / Fox)")
    parser.add_argument("--days", type=int, help="Last N days")
    parser.add_argument("--limit", type=int, default=20, help="Result limit")
    parser.add_argument("--latest", action="store_true", help="Latest news")

    parser.add_argument("--translate", action="store_true", help="Translate to Chinese")
    parser.add_argument(
        "--bilingual",
        action="store_true",
        help="Show English + Chinese",
    )

    args = parser.parse_args()

    if args.latest:
        args.region = None
        args.source = None
        args.days = None

    rows = fetch_news(args)
    print_news(rows, args)


if __name__ == "__main__":
    main()
