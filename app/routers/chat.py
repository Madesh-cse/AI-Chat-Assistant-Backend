from fastapi import ( # type: ignore
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from fastapi.responses import StreamingResponse  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from app.db.database import get_db
from app.models.user import User
from app.services.chat_database import ChatDatabase
from app.Schemas.chat import (
    ChatRequest,
    ChatResponse,
)
from app.services.chat_service import chat_service
from app.core.dependencies import get_current_user


router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


@router.post(
    "/",
    response_model=ChatResponse,
)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:

        if request.conversation_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Conversation ID is required",
            )

        conversation = ChatDatabase.get_conversation_for_user(
            db=db,
            conversation_id=request.conversation_id,
            user_id=current_user.id,
        )

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )

        response = chat_service.chat(
            message=request.message,
            conversation_id=request.conversation_id,
            user_id=current_user.id,
        )

        return ChatResponse(
            response=response,
        )

    except HTTPException:
        raise

    except Exception as e:
        print("\n==============================")
        print("CHAT ERROR")
        print("==============================")
        print(e)
        print("==============================\n")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process chat request",
        )

# STREAMING CHAT API

@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):


    if request.conversation_id is not None:

        conversation = ChatDatabase.get_conversation_for_user(
            db=db,
            conversation_id=request.conversation_id,
            user_id=current_user.id,
        )

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )


    print("\n==============================")
    print("STREAM ROUTER")
    print("==============================")

    print(
        "User ID:",
        current_user.id,
    )

    print(
        "Conversation ID:",
        request.conversation_id,
    )

    print(
        "Message:",
        request.message,
    )
    print("Stack Overflow:", request.stack_overflow_enabled)
    print("Notion:", request.notion_enabled)
    print("Language:", request.language)


    print("==============================\n")


    def generate():

        try:

            for chunk in chat_service.stream_chat(
                message=request.message,
                conversation_id=request.conversation_id,
                user_id=current_user.id,
                stack_overflow_enabled=request.stack_overflow_enabled,
                notion_enabled=request.notion_enabled,
                language=request.language,
            ):
                yield chunk

        except Exception as e:

            print("\n==============================")
            print("STREAM ERROR")
            print("==============================")
            print(e)
            print("==============================\n")

            yield f"\n❌ Error: {str(e)}"

    # ------------------------------------------
    # STREAM RESPONSE
    # ------------------------------------------

    return StreamingResponse(
        generate(),
        media_type="text/plain; charset=utf-8",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )