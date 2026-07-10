from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.file import File
from app.models.file_version import FileVersion
from app.models.user import User
from app.storage.local import save_file_locally
from app.storage.validation import validate_upload_file


# Core orchestration service to validate, persist physically, and register a user asset with version control
def upload_file(
    db: Session,
    upload_file: UploadFile,
    current_user: User,
) -> File:
    # Execute interceptor guards to validate mimetype depth and multi-part volumetric limits
    validate_upload_file(upload_file)

    # Persist the file stream to the local isolated storage disk using tenant scoping
    stored_filename, stored_path, size = save_file_locally(
        upload_file=upload_file,
        user_id=current_user.id
    )

    # Initialize the core database file record holding structural tracking metadata
    file_record = File(
        original_filename=upload_file.filename,
        stored_filename=stored_filename,
        stored_path=stored_path,
        content_type=upload_file.content_type,
        size=size,
        owner_id=current_user.id
    )

    # Enclose stateful write operations within a transaction block to preserve data integrity
    try:
        # Stage the file record instantiation to populate and generate the primary identity key
        db.add(file_record)
        db.flush()

        # Initialize the baseline historical version tracker linked to the newly generated file index
        initial_version = FileVersion(
            file_id=file_record.id,
            version_number=1,
            original_filename=file_record.original_filename,
            stored_filename=file_record.stored_filename,
            stored_path=file_record.stored_path,
            content_type=file_record.content_type,
            size=file_record.size
        )

        # Stage the history entry and atomitically commit both record states to the database
        db.add(initial_version)
        db.commit()
        db.refresh(file_record)

        # Return the synchronized core file record model object
        return file_record

    except Exception:
        # Roll back the active unit of work transaction to prevent orphaned or partial entity records
        db.rollback()

        # Instantiate a Path object pointing to the orphaned disk binary asset
        saved_path = Path(stored_path)

        # Unlink and purge the dangling binary from disk storage if it was partially written
        if saved_path.exists():
            saved_path.unlink()
        
        # Rethrow the original exception to upstream interceptors
        raise