# core/article_service.py

from core.article_repo import (
    get_article_by_link,
    save_article_en,
    save_article_zh,
)
from core.article_fetcher import fetch_article_content
from core.translator import translate_en_zh
from core.settings import AppSettings


def get_article(link: str) -> dict:
    """
    返回结构统一的文章对象：
    {
        "link": str,
        "title_en": str,
        "content_en": str,
        "content_zh": str | None
    }
    """

    # 1️⃣ 先查数据库
    article = get_article_by_link(link)

    if not article:
        # 理论上不该发生（因为 news 表里已有 link）
        raise RuntimeError(f"Article not found in DB: {link}")

    content_en = article.get("content_en")
    content_zh = article.get("content_zh")

    # 2️⃣ 没有英文正文 → 抓网页 + 存库
    if not content_en:
        content_en = fetch_article_content(link)
        save_article_en(link, content_en)

    # 3️⃣ 自动翻译（但只翻一次，翻完存）
    if AppSettings.auto_translate and not content_zh and content_en:
        try:
            content_zh = translate_en_zh(content_en)
            save_article_zh(link, content_zh)
        except Exception as e:
            content_zh = f"[Translation failed: {e}]"

    return {
        "link": link,
        "title_en": article.get("title"),
        "content_en": content_en,
        "content_zh": content_zh,
    }
