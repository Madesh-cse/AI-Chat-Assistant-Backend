import os

from langchain_openai import ChatOpenAI # type: ignore
from app.tools.weather import get_weather
from app.tools.city_image import get_city_image
from app.tools.news import get_news
from app.tools.wikipedia import search_wikipedia
from app.tools.web_search import web_search
from app.tools.movie import get_movie
from app.tools.stackoverflow import (
    search_stackoverflow,
)
from app.tools.notion import (
    search_notion,
    read_notion_page,
)


llm = ChatOpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
    model=os.getenv(
        "OPENROUTER_MODEL",
        "meta-llama/llama-3.3-70b-instruct",
    ),
    temperature=0.7,
)


llm_with_tools = llm.bind_tools(
    [get_weather,get_city_image, get_news,search_wikipedia,web_search,get_movie,   # Plugin
search_stackoverflow, search_notion,read_notion_page ]
)