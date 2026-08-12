import time

from app.chains.chat_chain import (
    get_llm_response,
)

from app.services.llm import (
    llm_with_tools,
)

from app.prompts.chat_prompt import (
    chat_prompt,
)


from app.tools.weather import (
    get_weather,
)

from app.tools.city_image import (
    get_city_image,
)

from app.tools.news import (
    get_news,
)

from app.tools.wikipedia import (
    search_wikipedia,
)

from app.tools.web_search import (
    web_search,
)

from app.tools.movie import (
    get_movie,
)


from langchain_core.messages import (  # type: ignore
    ToolMessage,
    HumanMessage,
    AIMessage,
)


from app.db.database import (
    SessionLocal,
)

from app.services.chat_database import (
    ChatDatabase,
)


# ==================================================
# AVAILABLE TOOLS
# ==================================================

TOOLS = {

    "get_weather": get_weather,

    "get_city_image": get_city_image,

    "get_news": get_news,

    "search_wikipedia": search_wikipedia,

    "web_search": web_search,

    "get_movie": get_movie,
}


# ==================================================
# CHAT SERVICE
# ==================================================

class ChatService:

    # ==================================================
    # EXECUTE TOOLS
    # ==================================================

    def execute_tools(
        self,
        response,
    ):

        tool_messages = []

        total_tool_start = (
            time.perf_counter()
        )

        for tool_call in response.tool_calls:

            tool_name = tool_call["name"]

            tool_args = tool_call.get(
                "args",
                {},
            )

            print(
                "\n=============================="
            )

            print("TOOL")

            print(
                "=============================="
            )

            print(
                "Name:",
                tool_name,
            )

            print(
                "Args:",
                tool_args,
            )

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
                        f"\n⏱️ {tool_name} TIME: "
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

            tool_messages.append(
                ToolMessage(
                    content=str(result),
                    tool_call_id=tool_call["id"],
                )
            )

        total_tool_time = (
            time.perf_counter()
            - total_tool_start
        )

        print(
            f"\n⏱️ TOTAL TOOL TIME: "
            f"{total_tool_time:.2f}s"
        )

        return tool_messages

    # ==================================================
    # NORMAL CHAT
    # ==================================================

    def chat(
        self,
        message: str,
    ) -> str:

        total_start = (
            time.perf_counter()
        )

        print(
            "\n=============================="
        )

        print("USER MESSAGE")

        print(
            "=============================="
        )

        print(message)

        # ------------------------------------------
        # FIRST LLM
        # ------------------------------------------

        llm_start = (
            time.perf_counter()
        )

        response = get_llm_response(
            message
        )

        llm_time = (
            time.perf_counter()
            - llm_start
        )

        print(
            f"\n⏱️ FIRST LLM CALL: "
            f"{llm_time:.2f}s"
        )

        print(
            "\n=============================="
        )

        print("QWEN RESPONSE")

        print(
            "=============================="
        )

        print(response)

        print("\nTOOL CALLS:")

        print(response.tool_calls)

        # ------------------------------------------
        # NO TOOL
        # ------------------------------------------

        if not response.tool_calls:

            total_time = (
                time.perf_counter()
                - total_start
            )

            print(
                f"\n⏱️ TOTAL REQUEST TIME: "
                f"{total_time:.2f}s"
            )

            return response.content

        # ------------------------------------------
        # EXECUTE TOOLS
        # ------------------------------------------

        tool_messages = (
            self.execute_tools(
                response
            )
        )

        # ------------------------------------------
        # FINAL CONVERSATION
        # ------------------------------------------

        final_messages = [

            HumanMessage(
                content=message
            ),

            response,

            *tool_messages,
        ]

        # ------------------------------------------
        # FINAL LLM
        # ------------------------------------------

        final_start = (
            time.perf_counter()
        )

        final_response = (
            llm_with_tools.invoke(
                final_messages
            )
        )

        final_time = (
            time.perf_counter()
            - final_start
        )

        print(
            f"\n⏱️ FINAL LLM CALL: "
            f"{final_time:.2f}s"
        )

        print(
            "\n=============================="
        )

        print("FINAL RESPONSE")

        print(
            "=============================="
        )

        print(
            final_response.content
        )

        total_time = (
            time.perf_counter()
            - total_start
        )

        print(
            f"\n⏱️ TOTAL REQUEST TIME: "
            f"{total_time:.2f}s"
        )

        return final_response.content

    # ==================================================
    # STREAMING CHAT
    # ==================================================

    def stream_chat(
        self,
        message: str,
        conversation_id: int | None = None,
    ):

        total_start = (
            time.perf_counter()
        )

        DEFAULT_USER_ID = 1

        db = SessionLocal()

        try:

            print(
                "\n=============================="
            )

            print("STREAM REQUEST")

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

            # ==================================================
            # 1. CREATE OR VALIDATE CONVERSATION
            # ==================================================

            if conversation_id is None:

                print(
                    "\n=============================="
                )

                print(
                    "CREATING NEW CONVERSATION"
                )

                print(
                    "=============================="
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

                # ------------------------------------------
                # IMPORTANT FK VALIDATION
                # ------------------------------------------

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
            # 2. SAVE USER MESSAGE
            # ==================================================

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

            print(
                "USER MESSAGE SAVED ✅"
            )

            # ==================================================
            # 3. BUILD PROMPT
            # ==================================================

            prompt_start = (
                time.perf_counter()
            )

            prompt_value = (
                chat_prompt.invoke(
                    {
                        "message": message
                    }
                )
            )

            prompt_time = (
                time.perf_counter()
                - prompt_start
            )

            print(
                f"\n⏱️ PROMPT BUILD TIME: "
                f"{prompt_time:.4f}s"
            )

            # ==================================================
            # 4. FIRST LLM STREAM
            # ==================================================

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

            for chunk in (
                llm_with_tools.stream(
                    prompt_value
                )
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

                chunks.append(
                    chunk
                )

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
            # 5. BUILD COMPLETE RESPONSE
            # ==================================================

            content = ""

            for chunk in chunks:

                if chunk.content:

                    content += chunk.content

            # ==================================================
            # 6. COLLECT TOOL CALLS
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

            print("Content:")

            print(content)

            print("\nTool Calls:")

            print(tool_calls)

            # ==================================================
            # 7. NO TOOL REQUIRED
            # ==================================================

            if not tool_calls:

                print(
                    "\n=============================="
                )

                print(
                    "NO TOOL REQUIRED"
                )

                print(
                    "=============================="
                )

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
            # 8. CREATE AI MESSAGE
            # ==================================================

            response = AIMessage(
                content=content,
                tool_calls=tool_calls,
            )

            # ==================================================
            # 9. EXECUTE TOOLS
            # ==================================================

            print(
                "\n=============================="
            )

            print(
                "EXECUTING TOOLS"
            )

            print(
                "=============================="
            )

            tool_messages = (
                self.execute_tools(
                    response
                )
            )

            # ==================================================
            # 10. BUILD FINAL CONVERSATION
            # ==================================================

            final_messages = [

                HumanMessage(
                    content=message
                ),

                response,

                *tool_messages,
            ]

            # ==================================================
            # 11. FINAL LLM STREAM
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
            # 12. SAVE AI RESPONSE
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
            # 13. TOTAL TIME
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

            print(e)

            db.rollback()

            raise

        finally:

            db.close()

            print(
                "\nDATABASE CONNECTION "
                "CLOSED ✅"
            )


# ==================================================
# SINGLETON
# ==================================================

chat_service = ChatService()