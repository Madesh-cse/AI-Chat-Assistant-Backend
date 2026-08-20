import time
import uuid
from typing import Any

from langchain_core.messages import ( # type: ignore
    ToolMessage,
    HumanMessage,
    AIMessage,
    SystemMessage,
    BaseMessage,
)

from app.services.llm import llm_with_tools

from app.tools.weather import get_weather
from app.tools.city_image import get_city_image
from app.tools.news import get_news
from app.tools.wikipedia import search_wikipedia
from app.tools.web_search import web_search
from app.tools.movie import get_movie

from app.tools.stackoverflow import search_stackoverflow
from app.tools.notion import (
    search_notion,
    read_notion_page,
)

from app.db.database import SessionLocal
from app.services.chat_database import ChatDatabase
from app.graph.graph import chat_graph

# ============================================================
# REDIS RESPONSE CACHE
# ============================================================

from app.core.cache import (
    get_cached_response,
    set_cached_response,
)

# ============================================================
# REDIS CONVERSATION HISTORY CACHE
# ============================================================

from app.core.chat_history_cache import (
    get_cached_history,
    set_cached_history,
)


# ============================================================
# TOOLS
# ============================================================

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


# ============================================================
# SYSTEM MESSAGE
# ============================================================

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


# ============================================================
# CHAT SERVICE
# ============================================================

class ChatService:

    # ========================================================
    # NORMALIZE MESSAGE
    # ========================================================

    def normalize_message(
        self,
        message: Any,
    ) -> BaseMessage | None:
        """
        Convert cached/database message representations
        into LangChain message objects.

        Supports:

        - HumanMessage
        - AIMessage
        - ToolMessage
        - SystemMessage
        - dict representations
        """

        # Already a LangChain message
        if isinstance(message, BaseMessage):
            return message

        # Dictionary representation
        if isinstance(message, dict):

            role = message.get("role")
            content = message.get("content", "")

            if role in ("user", "human"):

                return HumanMessage(
                    content=str(content)
                )

            if role in ("assistant", "ai"):

                tool_calls = message.get(
                    "tool_calls",
                    [],
                )

                if tool_calls:

                    return AIMessage(
                        content=str(content),
                        tool_calls=tool_calls,
                    )

                return AIMessage(
                    content=str(content)
                )

            if role == "tool":

                tool_call_id = (
                    message.get("tool_call_id")
                    or message.get("toolCallId")
                    or str(uuid.uuid4())
                )

                return ToolMessage(
                    content=str(content),
                    tool_call_id=tool_call_id,
                )

            if role == "system":

                return SystemMessage(
                    content=str(content)
                )

        print(
            "⚠️ Unable to normalize message:",
            type(message).__name__,
        )

        return None

    # ========================================================
    # NORMALIZE HISTORY
    # ========================================================

    def normalize_history(
        self,
        history: list[Any],
    ) -> list[BaseMessage]:

        normalized = []

        for message in history:

            normalized_message = (
                self.normalize_message(message)
            )

            if normalized_message is not None:

                normalized.append(
                    normalized_message
                )

        return normalized

    # ========================================================
    # EXECUTE TOOLS
    # ========================================================

    def execute_tools(
        self,
        response: AIMessage,
    ):

        tool_messages = []

        total_tool_start = time.perf_counter()

        print("\n==============================")
        print("TOOL NODE")
        print("==============================")

        print(
            "Number of tool calls:",
            len(response.tool_calls),
        )

        for index, tool_call in enumerate(
            response.tool_calls,
            start=1,
        ):

            # ------------------------------------------------
            # TOOL NAME
            # ------------------------------------------------

            tool_name = tool_call.get(
                "name",
                "",
            )

            # ------------------------------------------------
            # TOOL ARGUMENTS
            # ------------------------------------------------

            tool_args = tool_call.get(
                "args",
                {},
            )

            # ------------------------------------------------
            # TOOL CALL ID
            # ------------------------------------------------

            tool_call_id = tool_call.get(
                "id"
            )

            if not tool_call_id:

                tool_call_id = (
                    f"tool_call_"
                    f"{uuid.uuid4().hex}"
                )

                print(
                    "⚠️ Missing tool_call_id."
                )

                print(
                    "Generated fallback ID:",
                    tool_call_id,
                )

            print("\n------------------------------")
            print(
                f"TOOL EXECUTION #{index}"
            )
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

            # ------------------------------------------------
            # FIND TOOL
            # ------------------------------------------------

            tool = TOOLS.get(
                tool_name
            )

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

                    tool_start = (
                        time.perf_counter()
                    )

                    # Make sure args are a dictionary
                    if not isinstance(
                        tool_args,
                        dict,
                    ):

                        tool_args = {}

                    result = tool.invoke(
                        tool_args
                    )

                    tool_time = (
                        time.perf_counter()
                        - tool_start
                    )

                    print(
                        "\nTOOL RESULT:"
                    )

                    print(result)

                    print(
                        f"\n⏱️ TOOL TIME: "
                        f"{tool_time:.2f}s"
                    )

                except Exception as e:

                    print(
                        "\nTOOL ERROR:"
                    )

                    print(e)

                    result = (
                        f"Tool '{tool_name}' "
                        f"failed: {str(e)}"
                    )

            # ------------------------------------------------
            # CREATE TOOL MESSAGE
            # ------------------------------------------------

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
            f"Generated "
            f"{len(tool_messages)} "
            f"tool message(s)"
        )

        print(
            f"\n⏱️ TOTAL TOOL TIME: "
            f"{total_tool_time:.2f}s"
        )

        return tool_messages

    # ========================================================
    # LOAD CONVERSATION HISTORY
    # ========================================================

    def load_conversation_history(
        self,
        db,
        conversation_id: int,
    ):

        print("\n==============================")
        print("LOADING CONVERSATION HISTORY")
        print("==============================")

        print(
            "Conversation ID:",
            conversation_id,
        )

        # ----------------------------------------------------
        # 1. REDIS HISTORY
        # ----------------------------------------------------

        cached_history = get_cached_history(
            conversation_id=conversation_id,
        )

        if cached_history is not None:

            print(
                "🟢 REDIS HISTORY CACHE HIT"
            )

            print(
                "Cached history count:",
                len(cached_history),
            )

            normalized_history = (
                self.normalize_history(
                    cached_history
                )
            )

            print(
                "Normalized history count:",
                len(normalized_history),
            )

            return normalized_history

        # ----------------------------------------------------
        # 2. REDIS MISS
        # ----------------------------------------------------

        print(
            "🔴 REDIS HISTORY CACHE MISS"
        )

        print(
            "Loading conversation history "
            "from PostgreSQL..."
        )

        # ----------------------------------------------------
        # 3. POSTGRES
        # ----------------------------------------------------

        db_messages = ChatDatabase.get_messages(
            db=db,
            conversation_id=conversation_id,
        )

        messages = []

        # ----------------------------------------------------
        # 4. CONVERT DATABASE MESSAGES
        # ----------------------------------------------------

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

                if not tool_call_id:

                    print(
                        "⚠️ Skipping tool message "
                        "without tool_call_id"
                    )

                    continue

                messages.append(
                    ToolMessage(
                        content=content,
                        tool_call_id=tool_call_id,
                    )
                )

            else:

                print(
                    f"⚠️ Unknown message role: "
                    f"{role}"
                )

        # ----------------------------------------------------
        # 5. DEBUG HISTORY
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # 6. CACHE HISTORY
        # ----------------------------------------------------

        if messages:

            set_cached_history(
                conversation_id=conversation_id,
                messages=messages,
            )

            print(
                "🟢 CONVERSATION HISTORY "
                "CACHED IN REDIS"
            )

        else:

            print(
                "⚠️ No conversation history "
                "to cache."
            )

        return messages

    # ========================================================
    # UPDATE HISTORY CACHE
    # ========================================================

    def update_history_cache(
        self,
        conversation_id: int,
        history_messages: list[BaseMessage],
        new_messages: list[BaseMessage],
    ):

        updated_history = [
            *history_messages,
            *new_messages,
        ]

        set_cached_history(
            conversation_id=conversation_id,
            messages=updated_history,
        )

        print(
            "🟢 REDIS HISTORY UPDATED"
        )

        print(
            "Updated history count:",
            len(updated_history),
        )

        return updated_history

    # ========================================================
    # NORMAL CHAT
    # ========================================================

    def chat(
        self,
        message: str,
        conversation_id: int,
    ) -> str:

        total_start = time.perf_counter()

        DEFAULT_USER_ID = 1

        db = SessionLocal()

        try:

            print("\n==============================")
            print("USER MESSAGE")
            print("==============================")

            print(message)

            # ------------------------------------------------
            # 1. RESPONSE CACHE
            # ------------------------------------------------

            print(
                "\n=============================="
            )

            print(
                "REDIS RESPONSE CACHE CHECK"
            )

            print(
                "=============================="
            )

            cached = get_cached_response(
                user_id=DEFAULT_USER_ID,
                conversation_id=conversation_id,
                message=message,
            )

            if cached:

                cached_response = cached.get(
                    "response",
                    "",
                )

                if cached_response:

                    print(
                        "🟢 REDIS RESPONSE CACHE HIT"
                    )

                    return cached_response

            print(
                "🔴 REDIS RESPONSE CACHE MISS"
            )

            # ------------------------------------------------
            # 2. HISTORY
            # ------------------------------------------------

            history_messages = (
                self.load_conversation_history(
                    db=db,
                    conversation_id=conversation_id,
                )
            )

            # ------------------------------------------------
            # 3. BUILD MESSAGES
            # ------------------------------------------------

            messages = [
                SYSTEM_MESSAGE,
                *history_messages,
                HumanMessage(
                    content=message
                ),
            ]

            # ------------------------------------------------
            # 4. SAVE USER
            # ------------------------------------------------

            ChatDatabase.create_message(
                db=db,
                conversation_id=conversation_id,
                role="user",
                content=message,
            )

            # ------------------------------------------------
            # 5. RUN GRAPH
            # ------------------------------------------------

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

            # ------------------------------------------------
            # 6. RESPONSE
            # ------------------------------------------------

            response = result.get(
                "response",
                "",
            )

            print(
                "\n=============================="
            )

            print(
                "FINAL ANSWER"
            )

            print(
                "=============================="
            )

            print(response)

            # ------------------------------------------------
            # 7. SAVE ASSISTANT
            # ------------------------------------------------

            if response:

                ChatDatabase.create_message(
                    db=db,
                    conversation_id=conversation_id,
                    role="assistant",
                    content=response,
                )

                # Update Redis history directly.
                self.update_history_cache(
                    conversation_id=conversation_id,
                    history_messages=history_messages,
                    new_messages=[
                        HumanMessage(
                            content=message
                        ),
                        AIMessage(
                            content=response
                        ),
                    ],
                )

                # ------------------------------------------------
                # RESPONSE CACHE
                # ------------------------------------------------

                set_cached_response(
                    user_id=DEFAULT_USER_ID,
                    conversation_id=conversation_id,
                    message=message,
                    response=response,
                )

                print(
                    "🟢 RESPONSE CACHED IN REDIS"
                )

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

            print(
                "\n=============================="
            )

            print(
                "LANGGRAPH ERROR"
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
                "\nDATABASE CONNECTION CLOSED ✅"
            )

    # ========================================================
    # STREAMING CHAT
    # ========================================================

    def stream_chat(
        self,
        message: str,
        conversation_id: int | None = None,
    ):

        total_start = time.perf_counter()

        DEFAULT_USER_ID = 1

        db = SessionLocal()

        try:

            print(
                "\n=============================="
            )

            print(
                "STREAM REQUEST"
            )

            print(
                "=============================="
            )

            print(
                "Message:",
                message,
            )

            print(
                "Conversation ID:",
                conversation_id,
            )

            # =================================================
            # 1. CREATE / VALIDATE CONVERSATION
            # =================================================

            if conversation_id is None:

                print(
                    "\nCREATING NEW CONVERSATION"
                )

                title = (
                    message.strip()[:50]
                )

                if not title:

                    title = "New Conversation"

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

            # =================================================
            # 2. RESPONSE CACHE
            # =================================================

            print(
                "\n=============================="
            )

            print(
                "REDIS RESPONSE CACHE CHECK"
            )

            print(
                "=============================="
            )

            cached = get_cached_response(
                user_id=DEFAULT_USER_ID,
                conversation_id=conversation_id,
                message=message,
            )

            if cached:

                cached_response = cached.get(
                    "response",
                    "",
                )

                if cached_response:

                    print(
                        "🟢 REDIS RESPONSE CACHE HIT"
                    )

                    # -----------------------------------------
                    # Load current history from Redis.
                    # No PostgreSQL query if history exists
                    # in Redis.
                    # -----------------------------------------

                    history_messages = (
                        self.load_conversation_history(
                            db=db,
                            conversation_id=conversation_id,
                        )
                    )

                    # -----------------------------------------
                    # Save user message
                    # -----------------------------------------

                    ChatDatabase.create_message(
                        db=db,
                        conversation_id=conversation_id,
                        role="user",
                        content=message,
                    )

                    # -----------------------------------------
                    # Save assistant message
                    # -----------------------------------------

                    ChatDatabase.create_message(
                        db=db,
                        conversation_id=conversation_id,
                        role="assistant",
                        content=cached_response,
                    )

                    # -----------------------------------------
                    # Update Redis history
                    # -----------------------------------------

                    self.update_history_cache(
                        conversation_id=conversation_id,
                        history_messages=history_messages,
                        new_messages=[
                            HumanMessage(
                                content=message
                            ),
                            AIMessage(
                                content=cached_response
                            ),
                        ],
                    )

                    # -----------------------------------------
                    # Stream cached response
                    # -----------------------------------------

                    yield cached_response

                    return

            print(
                "🔴 REDIS RESPONSE CACHE MISS"
            )

            # =================================================
            # 3. LOAD CONVERSATION HISTORY
            # =================================================

            history_messages = (
                self.load_conversation_history(
                    db=db,
                    conversation_id=conversation_id,
                )
            )

            # Make absolutely sure history contains
            # LangChain message objects.
            history_messages = (
                self.normalize_history(
                    history_messages
                )
            )

            # =================================================
            # 4. BUILD LLM MESSAGES
            # =================================================

            messages = [
                SYSTEM_MESSAGE,
                *history_messages,
                HumanMessage(
                    content=message
                ),
            ]

            # =================================================
            # 5. SAVE USER MESSAGE
            # =================================================

            database_start = (
                time.perf_counter()
            )

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

            # =================================================
            # 6. FIRST LLM STREAM
            # =================================================

            print(
                "\n=============================="
            )

            print(
                "STARTING QWEN STREAM"
            )

            print(
                "=============================="
            )

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
                        f"\n⚡ TIME TO FIRST TOKEN: "
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

            # =================================================
            # 7. BUILD CONTENT
            # =================================================

            content = ""

            for chunk in chunks:

                if chunk.content:

                    content += chunk.content

            # =================================================
            # 8. COLLECT TOOL CALLS
            # =================================================

            tool_calls = []

            tool_call_map = {}

            for chunk in chunks:

                chunk_tool_calls = getattr(
                    chunk,
                    "tool_calls",
                    [],
                )

                if not chunk_tool_calls:

                    continue

                for tool_call in chunk_tool_calls:

                    if not isinstance(
                        tool_call,
                        dict,
                    ):

                        continue

                    # -----------------------------------------
                    # Determine key
                    # -----------------------------------------

                    tool_call_id = (
                        tool_call.get("id")
                    )

                    index = tool_call.get(
                        "index"
                    )

                    key = (
                        tool_call_id
                        or index
                    )

                    if key is None:

                        key = len(
                            tool_call_map
                        )

                    # -----------------------------------------
                    # Initialize
                    # -----------------------------------------

                    if key not in tool_call_map:

                        tool_call_map[key] = {
                            "name": "",
                            "args": {},
                            "id": (
                                tool_call_id
                                or (
                                    f"tool_call_"
                                    f"{uuid.uuid4().hex}"
                                )
                            ),
                        }

                    current = (
                        tool_call_map[key]
                    )

                    # -----------------------------------------
                    # Name
                    # -----------------------------------------

                    if tool_call.get(
                        "name"
                    ):

                        current["name"] = (
                            tool_call[
                                "name"
                            ]
                        )

                    # -----------------------------------------
                    # ID
                    # -----------------------------------------

                    if tool_call_id:

                        current["id"] = (
                            tool_call_id
                        )

                    # -----------------------------------------
                    # Args
                    # -----------------------------------------

                    args = tool_call.get(
                        "args"
                    )

                    if isinstance(
                        args,
                        dict,
                    ):

                        current["args"].update(
                            args
                        )

                    elif isinstance(
                        args,
                        str,
                    ):

                        # Some providers stream
                        # argument JSON as strings.
                        # Keep it temporarily.
                        current["_raw_args"] = (
                            current.get(
                                "_raw_args",
                                ""
                            )
                            + args
                        )

            # -------------------------------------------------
            # Convert collected calls
            # -------------------------------------------------

            for key, call in (
                tool_call_map.items()
            ):

                if not call.get(
                    "name"
                ):

                    print(
                        "⚠️ Skipping incomplete "
                        "tool call:",
                        call,
                    )

                    continue

                call.pop(
                    "_raw_args",
                    None,
                )

                if not isinstance(
                    call.get("args"),
                    dict,
                ):

                    call["args"] = {}

                tool_calls.append(
                    call
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

            # =================================================
            # 9. NO TOOL
            # =================================================

            if not tool_calls:

                if content:

                    # -----------------------------------------
                    # Save assistant to PostgreSQL
                    # -----------------------------------------

                    ChatDatabase.create_message(
                        db=db,
                        conversation_id=conversation_id,
                        role="assistant",
                        content=content,
                    )

                    print(
                        "AI MESSAGE SAVED ✅"
                    )

                    # -----------------------------------------
                    # Response cache
                    # -----------------------------------------

                    set_cached_response(
                        user_id=DEFAULT_USER_ID,
                        conversation_id=conversation_id,
                        message=message,
                        response=content,
                    )

                    print(
                        "🟢 RESPONSE CACHED IN REDIS"
                    )

                    # -----------------------------------------
                    # Update history cache
                    # -----------------------------------------

                    self.update_history_cache(
                        conversation_id=conversation_id,
                        history_messages=history_messages,
                        new_messages=[
                            HumanMessage(
                                content=message
                            ),
                            AIMessage(
                                content=content
                            ),
                        ],
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

            # =================================================
            # 10. CREATE AI TOOL CALL MESSAGE
            # =================================================

            response = AIMessage(
                content=content,
                tool_calls=tool_calls,
            )

            # =================================================
            # 11. EXECUTE TOOLS
            # =================================================

            tool_messages = (
                self.execute_tools(
                    response
                )
            )

            # =================================================
            # 12. FINAL LLM INPUT
            # =================================================

            final_messages = [
                *messages,
                response,
                *tool_messages,
            ]

            print(
                "\n=============================="
            )

            print(
                "FINAL LLM MESSAGE COUNT:",
                len(final_messages),
            )

            print(
                "=============================="
            )

            for index, msg in enumerate(
                final_messages,
                start=1,
            ):

                print(
                    f"{index}. "
                    f"{msg.__class__.__name__}"
                )

            # =================================================
            # 13. FINAL LLM STREAM
            # =================================================

            print(
                "\n=============================="
            )

            print(
                "STREAMING FINAL RESPONSE"
            )

            print(
                "=============================="
            )

            final_start = (
                time.perf_counter()
            )

            final_first_token = None

            ai_content = ""

            for chunk in (
                llm_with_tools.stream(
                    final_messages
                )
            ):

                if final_first_token is None:

                    final_first_token = (
                        time.perf_counter()
                        - final_start
                    )

                    print(
                        f"\n⚡ FINAL TIME TO "
                        f"FIRST TOKEN: "
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

            # =================================================
            # 14. SAVE FINAL RESPONSE
            # =================================================

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

                # -----------------------------------------
                # Response cache
                # -----------------------------------------

                set_cached_response(
                    user_id=DEFAULT_USER_ID,
                    conversation_id=conversation_id,
                    message=message,
                    response=ai_content,
                )

                print(
                    "🟢 RESPONSE CACHED IN REDIS"
                )

                # -----------------------------------------
                # History cache
                #
                # IMPORTANT:
                # Include:
                #   user
                #   AI tool call
                #   tool result(s)
                #   final AI response
                # -----------------------------------------

                self.update_history_cache(
                    conversation_id=conversation_id,
                    history_messages=history_messages,
                    new_messages=[
                        HumanMessage(
                            content=message
                        ),
                        response,
                        *tool_messages,
                        AIMessage(
                            content=ai_content
                        ),
                    ],
                )

            # =================================================
            # 15. COMPLETE
            # =================================================

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
                "\nDATABASE CONNECTION CLOSED ✅"
            )

    # ========================================================
    # REFRESH HISTORY CACHE
    # ========================================================

    def refresh_history_cache(
        self,
        db,
        conversation_id: int,
    ):

        print(
            "\n=============================="
        )

        print(
            "REFRESHING REDIS HISTORY CACHE"
        )

        print(
            "=============================="
        )

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

        set_cached_history(
            conversation_id=conversation_id,
            messages=messages,
        )

        print(
            "🟢 REDIS HISTORY CACHE UPDATED"
        )

        print(
            "History count:",
            len(messages),
        )

        return messages

    # ========================================================
    # RUN GRAPH
    # ========================================================

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


# ============================================================
# SINGLETON
# ============================================================

chat_service = ChatService()