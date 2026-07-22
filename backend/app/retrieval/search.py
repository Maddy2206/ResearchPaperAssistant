import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models import Chunk, ContentType, Section
from app.embeddings.client import embed_query

# Per-agent content-type boost: subtracted from cosine distance (lower distance = more relevant)
# for chunks whose content_type is in the boosted set, nudging them up the ranking
# without excluding other content types entirely.
_BOOST_AMOUNT = 0.08

_AGENT_BOOSTS: dict[str, set[ContentType]] = {
    "results_critique": {ContentType.TABLE},
    "math_algorithm": {ContentType.EQUATION},
    "architecture_flowchart": {ContentType.FIGURE},
}


async def similarity_search(
    db: AsyncSession,
    *,
    paper_id: uuid.UUID,
    query: str,
    agent_key: str | None = None,
    top_k: int | None = None,
) -> list[dict]:
    settings = get_settings()
    k = top_k or settings.retrieval_top_k
    query_vector = embed_query(query)

    distance = Chunk.embedding.cosine_distance(query_vector)
    stmt = (
        select(Chunk, Section, distance.label("distance"))
        .outerjoin(Section, Chunk.section_id == Section.id)
        .where(Chunk.paper_id == paper_id, Chunk.embedding.is_not(None))
        .order_by(distance)
        .limit(k * 3 if agent_key in _AGENT_BOOSTS else k)
    )
    result = await db.execute(stmt)
    rows = result.all()

    boosted_types = _AGENT_BOOSTS.get(agent_key or "", set())

    def effective_distance(row) -> float:
        chunk: Chunk = row[0]
        base = row[2]
        if chunk.content_type in boosted_types:
            return base - _BOOST_AMOUNT
        return base

    rows = sorted(rows, key=effective_distance)[:k]

    results: list[dict] = []
    for chunk, section, dist in rows:
        results.append(
            {
                "chunk_id": chunk.id,
                "text": chunk.text,
                "page_number": chunk.page_number,
                "section_title": section.title if section else None,
                "content_type": chunk.content_type.value,
                "score": float(1 - dist) if dist is not None else None,
            }
        )
    return results
