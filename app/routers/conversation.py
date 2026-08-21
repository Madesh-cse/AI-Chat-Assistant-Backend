from fastapi import APIRouter, Depends, HTTPException, status # type: ignore
from pydantic import BaseModel # type: ignore
from sqlalchemy.orm import Session # type: ignore

from app.db.database import get_db
from app.services.chat_database import ChatDatabase
from app.Schemas.conversation import (
    ConversationCreate,
    ConversationResponse,
)
from app.core.dependencies import get_current_user
from app.models.user import User


router = APIRouter(
    prefix="/conversations",
    tags=["Conversations"],
)


# =========================================================
# CREATE CONVERSATION
# =========================================================

@router.post(
    "/",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_conversation(
    request: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        conversation = ChatDatabase.create_conversation(
            db=db,
            title=request.title,
            user_id=current_user.id,
        )

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
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
        print("========================================\n")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create conversation",
        )


# =========================================================
# GET ALL CONVERSATIONS
# =========================================================

@router.get(
    "/",
    response_model=list[ConversationResponse],
)
def get_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        conversations = ChatDatabase.get_conversations(
            db=db,
            user_id=current_user.id,
        )

        return conversations

    except Exception as e:
        print("\n========================================")
        print("GET CONVERSATIONS ERROR")
        print("========================================")
        print(e)
        print("========================================\n")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get conversations",
        )


# =========================================================
# GET SINGLE CONVERSATION
# =========================================================

@router.get(
    "/{conversation_id}",
    response_model=ConversationResponse,
)
def get_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        conversation = ChatDatabase.get_conversation_for_user(
            db=db,
            conversation_id=conversation_id,
            user_id=current_user.id,
        )

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
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
        print("========================================\n")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get conversation",
        )


# =========================================================
# UPDATE CONVERSATION TITLE
# =========================================================

class UpdateConversationTitle(BaseModel):
    title: str


@router.patch(
    "/{conversation_id}/title",
    response_model=ConversationResponse,
)
def update_conversation_title(
    conversation_id: int,
    request: UpdateConversationTitle,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        # Verify ownership
        conversation = ChatDatabase.get_conversation_for_user(
            db=db,
            conversation_id=conversation_id,
            user_id=current_user.id,
        )

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )

        # Validate title
        title = request.title.strip()

        if not title:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Conversation title cannot be empty",
            )

        # Limit title length
        title = title[:100]

        # Update title
        conversation.title = title

        db.commit()
        db.refresh(conversation)

        return conversation

    except HTTPException:
        raise

    except Exception as e:
        db.rollback()

        print("\n========================================")
        print("UPDATE CONVERSATION TITLE ERROR")
        print("========================================")
        print(e)
        print("========================================\n")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update conversation title",
        )


# =========================================================
# DELETE CONVERSATION
# =========================================================

@router.delete(
    "/{conversation_id}",
)
def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        # Verify ownership first
        conversation = ChatDatabase.get_conversation_for_user(
            db=db,
            conversation_id=conversation_id,
            user_id=current_user.id,
        )

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )

        # Delete conversation
        deleted = ChatDatabase.delete_conversation(
            db=db,
            conversation_id=conversation_id,
        )

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
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
        print("========================================\n")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete conversation",
        )


# =========================================================
# PIN / UNPIN CONVERSATION
# =========================================================

@router.patch(
    "/{conversation_id}/pin",
    response_model=ConversationResponse,
)
def toggle_pin_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        # Verify ownership
        conversation = ChatDatabase.get_conversation_for_user(
            db=db,
            conversation_id=conversation_id,
            user_id=current_user.id,
        )

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )

        # Toggle pin
        conversation.is_pinned = not conversation.is_pinned

        db.commit()
        db.refresh(conversation)

        return conversation

    except HTTPException:
        raise

    except Exception as e:
        db.rollback()

        print("\n========================================")
        print("PIN CONVERSATION ERROR")
        print("========================================")
        print(e)
        print("========================================\n")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update conversation",
        )