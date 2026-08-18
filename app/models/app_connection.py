from datetime import datetime

from sqlalchemy import ( # type: ignore
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint, 
)
from sqlalchemy.orm import Mapped, mapped_column, relationship # type: ignore

from app.db.database import Base


class AppConnection(Base):
    __tablename__ = "app_connections"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    app_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    connected: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    user = relationship(
        "User",
        back_populates="app_connections",
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "app_id",
            name="uq_user_app_connection",
        ),
    )