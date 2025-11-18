"""
Leads API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from database.db import get_db
from services.lead_service import LeadService
from schemas.schemas import LeadCreate, LeadUpdate, LeadResponse

router = APIRouter(prefix="/api/leads", tags=["leads"])
lead_service = LeadService()


@router.get("/", response_model=List[LeadResponse])
def get_leads(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    lead_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get all leads with optional filtering

    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    - **status**: Filter by status (optional)
    - **lead_type**: Filter by type: 'drop-off' or 'dormant' (optional)
    """
    leads = lead_service.get_all_leads(
        db,
        skip=skip,
        limit=limit,
        status=status,
        lead_type=lead_type
    )
    return leads


@router.get("/{lead_id}", response_model=LeadResponse)
def get_lead(lead_id: int, db: Session = Depends(get_db)):
    """
    Get a single lead by ID
    """
    lead = lead_service.get_lead_by_id(db, lead_id)
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lead with ID {lead_id} not found"
        )
    return lead


@router.post("/", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
def create_lead(lead: LeadCreate, db: Session = Depends(get_db)):
    """
    Create a new lead

    - **name**: Lead's full name
    - **phone**: Phone number in E.164 format (e.g., +972501234567)
    - **type**: Either 'drop-off' or 'dormant'
    - **drop_stage**: Required for drop-off leads (e.g., 'identity_verify', 'funding')
    - **last_active**: Required for dormant leads (ISO datetime)
    - **notes**: Optional notes
    """
    try:
        print(f"📥 Received lead data: {lead.model_dump()}")
        created_lead = lead_service.create_lead(db, lead)
        print(f"✅ Lead created successfully with ID: {created_lead.id}")
        return created_lead
    except Exception as e:
        print(f"❌ Error creating lead: {type(e).__name__}: {str(e)}")
        raise


@router.put("/{lead_id}", response_model=LeadResponse)
def update_lead(lead_id: int, lead: LeadUpdate, db: Session = Depends(get_db)):
    """
    Update an existing lead

    Only provided fields will be updated. All fields are optional.
    """
    updated_lead = lead_service.update_lead(db, lead_id, lead)
    if not updated_lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lead with ID {lead_id} not found"
        )
    return updated_lead


@router.delete("/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lead(lead_id: int, db: Session = Depends(get_db)):
    """
    Delete a lead

    This will also delete all associated calls and results (cascade delete).
    """
    success = lead_service.delete_lead(db, lead_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lead with ID {lead_id} not found"
        )
    return None


@router.patch("/{lead_id}/status", response_model=LeadResponse)
def update_lead_status(lead_id: int, new_status: str, db: Session = Depends(get_db)):
    """
    Update only the status of a lead

    - **new_status**: One of: 'pending', 'calling', 'called', 'completed'
    """
    updated_lead = lead_service.update_lead_status(db, lead_id, new_status)
    if not updated_lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lead with ID {lead_id} not found"
        )
    return updated_lead


@router.get("/stats/count")
def get_leads_count(
    status: Optional[str] = None,
    lead_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get count of leads with optional filtering
    """
    count = lead_service.count_leads(db, status=status, lead_type=lead_type)
    return {"count": count}
