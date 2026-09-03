import os

from langchain_groq import ChatGroq  # type: ignore
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


llm = ChatGroq(
    api_key=os.getenv("GROQ_API_KEY"),
    model=os.getenv(
        "GROQ_MODEL",
        "llama-3.3-70b-versatile",
    ),
    temperature=0.7,
)


llm_with_tools = llm.bind_tools(
    [get_weather,get_city_image, get_news,search_wikipedia,web_search,get_movie,   # Plugin
search_stackoverflow, search_notion,read_notion_page ]
)