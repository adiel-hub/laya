"""
Calls API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional

from database.db import get_db
from services.call_service import CallService
from services.lead_service import LeadService
from services.voximplant_service import VoximplantService
from schemas.schemas import CallResponse, CallResultResponse, TriggerCallRequest

router = APIRouter(prefix="/api/calls", tags=["calls"])
call_service = CallService()
lead_service = LeadService()


@router.get("/", response_model=List[CallResponse])
def get_calls(
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
    lead_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Get all calls with optional filtering

    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    - **status**: Filter by status (optional)
    - **lead_id**: Filter by lead ID (optional)
    """
    calls = call_service.get_all_calls(
        db,
        skip=skip,
        limit=limit,
        status=status,
        lead_id=lead_id
    )
    return calls


@router.get("/{call_id}", response_model=CallResponse)
def get_call(call_id: str, db: Session = Depends(get_db)):
    """
    Get a single call by ID
    """
    call = call_service.get_call_by_id(db, call_id)
    if not call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Call with ID {call_id} not found"
        )
    return call


@router.get("/{call_id}/result", response_model=CallResultResponse)
def get_call_result(call_id: str, db: Session = Depends(get_db)):
    """
    Get call result (disposition, CX score, etc.)
    """
    result = call_service.get_call_result(db, call_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Call result for call ID {call_id} not found"
        )
    return result


@router.get("/{call_id}/details")
def get_call_details(call_id: str, db: Session = Depends(get_db)):
    """
    Get complete call information including lead and result
    """
    details = call_service.get_call_with_details(db, call_id)
    if not details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Call with ID {call_id} not found"
        )
    return {
        "call": details["call"],
        "lead": details["lead"],
        "result": details["result"]
    }


@router.post("/trigger", status_code=status.HTTP_202_ACCEPTED)
async def trigger_call(
    request: TriggerCallRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Trigger an outbound call to a lead

    This endpoint:
    1. Creates a call record in the database
    2. Updates lead status to 'calling'
    3. Triggers the call via Voximplant API
    4. Returns immediately (call happens in background)

    - **lead_id**: ID of the lead to call
    """
    # Get lead
    lead = lead_service.get_lead_by_id(db, request.lead_id)
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lead with ID {request.lead_id} not found"
        )

    # Check if lead is already being called
    if lead.status == "calling":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Lead is already being called"
        )

    # Create call record
    call = call_service.create_call(db, lead.id)

    # Update lead status
    lead_service.update_lead_status(db, lead.id, "calling")

    # Trigger Voximplant call
    try:
        voximplant_service = VoximplantService()
        result = voximplant_service.trigger_call(lead, call.call_id)

        if not result["success"]:
            # Update call status to failed
            call_service.update_call_status(db, call.call_id, "failed")
            lead_service.update_lead_status(db, lead.id, "pending")

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to trigger call: {result.get('error', 'Unknown error')}"
            )

        return {
            "message": "Call triggered successfully",
            "call_id": call.call_id,
            "lead": {
                "id": lead.id,
                "name": lead.name,
                "phone": lead.phone,
                "type": lead.type
            }
        }

    except Exception as e:
        # Update status on error
        call_service.update_call_status(db, call.call_id, "failed")
        lead_service.update_lead_status(db, lead.id, "pending")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error triggering call: {str(e)}"
        )


@router.get("/stats/count")
def get_calls_count(
    status: Optional[str] = None,
    lead_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get count of calls with optional filtering
    """
    count = call_service.count_calls(db, status=status, lead_type=lead_type)
    return {"count": count}
