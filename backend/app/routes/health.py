from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from datetime import datetime, timedelta
from uuid import UUID
from app.db.database import get_db
from app.models.models import User, HealthReading
from app.schemas.schemas import HealthReadingCreate, HealthReadingResponse
from app.routes.auth import get_current_user

router = APIRouter(prefix="/health", tags=["Health Monitoring"])

@router.post("/readings", response_model=HealthReadingResponse, status_code=status.HTTP_201_CREATED)
def create_health_reading(
    reading_in: HealthReadingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Saves a single health reading (e.g. from live sensor polling)."""
    new_reading = HealthReading(
        user_id=current_user.id,
        heart_rate=reading_in.heart_rate,
        systolic_bp=reading_in.systolic_bp,
        diastolic_bp=reading_in.diastolic_bp,
        spo2=reading_in.spo2,
        steps=reading_in.steps,
        sleep_hours=reading_in.sleep_hours,
        recorded_at=reading_in.recorded_at or datetime.now()
    )
    db.add(new_reading)
    db.commit()
    db.refresh(new_reading)
    return new_reading


@router.post("/readings/batch", response_model=List[HealthReadingResponse], status_code=status.HTTP_201_CREATED)
def create_batch_health_readings(
    readings_in: List[HealthReadingCreate],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Uploads a batch of health readings (e.g., historical synchronization from Health Connect)."""
    new_readings = []
    for r in readings_in:
        new_readings.append(
            HealthReading(
                user_id=current_user.id,
                heart_rate=r.heart_rate,
                systolic_bp=r.systolic_bp,
                diastolic_bp=r.diastolic_bp,
                spo2=r.spo2,
                steps=r.steps,
                sleep_hours=r.sleep_hours,
                recorded_at=r.recorded_at or datetime.now()
            )
        )
    db.add_all(new_readings)
    db.commit()
    # Refresh all
    for r in new_readings:
        db.refresh(r)
    return new_readings


@router.get("/readings", response_model=List[HealthReadingResponse])
def get_health_history(
    limit: int = Query(50, ge=1, le=500),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves historical health readings for the authenticated user, sorted chronologically descending."""
    query = db.query(HealthReading).filter(HealthReading.user_id == current_user.id)
    
    if start_date:
        query = query.filter(HealthReading.recorded_at >= start_date)
    if end_date:
        query = query.filter(HealthReading.recorded_at <= end_date)
        
    return query.order_by(desc(HealthReading.recorded_at)).limit(limit).all()


@router.get("/trends")
def get_health_trends(
    period: str = Query("day", pattern="^(day|week|month)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Calculates aggregated average health parameters grouped by day, week, or month.
    Returns structured data for historical charts.
    """
    # Define date truncation interval
    # In PostgreSQL, we can use date_trunc. Let's write the query using SQLAlchemy.
    trunc_date = func.date_trunc(period, HealthReading.recorded_at)
    
    trends = db.query(
        trunc_date.label("time_bucket"),
        func.avg(HealthReading.heart_rate).label("avg_heart_rate"),
        func.avg(HealthReading.systolic_bp).label("avg_systolic_bp"),
        func.avg(HealthReading.diastolic_bp).label("avg_diastolic_bp"),
        func.avg(HealthReading.spo2).label("avg_spo2"),
        func.sum(HealthReading.steps).label("total_steps"),
        func.avg(HealthReading.sleep_hours).label("avg_sleep_hours")
    ).filter(
        HealthReading.user_id == current_user.id
    ).group_by(
        "time_bucket"
    ).order_by(
        "time_bucket"
    ).all()
    
    result = []
    for t in trends:
        result.append({
            "time_bucket": t.time_bucket.isoformat() if t.time_bucket else None,
            "heart_rate": round(float(t.avg_heart_rate), 1) if t.avg_heart_rate is not None else 0.0,
            "systolic_bp": round(float(t.avg_systolic_bp), 1) if t.avg_systolic_bp is not None else 0.0,
            "diastolic_bp": round(float(t.avg_diastolic_bp), 1) if t.avg_diastolic_bp is not None else 0.0,
            "spo2": round(float(t.avg_spo2), 1) if t.avg_spo2 is not None else 0.0,
            "steps": int(t.total_steps) if t.total_steps is not None else 0,
            "sleep_hours": round(float(t.avg_sleep_hours), 1) if t.avg_sleep_hours is not None else 0.0
        })
        
    return result


@router.get("/latest", response_model=Optional[HealthReadingResponse])
def get_latest_health_reading(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves the most recent health reading recorded for the user."""
    return db.query(HealthReading)\
             .filter(HealthReading.user_id == current_user.id)\
             .order_by(desc(HealthReading.recorded_at))\
             .first()
