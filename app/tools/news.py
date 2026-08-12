import os
import requests # type: ignore

from dotenv import load_dotenv # type: ignore
from langchain_core.tools import tool  # type: ignore

load_dotenv()


@tool
def get_news(
    topic: str = "general",
    country: str = "in",
    limit: int = 5,
) -> str:
    """
    Get the latest news using NewsData.io.

    Topics:
    - general
    - politics
    - geopolitics
    - state politics
    - sports
    - entertainment
    - technology
    - business
    - science
    - health
    """

    api_key = os.getenv("NEWSDATA_API_KEY")

    if not api_key:
        return "News service is not configured."

    # --------------------------------
    # Map user topic to NewsData query
    # --------------------------------

    topic_queries = {
        "politics": "politics",
        "indian politics": "India politics",
        "state politics": "India state politics",
        "geopolitics": "geopolitics",
        "world politics": "international politics",
        "sports": "sports",
        "sport": "sports",
        "entertainment": "entertainment",
        "technology": "technology",
        "tech": "technology",
        "business": "business",
        "science": "science",
        "health": "health",
        "general": "latest news",
    }

    query = topic_queries.get(
        topic.lower().strip(),
        topic,
    )

    # --------------------------------
    # NewsData.io API
    # --------------------------------

    url = "https://newsdata.io/api/1/latest"

    params = {
        "apikey": api_key,
        "q": query,
        "country": country,
        "language": "en",
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=10,
        )

        data = response.json()

    except requests.RequestException as e:

        return f"News API request failed: {str(e)}"

    # --------------------------------
    # API error
    # --------------------------------

    if response.status_code != 200:

        return (
            f"NewsData API error "
            f"({response.status_code}): "
            f"{data.get('message', 'Unknown error')}"
        )

    # NewsData can also return an API-level error
    if data.get("status") == "error":

        return (
            "NewsData API error: "
            + str(
                data.get(
                    "results",
                    data,
                )
            )
        )

    articles = data.get(
        "results",
        [],
    )

    if not articles:

        return (
            f"No recent news found "
            f"for {topic}."
        )

    # --------------------------------
    # Format articles
    # --------------------------------

    results = []

    for index, article in enumerate(
        articles[:limit],
        start=1,
    ):

        title = article.get(
            "title",
            "No title",
        )

        description = article.get(
            "description",
            "",
        )

        source = article.get(
            "source_name",
            "Unknown source",
        )

        article_url = article.get(
            "link",
            "",
        )

        image_url = article.get(
            "image_url",
            "",
        )

        published_at = article.get(
            "pubDate",
            "",
        )

        results.append(
            f"""
NEWS {index}

Title: {title}

Source: {source}

Published: {published_at}

Description: {description}

URL: {article_url}

Image: {image_url}
"""
        )

    return "\n".join(results)