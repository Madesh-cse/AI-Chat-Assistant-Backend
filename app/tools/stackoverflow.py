from langchain_core.tools import tool  # type: ignore

from app.plugins.stackoverflow.plugin import (
    stackoverflow_plugin,
)


@tool
def search_stackoverflow(
    query: str,
) -> str:
    """
    Search Stack Overflow for programming
    questions related to the user's query.

    Use this tool when the user asks about:
    - programming errors
    - coding problems
    - framework issues
    - library issues
    - JavaScript
    - React
    - Angular
    - Python
    - Node.js
    - TypeScript
    - SQL
    - etc.
    """

    results = stackoverflow_plugin.search(
        query=query,
        limit=5,
    )

    if not results:

        return (
            "No relevant Stack Overflow "
            "questions were found."
        )

    formatted = []

    for index, item in enumerate(
        results,
        start=1,
    ):

        title = item.get(
            "title",
            "Untitled",
        )

        link = item.get(
            "link",
            "",
        )

        score = item.get(
            "score",
            0,
        )

        answer_count = item.get(
            "answer_count",
            0,
        )

        tags = item.get(
            "tags",
            [],
        )

        formatted.append(
            f"""
Result {index}

Title:
{title}

Score:
{score}

Answers:
{answer_count}

Tags:
{", ".join(tags)}

URL:
{link}
""".strip()
        )

    return "\n\n---\n\n".join(
        formatted
    )