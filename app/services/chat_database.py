from sqlalchemy.orm import Session, selectinload  # type: ignore

from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.pdf_document import PDFDocument


class ChatDatabase:

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
        return db.query(User).filter(User.id == user_id).first()

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

        conversation = (
            db.query(Conversation)
            .options(selectinload(Conversation.messages))
            .filter(Conversation.id == conversation.id)
            .first()
        )

        return conversation

    @staticmethod
    def get_conversation(
        db: Session,
        conversation_id: int,
    ):
        return (
            db.query(Conversation)
            .options(selectinload(Conversation.messages))
            .filter(Conversation.id == conversation_id)
            .first()
        )

    @staticmethod
    def get_conversations(
        db: Session,
        user_id: int,
    ):
        return (
            db.query(Conversation)
            .options(selectinload(Conversation.messages))
            .filter(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
            .all()
        )

    @staticmethod
    def get_conversation_for_user(
        db: Session,
        conversation_id: int,
        user_id: int,
    ):
        return (
            db.query(Conversation)
            .options(selectinload(Conversation.messages))
            .filter(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
            )
            .first()
        )

    @staticmethod
    def delete_conversation(
        db: Session,
        conversation_id: int,
    ):
        conversation = (
            db.query(Conversation).filter(Conversation.id == conversation_id).first()
        )

        if not conversation:
            return False

        db.delete(conversation)
        db.commit()

        return True

    @staticmethod
    def create_message(
        db: Session,
        conversation_id: int,
        role: str,
        content: str,
        tool_call_id: str | None = None,
        tool_calls: list | None = None,
    ):
        """
        Create a conversation message.

        Supports:
            user
            assistant
            tool

        For tool messages, tool_call_id is preserved so that
        LangChain can correctly associate the ToolMessage with
        the corresponding AIMessage tool call.
        """

        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            tool_call_id=tool_call_id,
            tool_calls=tool_calls,
        )

        db.add(message)
        db.commit()
        db.refresh(message)

        return message

    @staticmethod
    def get_messages(
        db: Session,
        conversation_id: int,
    ):
        return (
            db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .all()
        )

    @staticmethod
    def get_message(
        db: Session,
        message_id: int,
    ):
        return db.query(Message).filter(Message.id == message_id).first()

    @staticmethod
    def delete_message(
        db: Session,
        message_id: int,
    ):
        message = db.query(Message).filter(Message.id == message_id).first()

        if not message:
            return False

        db.delete(message)
        db.commit()

        return True

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

    @staticmethod
    def get_pdf_document(
        db: Session,
        pdf_id: int,
    ):
        return db.query(PDFDocument).filter(PDFDocument.id == pdf_id).first()

    @staticmethod
    def get_conversation_pdfs(
        db: Session,
        conversation_id: int,
    ):
        return (
            db.query(PDFDocument)
            .filter(PDFDocument.conversation_id == conversation_id)
            .order_by(PDFDocument.created_at.asc())
            .all()
        )

    @staticmethod
    def delete_pdf_document(
        db: Session,
        pdf_id: int,
    ):
        pdf = db.query(PDFDocument).filter(PDFDocument.id == pdf_id).first()

        if not pdf:
            return False

        db.delete(pdf)
        db.commit()

        return True
