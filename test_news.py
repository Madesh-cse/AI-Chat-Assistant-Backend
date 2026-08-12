from app.tools.news import get_news


result = get_news.invoke(
    {
        "topic": "sports",
        "country": "in",
        "limit": 5,
    }
)

print(result)