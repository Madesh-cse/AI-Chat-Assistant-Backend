from app.plugins.notion.client import NotionClient


class NotionPlugin:

    name = "notion"

    display_name = "Notion"

    description = (
        "Search and read pages from the user's "
        "connected Notion workspace."
    )

    def __init__(self):
        self.client = NotionClient()

    def search(
        self,
        query: str = "",
        limit: int = 5,
    ):
        return self.client.search(
            query=query,
            page_size=limit,
        )

    def get_page_content(
        self,
        page_id: str,
    ):
        return self.client.get_block_children(
            page_id
        )


notion_plugin = NotionPlugin()