import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.crud_papers import (
    create_paper,
    delete_paper,
    get_paper,
    get_paper_with_sections,
    list_papers,
)
from app.db.session import get_db
from app.schemas.papers import PaperDetailOut, PaperOut
from app.services.events import stream as event_stream
from app.services.ingestion_runner import spawn_ingestion
from app.services.storage import delete_paper_files, save_upload

router = APIRouter(prefix="/api/papers", tags=["papers"])


@router.post("", response_model=PaperOut)
async def upload_paper(file: UploadFile, db: AsyncSession = Depends(get_db)) -> PaperOut:
    if file.content_type != "application/pdf" and not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    paper = await create_paper(
        db, filename="", original_filename=file.filename or "paper.pdf", file_path=""
    )
    filename, file_path = await save_upload(paper.id, file)
    paper.filename = filename
    paper.file_path = file_path
    await db.commit()
    await db.refresh(paper)

    spawn_ingestion(paper.id)

    return PaperOut.model_validate(paper)


@router.get("", response_model=list[PaperOut])
async def get_papers(db: AsyncSession = Depends(get_db)) -> list[PaperOut]:
    papers = await list_papers(db)
    return [PaperOut.model_validate(p) for p in papers]


@router.get("/{paper_id}", response_model=PaperDetailOut)
async def get_paper_detail(paper_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> PaperDetailOut:
    paper = await get_paper_with_sections(db, paper_id)
    if paper is None:
        raise HTTPException(status_code=404, detail="Paper not found")
    return PaperDetailOut.model_validate(paper)


@router.get("/{paper_id}/ingest/stream")
async def stream_ingest_progress(paper_id: uuid.UUID) -> StreamingResponse:
    async def gen():
        async for event in event_stream(str(paper_id)):
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")


@router.get("/{paper_id}/file")
async def get_paper_file(paper_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    paper = await get_paper(db, paper_id)
    if paper is None:
        raise HTTPException(status_code=404, detail="Paper not found")
    return FileResponse(paper.file_path, media_type="application/pdf")


@router.delete("/{paper_id}")
async def remove_paper(paper_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> dict:
    paper = await get_paper(db, paper_id)
    if paper is None:
        raise HTTPException(status_code=404, detail="Paper not found")

    file_path = paper.file_path
    await delete_paper(db, paper_id)
    if file_path:
        delete_paper_files(paper_id, file_path)

    return {"deleted": True}
