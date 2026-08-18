from fastapi import FastAPI  # type: ignore
from fastapi.middleware.cors import CORSMiddleware  # type: ignore

from app.routers.chat import router as chat_router
from app.routers.pdf import router as pdf_router
from app.routers.conversation import router as conversation_router
from app.routers.settings import router as settings_router


app = FastAPI(
    title="AI Chat Bot",
    description="A simple AI chat bot using FastAPI and LangChain",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(chat_router)
app.include_router(pdf_router)
app.include_router(conversation_router)
app.include_router(settings_router)


@app.get("/")
async def read_root():

    return {
        "message": "Hello World"
    }