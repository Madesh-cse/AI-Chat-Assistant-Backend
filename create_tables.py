from app.db.database import Base, engine

# IMPORTANT: import every model
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.pdf_document import PDFDocument
from app.models.app_connection import AppConnection


print("Creating database tables...")

Base.metadata.create_all(bind=engine)

print("Database tables created successfully ✅")
