import asyncio
import uuid

from app.db.session import AsyncSessionLocal
from app.ingestion.pipeline import run_ingestion


def spawn_ingestion(paper_id: uuid.UUID) -> None:
    asyncio.create_task(_run(paper_id))


async def _run(paper_id: uuid.UUID) -> None:
    async with AsyncSessionLocal() as db:
        await run_ingestion(db, paper_id)
