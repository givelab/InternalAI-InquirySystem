# backend/src/main.py
from src.routers import users
from src.routers import tasks
from src.routers import chat

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.database import close_database, open_database, get_db_engine
from src.dependencies.logs import get_logger
from src.models import Base
from src.routers import users
from src.routers.exceptions import add_exception_handlers
from src.schemas.health_check import HealthCheck
from src.utils.logs import LogClient, LoggingMiddleware, set_basic_config


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    set_basic_config()
    open_database()
    engine = await get_db_engine()
    Base.metadata.create_all(bind=engine)
    yield
    close_database()


app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
# ...
app.include_router(users.router, prefix="/users")
app.include_router(tasks.router, prefix="/tasks")
app.include_router(chat.router, prefix="/chat")


# FastAPIのエラーハンドリングを追加します。
add_exception_handlers(app)

origins = [
    "http://localhost",
    "http://localhost:8000",
    # FIXME: 必要に応じて許可するOriginを追加してください。
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(LoggingMiddleware)

# エンドポイントごとにファイルを分割する場合、エンドポイントごとのルーターを追加していきます。
app.include_router(users.router, prefix="/users")


# 小規模なプロジェクトでは、main.py に全てのエンドポイントを書いてしまうこともあります。
# しかし、大規模なプロジェクトでは、エンドポイントごとにファイルを分割することが一般的です。
# ここでは記述の例としてhealth_checkエンドポイントをmain.pyに書いています。
@app.get("/health-check", response_model=HealthCheck)
def health_check(logger: LogClient = Depends(get_logger)) -> HealthCheck:
    logger.info("Health check")
    return HealthCheck(status="ok")
