from types import SimpleNamespace

from app.ingestion.chunker import build_chunks
from app.ingestion.extract_unstructured import RawElement
from app.ingestion.sectionizer import build_sections


def test_build_sections_uses_titles_as_boundaries():
    elements = [
        RawElement(category="Title", text="Attention Is All You Need", page_number=1),
        RawElement(
            category="Title",
            text="Ashish Vaswani∗ Google Brain avaswani@google.com",
            page_number=1,
        ),
        RawElement(category="Title", text="Abstract", page_number=1),
        RawElement(category="NarrativeText", text="We propose a new architecture.", page_number=1),
        RawElement(category="Title", text="1 Introduction", page_number=2),
        RawElement(category="NarrativeText", text="Recurrent models are slow.", page_number=2),
    ]

    sections = build_sections(elements)
    titles = [s.title for s in sections]

    # Real section headers are kept as boundaries...
    assert "Attention Is All You Need" in titles
    assert "Abstract" in titles
    assert "1 Introduction" in titles
    # ...but the author/email line is not treated as a new section.
    assert not any("@" in t for t in titles)

    intro = next(s for s in sections if s.title == "1 Introduction")
    assert intro.page_start == 2
    assert len(intro.elements) == 1
    assert intro.elements[0].text == "Recurrent models are slow."


def test_build_sections_filters_garbled_title_fragments():
    elements = [
        RawElement(category="Title", text="g u A 2", page_number=1),
        RawElement(category="Title", text="] L C . s c [", page_number=1),
        RawElement(category="Title", text="Related Work", page_number=1),
        RawElement(category="NarrativeText", text="Prior work explored RNNs.", page_number=1),
    ]

    sections = build_sections(elements)
    titles = [s.title for s in sections]

    assert "g u A 2" not in titles
    assert "] L C . s c [" not in titles
    assert "Related Work" in titles


def test_build_sections_leading_content_goes_to_front_matter():
    elements = [
        RawElement(category="NarrativeText", text="Some abstract text before any heading.", page_number=1),
        RawElement(category="Title", text="Introduction", page_number=2),
    ]

    sections = build_sections(elements)

    assert sections[0].title == "Front Matter"
    assert sections[0].elements[0].text == "Some abstract text before any heading."


def test_build_chunks_gives_tables_their_own_chunk():
    elements = [
        RawElement(category="NarrativeText", text="Results are shown below.", page_number=5),
        RawElement(
            category="Table",
            text="Model BLEU\nTransformer 28.4",
            page_number=5,
            table_html="<table><tr><td>Model</td><td>BLEU</td></tr></table>",
        ),
        RawElement(category="NarrativeText", text="The table shows our results.", page_number=5),
    ]
    sections = build_sections(elements)
    # First element isn't a Title, so it lands in a synthetic "Front Matter" section.
    chunks = build_chunks(sections)

    table_chunks = [c for c in chunks if c.content_type == "table"]
    assert len(table_chunks) == 1
    assert "<table>" in table_chunks[0].text

    text_chunks = [c for c in chunks if c.content_type == "text"]
    assert all("<table>" not in c.text for c in text_chunks)


def test_build_chunks_figures_are_metadata_only():
    elements = [
        RawElement(
            category="FigureCaption",
            text="Figure 1: The Transformer architecture.",
            page_number=3,
        ),
    ]
    sections = build_sections(elements)
    chunks = build_chunks(sections)

    assert len(chunks) == 1
    assert chunks[0].content_type == "figure"
    assert chunks[0].text == "Figure 1: The Transformer architecture."


def test_build_chunks_windows_long_text_with_overlap(monkeypatch):
    # Force a small window so a handful of short sentences span multiple chunks.
    monkeypatch.setattr(
        "app.ingestion.chunker.get_settings",
        lambda: SimpleNamespace(chunk_target_tokens=15, chunk_overlap_tokens=5),
    )

    elements = [
        RawElement(category="Title", text="Method", page_number=1),
        RawElement(category="NarrativeText", text="Sentence one is here now.", page_number=1),
        RawElement(category="NarrativeText", text="Sentence two follows right after.", page_number=1),
        RawElement(category="NarrativeText", text="Sentence three keeps going further.", page_number=1),
        RawElement(category="NarrativeText", text="Sentence four wraps things up nicely.", page_number=1),
    ]
    sections = build_sections(elements)
    chunks = build_chunks(sections)

    text_chunks = [c for c in chunks if c.content_type == "text"]
    assert len(text_chunks) > 1
    # Chunk indices stay contiguous and ordered.
    assert [c.chunk_index for c in chunks] == sorted(c.chunk_index for c in chunks)
