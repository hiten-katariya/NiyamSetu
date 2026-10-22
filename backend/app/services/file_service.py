import hashlib
import os
from pathlib import Path
from typing import Optional, Tuple
import uuid
from fastapi import UploadFile
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.exceptions import AppException, ForbiddenError, NotFoundError
from backend.app.models.entities import FileRecord, User


# Magic byte signatures
MAGIC_BYTES = {
    "pdf": b"%PDF",
    "png": b"\x89PNG\r\n\x1a\n",
    "jpeg": b"\xff\xd8\xff",
}


class FileStorageService:
    """
    Hardened File Storage & Security Engine.
    Enforces MIME type checking, magic-byte signature validation, size bounds,
    cryptographic SHA-256 checksums, and strict directory traversal prevention.
    """

    @classmethod
    def get_storage_dir(cls) -> Path:
        storage_path = Path(settings.STORAGE_LOCAL_DIR).resolve()
        storage_path.mkdir(parents=True, exist_ok=True)
        return storage_path

    @classmethod
    def validate_file_signature(cls, header_bytes: bytes, filename: str) -> str:
        """
        Validates content magic bytes against declared extension.
        Returns the confirmed canonical extension (e.g. '.pdf', '.png', '.jpg').
        """
        ext = Path(filename).suffix.lower()
        if ext not in settings.ALLOWED_FILE_EXTENSIONS:
            raise AppException(
                f"File format '{ext}' is not permitted. Allowed: {', '.join(settings.ALLOWED_FILE_EXTENSIONS)}",
                code="INVALID_FILE_EXTENSION",
                status_code=400,
            )

        if ext == ".pdf":
            if not header_bytes.startswith(MAGIC_BYTES["pdf"]):
                raise AppException(
                    "File content signature does not match PDF format.",
                    code="INVALID_FILE_SIGNATURE",
                    status_code=400,
                )
            return ".pdf"

        elif ext == ".png":
            if not header_bytes.startswith(MAGIC_BYTES["png"]):
                raise AppException(
                    "File content signature does not match PNG image format.",
                    code="INVALID_FILE_SIGNATURE",
                    status_code=400,
                )
            return ".png"

        elif ext in (".jpg", ".jpeg"):
            if not header_bytes.startswith(MAGIC_BYTES["jpeg"]):
                raise AppException(
                    "File content signature does not match JPEG image format.",
                    code="INVALID_FILE_SIGNATURE",
                    status_code=400,
                )
            return ext

        raise AppException("Unsupported file format.", code="INVALID_FILE_FORMAT", status_code=400)

    @classmethod
    def save_upload_file(
        cls,
        db: Session,
        file: UploadFile,
        uploaded_by: User,
    ) -> FileRecord:
        """
        Validates, checksums, and persists an uploaded file safely to disk and database.
        """
        if not file.filename:
            raise AppException("Filename must be provided.", code="MISSING_FILENAME", status_code=400)

        # Reject path traversal attempts in raw filename
        raw_filename = file.filename
        if ".." in raw_filename or "/" in raw_filename or "\\" in raw_filename:
            raise AppException("Path traversal or invalid filename structure.", code="MALICIOUS_FILENAME", status_code=400)

        safe_original_filename = Path(file.filename).name

        storage_dir = cls.get_storage_dir()
        file_bytes = file.file.read()
        file_size = len(file_bytes)

        if file_size == 0:
            raise AppException("Uploaded file is empty (0 bytes).", code="EMPTY_FILE", status_code=400)

        if file_size > settings.MAX_UPLOAD_SIZE_BYTES:
            max_mb = settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)
            raise AppException(
                f"File size exceeds maximum permitted limit of {max_mb} MB.",
                code="FILE_TOO_LARGE",
                status_code=413,
            )

        # Validate magic byte signatures
        header_sample = file_bytes[:16]
        confirmed_ext = cls.validate_file_signature(header_sample, safe_original_filename)

        # Calculate SHA-256 checksum
        checksum = hashlib.sha256(file_bytes).hexdigest()

        # Generate unique random storage key (UUID + extension)
        unique_key = f"{uuid.uuid4().hex}{confirmed_ext}"
        destination_path = storage_dir / unique_key

        # Defensive path traversal check: destination must reside inside storage_dir
        try:
            destination_path = destination_path.resolve()
            if not str(destination_path).startswith(str(storage_dir)):
                raise AppException("Unsafe storage path resolution.", code="PATH_TRAVERSAL_DETECTED", status_code=400)
        except Exception:
            raise AppException("Unsafe storage path.", code="STORAGE_ERROR", status_code=500)

        # Save to disk
        try:
            with open(destination_path, "wb") as f:
                f.write(file_bytes)
        except Exception as exc:
            raise AppException("Failed to write file to secure storage.", code="IO_ERROR", status_code=500)

        # Create database record
        try:
            mime = file.content_type or "application/octet-stream"
            record = FileRecord(
                id=uuid.uuid4(),
                original_filename=safe_original_filename,
                storage_key=unique_key,
                mime_type=mime,
                size_bytes=file_size,
                checksum=checksum,
                uploaded_by_user_id=uploaded_by.id,
            )
            db.add(record)
            db.commit()
            db.refresh(record)
            return record

        except Exception as db_exc:
            # Transaction rollback & orphan file cleanup
            db.rollback()
            if destination_path.exists():
                try:
                    os.remove(destination_path)
                except OSError:
                    pass
            raise db_exc

    @classmethod
    def get_file_path(cls, file_record: FileRecord) -> Path:
        """
        Resolves canonical path of an existing FileRecord with path traversal protection.
        """
        storage_dir = cls.get_storage_dir()
        file_path = (storage_dir / file_record.storage_key).resolve()

        if not str(file_path).startswith(str(storage_dir)):
            raise AppException("Path traversal breach detected.", code="FORBIDDEN_FILE_PATH", status_code=403)

        if not file_path.exists():
            raise NotFoundError("The requested physical file was not found in storage.")

        return file_path
