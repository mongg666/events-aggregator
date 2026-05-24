import logging
from fastapi import APIRouter, BackgroundTasks, Depends
from app.tasks import run_sync

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/sync/trigger", status_code=200)
async def trigger_sync(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_sync)
    return {"status": "sync started"}