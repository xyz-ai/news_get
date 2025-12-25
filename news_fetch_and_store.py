import sqlite3
from datetime import datetime
import requests
from lxml import etree

# -----------------------------
# RSS FEEDS（不含 Reuters）
# -----------------------------
FEEDS = {
    "The Guardian - World": {
        "url": "https://www.theguardian.com/world/rss",
        "region": "World",
    },
    "The Guardian - China": {
        "url": "https://www.theguardian.com/world/china/rss",
        "region": "China",
    },
    "The Guardian - US": {
        "url": "https://www.theguardian.com/us-news/rss",
        "region": "US",
    },
    "Fox News - World": {
        "url": "https://moxie.foxnews.com/google-publisher/world.xml",
        "region": "World",
    },
    "Fox News - US": {
        "url": "https://moxie.foxnews.com/google-publisher/us.xml",
        "region": "US",
    },
    "BBC - World": {
        "url": "https://feeds.bbci.co.uk/news/world/rss.xml",
        "region": "World",
    },
    "BBC - China": {
        "url": "https://feeds.bbci.co.uk/news/world/asia/china/rss.xml",
        "region": "China",
    },
    "BBC - US & Canada": {
        "url": "https://feeds.bbci.co.uk/news/world/us_and_canada/rss.xml",
        "region": "US",
    },
}

DB_PATH = "news.db"


# -----------------------------
# Database
# -----------------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT,
            region TEXT,
            title TEXT,
            link TEXT UNIQUE,
            published TEXT,
            fetched_at TEXT,
            content_en TEXT,
            content_zh TEXT,
            content_fetched INTEGER DEFAULT 0,
            content_updated_at TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def save_news(source, region, title, link, published):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT OR IGNORE INTO news
            (source, region, title, link, published, fetched_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                source,
                region,
                title,
                link,
                published,
                datetime.utcnow().isoformat(),
            ),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    finally:
        conn.close()


# -----------------------------
# RSS Fetch (NO feedparser)
# -----------------------------
def parse_rss(url):
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()

    root = etree.fromstring(resp.content)
    items = root.xpath("//item")

    results = []
    for item in items:
        title = get_text(item, "title")
        link = get_text(item, "link")
        published = get_text(item, "pubDate")

        results.append(
            {
                "title": title,
                "link": link,
                "published": published,
            }
        )

    return results


def get_text(node, tag):
    el = node.find(tag)
    return el.text.strip() if el is not None and el.text else ""


def fetch_and_store():
    for source, meta in FEEDS.items():
        url = meta["url"]
        region = meta["region"]

        print(f"\n===== {source} =====")

        try:
            entries = parse_rss(url)
        except Exception as e:
            print(f"{source} | ERROR | {e}")
            continue

        for entry in entries:
            title = entry["title"]
            link = entry["link"]
            published = entry["published"]

            save_news(source, region, title, link, published)
            print(f"✔ {title}")


def main():
    print("🗄 Initializing database...")
    init_db()
    print("🗞 Fetching & storing news...")
    fetch_and_store()
    print("\n✅ Done.")


if __name__ == "__main__":
    main()
