from dataclasses import dataclass

from unstructured.partition.pdf import partition_pdf

from app.config import get_settings


@dataclass
class RawElement:
    category: str  # "Title" | "NarrativeText" | "Table" | "FigureCaption" | "ListItem" | ...
    text: str
    page_number: int | None
    table_html: str | None = None


def extract_with_unstructured(pdf_path: str) -> list[RawElement]:
    settings = get_settings()
    elements = partition_pdf(
        filename=pdf_path,
        strategy=settings.unstructured_strategy,
        infer_table_structure=True,
    )

    result: list[RawElement] = []
    for el in elements:
        category = el.category
        text = (el.text or "").strip()
        if not text:
            continue
        page_number = getattr(el.metadata, "page_number", None)
        table_html = None
        if category == "Table":
            table_html = getattr(el.metadata, "text_as_html", None)
        result.append(
            RawElement(category=category, text=text, page_number=page_number, table_html=table_html)
        )
    return result
