import os

import requests  # type: ignore
from dotenv import load_dotenv  # type: ignore


load_dotenv()

class NotionClient:

    BASE_URL = "https://api.notion.com/v1"

    def __init__(self):

        self.token = os.getenv(
            "NOTION_ACCESS_TOKEN"
        )

        if not self.token:
            raise ValueError(
                "NOTION_ACCESS_TOKEN "
                "is not configured."
            )

        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }

    def search(
        self,
        query: str = "",
        page_size: int = 10,
    ):

        url = f"{self.BASE_URL}/search"

        payload = {
            "page_size": page_size,
        }

        if query:
            payload["query"] = query

        response = requests.post(
            url,
            headers=self.headers,
            json=payload,
            timeout=15,
        )

        response.raise_for_status()

        data = response.json()

        return data.get(
            "results",
            []
        )

    def get_page(
        self,
        page_id: str,
    ):

        url = (
            f"{self.BASE_URL}/pages/"
            f"{page_id}"
        )

        response = requests.get(
            url,
            headers=self.headers,
            timeout=15,
        )

        response.raise_for_status()

        return response.json()

    def get_block_children(
        self,
        block_id: str,
        start_cursor: str | None = None,
        page_size: int = 100,
    ):

        url = (
            f"{self.BASE_URL}/blocks/"
            f"{block_id}/children"
        )

        params = {
            "page_size": page_size,
        }

        if start_cursor:
            params["start_cursor"] = start_cursor

        response = requests.get(
            url,
            headers=self.headers,
            params=params,
            timeout=15,
        )

        response.raise_for_status()

        return response.json()


    def get_all_block_children(
        self,
        block_id: str,
    ):

        all_blocks = []

        cursor = None

        while True:

            data = self.get_block_children(
                block_id=block_id,
                start_cursor=cursor,
            )

            blocks = data.get(
                "results",
                []
            )

            all_blocks.extend(
                blocks
            )

            has_more = data.get(
                "has_more",
                False
            )

            if not has_more:
                break

            cursor = data.get(
                "next_cursor"
            )

            if not cursor:
                break

        return all_blocks


    def _extract_rich_text(
        self,
        rich_text,
    ):

        return "".join(
            item.get(
                "plain_text",
                ""
            )
            for item in rich_text
        )


    def get_page_content(
        self,
        page_id: str,
    ):

        blocks = self.get_all_block_children(
            page_id
        )

        content = []

        for block in blocks:

            block_type = block.get(
                "type"
            )

            block_data = block.get(
                block_type,
                {}
            )

            rich_text = block_data.get(
                "rich_text",
                []
            )

            text = self._extract_rich_text(
                rich_text
            )

            if block_type == "heading_1":

                content.append(
                    f"# {text}"
                )

            elif block_type == "heading_2":

                content.append(
                    f"## {text}"
                )

            elif block_type == "heading_3":

                content.append(
                    f"### {text}"
                )

            elif block_type == "paragraph":

                if text:
                    content.append(
                        text
                    )


            elif block_type == "bulleted_list_item":

                content.append(
                    f"- {text}"
                )


            elif block_type == "numbered_list_item":

                content.append(
                    f"1. {text}"
                )

            elif block_type == "to_do":

                checked = block_data.get(
                    "checked",
                    False
                )

                checkbox = (
                    "[x]"
                    if checked
                    else "[ ]"
                )

                content.append(
                    f"- {checkbox} {text}"
                )


            elif block_type == "quote":

                content.append(
                    f"> {text}"
                )


            elif block_type == "code":

                language = block_data.get(
                    "language",
                    ""
                )

                content.append(
                    f"```{language}\n"
                    f"{text}\n"
                    f"```"
                )

            elif block_type == "callout":

                if text:
                    content.append(
                        f"💡 {text}"
                    )

            elif block_type == "divider":

                content.append(
                    "---"
                )

            else:

                if text:
                    content.append(
                        text
                    )

        return "\n\n".join(
            content
        )