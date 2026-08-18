from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

OPENAPI_TAGS = [
    {"name": "Auth", "description": "OAuth Яндекс / ВК и сессия"},
    {"name": "Users", "description": "Управление пользователями"},
    {"name": "PrivateChats", "description": "Приватные чаты между пользователями"},
    {"name": "messages", "description": "Сообщения в чатах"},
    {"name": "WebSocket", "description": "Real-time обновления через WebSocket"},
    {"name": "Health", "description": "Проверка работоспособности сервиса"},
]


@asynccontextmanager
async def _lifespan(application):
    from chat_volc.routers.ws import start_subscriber
    start_subscriber()
    yield


app = FastAPI(
    title="Chat Volc API",
    description="REST API для чат-приложения на базе FastAPI.",
    version="1.2.0",
    openapi_tags=OPENAPI_TAGS,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=_lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from chat_volc.routers.auth import router as auth_router          # noqa: E402
from chat_volc.routers.chats import router as private_chat_router # noqa: E402
from chat_volc.routers.messages import router as message_router   # noqa: E402
from chat_volc.routers.users import router as users_router        # noqa: E402
from chat_volc.routers.ws import router as ws_router              # noqa: E402

app.include_router(auth_router)
app.include_router(private_chat_router)
app.include_router(users_router)
app.include_router(message_router)
app.include_router(ws_router)


@app.get("/healf_check", tags=["Health"], summary="Health check")
async def healf_check():
    return {"message": "alive"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
