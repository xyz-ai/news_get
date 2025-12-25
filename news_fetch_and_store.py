# news_fetch_and_store.py
import sqlite3
import requests
from lxml import etree
from datetime import datetime
from pathlib import Path

# ===============================
# Database
# ===============================

DB_PATH = Path("news.db")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT,
            title TEXT,
            link TEXT UNIQUE,
            summary TEXT,
            published TEXT,
            fetched_at TEXT
        )
        """
    )
    conn.commit()
    conn.close()


# ===============================
# RSS Parsing (NO feedparser)
# ===============================

def parse_rss(url: str):
    """
    Parse RSS feed using requests + lxml
    Returns list of dicts
    """
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()

    root = etree.fromstring(resp.content)

    items = root.xpath("//item")
    results = []

    for item in items:
        title = _text(item, "title")
        link = _text(item, "link")
        summary = _text(item, "description")
        pub_date = _text(item, "pubDate")

        results.append(
            {
                "title": title,
                "link": link,
                "summary": summary,
                "published": pub_date,
            }
        )

    return results


def _text(node, tag):
    el = node.find(tag)
    return el.text.strip() if el is not None and el.text else ""


# ===============================
# Fetch & Store
# ===============================

def fetch_and_store(source_name: str, rss_url: str):
    """
    Fetch RSS and store new items into SQLite
    Returns number of inserted rows
    """
    init_db()

    try:
        items = parse_rss(rss_url)
    except Exception as e:
        print(f"[ERROR] Failed to fetch {rss_url}: {e}")
        return 0

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    inserted = 0
    now = datetime.utcnow().isoformat(timespec="seconds")

    for item in items:
        try:
            c.execute(
                """
                INSERT OR IGNORE INTO news
                (source, title, link, summary, published, fetched_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    source_name,
                    item["title"],
                    item["link"],
                    item["summary"],
                    item["published"],
                    now,
                ),
            )
            if c.rowcount > 0:
                inserted += 1
        except Exception as e:
            print(f"[WARN] Failed to insert item: {e}")

    conn.commit()
    conn.close()

    return inserted
