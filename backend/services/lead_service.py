"""
Lead Service - Business logic for lead management
"""

from sqlalchemy.orm import Session
from database.models import Lead
from schemas.schemas import LeadCreate, LeadUpdate
from datetime import datetime
from typing import List, Optional


class LeadService:
    """Service class for managing leads"""

    def get_all_leads(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        lead_type: Optional[str] = None
    ) -> List[Lead]:
        """
        Get all leads with optional filtering

        Args:
            db: Database session
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return
            status: Filter by status (optional)
            lead_type: Filter by type (optional)

        Returns:
            List of Lead objects
        """
        query = db.query(Lead)

        if status:
            query = query.filter(Lead.status == status)
        if lead_type:
            query = query.filter(Lead.type == lead_type)

        return query.order_by(Lead.created_at.desc()).offset(skip).limit(limit).all()

    def get_lead_by_id(self, db: Session, lead_id: int) -> Optional[Lead]:
        """
        Get a single lead by ID

        Args:
            db: Database session
            lead_id: Lead ID

        Returns:
            Lead object or None if not found
        """
        return db.query(Lead).filter(Lead.id == lead_id).first()

    def create_lead(self, db: Session, lead: LeadCreate) -> Lead:
        """
        Create a new lead

        Args:
            db: Database session
            lead: Lead data

        Returns:
            Created Lead object
        """
        db_lead = Lead(
            name=lead.name,
            phone=lead.phone,
            type=lead.type,
            drop_stage=lead.drop_stage,
            last_active=lead.last_active,
            notes=lead.notes,
            status="pending"
        )
        db.add(db_lead)
        db.commit()
        db.refresh(db_lead)
        return db_lead

    def update_lead(self, db: Session, lead_id: int, lead: LeadUpdate) -> Optional[Lead]:
        """
        Update an existing lead

        Args:
            db: Database session
            lead_id: Lead ID
            lead: Updated lead data

        Returns:
            Updated Lead object or None if not found
        """
        db_lead = self.get_lead_by_id(db, lead_id)
        if not db_lead:
            return None

        # Update only provided fields
        update_data = lead.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_lead, key, value)

        db_lead.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_lead)
        return db_lead

    def delete_lead(self, db: Session, lead_id: int) -> bool:
        """
        Delete a lead

        Args:
            db: Database session
            lead_id: Lead ID

        Returns:
            True if deleted, False if not found
        """
        db_lead = self.get_lead_by_id(db, lead_id)
        if not db_lead:
            return False

        db.delete(db_lead)
        db.commit()
        return True

    def update_lead_status(self, db: Session, lead_id: int, status: str) -> Optional[Lead]:
        """
        Update only the status of a lead

        Args:
            db: Database session
            lead_id: Lead ID
            status: New status

        Returns:
            Updated Lead object or None if not found
        """
        db_lead = self.get_lead_by_id(db, lead_id)
        if not db_lead:
            return None

        db_lead.status = status
        db_lead.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_lead)
        return db_lead

    def count_leads(
        self,
        db: Session,
        status: Optional[str] = None,
        lead_type: Optional[str] = None
    ) -> int:
        """
        Count leads with optional filtering

        Args:
            db: Database session
            status: Filter by status (optional)
            lead_type: Filter by type (optional)

        Returns:
            Count of leads
        """
        query = db.query(Lead)

        if status:
            query = query.filter(Lead.status == status)
        if lead_type:
            query = query.filter(Lead.type == lead_type)

        return query.count()
