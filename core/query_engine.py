import sqlite3

DB = "news.db"


def query_news(
    sources=None,
    region=None,
    keyword=None,
    hours=None
):
    sql = "SELECT title, source, region, published, link FROM news WHERE 1=1"
    params = []

    if sources:
        sql += f" AND source IN ({','.join(['?']*len(sources))})"
        params.extend(sources)

    if region:
        sql += " AND region = ?"
        params.append(region)

    if keyword:
        sql += " AND title LIKE ?"
        params.append(f"%{keyword}%")

    if hours:
        sql += " AND fetched_at >= datetime('now', ?)"
        params.append(f"-{hours} hours")

    sql += " ORDER BY fetched_at DESC LIMIT 200"

    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()

    return rows
