from app.db.models import ContentType
from app.embeddings.client import embed_texts
from app.retrieval.search import similarity_search
from tests.conftest import make_chunk


async def test_similarity_search_ranks_relevant_chunk_first(db_session, sample_paper, sample_section):
    texts = [
        "The attention mechanism computes a weighted sum over value vectors.",
        "Our favorite pasta recipe starts with fresh tomatoes and basil.",
    ]
    vectors = embed_texts(texts)

    await make_chunk(
        db_session, sample_paper, sample_section,
        text=texts[0], content_type=ContentType.TEXT, embedding=vectors[0],
    )
    await make_chunk(
        db_session, sample_paper, sample_section,
        text=texts[1], content_type=ContentType.TEXT, embedding=vectors[1],
    )
    await db_session.flush()

    results = await similarity_search(
        db_session, paper_id=sample_paper.id, query="how does the attention mechanism work?"
    )

    assert len(results) == 2
    assert "attention mechanism" in results[0]["text"]
    assert results[0]["page_number"] == sample_section.page_start
    assert results[0]["section_title"] == sample_section.title


async def test_similarity_search_boosts_content_type_for_agent(db_session, sample_paper, sample_section):
    # Identical text/embedding, different content_type — without the boost
    # these would tie; the results_critique agent should still prefer the
    # table chunk.
    text = "Model BLEU: Transformer 28.4, previous best 25.1"
    vector = embed_texts([text])[0]

    await make_chunk(
        db_session, sample_paper, sample_section,
        text=text, content_type=ContentType.TEXT, embedding=vector, chunk_index=0,
    )
    table_chunk = await make_chunk(
        db_session, sample_paper, sample_section,
        text=text, content_type=ContentType.TABLE, embedding=vector, chunk_index=1,
    )
    await db_session.flush()

    results = await similarity_search(
        db_session,
        paper_id=sample_paper.id,
        query="What BLEU score did the model achieve?",
        agent_key="results_critique",
    )

    assert results[0]["chunk_id"] == table_chunk.id
    assert results[0]["content_type"] == "table"


async def test_similarity_search_scoped_to_paper(db_session, sample_paper):
    from app.db.models import Paper, PaperStatus

    other_paper = Paper(
        filename="other.pdf",
        original_filename="other.pdf",
        file_path="/tmp/other.pdf",
        status=PaperStatus.READY,
    )
    db_session.add(other_paper)
    await db_session.flush()

    vector = embed_texts(["shared phrasing about transformers"])[0]
    await make_chunk(
        db_session, other_paper, None,
        text="This chunk belongs to a different paper.", content_type=ContentType.TEXT, embedding=vector,
    )
    await db_session.flush()

    results = await similarity_search(
        db_session, paper_id=sample_paper.id, query="transformers"
    )

    assert results == []
