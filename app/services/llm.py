import os

from langchain_nvidia_ai_endpoints import ChatNVIDIA # type: ignore

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


# --------------------------------
# NVIDIA LLM
# --------------------------------

llm = ChatNVIDIA(
    model="deepseek-ai/deepseek-v4-pro-0813",
    api_key=os.getenv("NVIDIA_API_KEY"),
    temperature=1,
    top_p=0.95,
    max_tokens=16384,
    seed=42,
    chat_template_kwargs={
        "thinking": False,
    },
)


# --------------------------------
# LLM + TOOLS
# --------------------------------

llm_with_tools = llm.bind_tools(
    [
        get_weather,
        get_city_image,
        get_news,
        search_wikipedia,
        web_search,
        get_movie,

        # Plugin tools
        search_stackoverflow,
        search_notion,
        read_notion_page,
    ]
)