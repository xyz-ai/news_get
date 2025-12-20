import sqlite3
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.rule import Rule
from deep_translator import GoogleTranslator

DB_PATH = "news.db"

console = Console()
translator = GoogleTranslator(source="en", target="zh-CN")


def fetch_latest(limit=20):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT source, region, title, link, published
        FROM news
        ORDER BY fetched_at DESC
        LIMIT ?
        """,
        (limit,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def render_news(rows, translate=False, bilingual=False):
    for source, region, title, link, published in rows:
        header = Text(f"{source} | {region}", style="bold cyan")
        console.print(Panel(header, expand=False))

        if translate or bilingual:
            try:
                zh = translator.translate(title)
            except Exception:
                zh = "[Translation failed]"

            if bilingual:
                console.print(Text(f"EN: {title}", style="white"))
                console.print(Text(f"ZH: {zh}", style="bold yellow"))
            else:
                console.print(Text(zh, style="bold yellow"))
        else:
            console.print(Text(title, style="white"))

        if published:
            console.print(Text(f"🕒 {published}", style="dim"))
        console.print(Text(f"🔗 {link}", style="blue underline"))
        console.print(Rule())


def main():
    console.print("\n📰 [bold green]Latest News Reader[/bold green]\n")

    rows = fetch_latest(limit=20)
    render_news(rows, translate=True, bilingual=False)


if __name__ == "__main__":
    main()
