from dataclasses import dataclass

import tiktoken

from app.config import get_settings
from app.ingestion.sectionizer import SectionDraft

_ENCODING = tiktoken.get_encoding("cl100k_base")

_FIGURE_CATEGORIES = {"FigureCaption", "Image"}
_TABLE_CATEGORIES = {"Table"}
_TEXT_CATEGORIES = {"NarrativeText", "ListItem", "UncategorizedText", "Title"}


@dataclass
class ChunkDraft:
    section_order_index: int
    content_type: str  # "text" | "table" | "figure"
    text: str
    page_number: int | None
    chunk_index: int
    token_count: int


def _token_count(text: str) -> int:
    return len(_ENCODING.encode(text))


def _windowed_chunks(text_blocks: list[tuple[str, int | None]]) -> list[tuple[str, int | None]]:
    """text_blocks: list of (text, page_number). Greedily packs blocks into
    token windows of ~chunk_target_tokens with chunk_overlap_tokens overlap,
    never splitting a block itself."""
    settings = get_settings()
    target = settings.chunk_target_tokens
    overlap = settings.chunk_overlap_tokens

    chunks: list[tuple[str, int | None]] = []
    current_texts: list[str] = []
    current_pages: list[int] = []
    current_tokens = 0

    def flush() -> None:
        if not current_texts:
            return
        page = current_pages[0] if current_pages else None
        chunks.append((" ".join(current_texts), page))

    for text, page in text_blocks:
        block_tokens = _token_count(text)
        if current_tokens + block_tokens > target and current_texts:
            flush()
            # carry the tail of the previous chunk forward for overlap
            overlap_texts: list[str] = []
            overlap_tokens = 0
            for t in reversed(current_texts):
                t_tokens = _token_count(t)
                if overlap_tokens + t_tokens > overlap:
                    break
                overlap_texts.insert(0, t)
                overlap_tokens += t_tokens
            current_texts = overlap_texts
            current_pages = current_pages[-len(overlap_texts):] if overlap_texts else []
            current_tokens = overlap_tokens

        current_texts.append(text)
        if page is not None:
            current_pages.append(page)
        current_tokens += block_tokens

    flush()
    return chunks


def build_chunks(sections: list[SectionDraft]) -> list[ChunkDraft]:
    chunks: list[ChunkDraft] = []
    global_index = 0

    for section in sections:
        text_blocks: list[tuple[str, int | None]] = []

        for el in section.elements:
            if el.category in _TABLE_CATEGORIES:
                # Tables are never merged with surrounding prose; each is its own chunk.
                if text_blocks:
                    for text, page in _windowed_chunks(text_blocks):
                        chunks.append(
                            ChunkDraft(
                                section_order_index=section.order_index,
                                content_type="text",
                                text=text,
                                page_number=page,
                                chunk_index=global_index,
                                token_count=_token_count(text),
                            )
                        )
                        global_index += 1
                    text_blocks = []

                table_text = el.table_html or el.text
                chunks.append(
                    ChunkDraft(
                        section_order_index=section.order_index,
                        content_type="table",
                        text=table_text,
                        page_number=el.page_number,
                        chunk_index=global_index,
                        token_count=_token_count(table_text),
                    )
                )
                global_index += 1

            elif el.category in _FIGURE_CATEGORIES:
                chunks.append(
                    ChunkDraft(
                        section_order_index=section.order_index,
                        content_type="figure",
                        text=el.text,
                        page_number=el.page_number,
                        chunk_index=global_index,
                        token_count=_token_count(el.text),
                    )
                )
                global_index += 1

            elif el.category in _TEXT_CATEGORIES:
                text_blocks.append((el.text, el.page_number))

        if text_blocks:
            for text, page in _windowed_chunks(text_blocks):
                chunks.append(
                    ChunkDraft(
                        section_order_index=section.order_index,
                        content_type="text",
                        text=text,
                        page_number=page,
                        chunk_index=global_index,
                        token_count=_token_count(text),
                    )
                )
                global_index += 1

    return chunks
