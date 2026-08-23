import os

from langchain_ollama import ChatOllama # type: ignore
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

llm = ChatOllama(
    model = "qwen2.5:3b",
    temperature=0.7,
    base_url= os.getenv(
        "OLLAMA_BASE_URL",
        "http://localhost:11434"
    ),
    
)
llm_with_tools = llm.bind_tools(
    [get_weather,get_city_image, get_news,search_wikipedia,web_search,get_movie,   # Plugin
search_stackoverflow, search_notion,read_notion_page ]
)