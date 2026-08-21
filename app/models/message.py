from datetime import datetime

from sqlalchemy import ( # type: ignore
    Text,
    String,
    DateTime,
    ForeignKey,
    JSON,
)

from sqlalchemy.orm import ( # type: ignore
    Mapped,
    mapped_column,
    relationship,
)

from app.db.database import Base


class Message(Base):

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    conversation_id: Mapped[int] = mapped_column(
        ForeignKey(
            "conversations.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    tool_call_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )

    tool_calls: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    conversation = relationship(
        "Conversation",
        back_populates="messages",
    )