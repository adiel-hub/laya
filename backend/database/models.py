"""
SQLAlchemy database models for LAYA Calling Agent
"""

from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class Lead(Base):
    """Lead model - represents potential customers"""
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    type = Column(String, nullable=False)  # 'drop-off' or 'dormant'
    drop_stage = Column(String)  # For drop-off leads: 'identity_verify', 'funding', etc.
    last_active = Column(DateTime)  # For dormant leads
    status = Column(String, default="pending")  # 'pending', 'calling', 'called', 'completed'
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    calls = relationship("Call", back_populates="lead", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Lead(id={self.id}, name='{self.name}', phone='{self.phone}', type='{self.type}')>"


class Call(Base):
    """Call model - represents individual call sessions"""
    __tablename__ = "calls"

    id = Column(Integer, primary_key=True, index=True)
    call_id = Column(String, unique=True, nullable=False, index=True)  # UUID
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    voximplant_call_id = Column(String)  # Voximplant's internal call ID
    status = Column(String, default="initiated")  # 'initiated', 'ringing', 'connected', 'completed', 'failed'
    started_at = Column(DateTime)
    ended_at = Column(DateTime)
    duration_seconds = Column(Integer)

    # Relationships
    lead = relationship("Lead", back_populates="calls")
    result = relationship("CallResult", back_populates="call", uselist=False)

    def __repr__(self):
        return f"<Call(id={self.id}, call_id='{self.call_id}', status='{self.status}')>"


class CallResult(Base):
    """Call Result model - stores outcomes and analytics of calls"""
    __tablename__ = "call_results"

    id = Column(Integer, primary_key=True, index=True)
    call_id = Column(String, ForeignKey("calls.call_id"), unique=True, nullable=False)
    disposition = Column(String, nullable=False)  # Call outcome category
    cx_score = Column(Integer, CheckConstraint('cx_score >= 1 AND cx_score <= 10'))
    summary = Column(Text)  # Hebrew summary from Gemini
    full_transcript = Column(Text)  # Complete conversation transcript
    key_objections = Column(Text)  # JSON string of objections raised
    next_actions = Column(Text)  # JSON string of recommended follow-ups
    recording_url = Column(String)  # URL to call recording (if available)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    call = relationship("Call", back_populates="result")

    def __repr__(self):
        return f"<CallResult(call_id='{self.call_id}', disposition='{self.disposition}', cx_score={self.cx_score})>"


# Disposition constants for reference
DISPOSITIONS = {
    "DROP_OFF": [
        "COMPLETED_REGISTRATION",
        "SCHEDULED_COMPLETION",
        "NEEDS_HELP",
        "NOT_INTERESTED",
        "WRONG_NUMBER"
    ],
    "DORMANT": [
        "REACTIVATED",
        "REMINDED_VALUE",
        "NO_TRAVEL_PLANS",
        "FOUND_ALTERNATIVE",
        "NOT_INTERESTED"
    ]
}
