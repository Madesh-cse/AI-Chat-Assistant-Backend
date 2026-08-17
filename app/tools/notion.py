from langchain_core.tools import tool  # type: ignore

from app.plugins.notion.plugin import (
    notion_plugin,
)


@tool
def search_notion(
    query: str,
) -> str:
    """
    Search the user's connected Notion workspace.

    Use this when the user asks about
    information stored in Notion.
    """

    results = notion_plugin.search(
        query=query,
        limit=5,
    )

    if not results:
        return (
            "No relevant Notion pages "
            "were found."
        )

    formatted = []

    for index, item in enumerate(
        results,
        start=1,
    ):

        properties = item.get(
            "properties",
            {}
        )

        title = "Untitled"

        for prop in properties.values():

            if prop.get("type") == "title":

                title_items = prop.get(
                    "title",
                    []
                )

                title = "".join(
                    item.get(
                        "plain_text",
                        ""
                    )
                    for item in title_items
                )

                break

        formatted.append(
            f"""
Result {index}

Title:
{title}

Page ID:
{item.get("id", "")}

URL:
{item.get("url", "")}
""".strip()
        )

    return "\n\n---\n\n".join(
        formatted
    )


@tool
def read_notion_page(
    page_id: str,
) -> str:
    """
    Read the actual content of a Notion page.

    Use this after search_notion finds a relevant
    Notion page and the user wants to know what
    is inside the page.
    """

    content = notion_plugin.get_page_content(
        page_id
    )

    if not content:
        return (
            "The Notion page was found, "
            "but it contains no readable content."
        )

    return (
        f"Notion Page Content:\n\n"
        f"{content}"
    )