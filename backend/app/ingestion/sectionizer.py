from dataclasses import dataclass, field

from app.ingestion.extract_unstructured import RawElement

# Titles matching these tend to be noise (running headers, not real sections) when very short.
_TITLE_MAX_WORDS = 12


@dataclass
class SectionDraft:
    title: str
    order_index: int
    page_start: int | None
    page_end: int | None
    elements: list[RawElement] = field(default_factory=list)


def _looks_like_section_title(el: RawElement) -> bool:
    if el.category != "Title":
        return False
    text = el.text.strip()
    words = text.split()
    word_count = len(words)
    if not (1 <= word_count <= _TITLE_MAX_WORDS):
        return False

    # Reject author/affiliation lines (near-universally contain an email).
    if "@" in text:
        return False

    # Reject garbled/symbol-heavy fragments (e.g. rotated arXiv sidebar text
    # like "g u A 2" or "] L C . s c [") that "fast"-strategy title detection
    # occasionally misfires on.
    alpha_chars = sum(c.isalpha() for c in text)
    if alpha_chars < max(3, len(text) * 0.5):
        return False
    short_tokens = sum(1 for w in words if len(w) <= 2)
    if word_count > 2 and short_tokens / word_count > 0.6:
        return False

    return True


def build_sections(elements: list[RawElement]) -> list[SectionDraft]:
    """Groups elements into sections using Unstructured's Title-tagged elements as
    boundaries (Unstructured preserves correct multi-column reading order, unlike
    raw PyMuPDF text extraction, so it's the primary source for section structure).
    """
    sections: list[SectionDraft] = []
    current: SectionDraft | None = None

    for el in elements:
        if _looks_like_section_title(el):
            if current is not None:
                sections.append(current)
            current = SectionDraft(
                title=el.text,
                order_index=len(sections),
                page_start=el.page_number,
                page_end=el.page_number,
            )
            continue

        if current is None:
            # Content before the first detected title (e.g. abstract) gets a
            # synthetic leading section.
            current = SectionDraft(
                title="Front Matter",
                order_index=0,
                page_start=el.page_number,
                page_end=el.page_number,
            )

        current.elements.append(el)
        if el.page_number is not None:
            if current.page_start is None:
                current.page_start = el.page_number
            current.page_end = el.page_number

    if current is not None:
        sections.append(current)

    for i, s in enumerate(sections):
        s.order_index = i

    return sections
