import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.db.models import PaperStatus


class SectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    level: int
    order_index: int
    page_start: int | None
    page_end: int | None


class PaperOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    filename: str
    original_filename: str
    title: str | None
    authors: list | None
    abstract: str | None
    num_pages: int | None
    status: PaperStatus
    error_message: str | None
    created_at: datetime
    updated_at: datetime


class PaperDetailOut(PaperOut):
    sections: list[SectionOut] = []
