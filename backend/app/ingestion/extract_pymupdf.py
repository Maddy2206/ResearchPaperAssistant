from dataclasses import dataclass, field
from pathlib import Path

import fitz  # PyMuPDF


@dataclass
class PageInfo:
    page_number: int  # 1-indexed
    text: str


@dataclass
class TocEntry:
    level: int
    title: str
    page: int  # 1-indexed


@dataclass
class PyMuPdfResult:
    title: str | None
    authors: list[str]
    num_pages: int
    toc: list[TocEntry] = field(default_factory=list)
    pages: list[PageInfo] = field(default_factory=list)


def extract_with_pymupdf(pdf_path: str) -> PyMuPdfResult:
    doc = fitz.open(pdf_path)
    try:
        meta = doc.metadata or {}
        title = (meta.get("title") or "").strip() or None
        author_raw = (meta.get("author") or "").strip()
        authors = [a.strip() for a in author_raw.split(",") if a.strip()] if author_raw else []

        toc_raw = doc.get_toc(simple=True) or []
        toc = [TocEntry(level=lvl, title=t.strip(), page=page) for lvl, t, page in toc_raw]

        pages = [
            PageInfo(page_number=i + 1, text=doc[i].get_text("text"))
            for i in range(doc.page_count)
        ]

        return PyMuPdfResult(
            title=title,
            authors=authors,
            num_pages=doc.page_count,
            toc=toc,
            pages=pages,
        )
    finally:
        doc.close()


def render_page_thumbnails(pdf_path: str, out_dir: Path, dpi: int = 150, max_pages: int | None = None) -> list[str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf_path)
    paths: list[str] = []
    try:
        count = doc.page_count if max_pages is None else min(max_pages, doc.page_count)
        for i in range(count):
            pix = doc[i].get_pixmap(dpi=dpi)
            out_path = out_dir / f"page-{i + 1}.png"
            pix.save(str(out_path))
            paths.append(str(out_path))
        return paths
    finally:
        doc.close()
