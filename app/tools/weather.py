import requests # type: ignore
from langchain_core.tools import tool # type: ignore



@tool
def get_weather(city: str) -> str:
    """
    Get the current weather for a city.

    Use this tool when the user asks about current weather,
    temperature, rain, wind, or weather conditions.
    """

    try:
        # Step 1: Find the city coordinates
        geo_url = "https://geocoding-api.open-meteo.com/v1/search"

        geo_response = requests.get(
            geo_url,
            params={
                "name": city,
                "count": 1,
                "language": "en",
                "format": "json",
            },
            timeout=10,
        )

        geo_response.raise_for_status()

        geo_data = geo_response.json()

        if not geo_data.get("results"):
            return f"Sorry, I couldn't find the city '{city}'."

        location = geo_data["results"][0]

        latitude = location["latitude"]
        longitude = location["longitude"]
        city_name = location["name"]
        country = location.get("country", "")

        # Step 2: Get current weather
        weather_url = "https://api.open-meteo.com/v1/forecast"

        weather_response = requests.get(
            weather_url,
            params={
                "latitude": latitude,
                "longitude": longitude,
                "current": (
                    "temperature_2m,"
                    "relative_humidity_2m,"
                    "apparent_temperature,"
                    "weather_code,"
                    "wind_speed_10m"
                ),
                "timezone": "auto",
            },
            timeout=10,
        )

        weather_response.raise_for_status()

        weather_data = weather_response.json()

        current = weather_data["current"]

        return (
            f"Current weather in {city_name}, {country}: "
            f"Temperature: {current['temperature_2m']}°C, "
            f"Feels like: {current['apparent_temperature']}°C, "
            f"Humidity: {current['relative_humidity_2m']}%, "
            f"Wind speed: {current['wind_speed_10m']} km/h."
        )

    except requests.RequestException as error:
        return f"Weather API error: {error}"

    except Exception as error:
        return f"Unable to get weather information: {error}"
