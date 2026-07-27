import shutil
import uuid
from pathlib import Path

from fastapi import UploadFile

from app.config import get_settings


def _storage_root() -> Path:
    root = Path(get_settings().storage_dir)
    root.mkdir(parents=True, exist_ok=True)
    return root


def papers_dir() -> Path:
    d = _storage_root() / "papers"
    d.mkdir(parents=True, exist_ok=True)
    return d


def images_dir(paper_id: uuid.UUID) -> Path:
    d = _storage_root() / "images" / str(paper_id)
    d.mkdir(parents=True, exist_ok=True)
    return d


async def save_upload(paper_id: uuid.UUID, upload: UploadFile) -> tuple[str, str]:
    """Persists the uploaded PDF to disk. Returns (filename, absolute_path)."""
    filename = f"{paper_id}.pdf"
    dest = papers_dir() / filename
    content = await upload.read()
    dest.write_bytes(content)
    return filename, str(dest)


def paper_file_path(filename: str) -> Path:
    return papers_dir() / filename


def delete_paper_files(paper_id: uuid.UUID, file_path: str) -> None:
    """Removes the stored PDF and any extracted images for a paper.
    Best-effort: a missing file is not an error (DB row may already be
    gone or ingestion may have failed before writing anything)."""
    pdf_path = Path(file_path)
    pdf_path.unlink(missing_ok=True)

    images = _storage_root() / "images" / str(paper_id)
    if images.exists():
        shutil.rmtree(images, ignore_errors=True)
