from fastapi import FastAPI

OPENAPI_TAGS = [
    {"name": "Users", "description": "Управление пользователями"},
    {"name": "PrivateChats", "description": "Приватные чаты между пользователями"},
    {"name": "messages", "description": "Сообщения в чатах"},
    {"name": "Health", "description": "Проверка работоспособности сервиса"},
]

app = FastAPI(
    title="Chat Volc API",
    description="REST API для чат-приложения на базе FastAPI.",
    version="1.0.0",
    openapi_tags=OPENAPI_TAGS,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

from chat_volc.routers.chats import router as private_chat_router
from chat_volc.routers.users import router as users_router
from chat_volc.routers.messages import router as message_router

app.include_router(private_chat_router)
app.include_router(users_router)
app.include_router(message_router)


@app.get("/healf_check", tags=["Health"], summary="Health check")
async def healf_check():
    return {"message": "alive"}



if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8010, reload=True)
