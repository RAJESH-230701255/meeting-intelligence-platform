"""Transcript routes — upload transcript files, view transcripts."""

import os
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.dependencies import get_current_user, get_db, require_role
from app.models.meeting import Meeting
from app.models.transcript import Transcript
from app.models.user import User
from app.schemas.transcript import TranscriptResponse, TranscriptUpload
from app.services.audit_service import log_action
from app.services.file_processor import (
    ALLOWED_TRANSCRIPT_EXTENSIONS,
    extract_text_from_file,
    validate_file,
)

router = APIRouter(prefix="/api/meetings", tags=["Transcripts"])
settings = get_settings()


@router.post("/{meeting_id}/transcript", response_model=TranscriptResponse)
def upload_transcript_text(
    meeting_id: int,
    req: TranscriptUpload,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN", "MANAGER")),
):
    """Upload a transcript as plain text."""
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    existing = db.query(Transcript).filter(Transcript.meeting_id == meeting_id).first()
    if existing:
        existing.content = req.content
        existing.source = req.source
        existing.language = req.language
        db.commit()
        db.refresh(existing)
        return TranscriptResponse.model_validate(existing)

    transcript = Transcript(
        meeting_id=meeting_id,
        source=req.source,
        content=req.content,
        language=req.language,
    )
    db.add(transcript)

    meeting.source_type = "UPLOADED_TRANSCRIPT"
    db.commit()
    db.refresh(transcript)

    log_action(db, current_user.id, "UPLOAD_TRANSCRIPT", "meeting", meeting_id)

    return TranscriptResponse.model_validate(transcript)


@router.post("/{meeting_id}/transcript/upload", response_model=TranscriptResponse)
async def upload_transcript_file(
    meeting_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN", "MANAGER")),
):
    """Upload a transcript file (TXT, DOCX, PDF)."""
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    content_bytes = await file.read()
    file_size = len(content_bytes)

    try:
        validate_file(file.filename, file_size, ALLOWED_TRANSCRIPT_EXTENSIONS, settings.MAX_UPLOAD_SIZE_MB)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Save temp file for text extraction
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    ext = os.path.splitext(file.filename)[1].lower()
    temp_filename = f"transcript_{meeting_id}_{uuid.uuid4().hex[:8]}{ext}"
    temp_path = os.path.join(settings.UPLOAD_DIR, temp_filename)

    with open(temp_path, "wb") as f:
        f.write(content_bytes)

    try:
        transcript_text = extract_text_from_file(temp_path)
    except ValueError as e:
        os.remove(temp_path)
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    # Save transcript
    existing = db.query(Transcript).filter(Transcript.meeting_id == meeting_id).first()
    if existing:
        existing.content = transcript_text
        existing.source = "UPLOADED_FILE"
        db.commit()
        db.refresh(existing)
        result = existing
    else:
        transcript = Transcript(
            meeting_id=meeting_id,
            source="UPLOADED_FILE",
            content=transcript_text,
            language="en",
        )
        db.add(transcript)
        meeting.source_type = "UPLOADED_TRANSCRIPT"
        db.commit()
        db.refresh(transcript)
        result = transcript

    log_action(db, current_user.id, "UPLOAD_TRANSCRIPT_FILE", "meeting", meeting_id)

    return TranscriptResponse.model_validate(result)


@router.get("/{meeting_id}/transcript", response_model=TranscriptResponse)
def get_transcript(
    meeting_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the transcript for a meeting."""
    transcript = db.query(Transcript).filter(Transcript.meeting_id == meeting_id).first()
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")
    return TranscriptResponse.model_validate(transcript)
