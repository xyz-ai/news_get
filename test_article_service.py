from core.article_service import get_article

url = "https://www.bbc.com/news/articles/ce3wp0qelreo"

article = get_article(url)

print("EN:")
print(article["en"][:500])
print("\nZH:")
print(article["zh"][:300])
