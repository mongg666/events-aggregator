import asyncio
import logging

from app.clients import EventsProviderClient
from app.config import settings
from app.database import async_session_factory
from app.repositories import EventRepository, SyncRepository
from app.usecases import SyncEventsUsecase

logger = logging.getLogger(__name__)


async def run_sync():
    logger.info("Background sync triggered")
    client = EventsProviderClient()
    try:
        async with async_session_factory() as session:
            event_repo = EventRepository(session)
            sync_repo = SyncRepository(session)
            usecase = SyncEventsUsecase(client, event_repo, sync_repo)
            await usecase.run()
            await session.commit()
    except Exception as e:
        logger.error("Sync failed: %s", e)
    finally:
        await client.close()


async def periodic_sync(interval: int = settings.sync_interval_seconds):
    while True:
        await asyncio.sleep(interval)
        await run_sync()
