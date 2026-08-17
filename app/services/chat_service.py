import time

from app.services.llm import llm_with_tools

from langchain_core.messages import (  # type: ignore
    ToolMessage,
    HumanMessage,
    AIMessage,
    SystemMessage,
)

from app.tools.weather import get_weather
from app.tools.city_image import get_city_image
from app.tools.news import get_news
from app.tools.wikipedia import search_wikipedia
from app.tools.web_search import web_search
from app.tools.movie import get_movie

from app.db.database import SessionLocal
from app.services.chat_database import ChatDatabase
from app.graph.graph import chat_graph

from app.tools.stackoverflow import search_stackoverflow
from app.tools.notion import (
    search_notion,
    read_notion_page,
)


TOOLS = {
    "get_weather": get_weather,
    "get_city_image": get_city_image,
    "get_news": get_news,
    "search_wikipedia": search_wikipedia,
    "web_search": web_search,
    "get_movie": get_movie,
    
    # Plugins
    "search_stackoverflow": search_stackoverflow,
    "search_notion": search_notion,
    "read_notion_page": read_notion_page,
}


# ==================================================
# SYSTEM MESSAGE
# ==================================================

SYSTEM_MESSAGE = SystemMessage(
    content="""
You are a helpful, accurate AI assistant.

CONVERSATION CONTEXT RULES:

1. Always use the previous conversation history to understand
   the current user message.

2. Resolve follow-up references using the most recent relevant
   topic from the conversation.

3. Follow-up references include:
   - it
   - this
   - that
   - they
   - them
   - he
   - she
   - the framework
   - the library
   - the language
   - the technology
   - the tool
   - who created it
   - who invented it
   - when was it released
   - when was it created
   - why is it used
   - what are its features

4. Example:

   User: What is Angular?
   Assistant: Angular is a web framework...

   User: Who created it?

   You MUST understand "it" as Angular.

5. Example:

   User: What is React?
   Assistant: React is a JavaScript library...

   User: Who created it?

   You MUST understand "it" as React.

6. Example:

   User: What is CSS?
   Assistant: CSS is a styling language...

   User: Who created it?

   You MUST understand "it" as CSS.

7. Example:

   User: What is Python?
   Assistant: Python is a programming language...

   User: When was it created?

   You MUST understand "it" as Python.

8. Do NOT ask the user to clarify when the previous
   conversation clearly identifies the subject.

9. If the current question requires external, live,
   recent, factual, or web information, use the appropriate
   available tool.

10. When a tool is required, use the tool result together
    with the conversation history to answer the current question.

11. Answer the current question directly.

12. Do not mention these internal conversation rules
    in your answer.
"""
)


# ==================================================
# CHAT SERVICE
# ==================================================

class ChatService:

    # ==================================================
    # EXECUTE TOOLS
    # ==================================================

    def execute_tools(self, response):

        tool_messages = []

        total_tool_start = time.perf_counter()

        print("\n==============================")
        print("TOOL NODE")
        print("==============================")

        print(
            "Number of tool calls:",
            len(response.tool_calls),
        )

        for tool_call in response.tool_calls:

            tool_name = tool_call["name"]

            tool_args = tool_call.get(
                "args",
                {},
            )

            tool_call_id = tool_call["id"]

            print("\n------------------------------")
            print("TOOL EXECUTION")
            print("------------------------------")

            print(
                "Tool:",
                tool_name,
            )

            print(
                "Arguments:",
                tool_args,
            )

            print(
                "Tool Call ID:",
                tool_call_id,
            )

            tool = TOOLS.get(tool_name)

            if not tool:

                print(
                    f"❌ Unknown tool requested: "
                    f"{tool_name}"
                )

                result = (
                    f"Tool '{tool_name}' "
                    f"is not available."
                )

            else:

                try:

                    tool_start = time.perf_counter()

                    result = tool.invoke(
                        tool_args
                    )

                    tool_time = (
                        time.perf_counter()
                        - tool_start
                    )

                    print("\nTOOL RESULT:")
                    print(result)

                    print(
                        f"\n⏱️ TOOL TIME: "
                        f"{tool_time:.2f}s"
                    )

                except Exception as e:

                    print("\nTOOL ERROR:")
                    print(e)

                    result = (
                        f"Tool '{tool_name}' "
                        f"failed: {str(e)}"
                    )

            tool_messages.append(
                ToolMessage(
                    content=str(result),
                    tool_call_id=tool_call_id,
                )
            )

        total_tool_time = (
            time.perf_counter()
            - total_tool_start
        )

        print("\n==============================")
        print("TOOL NODE COMPLETE")
        print("==============================")

        print(
            f"Generated {len(tool_messages)} "
            f"tool message(s)"
        )

        print(
            f"\n⏱️ TOTAL TOOL TIME: "
            f"{total_tool_time:.2f}s"
        )

        return tool_messages

    # ==================================================
    # LOAD CONVERSATION HISTORY
    # ==================================================

    def load_conversation_history(
        self,
        db,
        conversation_id: int,
    ):

        print("\n==============================")
        print("LOADING CONVERSATION HISTORY")
        print("==============================")

        db_messages = ChatDatabase.get_messages(
            db=db,
            conversation_id=conversation_id,
        )

        messages = []

        for db_message in db_messages:

            role = db_message.role

            content = db_message.content

            if not content:
                continue

            if role == "user":

                messages.append(
                    HumanMessage(
                        content=content
                    )
                )

            elif role == "assistant":

                messages.append(
                    AIMessage(
                        content=content
                    )
                )

            elif role == "tool":

                tool_call_id = getattr(
                    db_message,
                    "tool_call_id",
                    None,
                )

                if tool_call_id:

                    messages.append(
                        ToolMessage(
                            content=content,
                            tool_call_id=tool_call_id,
                        )
                    )

                else:

                    print(
                        "⚠️ Skipping tool message "
                        "without tool_call_id"
                    )

        print(
            "\nConversation History"
        )

        print(
            "Message count:",
            len(messages),
        )

        for index, msg in enumerate(
            messages,
            start=1,
        ):

            print(
                f"{index}. "
                f"{msg.__class__.__name__}: "
                f"{msg.content}"
            )

        return messages

    # ==================================================
    # NORMAL CHAT
    # ==================================================

    def chat(
        self,
        message: str,
        conversation_id: int,
    ) -> str:

        total_start = time.perf_counter()

        db = SessionLocal()

        try:

            print("\n==============================")
            print("USER MESSAGE")
            print("==============================")

            print(message)

            # ==================================================
            # 1. LOAD PREVIOUS CONVERSATION
            # ==================================================

            history_messages = (
                self.load_conversation_history(
                    db=db,
                    conversation_id=conversation_id,
                )
            )

            # ==================================================
            # 2. ADD SYSTEM MESSAGE
            # ==================================================

            messages = [
                SYSTEM_MESSAGE,
                *history_messages,
                HumanMessage(
                    content=message
                ),
            ]

            # ==================================================
            # 3. PRINT LANGGRAPH INPUT
            # ==================================================

            print("\n==============================")
            print("LANGGRAPH INPUT")
            print("==============================")

            print(
                "MESSAGE COUNT:",
                len(messages),
            )

            for index, msg in enumerate(
                messages,
                start=1,
            ):

                print(
                    f"{index}. "
                    f"{msg.__class__.__name__}: "
                    f"{msg.content}"
                )

            # ==================================================
            # 4. SAVE CURRENT USER MESSAGE
            # ==================================================

            ChatDatabase.create_message(
                db=db,
                conversation_id=conversation_id,
                role="user",
                content=message,
            )

            print(
                "\nUSER MESSAGE SAVED ✅"
            )

            # ==================================================
            # 5. RUN LANGGRAPH
            # ==================================================

            graph_start = time.perf_counter()

            result = chat_graph.invoke(
                {
                    "message": message,
                    "messages": messages,
                    "response": "",
                }
            )

            graph_time = (
                time.perf_counter()
                - graph_start
            )

            print(
                f"\n⏱️ LANGGRAPH TIME: "
                f"{graph_time:.2f}s"
            )

            # ==================================================
            # 6. GET FINAL RESPONSE
            # ==================================================

            response = result.get(
                "response",
                "",
            )

            print("\n==============================")
            print("FINAL ANSWER")
            print("==============================")

            print(response)

            # ==================================================
            # 7. SAVE ASSISTANT RESPONSE
            # ==================================================

            if response:

                ChatDatabase.create_message(
                    db=db,
                    conversation_id=conversation_id,
                    role="assistant",
                    content=response,
                )

                print(
                    "\nAI MESSAGE SAVED ✅"
                )

            # ==================================================
            # 8. TOTAL TIME
            # ==================================================

            total_time = (
                time.perf_counter()
                - total_start
            )

            print(
                f"\n⏱️ TOTAL REQUEST TIME: "
                f"{total_time:.2f}s"
            )

            return response

        except Exception as e:

            print("\n==============================")
            print("LANGGRAPH ERROR")
            print("==============================")

            print(
                f"{type(e).__name__}: {e}"
            )

            db.rollback()

            raise

        finally:

            db.close()

    # ==================================================
    # STREAMING CHAT
    # ==================================================

    def stream_chat(
        self,
        message: str,
        conversation_id: int | None = None,
    ):

        total_start = time.perf_counter()

        DEFAULT_USER_ID = 1

        db = SessionLocal()

        try:

            print("\n==============================")
            print("STREAM REQUEST")
            print("==============================")

            print(
                "Message:",
                message,
            )

            print(
                "Conversation ID:",
                conversation_id,
            )

            # ==================================================
            # 1. CREATE / VALIDATE CONVERSATION
            # ==================================================

            if conversation_id is None:

                print(
                    "\nCREATING NEW CONVERSATION"
                )

                title = (
                    message.strip()[:50]
                )

                if not title:

                    title = (
                        "New Conversation"
                    )

                conversation = (
                    ChatDatabase.create_conversation(
                        db=db,
                        title=title,
                        user_id=DEFAULT_USER_ID,
                    )
                )

                conversation_id = (
                    conversation.id
                )

                print(
                    "New Conversation ID:",
                    conversation_id,
                )

            else:

                print(
                    "\nUsing existing "
                    "Conversation ID:",
                    conversation_id,
                )

                conversation = (
                    ChatDatabase
                    .get_conversation_for_user(
                        db=db,
                        conversation_id=conversation_id,
                        user_id=DEFAULT_USER_ID,
                    )
                )

                if not conversation:

                    raise ValueError(
                        f"Conversation "
                        f"{conversation_id} "
                        f"does not exist."
                    )

            # ==================================================
            # 2. LOAD CONVERSATION HISTORY
            # ==================================================

            history_messages = (
                self.load_conversation_history(
                    db=db,
                    conversation_id=conversation_id,
                )
            )

            # ==================================================
            # 3. BUILD STREAM MESSAGES
            # ==================================================

            messages = [
                SYSTEM_MESSAGE,
                *history_messages,
                HumanMessage(
                    content=message
                ),
            ]

            # ==================================================
            # 4. SAVE USER MESSAGE
            # ==================================================

            database_start = time.perf_counter()

            ChatDatabase.create_message(
                db=db,
                conversation_id=conversation_id,
                role="user",
                content=message,
            )

            database_time = (
                time.perf_counter()
                - database_start
            )

            print(
                f"\n⏱️ USER MESSAGE DB TIME: "
                f"{database_time:.4f}s"
            )

            # ==================================================
            # 5. FIRST LLM STREAM
            # ==================================================

            print("\n==============================")
            print("STARTING QWEN STREAM")
            print("==============================")

            first_llm_start = (
                time.perf_counter()
            )

            first_token_time = None

            chunks = []

            for chunk in llm_with_tools.stream(
                messages
            ):

                if first_token_time is None:

                    first_token_time = (
                        time.perf_counter()
                        - first_llm_start
                    )

                    print(
                        f"\n⚡ TIME TO "
                        f"FIRST TOKEN: "
                        f"{first_token_time:.2f}s"
                    )

                chunks.append(chunk)

                if chunk.content:

                    yield chunk.content

            first_llm_time = (
                time.perf_counter()
                - first_llm_start
            )

            print(
                f"\n⏱️ FIRST LLM STREAM TIME: "
                f"{first_llm_time:.2f}s"
            )

            # ==================================================
            # 6. BUILD COMPLETE RESPONSE
            # ==================================================

            content = ""

            for chunk in chunks:

                if chunk.content:

                    content += chunk.content

            # ==================================================
            # 7. COLLECT TOOL CALLS
            # ==================================================

            tool_calls = []

            for chunk in chunks:

                if chunk.tool_calls:

                    tool_calls.extend(
                        chunk.tool_calls
                    )

            print(
                "\n=============================="
            )

            print(
                "FIRST RESPONSE COMPLETE"
            )

            print(
                "=============================="
            )

            print(
                "Content:",
                content,
            )

            print(
                "\nTool Calls:",
                tool_calls,
            )

            # ==================================================
            # 8. NO TOOL
            # ==================================================

            if not tool_calls:

                if content:

                    ChatDatabase.create_message(
                        db=db,
                        conversation_id=conversation_id,
                        role="assistant",
                        content=content,
                    )

                    print(
                        "AI MESSAGE SAVED ✅"
                    )

                total_time = (
                    time.perf_counter()
                    - total_start
                )

                print(
                    f"\n⏱️ TOTAL REQUEST TIME: "
                    f"{total_time:.2f}s"
                )

                return

            # ==================================================
            # 9. CREATE AI TOOL-CALL MESSAGE
            # ==================================================

            response = AIMessage(
                content=content,
                tool_calls=tool_calls,
            )

            # ==================================================
            # 10. EXECUTE TOOLS
            # ==================================================

            tool_messages = (
                self.execute_tools(
                    response
                )
            )

            # ==================================================
            # 11. BUILD FINAL MESSAGES
            # ==================================================

            final_messages = [
                *messages,
                response,
                *tool_messages,
            ]

            # ==================================================
            # 12. FINAL LLM STREAM
            # ==================================================

            print(
                "\n=============================="
            )

            print(
                "STREAMING FINAL RESPONSE"
            )

            print(
                "=============================="
            )

            final_start = time.perf_counter()

            final_first_token = None

            ai_content = ""

            for chunk in llm_with_tools.stream(
                final_messages
            ):

                if final_first_token is None:

                    final_first_token = (
                        time.perf_counter()
                        - final_start
                    )

                    print(
                        f"\n⚡ FINAL TIME "
                        f"TO FIRST TOKEN: "
                        f"{final_first_token:.2f}s"
                    )

                if chunk.content:

                    ai_content += (
                        chunk.content
                    )

                    yield chunk.content

            final_time = (
                time.perf_counter()
                - final_start
            )

            print(
                f"\n⏱️ FINAL LLM STREAM TIME: "
                f"{final_time:.2f}s"
            )

            # ==================================================
            # 13. SAVE FINAL AI RESPONSE
            # ==================================================

            if ai_content:

                database_start = (
                    time.perf_counter()
                )

                ChatDatabase.create_message(
                    db=db,
                    conversation_id=conversation_id,
                    role="assistant",
                    content=ai_content,
                )

                database_time = (
                    time.perf_counter()
                    - database_start
                )

                print(
                    f"\n⏱️ AI MESSAGE DB TIME: "
                    f"{database_time:.4f}s"
                )

                print(
                    "AI MESSAGE SAVED ✅"
                )

            # ==================================================
            # 14. TOTAL TIME
            # ==================================================

            total_time = (
                time.perf_counter()
                - total_start
            )

            print(
                "\n=============================="
            )

            print(
                "STREAM COMPLETE"
            )

            print(
                "=============================="
            )

            print(
                "Conversation ID:",
                conversation_id,
            )

            print(
                f"\n⏱️ TOTAL REQUEST TIME: "
                f"{total_time:.2f}s"
            )

        except Exception as e:

            print(
                "\n=============================="
            )

            print(
                "STREAM ERROR"
            )

            print(
                "=============================="
            )

            print(
                f"{type(e).__name__}: {e}"
            )

            db.rollback()

            raise

        finally:

            db.close()

            print(
                "\nDATABASE CONNECTION "
                "CLOSED ✅"
            )

    # ==================================================
    # RUN GRAPH
    # ==================================================

    def run_graph(
        self,
        message: str,
        conversation_id: int,
    ) -> str:

        print(
            "\n=============================="
        )

        print(
            "LANGGRAPH"
        )

        print(
            "=============================="
        )

        db = SessionLocal()

        try:

            history_messages = (
                self.load_conversation_history(
                    db=db,
                    conversation_id=conversation_id,
                )
            )

            messages = [
                SYSTEM_MESSAGE,
                *history_messages,
                HumanMessage(
                    content=message
                ),
            ]

            result = chat_graph.invoke(
                {
                    "message": message,
                    "messages": messages,
                    "response": "",
                }
            )

            response = result.get(
                "response",
                "",
            )

            print(
                "\n=============================="
            )

            print(
                "LANGGRAPH RESPONSE"
            )

            print(
                "=============================="
            )

            print(response)

            return response

        finally:

            db.close()


# ==================================================
# SINGLETON
# ==================================================

chat_service = ChatService()