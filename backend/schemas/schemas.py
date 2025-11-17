"""
Pydantic schemas for request/response validation
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# Lead Schemas
class LeadBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    phone: str = Field(..., pattern=r"^\+?[1-9]\d{1,14}$")  # E.164 format
    type: str = Field(..., pattern="^(drop-off|dormant)$")
    drop_stage: Optional[str] = None
    last_active: Optional[datetime] = None
    notes: Optional[str] = None


class LeadCreate(LeadBase):
    pass


class LeadUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, pattern=r"^\+?[1-9]\d{1,14}$")
    type: Optional[str] = Field(None, pattern="^(drop-off|dormant)$")
    drop_stage: Optional[str] = None
    last_active: Optional[datetime] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class LeadResponse(LeadBase):
    id: int
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Call Schemas
class CallBase(BaseModel):
    lead_id: int


class CallCreate(CallBase):
    pass


class CallResponse(BaseModel):
    id: int
    call_id: str
    lead_id: int
    voximplant_call_id: Optional[str]
    status: str
    started_at: Optional[datetime]
    ended_at: Optional[datetime]
    duration_seconds: Optional[int]

    class Config:
        from_attributes = True


# Call Result Schemas
class CallResultBase(BaseModel):
    disposition: str
    cx_score: int = Field(..., ge=1, le=10)
    summary: str
    full_transcript: Optional[str] = None
    key_objections: Optional[str] = None
    next_actions: Optional[str] = None
    recording_url: Optional[str] = None


class CallResultCreate(CallResultBase):
    call_id: str


class CallResultResponse(CallResultBase):
    id: int
    call_id: str
    created_at: datetime

    class Config:
        from_attributes = True


# Webhook Schemas
class WebhookCallStarted(BaseModel):
    type: str = "call_started"
    call_id: str
    lead_id: int
    lead_name: str
    lead_type: str


class WebhookCallResult(BaseModel):
    type: str = "call_result"
    call_id: str
    lead_id: int
    disposition: str
    cx_score: int = Field(..., ge=1, le=10)
    summary: str


class WebhookCallEnded(BaseModel):
    type: str = "call_ended"
    call_id: str


# Analytics Schemas
class AnalyticsSummary(BaseModel):
    total_calls: int
    completed_calls: int
    avg_duration_seconds: float
    avg_cx_score: float
    dispositions: dict
    calls_by_type: dict


# Trigger Call Request
class TriggerCallRequest(BaseModel):
    lead_id: int
