import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import Base, engine
from app.routers import events, health, sync, tickets
from app.tasks import periodic_sync

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Создаём таблицы при старте (для простоты; в продакшене используем миграции)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Запускаем фоновую синхронизацию
    task = asyncio.create_task(periodic_sync())
    logger.info("Application started")
    yield
    task.cancel()
    await engine.dispose()


app = FastAPI(title="Events Aggregator", lifespan=lifespan)

app.include_router(health.router, tags=["health"])
app.include_router(events.router, prefix="/api", tags=["events"])
app.include_router(tickets.router, prefix="/api", tags=["tickets"])
app.include_router(sync.router, prefix="/api", tags=["sync"])
