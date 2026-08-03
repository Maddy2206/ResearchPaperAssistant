import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Chunk, ContentType, PaperStatus
from app.db.crud_papers import (
    add_section,
    get_paper,
    update_paper_metadata,
    update_paper_status,
)
from app.embeddings.client import embed_texts
from app.ingestion.chunker import build_chunks
from app.ingestion.extract_pymupdf import extract_with_pymupdf
from app.ingestion.extract_unstructured import extract_with_unstructured
from app.ingestion.sectionizer import build_sections
from app.services.chat_runner import spawn_paper_kickoffs
from app.services.events import close, publish


async def run_ingestion(db: AsyncSession, paper_id: uuid.UUID) -> None:
    paper = await get_paper(db, paper_id)
    if paper is None:
        return

    key = str(paper_id)
    try:
        await update_paper_status(db, paper_id, PaperStatus.PROCESSING)
        await publish(key, {"event": "parsing_started", "paper_id": key})

        pdf_result = extract_with_pymupdf(paper.file_path)
        await update_paper_metadata(
            db,
            paper_id,
            title=pdf_result.title or paper.original_filename,
            authors=pdf_result.authors,
            num_pages=pdf_result.num_pages,
        )

        raw_elements = extract_with_unstructured(paper.file_path)
        section_drafts = build_sections(raw_elements)

        section_id_by_index: dict[int, uuid.UUID] = {}
        for draft in section_drafts:
            section = await add_section(
                db,
                paper_id=paper_id,
                title=draft.title,
                level=0,
                order_index=draft.order_index,
                page_start=draft.page_start,
                page_end=draft.page_end,
            )
            section_id_by_index[draft.order_index] = section.id

        await publish(
            key,
            {"event": "sections_extracted", "paper_id": key, "count": len(section_drafts)},
        )

        chunk_drafts = build_chunks(section_drafts)
        total = len(chunk_drafts)

        batch_size = 32
        for start in range(0, total, batch_size):
            batch = chunk_drafts[start : start + batch_size]
            vectors = embed_texts([c.text for c in batch])

            for draft, vector in zip(batch, vectors):
                db.add(
                    Chunk(
                        paper_id=paper_id,
                        section_id=section_id_by_index.get(draft.section_order_index),
                        content_type=ContentType(draft.content_type),
                        text=draft.text,
                        page_number=draft.page_number,
                        chunk_index=draft.chunk_index,
                        token_count=draft.token_count,
                        embedding=vector,
                    )
                )
            await db.commit()

            await publish(
                key,
                {
                    "event": "embedding_progress",
                    "paper_id": key,
                    "done": min(start + batch_size, total),
                    "total": total,
                },
            )

        await update_paper_status(db, paper_id, PaperStatus.READY)
        await publish(key, {"event": "ingestion_completed", "paper_id": key})
        spawn_paper_kickoffs(paper_id)

    except Exception as exc:  # noqa: BLE001
        await update_paper_status(db, paper_id, PaperStatus.FAILED, error_message=str(exc))
        await publish(key, {"event": "ingestion_failed", "paper_id": key, "error": str(exc)})
    finally:
        await close(key)
