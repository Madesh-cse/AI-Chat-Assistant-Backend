import os
import requests  # type: ignore

from dotenv import load_dotenv  # type: ignore
from langchain_core.tools import tool  # type: ignore


load_dotenv()

OMDB_API_KEY = os.getenv("OMDB_API_KEY")

OMDB_URL = "https://www.omdbapi.com/"


@tool
def get_movie(movie: str) -> str:
    """
    Search OMDb for a movie and return movie information.

    Use this tool when the user asks about:
    - movies
    - latest movies
    - movie details
    - movie ratings
    - movie posters
    - movie cast
    - movie plot
    - movie release dates
    - Marvel movies
    - Bollywood movies
    - Hollywood movies
    """

    if not OMDB_API_KEY:
        return "Movie service is not configured. OMDB_API_KEY is missing."

    try:

        params = {
            "apikey": OMDB_API_KEY,
            "t": movie,
            "type": "movie",
            "plot": "full",
        }

        response = requests.get(
            OMDB_URL,
            params=params,
            timeout=10,
        )

        response.raise_for_status()

        data = response.json()

        # -----------------------------------------
        # OMDb error
        # -----------------------------------------

        if data.get("Response") == "False":

            return (
                f"Movie not found: {movie}. "
                f"OMDb message: {data.get('Error', 'Unknown error')}"
            )

        # -----------------------------------------
        # Extract information
        # -----------------------------------------

        title = data.get("Title", "Unknown")
        year = data.get("Year", "Unknown")
        rated = data.get("Rated", "N/A")
        released = data.get("Released", "N/A")
        runtime = data.get("Runtime", "N/A")
        genre = data.get("Genre", "N/A")
        director = data.get("Director", "N/A")
        actors = data.get("Actors", "N/A")
        plot = data.get("Plot", "N/A")
        language = data.get("Language", "N/A")
        country = data.get("Country", "N/A")
        imdb_rating = data.get("imdbRating", "N/A")
        imdb_votes = data.get("imdbVotes", "N/A")
        poster = data.get("Poster", "N/A")

        # -----------------------------------------
        # Return clean result
        # -----------------------------------------

        return f"""
MOVIE INFORMATION

Title:
{title}

Year:
{year}

Rated:
{rated}

Released:
{released}

Runtime:
{runtime}

Genre:
{genre}

Director:
{director}

Actors:
{actors}

Language:
{language}

Country:
{country}

IMDb Rating:
{imdb_rating}

IMDb Votes:
{imdb_votes}

Plot:
{plot}

Poster:
{poster}
"""

    except requests.exceptions.Timeout:

        return "Movie service request timed out."

    except requests.exceptions.RequestException as e:

        return f"Movie API request failed: {str(e)}"

    except Exception as e:

        return f"Movie search failed: {str(e)}"