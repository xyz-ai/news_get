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

        raw_soup = BeautifulSoup(resp.text, "html.parser")

        # Remove media / scripts before readability to avoid video-only noise
        for tag in raw_soup.find_all(
            ["script", "style", "noscript", "video", "iframe", "source", "track"]
        ):
            tag.decompose()
        for fig in raw_soup.find_all("figure", class_="media"):
            fig.decompose()

        doc = Document(str(raw_soup))
        html = doc.summary(html_partial=True)

        soup = BeautifulSoup(html, "html.parser")

        # 清理无用标签
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
            paragraphs = [l.strip() for l in text.splitlines() if l.strip()]

        return "\n\n".join(paragraphs)

    except Exception as e:
        return f"[Failed to fetch article]\n{e}"
