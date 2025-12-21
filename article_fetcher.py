# article_fetcher.py
import requests
from readability import Document
from bs4 import BeautifulSoup


def fetch_article_content(url: str) -> str:
    try:
        resp = requests.get(
            url,
            timeout=10,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )
        resp.raise_for_status()

        doc = Document(resp.text)
        html = doc.summary(html_partial=True)

        soup = BeautifulSoup(html, "html.parser")

        paragraphs = []
        for p in soup.find_all("p"):
            text = p.get_text(strip=True)
            if text:
                paragraphs.append(text)

        return "\n\n".join(paragraphs)

    except Exception as e:
        return f"[Failed to load article]\n{e}"
