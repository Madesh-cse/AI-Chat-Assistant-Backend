import json
import time
import uuid
from typing import Any

from langchain_core.messages import (  # type: ignore
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
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

from app.core.cache import (
    get_cached_response,
    set_cached_response,
)

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

1. Always use the previous conversation history to understand the current user message.

2. Resolve follow-up references using the most recent relevant topic from the conversation.

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

8. Do NOT ask the user to clarify when the previous conversation clearly identifies the subject.

9. If the current question requires external, live, recent, factual, or web information, use the appropriate available tool.

10. When a tool is required, use the tool result together with the conversation history to answer the current question.

11. Answer the current question directly.

12. Do not mention these internal conversation rules in your answer.
"""
)


# ============================================================
# CHAT SERVICE
# ============================================================

class ChatService:

    # ========================================================
    # MESSAGE NORMALIZATION
    # ========================================================

    def normalize_message(
        self,
        message: Any,
    ) -> BaseMessage | None:

        if isinstance(message, BaseMessage):
            return message

        if isinstance(message, dict):

            role = message.get("role")
            content = message.get("content", "")

            # ----------------------------
            # USER
            # ----------------------------

            if role in ("user", "human"):
                return HumanMessage(
                    content=str(content)
                )

            # ----------------------------
            # ASSISTANT
            # ----------------------------

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

            # ----------------------------
            # TOOL
            # ----------------------------

            if role == "tool":

                tool_call_id = (
                    message.get("tool_call_id")
                    or message.get("toolCallId")
                )

                if not tool_call_id:
                    return None

                return ToolMessage(
                    content=str(content),
                    tool_call_id=tool_call_id,
                )

            # ----------------------------
            # SYSTEM
            # ----------------------------

            if role == "system":

                return SystemMessage(
                    content=str(content)
                )

        return None

    # ========================================================
    # NORMALIZE HISTORY
    # ========================================================

    def normalize_history(
        self,
        history: list[Any],
    ) -> list[BaseMessage]:

        normalized: list[BaseMessage] = []

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
    # SERIALIZE MESSAGE
    # ========================================================

    def serialize_message(
        self,
        message: BaseMessage,
    ) -> dict[str, Any]:

        if isinstance(message, HumanMessage):

            return {
                "role": "user",
                "content": str(message.content),
            }

        if isinstance(message, AIMessage):

            data = {
                "role": "assistant",
                "content": str(message.content),
            }

            tool_calls = getattr(
                message,
                "tool_calls",
                [],
            )

            if tool_calls:
                data["tool_calls"] = tool_calls

            return data

        if isinstance(message, ToolMessage):

            return {
                "role": "tool",
                "content": str(message.content),
                "tool_call_id": message.tool_call_id,
            }

        if isinstance(message, SystemMessage):

            return {
                "role": "system",
                "content": str(message.content),
            }

        return {
            "role": "unknown",
            "content": str(message.content),
        }

    # ========================================================
    # SERIALIZE HISTORY
    # ========================================================

    def serialize_history(
        self,
        messages: list[BaseMessage],
    ) -> list[dict[str, Any]]:

        return [
            self.serialize_message(message)
            for message in messages
        ]

    # ========================================================
    # EXECUTE TOOLS
    # ========================================================

    def execute_tools(
        self,
        response: AIMessage,
    ) -> list[ToolMessage]:

        tool_messages: list[ToolMessage] = []

        tool_calls = getattr(
            response,
            "tool_calls",
            [],
        )

        for tool_call in tool_calls:

            tool_name = tool_call.get(
                "name",
                "",
            )

            tool_args = tool_call.get(
                "args",
                {},
            )

            tool_call_id = tool_call.get(
                "id"
            )

            if not tool_call_id:

                tool_call_id = (
                    f"tool_call_{uuid.uuid4().hex}"
                )

            tool = TOOLS.get(
                tool_name
            )

            # --------------------------------
            # TOOL NOT FOUND
            # --------------------------------

            if not tool:

                result = (
                    f"Tool '{tool_name}' "
                    f"is not available."
                )

            # --------------------------------
            # EXECUTE TOOL
            # --------------------------------

            else:

                try:

                    if not isinstance(
                        tool_args,
                        dict,
                    ):
                        tool_args = {}

                    result = tool.invoke(
                        tool_args
                    )

                except Exception as e:

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

        return tool_messages

    # ========================================================
    # LOAD CONVERSATION HISTORY
    # ========================================================

    def load_conversation_history(
        self,
        db,
        conversation_id: int,
    ) -> list[BaseMessage]:

        # --------------------------------
        # REDIS
        # --------------------------------

        cached_history = get_cached_history(
            conversation_id=conversation_id,
        )

        if cached_history is not None:

            return self.normalize_history(
                cached_history
            )

        # --------------------------------
        # DATABASE
        # --------------------------------

        db_messages = ChatDatabase.get_messages(
            db=db,
            conversation_id=conversation_id,
        )

        messages: list[BaseMessage] = []

        for db_message in db_messages:

            role = db_message.role
            content = db_message.content

            if not content:
                continue

            # USER
            if role == "user":

                messages.append(
                    HumanMessage(
                        content=content
                    )
                )

            # ASSISTANT
            elif role == "assistant":

                messages.append(
                    AIMessage(
                        content=content
                    )
                )

            # TOOL
            elif role == "tool":

                tool_call_id = getattr(
                    db_message,
                    "tool_call_id",
                    None,
                )

                if not tool_call_id:
                    continue

                messages.append(
                    ToolMessage(
                        content=content,
                        tool_call_id=tool_call_id,
                    )
                )

        # --------------------------------
        # CACHE HISTORY
        # --------------------------------

        if messages:

            set_cached_history(
                conversation_id=conversation_id,
                messages=messages,
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
    ) -> list[BaseMessage]:

        updated_history = [
            *history_messages,
            *new_messages,
        ]

        set_cached_history(
            conversation_id=conversation_id,
            messages=updated_history,
        )

        return updated_history

    # ========================================================
    # SAVE MESSAGE
    # ========================================================

    def save_message(
        self,
        db,
        conversation_id: int,
        role: str,
        content: str,
    ):

        if not content:
            return None

        return ChatDatabase.create_message(
            db=db,
            conversation_id=conversation_id,
            role=role,
            content=content,
        )

    # ========================================================
    # GET / CREATE CONVERSATION
    # ========================================================

    def get_or_create_conversation(
        self,
        db,
        user_id: int,
        conversation_id: int | None,
        message: str,
    ):

        # --------------------------------
        # CREATE NEW CONVERSATION
        # --------------------------------

        if conversation_id is None:

            title = message.strip()[:50]

            if not title:
                title = "New Conversation"

            conversation = (
                ChatDatabase.create_conversation(
                    db=db,
                    title=title,
                    user_id=user_id,
                )
            )

            return conversation

        # --------------------------------
        # EXISTING CONVERSATION
        # --------------------------------

        conversation = (
            ChatDatabase.get_conversation_for_user(
                db=db,
                conversation_id=conversation_id,
                user_id=user_id,
            )
        )

        if not conversation:

            raise ValueError(
                f"Conversation {conversation_id} "
                f"does not exist for user {user_id}."
            )

        return conversation

    # ========================================================
    # NORMAL CHAT
    # ========================================================

    def chat(
        self,
        message: str,
        user_id: int,
        conversation_id: int | None = None,
    ) -> str:

        total_start = time.perf_counter()

        db = SessionLocal()

        try:

            # --------------------------------
            # GET / CREATE CONVERSATION
            # --------------------------------

            conversation = (
                self.get_or_create_conversation(
                    db=db,
                    user_id=user_id,
                    conversation_id=conversation_id,
                    message=message,
                )
            )

            conversation_id = conversation.id

            # --------------------------------
            # RESPONSE CACHE
            # --------------------------------

            cached = get_cached_response(
                user_id=user_id,
                conversation_id=conversation_id,
                message=message,
            )

            if cached:

                cached_response = cached.get(
                    "response",
                    "",
                )

                if cached_response:

                    history_messages = (
                        self.load_conversation_history(
                            db=db,
                            conversation_id=conversation_id,
                        )
                    )

                    self.save_message(
                        db=db,
                        conversation_id=conversation_id,
                        role="user",
                        content=message,
                    )

                    self.save_message(
                        db=db,
                        conversation_id=conversation_id,
                        role="assistant",
                        content=cached_response,
                    )

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

                    return cached_response

            # --------------------------------
            # LOAD HISTORY
            # --------------------------------

            history_messages = (
                self.load_conversation_history(
                    db=db,
                    conversation_id=conversation_id,
                )
            )

            # --------------------------------
            # BUILD MESSAGES
            # --------------------------------

            messages = [
                SYSTEM_MESSAGE,
                *history_messages,
                HumanMessage(
                    content=message
                ),
            ]

            # --------------------------------
            # SAVE USER MESSAGE
            # --------------------------------

            self.save_message(
                db=db,
                conversation_id=conversation_id,
                role="user",
                content=message,
            )

            # --------------------------------
            # LANGGRAPH
            # --------------------------------

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

            # --------------------------------
            # SAVE RESPONSE
            # --------------------------------

            if response:

                self.save_message(
                    db=db,
                    conversation_id=conversation_id,
                    role="assistant",
                    content=response,
                )

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

                set_cached_response(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    message=message,
                    response=response,
                )

            # --------------------------------
            # COMMIT
            # --------------------------------

            db.commit()

            total_time = (
                time.perf_counter()
                - total_start
            )

            print(
                f"TOTAL REQUEST TIME: "
                f"{total_time:.2f}s"
            )

            return response

        except Exception:

            db.rollback()
            raise

        finally:

            db.close()

    # ========================================================
    # STREAM CHAT
    # ========================================================

    def stream_chat(
        self,
        message: str,
        user_id: int,
        conversation_id: int | None = None,
    ):

        total_start = time.perf_counter()

        db = SessionLocal()

        try:

            # --------------------------------
            # GET / CREATE CONVERSATION
            # --------------------------------

            conversation = (
                self.get_or_create_conversation(
                    db=db,
                    user_id=user_id,
                    conversation_id=conversation_id,
                    message=message,
                )
            )

            conversation_id = conversation.id

            # --------------------------------
            # RESPONSE CACHE
            # --------------------------------

            cached = get_cached_response(
                user_id=user_id,
                conversation_id=conversation_id,
                message=message,
            )

            if cached:

                cached_response = cached.get(
                    "response",
                    "",
                )

                if cached_response:

                    history_messages = (
                        self.load_conversation_history(
                            db=db,
                            conversation_id=conversation_id,
                        )
                    )

                    self.save_message(
                        db=db,
                        conversation_id=conversation_id,
                        role="user",
                        content=message,
                    )

                    self.save_message(
                        db=db,
                        conversation_id=conversation_id,
                        role="assistant",
                        content=cached_response,
                    )

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

                    db.commit()

                    yield cached_response
                    return

            # --------------------------------
            # LOAD HISTORY
            # --------------------------------

            history_messages = (
                self.load_conversation_history(
                    db=db,
                    conversation_id=conversation_id,
                )
            )

            history_messages = (
                self.normalize_history(
                    history_messages
                )
            )

            # --------------------------------
            # BUILD MESSAGES
            # --------------------------------

            messages = [
                SYSTEM_MESSAGE,
                *history_messages,
                HumanMessage(
                    content=message
                ),
            ]

            # --------------------------------
            # SAVE USER MESSAGE
            # --------------------------------

            self.save_message(
                db=db,
                conversation_id=conversation_id,
                role="user",
                content=message,
            )

            db.commit()

            # --------------------------------
            # FIRST LLM CALL
            # --------------------------------

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
                        "TIME TO FIRST TOKEN: "
                        f"{first_token_time:.2f}s"
                    )

                chunks.append(chunk)

                if chunk.content:

                    yield chunk.content

            # --------------------------------
            # COMBINE CONTENT
            # --------------------------------

            content = ""

            for chunk in chunks:

                if chunk.content:

                    content += chunk.content

            # --------------------------------
            # COLLECT TOOL CALLS
            # --------------------------------

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

                    if tool_call.get("name"):

                        current["name"] = (
                            tool_call["name"]
                        )

                    if tool_call_id:

                        current["id"] = (
                            tool_call_id
                        )

                    args = tool_call.get(
                        "args"
                    )

                    if isinstance(
                        args,
                        dict,
                    ):

                        current[
                            "args"
                        ].update(args)

                    elif isinstance(
                        args,
                        str,
                    ):

                        current[
                            "_raw_args"
                        ] = (
                            current.get(
                                "_raw_args",
                                "",
                            )
                            + args
                        )

            # --------------------------------
            # PARSE TOOL ARGUMENTS
            # --------------------------------

            for call in (
                tool_call_map.values()
            ):

                if not call.get("name"):
                    continue

                raw_args = call.pop(
                    "_raw_args",
                    None,
                )

                if (
                    raw_args
                    and not call["args"]
                ):

                    try:

                        parsed_args = json.loads(
                            raw_args
                        )

                        if isinstance(
                            parsed_args,
                            dict,
                        ):

                            call["args"] = (
                                parsed_args
                            )

                    except json.JSONDecodeError:

                        call["args"] = {}

                if not isinstance(
                    call.get("args"),
                    dict,
                ):

                    call["args"] = {}

                tool_calls.append(call)

            # --------------------------------
            # NO TOOL CALL
            # --------------------------------

            if not tool_calls:

                if content:

                    self.save_message(
                        db=db,
                        conversation_id=conversation_id,
                        role="assistant",
                        content=content,
                    )

                    set_cached_response(
                        user_id=user_id,
                        conversation_id=conversation_id,
                        message=message,
                        response=content,
                    )

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

                    db.commit()

                total_time = (
                    time.perf_counter()
                    - total_start
                )

                print(
                    "TOTAL REQUEST TIME: "
                    f"{total_time:.2f}s"
                )

                return

            # --------------------------------
            # AI TOOL-CALL MESSAGE
            # --------------------------------

            response = AIMessage(
                content=content,
                tool_calls=tool_calls,
            )

            # --------------------------------
            # EXECUTE TOOLS
            # --------------------------------

            tool_messages = (
                self.execute_tools(
                    response
                )
            )

            # --------------------------------
            # FINAL LLM MESSAGES
            # --------------------------------

            final_messages = [
                *messages,
                response,
                *tool_messages,
            ]

            # --------------------------------
            # FINAL LLM CALL
            # --------------------------------

            final_start = (
                time.perf_counter()
            )

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
                        "FINAL TIME TO FIRST TOKEN: "
                        f"{final_first_token:.2f}s"
                    )

                if chunk.content:

                    ai_content += chunk.content

                    yield chunk.content

            # --------------------------------
            # SAVE FINAL RESPONSE
            # --------------------------------

            if ai_content:

                self.save_message(
                    db=db,
                    conversation_id=conversation_id,
                    role="assistant",
                    content=ai_content,
                )

                set_cached_response(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    message=message,
                    response=ai_content,
                )

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

            db.commit()

            total_time = (
                time.perf_counter()
                - total_start
            )

            print(
                "TOTAL REQUEST TIME: "
                f"{total_time:.2f}s"
            )

        except Exception:

            db.rollback()
            raise

        finally:

            db.close()

    # ========================================================
    # REFRESH REDIS HISTORY
    # ========================================================

    def refresh_history_cache(
        self,
        db,
        conversation_id: int,
    ):

        db_messages = ChatDatabase.get_messages(
            db=db,
            conversation_id=conversation_id,
        )

        messages: list[BaseMessage] = []

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

        set_cached_history(
            conversation_id=conversation_id,
            messages=messages,
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

            return result.get(
                "response",
                "",
            )

        finally:

            db.close()


# ============================================================
# SINGLE SERVICE INSTANCE
# ============================================================

chat_service = ChatService()