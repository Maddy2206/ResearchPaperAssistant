from collections.abc import AsyncIterator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.config import get_settings
from app.db.models import Chunk, ContentType, Paper, PaperStatus, Section


@pytest.fixture
async def test_engine():
    # A dedicated per-test NullPool engine (rather than the app's shared
    # pooled `engine`, or a session-scoped one) avoids asyncpg "another
    # operation is in progress" errors: pytest-asyncio's `auto` mode runs
    # each test in its own function-scoped event loop, so the engine/
    # connection must be created fresh within that same loop rather than
    # shared across tests.
    engine = create_async_engine(get_settings().database_url, poolclass=NullPool)
    yield engine
    await engine.dispose()


@pytest.fixture
async def db_session(test_engine) -> AsyncIterator[AsyncSession]:
    """Each test runs inside its own transaction, rolled back on teardown —
    tests can freely write to the real dev DB without leaving data behind
    or needing a separate test database."""
    connection = await test_engine.connect()
    transaction = await connection.begin()
    session_factory = async_sessionmaker(bind=connection, expire_on_commit=False)
    session = session_factory()

    try:
        yield session
    finally:
        await session.close()
        await transaction.rollback()
        await connection.close()


@pytest.fixture
async def sample_paper(db_session: AsyncSession) -> Paper:
    paper = Paper(
        filename="test.pdf",
        original_filename="test.pdf",
        file_path="/tmp/test.pdf",
        title="Test Paper",
        status=PaperStatus.READY,
        num_pages=10,
    )
    db_session.add(paper)
    await db_session.flush()
    return paper


@pytest.fixture
async def sample_section(db_session: AsyncSession, sample_paper: Paper) -> Section:
    section = Section(
        paper_id=sample_paper.id,
        title="Results",
        level=0,
        order_index=0,
        page_start=5,
        page_end=6,
    )
    db_session.add(section)
    await db_session.flush()
    return section


async def make_chunk(
    db_session: AsyncSession,
    paper: Paper,
    section: Section | None,
    *,
    text: str,
    content_type: ContentType,
    embedding: list[float],
    page_number: int = 5,
    chunk_index: int = 0,
) -> Chunk:
    chunk = Chunk(
        paper_id=paper.id,
        section_id=section.id if section else None,
        content_type=content_type,
        text=text,
        page_number=page_number,
        chunk_index=chunk_index,
        embedding=embedding,
    )
    db_session.add(chunk)
    await db_session.flush()
    return chunk


