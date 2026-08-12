import requests # type: ignore

from langchain_core.tools import tool  # type: ignore


@tool
def search_wikipedia(query: str) -> str:
    """
    Search Wikipedia for factual information about a person,
    place, company, technology, historical event, scientific
    concept, or other general knowledge topic.
    """

    try:
        # -----------------------------------------
        # 1. Search Wikipedia
        # -----------------------------------------

        search_url = "https://en.wikipedia.org/w/api.php"

        search_params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "format": "json",
            "utf8": 1,
            "srlimit": 5,
        }

        headers = {
            "User-Agent": "AI-Chat-Bot/1.0"
        }

        search_response = requests.get(
            search_url,
            params=search_params,
            headers=headers,
            timeout=10,
        )

        search_response.raise_for_status()

        search_data = search_response.json()

        results = search_data.get(
            "query",
            {}
        ).get(
            "search",
            []
        )

        if not results:

            return (
                f"No Wikipedia results found for: {query}"
            )

        # -----------------------------------------
        # 2. Get best result
        # -----------------------------------------

        title = results[0]["title"]

        page_params = {
            "action": "query",
            "prop": "extracts|info",
            "exintro": True,
            "explaintext": True,
            "inprop": "url",
            "titles": title,
            "format": "json",
        }

        page_response = requests.get(
            search_url,
            params=page_params,
            headers=headers,
            timeout=10,
        )

        page_response.raise_for_status()

        page_data = page_response.json()

        pages = page_data.get(
            "query",
            {}
        ).get(
            "pages",
            {}
        )

        # -----------------------------------------
        # 3. Extract page
        # -----------------------------------------

        page = next(
            iter(pages.values())
        )

        if "missing" in page:

            return (
                f"Wikipedia page not found for: {query}"
            )

        summary = page.get(
            "extract",
            "No summary available."
        )

        url = page.get(
            "fullurl",
            f"https://en.wikipedia.org/wiki/"
            f"{title.replace(' ', '_')}"
        )

        # -----------------------------------------
        # 4. Return clean result
        # -----------------------------------------

        return f"""
Wikipedia Result

Title:
{title}

Summary:
{summary}

URL:
{url}
"""

    except requests.exceptions.Timeout:

        return (
            "Wikipedia request timed out. "
            "Please try again."
        )

    except requests.exceptions.RequestException as e:

        return (
            f"Wikipedia API request failed: {str(e)}"
        )

    except Exception as e:

        return (
            f"Wikipedia search failed: {str(e)}"
        )