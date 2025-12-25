# core/article_fetcher.py

import requests
from bs4 import BeautifulSoup


def fetch_article_content(url: str) -> str:
    try:
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()

        # 初始解析
        soup = BeautifulSoup(resp.text, "lxml")

        # -----------------------------
        # 第一步：全局清理无关内容
        # -----------------------------
        for tag in soup.find_all(
            ["script", "style", "noscript", "video", "iframe", "source", "track"]
        ):
            tag.decompose()

        for fig in soup.find_all("figure", class_="media"):
            fig.decompose()

        # -----------------------------
        # 第二步：尝试定位正文容器
        # -----------------------------
        article = (
            soup.find("article")
            or soup.find("main")
            or soup.find("div", {"id": "content"})
            or soup.find("div", {"class": "content"})
        )

        if article is None:
            article = soup.body or soup

        # -----------------------------
        # 第三步：提取段落文本
        # -----------------------------
        paragraphs = []
        for p in article.find_all("p"):
            text = p.get_text(" ", strip=True)
            if text and len(text) > 40:  # 过滤导航、广告、版权声明
                paragraphs.append(text)

        # -----------------------------
        # 第四步：兜底策略（极端页面）
        # -----------------------------
        if not paragraphs:
            text = article.get_text("\n", strip=True)
            paragraphs = [
                line for line in text.splitlines()
                if len(line.strip()) > 40
            ]

        if not paragraphs:
            return "[Failed to fetch article]\nNo readable content found."

        return "\n\n".join(paragraphs)

    except Exception as e:
        return f"[Failed to fetch article]\n{e}"
