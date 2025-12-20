import feedparser

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

FEEDS = {
    "The Guardian - World": "https://www.theguardian.com/world/rss",
    "The Guardian - China": "https://www.theguardian.com/world/china/rss",
    "The Guardian - US": "https://www.theguardian.com/us-news/rss",

    "Fox News - World": "https://moxie.foxnews.com/google-publisher/world.xml",
    "Fox News - US": "https://moxie.foxnews.com/google-publisher/us.xml",

    "BBC - World": "https://feeds.bbci.co.uk/news/world/rss.xml",
    "BBC - China": "https://feeds.bbci.co.uk/news/world/asia/china/rss.xml",
    "BBC - US & Canada": "https://feeds.bbci.co.uk/news/world/us_and_canada/rss.xml",
}


def safe_get(entry, key, fallback=""):
    value = entry.get(key, fallback)
    return value if value is not None else fallback


def fetch_feed(source_name, url):
    print(f"\n===== {source_name} =====")
    feed = feedparser.parse(url, request_headers=HEADERS)

    if feed.bozo:
        print(f"{source_name} | ERROR | {feed.bozo_exception}")
        return

    if not feed.entries:
        print(f"{source_name} | WARNING | No entries found")
        return

    for entry in feed.entries[:10]:
        title = safe_get(entry, "title")
        published = safe_get(entry, "published")
        link = safe_get(entry, "link")
        print(f"{source_name} | {title} | {published} | {link}")


def main():
    print("🗞 Fetching news from RSS feeds...\n")
    for source_name, url in FEEDS.items():
        fetch_feed(source_name, url)


if __name__ == "__main__":
    main()
