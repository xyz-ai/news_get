# core/article_fetcher.py

import requests
from readability import Document
from bs4 import BeautifulSoup


def fetch_article_content(url: str) -> str:
    try:
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()

        doc = Document(resp.text)
        html = doc.summary(html_partial=True)

        soup = BeautifulSoup(html, "html.parser")

        # 清理无用标签
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        text = soup.get_text("\n")
        lines = [l.strip() for l in text.splitlines() if l.strip()]

        return "\n\n".join(lines)

    except Exception as e:
        return f"[Failed to fetch article]\n{e}"
