from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.lead import Lead
from app.schemas.lead import LeadCreate, LeadRead
from app.services.email import get_email_service
from app.services.resume_storage import ResumeStorageError, save_resume_upload

router = APIRouter(prefix="/api", tags=["leads"])


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
