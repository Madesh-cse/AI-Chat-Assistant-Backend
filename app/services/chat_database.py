from sqlalchemy.orm import Session, selectinload  # type: ignore

from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.pdf_document import PDFDocument


class ChatDatabase:

    # ============================================================
    # USER
    # ============================================================

    @staticmethod
    def create_user(
        db: Session,
        name: str,
        email: str,
    ):
        user = User(
            name=name,
            email=email,
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        return user

    @staticmethod
    def get_user(
        db: Session,
        user_id: int,
    ):
        return (
            db.query(User)
            .filter(
                User.id == user_id
            )
            .first()
        )

    # ============================================================
    # CREATE CONVERSATION
    # ============================================================

    @staticmethod
    def create_conversation(
        db: Session,
        title: str,
        user_id: int,
    ):
        conversation = Conversation(
            title=title,
            user_id=user_id,
        )

        db.add(conversation)

        db.commit()

        db.refresh(conversation)

        # --------------------------------------------------------
        # IMPORTANT
        #
        # Reload the conversation with messages eagerly loaded.
        #
        # This prevents DetachedInstanceError when FastAPI
        # serializes ConversationResponse.
        # --------------------------------------------------------

        conversation = (
            db.query(Conversation)
            .options(
                selectinload(
                    Conversation.messages
                )
            )
            .filter(
                Conversation.id == conversation.id
            )
            .first()
        )

        return conversation

    # ============================================================
    # GET CONVERSATION
    # ============================================================

    @staticmethod
    def get_conversation(
        db: Session,
        conversation_id: int,
    ):
        return (
            db.query(Conversation)
            .options(
                selectinload(
                    Conversation.messages
                )
            )
            .filter(
                Conversation.id == conversation_id
            )
            .first()
        )

    # ============================================================
    # GET ALL CONVERSATIONS FOR USER
    # ============================================================

    @staticmethod
    def get_conversations(
        db: Session,
        user_id: int,
    ):
        return (
            db.query(Conversation)
            .options(
                selectinload(
                    Conversation.messages
                )
            )
            .filter(
                Conversation.user_id == user_id
            )
            .order_by(
                Conversation.updated_at.desc()
            )
            .all()
        )

    # ============================================================
    # GET SINGLE CONVERSATION FOR USER
    # ============================================================

    @staticmethod
    def get_conversation_for_user(
        db: Session,
        conversation_id: int,
        user_id: int,
    ):
        return (
            db.query(Conversation)
            .options(
                selectinload(
                    Conversation.messages
                )
            )
            .filter(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
            )
            .first()
        )

    # ============================================================
    # DELETE CONVERSATION
    # ============================================================

    @staticmethod
    def delete_conversation(
        db: Session,
        conversation_id: int,
    ):
        conversation = (
            db.query(Conversation)
            .filter(
                Conversation.id == conversation_id
            )
            .first()
        )

        if not conversation:
            return False

        db.delete(conversation)

        db.commit()

        return True

    # ============================================================
    # CREATE MESSAGE
    # ============================================================

    @staticmethod
    def create_message(
        db: Session,
        conversation_id: int,
        role: str,
        content: str,
    ):
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
        )

        db.add(message)

        db.commit()

        db.refresh(message)

        return message

    # GET MESSAGES

    @staticmethod
    def get_messages(
        db: Session,
        conversation_id: int,
    ):
        return (
            db.query(Message)
            .filter(
                Message.conversation_id == conversation_id
            )
            .order_by(
                Message.created_at.asc()
            )
            .all()
        )

    # PDF

    @staticmethod
    def create_pdf_document(
        db: Session,
        filename: str,
        file_path: str,
        conversation_id: int,
    ):
        pdf = PDFDocument(
            filename=filename,
            file_path=file_path,
            conversation_id=conversation_id,
        )

        db.add(pdf)

        db.commit()

        db.refresh(pdf)

        return pdf

    # ============================================================
    # GET PDF
    # ============================================================

    @staticmethod
    def get_pdf_document(
        db: Session,
        pdf_id: int,
    ):
        return (
            db.query(PDFDocument)
            .filter(
                PDFDocument.id == pdf_id
            )
            .first()
        )

    # ============================================================
    # GET CONVERSATION PDFS
    # ============================================================

    @staticmethod
    def get_conversation_pdfs(
        db: Session,
        conversation_id: int,
    ):
        return (
            db.query(PDFDocument)
            .filter(
                PDFDocument.conversation_id == conversation_id
            )
            .order_by(
                PDFDocument.created_at.asc()
            )
            .all()
        )