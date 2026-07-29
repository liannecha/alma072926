from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from fastapi import UploadFile

from app.core.config import settings

MAX_UPLOAD_SIZE_BYTES: Final[int] = 5 * 1024 * 1024
ALLOWED_CONTENT_TYPES: Final[set[str]] = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


class ResumeStorageError(Exception):
    """Raised when a resume upload cannot be processed."""


@dataclass(frozen=True)
class ResumeStorageResult:
    original_filename: str
    content_type: str
    storage_path: str


class ResumeStorageService:
    def __init__(self, storage_dir: str | None = None) -> None:
        self.storage_dir = Path(storage_dir or settings.resume_storage_dir)

    def ensure_storage_dir(self) -> None:
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def _sanitize_filename(self, filename: str) -> str:
        sanitized = re.sub(r"[^A-Za-z0-9._-]+", "_", filename).strip("._")
        if not sanitized:
            sanitized = "resume"
        return f"{uuid.uuid4()}_{sanitized}"

    def save_upload(self, upload_file: UploadFile) -> ResumeStorageResult:
        if upload_file is None:
            raise ResumeStorageError("No file provided")

        if upload_file.filename is None or not upload_file.filename.strip():
            raise ResumeStorageError("Uploaded file is missing a filename")

        content_type = upload_file.content_type or ""
        if content_type not in ALLOWED_CONTENT_TYPES:
            raise ResumeStorageError("Unsupported file type")

        self.ensure_storage_dir()

        file_bytes = upload_file.file.read()
        if len(file_bytes) > MAX_UPLOAD_SIZE_BYTES:
            raise ResumeStorageError("File exceeds the 5 MB limit")

        safe_filename = self._sanitize_filename(upload_file.filename)
        destination_path = self.storage_dir / safe_filename
        with destination_path.open("wb") as destination:
            destination.write(file_bytes)

        return ResumeStorageResult(
            original_filename=upload_file.filename,
            content_type=content_type,
            storage_path=str(destination_path),
        )


def save_resume_upload(upload_file: UploadFile) -> ResumeStorageResult:
    return ResumeStorageService().save_upload(upload_file)
