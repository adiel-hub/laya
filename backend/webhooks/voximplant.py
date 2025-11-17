"""
Voximplant Webhook Handler
Receives events from VoxEngine scenarios
"""

from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any
import json

from database.db import get_db
from services.call_service import CallService
from services.lead_service import LeadService

router = APIRouter(prefix="/webhook", tags=["webhooks"])
call_service = CallService()
lead_service = LeadService()

# WebSocket manager will be injected from main.py
websocket_manager = None


def set_websocket_manager(manager):
    """Set the WebSocket manager instance"""
    global websocket_manager
    websocket_manager = manager


@router.post("/voximplant")
async def voximplant_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Handle webhooks from Voximplant VoxEngine scenarios

    Event types:
    - call_started: Call has been initiated and connected
    - call_result: Gemini function returned disposition and CX score
    - call_ended: Call has been terminated
    """
    try:
        data = await request.json()
        event_type = data.get("type")

        print(f"📥 Webhook received: {event_type}")
        print(f"   Data: {json.dumps(data, indent=2)}")

        if event_type == "call_started":
            await handle_call_started(data, db)

        elif event_type == "call_result":
            await handle_call_result(data, db)

        elif event_type == "call_ended":
            await handle_call_ended(data, db)

        else:
            print(f"⚠️  Unknown webhook event type: {event_type}")

        return {"status": "ok", "event": event_type}

    except Exception as e:
        print(f"❌ Error processing webhook: {e}")
        return {"status": "error", "message": str(e)}


async def handle_call_started(data: Dict[str, Any], db: Session):
    """
    Handle call_started event

    Updates call status to 'connected' and broadcasts to UI
    """
    call_id = data.get("call_id")
    lead_id = data.get("lead_id")
    lead_name = data.get("lead_name")
    voximplant_call_id = data.get("voximplant_call_id")

    # Update call status
    call_service.update_call_status(
        db,
        call_id,
        "connected",
        voximplant_call_id=voximplant_call_id
    )

    print(f"✅ Call started: {call_id} with {lead_name}")

    # Broadcast to WebSocket clients
    if websocket_manager:
        await websocket_manager.broadcast({
            "type": "call_started",
            "call_id": call_id,
            "lead_id": lead_id,
            "lead_name": lead_name,
            "timestamp": data.get("timestamp")
        })


async def handle_call_result(data: Dict[str, Any], db: Session):
    """
    Handle call_result event

    Saves the call result (disposition, CX score, summary) and broadcasts to UI
    """
    call_id = data.get("call_id")
    disposition = data.get("disposition")
    cx_score = data.get("cx_score")
    summary = data.get("summary")
    full_transcript = data.get("full_transcript")

    # Save call result
    call_service.save_call_result(
        db,
        call_id=call_id,
        disposition=disposition,
        cx_score=cx_score,
        summary=summary,
        full_transcript=full_transcript
    )

    print(f"✅ Call result saved: {call_id}")
    print(f"   Disposition: {disposition}, CX Score: {cx_score}")

    # Broadcast to WebSocket clients
    if websocket_manager:
        await websocket_manager.broadcast({
            "type": "call_result",
            "call_id": call_id,
            "disposition": disposition,
            "cx_score": cx_score,
            "summary": summary
        })


async def handle_call_ended(data: Dict[str, Any], db: Session):
    """
    Handle call_ended event

    Updates call status to 'completed' and updates lead status
    """
    call_id = data.get("call_id")

    # Update call status
    call = call_service.update_call_status(db, call_id, "completed")

    if call:
        # Update lead status
        lead_service.update_lead_status(db, call.lead_id, "called")

        print(f"✅ Call ended: {call_id}")
        print(f"   Duration: {call.duration_seconds}s")

    # Broadcast to WebSocket clients
    if websocket_manager:
        await websocket_manager.broadcast({
            "type": "call_ended",
            "call_id": call_id,
            "duration_seconds": call.duration_seconds if call else None
        })


@router.get("/voximplant/test")
def test_webhook():
    """
    Test endpoint to verify webhook configuration
    """
    return {
        "status": "ok",
        "message": "Webhook endpoint is working",
        "timestamp": "2025-01-17T00:00:00Z"
    }
