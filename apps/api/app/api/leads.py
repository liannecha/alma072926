from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_internal_auth
from app.models.lead import Lead, LeadStatus
from app.schemas.lead import LeadCreate, LeadRead, LeadStatusUpdate
from app.services.email import get_email_service
from app.services.resume_storage import ResumeStorageError, save_resume_upload

router = APIRouter(prefix="/api", tags=["leads"])


@router.get("/leads", response_model=list[LeadRead])
def list_leads(
    db: Session = Depends(get_db),
    _auth: None = Depends(require_internal_auth),
) -> list[Lead]:
    leads = db.query(Lead).order_by(Lead.created_at.desc()).all()
    return leads


@router.get("/leads/{lead_id}/resume")
def download_lead_resume(
    lead_id: int,
    db: Session = Depends(get_db),
    _auth: None = Depends(require_internal_auth),
) -> FileResponse:
    lead = db.get(Lead, lead_id)
    if lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")

    if not lead.resume_storage_path:
        raise HTTPException(status_code=404, detail="Resume not found")

    stored_path = Path(lead.resume_storage_path)
    file_path = stored_path if stored_path.is_absolute() else (Path.cwd() / stored_path).resolve()
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Resume not found")

    return FileResponse(
        path=file_path,
        media_type=lead.resume_content_type,
        filename=lead.resume_original_filename,
    )


@router.patch("/leads/{lead_id}/status", response_model=LeadRead)
def update_lead_status(
    lead_id: int,
    payload: LeadStatusUpdate,
    db: Session = Depends(get_db),
    _auth: None = Depends(require_internal_auth),
) -> Lead:
    lead = db.get(Lead, lead_id)
    if lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")

    if payload.status == LeadStatus.REACHED_OUT and lead.status == LeadStatus.PENDING:
        lead.status = LeadStatus.REACHED_OUT
        lead.reached_out_at = datetime.now(timezone.utc)
    elif payload.status == LeadStatus.REACHED_OUT and lead.status == LeadStatus.REACHED_OUT:
        # Idempotent success for already-reached-out leads.
        pass

    db.commit()
    db.refresh(lead)
    return lead


@router.post("/leads", response_model=LeadRead)
def create_lead(
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    resume: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> Lead:
    try:
        payload = LeadCreate(first_name=first_name, last_name=last_name, email=email)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc

    try:
        resume_result = save_resume_upload(resume)
    except ResumeStorageError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    lead = Lead(
        first_name=payload.first_name,
        last_name=payload.last_name,
        email=str(payload.email),
        resume_original_filename=resume_result.original_filename,
        resume_content_type=resume_result.content_type,
        resume_storage_path=resume_result.storage_path,
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)

    email_service = get_email_service()
    try:
        email_service.send_prospect_confirmation(
            first_name=lead.first_name,
            last_name=lead.last_name,
            email=lead.email,
            resume_original_filename=lead.resume_original_filename,
        )
        email_service.send_internal_notification(
            first_name=lead.first_name,
            last_name=lead.last_name,
            email=lead.email,
            resume_original_filename=lead.resume_original_filename,
        )
    except Exception as exc:  # pragma: no cover - local logging path
        print(f"Email sending failed: {exc}")

    return lead
