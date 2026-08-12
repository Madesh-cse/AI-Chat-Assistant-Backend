import os

from dotenv import load_dotenv # type: ignore
from langchain_core.tools import tool # type: ignore
from tavily import TavilyClient # type: ignore

load_dotenv()


@tool
def web_search(query: str) -> str:
    """
    Search the web for current information, recent events,
    latest news, technical documentation, and other
    information that may not be available in the LLM's
    knowledge.
    """

    api_key = os.getenv("TAVILY_API_KEY")

    if not api_key:
        return "Web search is not configured. TAVILY_API_KEY is missing."

    try:
        client = TavilyClient(api_key=api_key)

        response = client.search(
            query=query,
            search_depth="advanced",
            max_results=5,
            include_answer=True,
            include_images=True,
        )

        results = response.get("results", [])

        if not results:
            return f"No web results found for: {query}"

        output = []

        if response.get("answer"):
            output.append(
                f"Web Search Answer:\n{response['answer']}"
            )

        output.append("\nSearch Results:\n")

        for index, result in enumerate(results, start=1):

            title = result.get("title", "No title")
            content = result.get("content", "No content")
            url = result.get("url", "")

            output.append(
                f"""
{index}. {title}

Content:
{content}

URL:
{url}
"""
            )

        return "\n".join(output)

    except Exception as e:

        return f"Web search failed: {str(e)}"