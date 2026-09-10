import requests # type: ignore
from langchain_core.tools import tool # type: ignore


@tool
def search_places(location: str, query: str) -> str:
    """
    Search for places near a location using OpenStreetMap Nominatim.

    Args:
        location: City or area, for example "Madurai".
        query: Type of place, for example "restaurants".
    """

    try:
        # First, convert the location into latitude/longitude
        geocode_url = "https://nominatim.openstreetmap.org/search"

        headers = {
            "User-Agent": "AI-Chat-Assistant/1.0"
        }

        geocode_params = {
            "q": location,
            "format": "json",
            "limit": 1,
        }

        geocode_response = requests.get(
            geocode_url,
            params=geocode_params,
            headers=headers,
            timeout=10,
        )

        geocode_response.raise_for_status()

        locations = geocode_response.json()

        if not locations:
            return f"Could not find the location: {location}"

        latitude = float(locations[0]["lat"])
        longitude = float(locations[0]["lon"])

        # Search nearby places
        search_params = {
            "q": f"{query} near {location}",
            "format": "json",
            "limit": 10,
        }

        search_response = requests.get(
            geocode_url,
            params=search_params,
            headers=headers,
            timeout=10,
        )

        search_response.raise_for_status()

        places = search_response.json()

        if not places:
            return f"No {query} found near {location}."

        results = []

        for place in places:
            results.append({
                "name": place.get("display_name", "Unknown"),
                "latitude": float(place["lat"]),
                "longitude": float(place["lon"]),
                "type": place.get("type", ""),
            })

        return str({
            "location": location,
            "center": {
                "latitude": latitude,
                "longitude": longitude,
            },
            "places": results,
        })

    except requests.RequestException as e:
        return f"Place search failed: {str(e)}"

    except Exception as e:
        return f"Unexpected error while searching places: {str(e)}"