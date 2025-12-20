import sqlite3
from datetime import datetime, timedelta
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.rule import Rule
from deep_translator import GoogleTranslator

DB_PATH = "news.db"
PAGE_SIZE = 10

console = Console()
translator = GoogleTranslator(source="en", target="zh-CN")

THEMES = {
    "dark": {
        "title": "white",
        "meta": "dim",
        "link": "blue underline",
        "source": "bold cyan",
        "zh": "bold yellow",
    }
}

theme = THEMES["dark"]


def fetch_page(offset):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT source, region, title, link, published
        FROM news
        ORDER BY fetched_at DESC
        LIMIT ? OFFSET ?
        """,
        (PAGE_SIZE, offset),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def clear_old_news(days=7):
    cutoff = datetime.utcnow() - timedelta(days=days)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM news WHERE fetched_at < ?",
        (cutoff.isoformat(),),
    )
    deleted = cur.rowcount
    conn.commit()
    conn.close()
    return deleted


def render(rows, mode):
    console.clear()
    console.print(f"📰 News Reader  | Mode: {mode.upper()}  | n/p 翻页 | t 翻译 | b 对照 | c 清理 | q 退出\n")

    for source, region, title, link, published in rows:
        header = Text(f"{source} | {region}", style=theme["source"])
        console.print(Panel(header, expand=False))

        if mode in ("translate", "bilingual"):
            try:
                zh = translator.translate(title)
            except Exception:
                zh = "[Translation failed]"

            if mode == "bilingual":
                console.print(Text(f"EN: {title}", style=theme["title"]))
                console.print(Text(f"ZH: {zh}", style=theme["zh"]))
            else:
                console.print(Text(zh, style=theme["zh"]))
        else:
            console.print(Text(title, style=theme["title"]))

        if published:
            console.print(Text(f"🕒 {published}", style=theme["meta"]))
        console.print(Text(f"🔗 {link}", style=theme["link"]))
        console.print(Rule())


def main():
    offset = 0
    mode = "translate"

    while True:
        rows = fetch_page(offset)
        if not rows:
            offset = max(0, offset - PAGE_SIZE)
            continue

        render(rows, mode)
        key = input(">>> ").strip().lower()

        if key == "n":
            offset += PAGE_SIZE
        elif key == "p":
            offset = max(0, offset - PAGE_SIZE)
        elif key == "t":
            mode = "translate"
        elif key == "b":
            mode = "bilingual"
        elif key == "c":
            days = input("保留最近多少天？(默认7)：").strip()
            days = int(days) if days.isdigit() else 7
            deleted = clear_old_news(days)
            console.print(f"🗑 已删除 {deleted} 条旧新闻")
            input("按回车继续...")
        elif key == "q":
            break


if __name__ == "__main__":
    main()
