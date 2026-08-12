import os

from dotenv import load_dotenv  # type: ignore
from sqlalchemy import create_engine  # type: ignore
from sqlalchemy.orm import (DeclarativeBase, sessionmaker,)  # type: ignore

# ENVIRONMENT

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL is not configured"
    )

# DATABASE ENGINE

engine = create_engine(
    DATABASE_URL,
    echo=True,
)

# SESSION

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)

# BASE

class Base(DeclarativeBase):
    pass


# CREATE TABLES

def create_tables():

    # Import models here so SQLAlchemy knows about them
    from app.models.user import User
    from app.models.conversation import Conversation
    from app.models.message import Message
    from app.models.pdf_document import PDFDocument

    print("\n==============================")
    print("CREATING DATABASE TABLES")
    print("==============================")

    Base.metadata.create_all(
        bind=engine
    )

    print("DATABASE TABLES READY ✅")