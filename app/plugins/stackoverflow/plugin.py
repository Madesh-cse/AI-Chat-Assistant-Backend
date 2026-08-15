from app.plugins.stackoverflow.client import (
    StackOverflowClient,
)


class StackOverflowPlugin:

    name = "stackoverflow"

    display_name = "Stack Overflow"

    description = (
        "Search Stack Overflow questions "
        "and developer solutions."
    )

    def __init__(self):

        self.client = StackOverflowClient()

    def search(
        self,
        query: str,
        limit: int = 5,
    ):

        return self.client.search_questions(
            query=query,
            limit=limit,
        )


stackoverflow_plugin = StackOverflowPlugin()