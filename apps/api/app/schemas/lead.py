from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.lead import LeadStatus


class LeadBase(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr


class LeadCreate(LeadBase):
    pass


class LeadRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: str
    last_name: str
    email: EmailStr
    resume_original_filename: str
    resume_content_type: str
    status: LeadStatus
    created_at: datetime
    updated_at: datetime
    reached_out_at: datetime | None = None


class LeadStatusUpdate(BaseModel):
    status: LeadStatus = Field(...)

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: LeadStatus) -> LeadStatus:
        if value != LeadStatus.REACHED_OUT:
            raise ValueError("Only REACHED_OUT is supported for now")
        return value
