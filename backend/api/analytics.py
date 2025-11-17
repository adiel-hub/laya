"""
Analytics API endpoints
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional

from database.db import get_db
from services.call_service import CallService
from services.lead_service import LeadService
from schemas.schemas import AnalyticsSummary

router = APIRouter(prefix="/api/analytics", tags=["analytics"])
call_service = CallService()
lead_service = LeadService()


@router.get("/summary", response_model=AnalyticsSummary)
def get_analytics_summary(db: Session = Depends(get_db)):
    """
    Get overall analytics summary

    Returns:
    - Total calls
    - Completed calls
    - Average duration
    - Average CX score
    - Disposition breakdown
    - Calls by type (drop-off vs dormant)
    """
    # Total calls
    total_calls = call_service.count_calls(db)
    completed_calls = call_service.count_calls(db, status="completed")

    # Average duration
    from sqlalchemy import func
    from database.models import Call
    avg_duration = db.query(func.avg(Call.duration_seconds)).filter(
        Call.status == "completed"
    ).scalar()
    avg_duration = round(avg_duration, 2) if avg_duration else 0.0

    # Average CX score
    avg_cx_score = call_service.get_average_cx_score(db)

    # Disposition breakdown
    dispositions = call_service.get_disposition_breakdown(db)

    # Calls by type
    calls_drop_off = call_service.count_calls(db, lead_type="drop-off")
    calls_dormant = call_service.count_calls(db, lead_type="dormant")

    return {
        "total_calls": total_calls,
        "completed_calls": completed_calls,
        "avg_duration_seconds": avg_duration,
        "avg_cx_score": avg_cx_score,
        "dispositions": dispositions,
        "calls_by_type": {
            "drop-off": calls_drop_off,
            "dormant": calls_dormant
        }
    }


@router.get("/trends")
def get_trends(
    days: int = 30,
    db: Session = Depends(get_db)
):
    """
    Get call trends over time

    - **days**: Number of days to look back (default: 30)

    Returns daily call counts and average CX scores
    """
    from sqlalchemy import func, cast, Date
    from database.models import Call, CallResult

    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # Get daily call counts
    daily_calls = db.query(
        cast(Call.started_at, Date).label('date'),
        func.count(Call.id).label('count')
    ).filter(
        Call.started_at >= start_date,
        Call.started_at <= end_date
    ).group_by(
        cast(Call.started_at, Date)
    ).all()

    # Get daily average CX scores
    daily_cx = db.query(
        cast(Call.started_at, Date).label('date'),
        func.avg(CallResult.cx_score).label('avg_cx')
    ).join(
        CallResult, Call.call_id == CallResult.call_id
    ).filter(
        Call.started_at >= start_date,
        Call.started_at <= end_date
    ).group_by(
        cast(Call.started_at, Date)
    ).all()

    # Convert to dictionaries
    calls_by_date = {str(date): count for date, count in daily_calls}
    cx_by_date = {str(date): round(float(avg_cx), 2) for date, avg_cx in daily_cx if avg_cx}

    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "daily_calls": calls_by_date,
        "daily_avg_cx": cx_by_date
    }


@router.get("/dispositions")
def get_disposition_details(db: Session = Depends(get_db)):
    """
    Get detailed disposition breakdown with percentages
    """
    dispositions = call_service.get_disposition_breakdown(db)
    total = sum(dispositions.values())

    detailed = {}
    for disposition, count in dispositions.items():
        percentage = (count / total * 100) if total > 0 else 0
        detailed[disposition] = {
            "count": count,
            "percentage": round(percentage, 2)
        }

    return {
        "total": total,
        "breakdown": detailed
    }


@router.get("/leads/status")
def get_leads_status_breakdown(db: Session = Depends(get_db)):
    """
    Get breakdown of leads by status
    """
    from sqlalchemy import func
    from database.models import Lead

    results = db.query(
        Lead.status,
        func.count(Lead.id)
    ).group_by(Lead.status).all()

    breakdown = {status: count for status, count in results}
    total = sum(breakdown.values())

    return {
        "total": total,
        "breakdown": breakdown
    }


@router.get("/performance")
def get_performance_metrics(db: Session = Depends(get_db)):
    """
    Get key performance metrics

    - Conversion rate (completed registrations / total drop-off calls)
    - Reactivation rate (reactivated / total dormant calls)
    - Average call duration by type
    - CX score distribution
    """
    from sqlalchemy import func
    from database.models import Call, CallResult, Lead

    # Conversion rate for drop-off leads
    drop_off_calls = db.query(Call).join(Lead).filter(Lead.type == "drop-off").count()
    completed_registrations = db.query(CallResult).join(Call).join(Lead).filter(
        Lead.type == "drop-off",
        CallResult.disposition == "COMPLETED_REGISTRATION"
    ).count()
    conversion_rate = (completed_registrations / drop_off_calls * 100) if drop_off_calls > 0 else 0

    # Reactivation rate for dormant leads
    dormant_calls = db.query(Call).join(Lead).filter(Lead.type == "dormant").count()
    reactivated = db.query(CallResult).join(Call).join(Lead).filter(
        Lead.type == "dormant",
        CallResult.disposition == "REACTIVATED"
    ).count()
    reactivation_rate = (reactivated / dormant_calls * 100) if dormant_calls > 0 else 0

    # Average duration by type
    avg_duration_drop_off = db.query(func.avg(Call.duration_seconds)).join(Lead).filter(
        Lead.type == "drop-off",
        Call.status == "completed"
    ).scalar() or 0

    avg_duration_dormant = db.query(func.avg(Call.duration_seconds)).join(Lead).filter(
        Lead.type == "dormant",
        Call.status == "completed"
    ).scalar() or 0

    # CX score distribution
    cx_distribution = db.query(
        CallResult.cx_score,
        func.count(CallResult.id)
    ).group_by(CallResult.cx_score).all()

    cx_dist_dict = {score: count for score, count in cx_distribution}

    return {
        "conversion_rate": round(conversion_rate, 2),
        "reactivation_rate": round(reactivation_rate, 2),
        "avg_duration_by_type": {
            "drop-off": round(float(avg_duration_drop_off), 2),
            "dormant": round(float(avg_duration_dormant), 2)
        },
        "cx_score_distribution": cx_dist_dict
    }
