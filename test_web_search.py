from app.tools.web_search import web_search


result = web_search.invoke(
    {
        "query": "latest LangChain news"
    }
)

print(result)