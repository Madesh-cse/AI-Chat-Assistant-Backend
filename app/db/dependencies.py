from collections.abc import Generator

from app.db.database import SessionLocal


def get_db() -> Generator:

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()