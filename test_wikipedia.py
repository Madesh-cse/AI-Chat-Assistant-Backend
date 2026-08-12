from app.tools.wikipedia import search_wikipedia


result = search_wikipedia.invoke(
    {
        "query": "history of Chennai"
    }
)

print(result)