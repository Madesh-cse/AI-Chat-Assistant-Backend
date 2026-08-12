import requests # type: ignore
import os
from dotenv import load_dotenv # type: ignore
from langchain_core.tools import tool # type: ignore

load_dotenv()


@tool
def get_city_image(city: str) -> str:
    """
    Get a representative image URL for a city.
    Use this when the user asks for a city image,
    city picture, or wants to see what a city looks like.
    """

    api_key = os.getenv("UNSPLASH_ACCESS_KEY")

    if not api_key:
        return "Image service is not configured."

    url = "https://api.unsplash.com/search/photos"

    params = {
        "query": f"{city} city",
        "per_page": 1,
        "orientation": "landscape",
    }

    headers = {
        "Authorization": f"Client-ID {api_key}"
    }

    response = requests.get(
        url,
        params=params,
        headers=headers,
        timeout=10,
    )

    response.raise_for_status()

    data = response.json()

    results = data.get("results", [])

    if not results:
        return f"No image found for {city}."

    photo = results[0]

    image_url = photo["urls"]["regular"]

    photographer = photo["user"]["name"]
    photo_url = photo["links"]["html"]

    return (
        f"IMAGE_URL: {image_url}\n"
        f"PHOTOGRAPHER: {photographer}\n"
        f"PHOTO_URL: {photo_url}"
    )