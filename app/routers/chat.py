from fastapi import (APIRouter,HTTPException,)  # type: ignore

from fastapi.responses import (StreamingResponse,)  # type: ignore

from app.Schemas.chat import (
    ChatRequest,
    ChatResponse,
)

from app.services.chat_service import (
    chat_service,
)


router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


# ==================================================
# NORMAL CHAT API
# ==================================================

@router.post(
    "/",
    response_model=ChatResponse,
)
async def chat(
    request: ChatRequest,
):

    try:

        response = chat_service.chat(
            request.message
        )

        return ChatResponse(
            response=response
        )

    except Exception as e:

        print(
            "\n=============================="
        )

        print("CHAT ERROR")

        print(
            "=============================="
        )

        print(e)

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


# ==================================================
# STREAMING CHAT API
# ==================================================

@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
):

    def generate():

        try:

            print(
                "\n=============================="
            )

            print("STREAM ROUTER")

            print(
                "=============================="
            )

            print(
                "Conversation ID:",
                request.conversation_id,
            )

            print(
                "Message:",
                request.message,
            )

            # ------------------------------------------
            # START CHAT SERVICE
            # ------------------------------------------

            for chunk in chat_service.stream_chat(
                message=request.message,
                conversation_id=request.conversation_id,
            ):

                yield chunk

        except Exception as e:

            print(
                "\n=============================="
            )

            print("STREAM ERROR")

            print(
                "=============================="
            )

            print(e)

            yield (
                f"\n❌ Error: {str(e)}"
            )

    return StreamingResponse(
        generate(),
        media_type="text/plain; charset=utf-8",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )