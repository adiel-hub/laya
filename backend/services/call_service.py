"""
Call Service - Business logic for call management
"""

from sqlalchemy.orm import Session
from database.models import Call, CallResult, Lead
from datetime import datetime
from typing import List, Optional
import uuid


class CallService:
    """Service class for managing calls and call results"""

    def create_call(
        self,
        db: Session,
        lead_id: int,
        voximplant_call_id: Optional[str] = None
    ) -> Call:
        """
        Create a new call record

        Args:
            db: Database session
            lead_id: ID of the lead being called
            voximplant_call_id: Voximplant's internal call ID (optional)

        Returns:
            Created Call object
        """
        call_id = str(uuid.uuid4())
        db_call = Call(
            call_id=call_id,
            lead_id=lead_id,
            voximplant_call_id=voximplant_call_id,
            status="initiated",
            started_at=datetime.utcnow()
        )
        db.add(db_call)
        db.commit()
        db.refresh(db_call)
        return db_call

    def get_call_by_id(self, db: Session, call_id: str) -> Optional[Call]:
        """
        Get a call by its ID

        Args:
            db: Database session
            call_id: Call ID

        Returns:
            Call object or None if not found
        """
        return db.query(Call).filter(Call.call_id == call_id).first()

    def get_all_calls(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 50,
        status: Optional[str] = None,
        lead_id: Optional[int] = None
    ) -> List[Call]:
        """
        Get all calls with optional filtering

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            status: Filter by status (optional)
            lead_id: Filter by lead ID (optional)

        Returns:
            List of Call objects
        """
        query = db.query(Call)

        if status:
            query = query.filter(Call.status == status)
        if lead_id:
            query = query.filter(Call.lead_id == lead_id)

        return query.order_by(Call.started_at.desc()).offset(skip).limit(limit).all()

    def update_call_status(
        self,
        db: Session,
        call_id: str,
        status: str,
        voximplant_call_id: Optional[str] = None
    ) -> Optional[Call]:
        """
        Update call status

        Args:
            db: Database session
            call_id: Call ID
            status: New status
            voximplant_call_id: Voximplant call ID (optional, for initial connection)

        Returns:
            Updated Call object or None if not found
        """
        db_call = self.get_call_by_id(db, call_id)
        if not db_call:
            return None

        db_call.status = status

        if voximplant_call_id and not db_call.voximplant_call_id:
            db_call.voximplant_call_id = voximplant_call_id

        # Set ended_at and calculate duration when call completes or fails
        if status in ["completed", "failed"] and not db_call.ended_at:
            db_call.ended_at = datetime.utcnow()
            if db_call.started_at:
                duration = (db_call.ended_at - db_call.started_at).seconds
                db_call.duration_seconds = duration

        db.commit()
        db.refresh(db_call)
        return db_call

    def save_call_result(
        self,
        db: Session,
        call_id: str,
        disposition: str,
        cx_score: int,
        summary: str,
        full_transcript: Optional[str] = None,
        key_objections: Optional[str] = None,
        next_actions: Optional[str] = None,
        recording_url: Optional[str] = None
    ) -> CallResult:
        """
        Save call result and analytics

        Args:
            db: Database session
            call_id: Call ID
            disposition: Call outcome
            cx_score: Customer experience score (1-10)
            summary: Hebrew summary
            full_transcript: Complete conversation transcript
            key_objections: JSON string of objections
            next_actions: JSON string of recommended actions
            recording_url: URL to call recording

        Returns:
            Created CallResult object
        """
        db_result = CallResult(
            call_id=call_id,
            disposition=disposition,
            cx_score=cx_score,
            summary=summary,
            full_transcript=full_transcript,
            key_objections=key_objections,
            next_actions=next_actions,
            recording_url=recording_url
        )
        db.add(db_result)
        db.commit()
        db.refresh(db_result)
        return db_result

    def get_call_result(self, db: Session, call_id: str) -> Optional[CallResult]:
        """
        Get call result by call ID

        Args:
            db: Database session
            call_id: Call ID

        Returns:
            CallResult object or None if not found
        """
        return db.query(CallResult).filter(CallResult.call_id == call_id).first()

    def get_call_with_details(self, db: Session, call_id: str) -> Optional[dict]:
        """
        Get complete call information including lead and result

        Args:
            db: Database session
            call_id: Call ID

        Returns:
            Dictionary with call, lead, and result information
        """
        call = self.get_call_by_id(db, call_id)
        if not call:
            return None

        return {
            "call": call,
            "lead": call.lead,
            "result": call.result
        }

    def count_calls(
        self,
        db: Session,
        status: Optional[str] = None,
        lead_type: Optional[str] = None
    ) -> int:
        """
        Count calls with optional filtering

        Args:
            db: Database session
            status: Filter by call status
            lead_type: Filter by lead type

        Returns:
            Count of calls
        """
        query = db.query(Call)

        if status:
            query = query.filter(Call.status == status)
        if lead_type:
            query = query.join(Lead).filter(Lead.type == lead_type)

        return query.count()

    def get_average_cx_score(self, db: Session) -> float:
        """
        Calculate average CX score across all calls

        Args:
            db: Database session

        Returns:
            Average CX score
        """
        from sqlalchemy import func
        result = db.query(func.avg(CallResult.cx_score)).scalar()
        return round(result, 2) if result else 0.0

    def get_disposition_breakdown(self, db: Session) -> dict:
        """
        Get count of calls by disposition

        Args:
            db: Database session

        Returns:
            Dictionary with disposition counts
        """
        from sqlalchemy import func
        results = db.query(
            CallResult.disposition,
            func.count(CallResult.id)
        ).group_by(CallResult.disposition).all()

        return {disposition: count for disposition, count in results}
