from fastapi import APIRouter, HTTPException  # type: ignore
from pydantic import BaseModel  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from app.db.database import SessionLocal

from app.services.chat_database import ChatDatabase

from app.Schemas.conversation import (
    ConversationCreate,
    ConversationResponse,
)

# ROUTER

router = APIRouter(
    prefix="/conversations",
    tags=["Conversations"],
)

# TEMPORARY USER

DEFAULT_USER_ID = 1


# CREATE CONVERSATION
@router.post(
    "/",
    response_model=ConversationResponse,
)
def create_conversation(
    request: ConversationCreate,
):

    db = SessionLocal()

    try:

        # ----------------------------------------------------
        # Check user
        # ----------------------------------------------------

        user = ChatDatabase.get_user(
            db=db,
            user_id=DEFAULT_USER_ID,
        )

        if not user:

            raise HTTPException(
                status_code=404,
                detail="User not found",
            )

        # ----------------------------------------------------
        # Create conversation
        # ----------------------------------------------------

        conversation = ChatDatabase.create_conversation(
            db=db,
            title=request.title,
            user_id=DEFAULT_USER_ID,
        )

        if not conversation:

            raise HTTPException(
                status_code=500,
                detail="Failed to create conversation",
            )

        return conversation

    except HTTPException:

        raise

    except Exception as e:

        db.rollback()

        print("\n========================================")

        print("CREATE CONVERSATION ERROR")

        print("========================================")

        print(e)

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )

    finally:

        db.close()


# GET ALL CONVERSATIONS


@router.get(
    "/",
    response_model=list[ConversationResponse],
)
def get_conversations():

    db = SessionLocal()

    try:

        conversations = ChatDatabase.get_conversations(
            db=db,
            user_id=DEFAULT_USER_ID,
        )

        return conversations

    except Exception as e:

        print("\n========================================")

        print("GET CONVERSATIONS ERROR")

        print("========================================")

        print(e)

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )

    finally:

        db.close()


# GET SINGLE CONVERSATION


@router.get(
    "/{conversation_id}",
    response_model=ConversationResponse,
)
def get_conversation(
    conversation_id: int,
):

    db = SessionLocal()

    try:

        conversation = ChatDatabase.get_conversation_for_user(
            db=db,
            conversation_id=conversation_id,
            user_id=DEFAULT_USER_ID,
        )

        if not conversation:

            raise HTTPException(
                status_code=404,
                detail="Conversation not found",
            )

        return conversation

    except HTTPException:

        raise

    except Exception as e:

        print("\n========================================")

        print("GET CONVERSATION ERROR")

        print("========================================")

        print(e)

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )

    finally:

        db.close()


# UPDATE CONVERSATION TITLE

# ============================================================
# UPDATE CONVERSATION TITLE
# ============================================================


class UpdateConversationTitle(BaseModel):

    title: str


@router.patch(
    "/{conversation_id}/title",
)
def update_conversation_title(
    conversation_id: int,
    request: UpdateConversationTitle,
):

    db = SessionLocal()

    try:

        # VERIFY CONVERSATION

        conversation = ChatDatabase.get_conversation_for_user(
            db=db,
            conversation_id=conversation_id,
            user_id=DEFAULT_USER_ID,
        )

        if not conversation:

            raise HTTPException(
                status_code=404,
                detail="Conversation not found",
            )

        # VALIDATE TITLE
        title = request.title.strip()

        if not title:

            raise HTTPException(
                status_code=400,
                detail="Conversation title cannot be empty",
            )

        # Optional: limit title length
        title = title[:100]

        # UPDATE TITLE

        conversation.title = title

        db.commit()

        db.refresh(conversation)

        print("\n========================================")
        print("CONVERSATION TITLE UPDATED")
        print("========================================")

        print(
            "Conversation ID:",
            conversation_id,
        )

        print(
            "New Title:",
            conversation.title,
        )

        # RESPONSE
        return conversation

    except HTTPException:

        raise

    except Exception as e:

        db.rollback()

        print("\n========================================")
        print("UPDATE CONVERSATION TITLE ERROR")
        print("========================================")

        print(e)

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )

    finally:

        db.close()


# DELETE CONVERSATION


@router.delete(
    "/{conversation_id}",
)
def delete_conversation(
    conversation_id: int,
):

    db = SessionLocal()

    try:

        # ----------------------------------------------------
        # Verify conversation belongs to user
        # ----------------------------------------------------

        conversation = ChatDatabase.get_conversation_for_user(
            db=db,
            conversation_id=conversation_id,
            user_id=DEFAULT_USER_ID,
        )

        if not conversation:

            raise HTTPException(
                status_code=404,
                detail="Conversation not found",
            )

        # ----------------------------------------------------
        # Delete
        # ----------------------------------------------------

        deleted = ChatDatabase.delete_conversation(
            db=db,
            conversation_id=conversation_id,
        )

        if not deleted:

            raise HTTPException(
                status_code=404,
                detail="Conversation not found",
            )

        return {
            "success": True,
            "conversation_id": conversation_id,
            "message": "Conversation deleted successfully",
        }

    except HTTPException:

        raise

    except Exception as e:

        db.rollback()

        print("\n========================================")

        print("DELETE CONVERSATION ERROR")

        print("========================================")

        print(e)

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )

    finally:

        db.close()
