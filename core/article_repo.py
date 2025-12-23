# core/article_repo.py

import sqlite3
from pathlib import Path

DB_PATH = Path("news.db")


def _get_conn():
    return sqlite3.connect(DB_PATH)


def get_article_by_link(link: str) -> dict | None:
    """
    从数据库读取文章（包含正文缓存）
    """
    conn = _get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT title, link, content_en, content_zh
        FROM news
        WHERE link = ?
        """,
        (link,),
    )
    row = cur.fetchone()
    conn.close()

    if not row:
        return None

    title, link, content_en, content_zh = row
    return {
        "title": title,
        "link": link,
        "content_en": content_en,
        "content_zh": content_zh,
    }


def save_article_en(link: str, content_en: str):
    """
    保存英文正文（只写一次，后续直接复用）
    """
    conn = _get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE news
        SET content_en = ?
        WHERE link = ?
        """,
        (content_en, link),
    )

    conn.commit()
    conn.close()


def save_article_zh(link: str, content_zh: str):
    """
    保存中文翻译正文
    """
    conn = _get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE news
        SET content_zh = ?
        WHERE link = ?
        """,
        (content_zh, link),
    )

    conn.commit()
    conn.close()


def clear_all_news():
    """
    删除所有新闻数据与正文缓存。
    """
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM news")
    conn.commit()
    cur.execute("VACUUM")
    conn.close()
