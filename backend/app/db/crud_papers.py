import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Paper, PaperStatus, Section


async def create_paper(
    db: AsyncSession, *, filename: str, original_filename: str, file_path: str
) -> Paper:
    paper = Paper(
        filename=filename,
        original_filename=original_filename,
        file_path=file_path,
        status=PaperStatus.UPLOADED,
    )
    db.add(paper)
    await db.commit()
    await db.refresh(paper)
    return paper


async def list_papers(db: AsyncSession) -> list[Paper]:
    result = await db.execute(select(Paper).order_by(Paper.created_at.desc()))
    return list(result.scalars().all())


async def get_paper(db: AsyncSession, paper_id: uuid.UUID) -> Paper | None:
    result = await db.execute(select(Paper).where(Paper.id == paper_id))
    return result.scalar_one_or_none()


async def get_paper_with_sections(db: AsyncSession, paper_id: uuid.UUID) -> Paper | None:
    result = await db.execute(
        select(Paper)
        .options(selectinload(Paper.sections))
        .where(Paper.id == paper_id)
    )
    return result.scalar_one_or_none()


async def update_paper_status(
    db: AsyncSession, paper_id: uuid.UUID, status: PaperStatus, error_message: str | None = None
) -> None:
    paper = await get_paper(db, paper_id)
    if paper is None:
        return
    paper.status = status
    paper.error_message = error_message
    await db.commit()


async def update_paper_metadata(
    db: AsyncSession,
    paper_id: uuid.UUID,
    *,
    title: str | None = None,
    authors: list | None = None,
    abstract: str | None = None,
    num_pages: int | None = None,
) -> None:
    paper = await get_paper(db, paper_id)
    if paper is None:
        return
    if title is not None:
        paper.title = title
    if authors is not None:
        paper.authors = authors
    if abstract is not None:
        paper.abstract = abstract
    if num_pages is not None:
        paper.num_pages = num_pages
    await db.commit()


async def delete_paper(db: AsyncSession, paper_id: uuid.UUID) -> bool:
    paper = await get_paper(db, paper_id)
    if paper is None:
        return False
    await db.delete(paper)
    await db.commit()
    return True


async def add_section(
    db: AsyncSession,
    *,
    paper_id: uuid.UUID,
    title: str,
    level: int,
    order_index: int,
    page_start: int | None,
    page_end: int | None,
) -> Section:
    section = Section(
        paper_id=paper_id,
        title=title,
        level=level,
        order_index=order_index,
        page_start=page_start,
        page_end=page_end,
    )
    db.add(section)
    await db.commit()
    await db.refresh(section)
    return section
