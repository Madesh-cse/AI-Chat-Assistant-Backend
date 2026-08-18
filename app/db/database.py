import os

from dotenv import load_dotenv  # type: ignore
from sqlalchemy import create_engine  # type: ignore
from sqlalchemy.orm import (  # type: ignore
    DeclarativeBase,
    sessionmaker,
) 


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL is not configured"
    )


engine = create_engine(
    DATABASE_URL,
    echo=True,
)


SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    pass



def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()

# CREATE TABLES

def create_tables():

    from app.models.user import User
    from app.models.conversation import Conversation
    from app.models.message import Message
    from app.models.pdf_document import PDFDocument
    from app.models.app_connection import AppConnection

    print("\n==============================")
    print("CREATING DATABASE TABLES")
    print("==============================")

    Base.metadata.create_all(
        bind=engine
    )

    print("DATABASE TABLES READY ✅")