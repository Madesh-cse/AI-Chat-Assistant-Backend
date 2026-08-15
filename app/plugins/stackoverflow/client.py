import httpx # type: ignore


class StackOverflowClient:

    BASE_URL = "https://api.stackexchange.com/2.3"

    def __init__(self):
        self.timeout = 10.0

    def search_questions(
        self,
        query: str,
        limit: int = 5,
    ):

        params = {
            "site": "stackoverflow",
            "q": query,
            "sort": "relevance",
            "order": "desc",
            "pagesize": limit,
        }

        try:

            response = httpx.get(
                f"{self.BASE_URL}/search/advanced",
                params=params,
                timeout=self.timeout,
            )

            response.raise_for_status()

            data = response.json()

            return data.get("items", [])

        except httpx.HTTPError as e:

            print(
                "Stack Overflow API error:",
                e,
            )

            return []