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

        soup_raw = BeautifulSoup(resp.text, "html.parser")

        # Remove media/script tags before readability to avoid video-only text
        for tag in soup_raw.find_all(
            ["script", "style", "noscript", "video", "iframe", "source", "track"]
        ):
            tag.decompose()
        for fig in soup_raw.find_all("figure", class_="media"):
            fig.decompose()

        doc = Document(str(soup_raw))
        html = doc.summary(html_partial=True)

        soup = BeautifulSoup(html, "html.parser")

        for tag in soup(
            ["script", "style", "noscript", "video", "iframe", "source", "track"]
        ):
            tag.decompose()
        for fig in soup.find_all("figure", class_="media"):
            fig.decompose()

        paragraphs = []
        for p in soup.find_all("p"):
            text = p.get_text(" ", strip=True)
            if text:
                paragraphs.append(text)

        if not paragraphs:
            text = soup.get_text("\n")
            paragraphs = [line.strip() for line in text.splitlines() if line.strip()]

        return "\n\n".join(paragraphs)

    except Exception as e:
        return f"[Failed to load article]\n{e}"
