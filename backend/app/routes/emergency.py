from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime
from uuid import UUID
from app.db.database import get_db
from app.models.models import User, EmergencySession, GPSCoordinate, EmergencyContact, HealthReading, AlertLog
from app.schemas.schemas import (
    EmergencySessionCreate, EmergencySessionResolve, EmergencySessionResponse,
    GPSCoordinateCreate, GPSCoordinateResponse, EmergencyDetailsResponse,
    OfflineEmergencySessionSync
)
from app.routes.auth import get_current_user

router = APIRouter(prefix="/emergency", tags=["Emergency Operations"])

@router.post("/sessions", response_model=EmergencySessionResponse, status_code=status.HTTP_201_CREATED)
def start_emergency_session(
    session_in: EmergencySessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Initiates a new active emergency tracking session.
    Automatically cancels/resolves any other active sessions for this user.
    """
    # Deactivate existing active sessions
    db.query(EmergencySession)\
      .filter(EmergencySession.user_id == current_user.id, EmergencySession.status == "active")\
      .update({EmergencySession.status: "resolved", EmergencySession.ended_at: datetime.now(), EmergencySession.resolution_notes: "Auto-resolved to start new session"})
      
    new_session = EmergencySession(
        user_id=current_user.id,
        status="active",
        started_at=datetime.now()
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session


@router.get("/sessions/active", response_model=Optional[EmergencySessionResponse])
def get_active_session(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns the user's currently active emergency session, if any."""
    return db.query(EmergencySession)\
             .filter(EmergencySession.user_id == current_user.id, EmergencySession.status == "active")\
             .first()


@router.post("/sessions/{session_id}/coordinates", response_model=GPSCoordinateResponse, status_code=status.HTTP_201_CREATED)
def add_gps_coordinate(
    session_id: UUID,
    coord_in: GPSCoordinateCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Accepts streamed GPS coordinates (every 5-10 seconds) during active emergencies.
    Requires user ownership of the session.
    """
    session = db.query(EmergencySession).filter(EmergencySession.id == session_id, EmergencySession.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Active emergency session not found")
        
    if session.status != "active":
        raise HTTPException(status_code=400, detail="Cannot upload coordinates to an inactive session")

    new_coord = GPSCoordinate(
        session_id=session.id,
        latitude=coord_in.latitude,
        longitude=coord_in.longitude,
        recorded_at=datetime.now()
    )
    db.add(new_coord)
    db.commit()
    db.refresh(new_coord)
    return new_coord


@router.put("/sessions/{session_id}/resolve", response_model=EmergencySessionResponse)
def resolve_emergency_session(
    session_id: UUID,
    resolve_in: EmergencySessionResolve,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Marks an active emergency session as resolved or cancelled (e.g. 'I am fine')."""
    session = db.query(EmergencySession).filter(EmergencySession.id == session_id, EmergencySession.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Active emergency session not found")
        
    session.status = "resolved"
    session.ended_at = datetime.now()
    session.resolution_notes = resolve_in.resolution_notes
    
    db.commit()
    db.refresh(session)
    return session


@router.get("/track/{session_id}", response_model=EmergencyDetailsResponse)
def get_public_tracking_details(
    session_id: UUID,
    db: Session = Depends(get_db)
):
    """
    PUBLIC ENDPOINT: Allows emergency contacts/responders to view tracking details 
    of an emergency session using a unique tracking link without authentication.
    """
    session = db.query(EmergencySession).filter(EmergencySession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Emergency session not found")
        
    # Get user profile metadata
    user = db.query(User).filter(User.id == session.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Get latest coordinates
    last_coord = db.query(GPSCoordinate)\
                   .filter(GPSCoordinate.session_id == session.id)\
                   .order_by(desc(GPSCoordinate.recorded_at))\
                   .first()
                   
    # Get latest health reading
    latest_reading = db.query(HealthReading)\
                       .filter(HealthReading.user_id == session.user_id)\
                       .order_by(desc(HealthReading.recorded_at))\
                       .first()
                       
    # Get contacts list
    contacts = db.query(EmergencyContact).filter(EmergencyContact.user_id == session.user_id).all()
    
    # Map to schemas
    # Note: Pydantic will auto-coerce SQLAlchemy models to dicts/objects if from_attributes=True
    return {
        "session": session,
        "user_name": user.full_name,
        "contacts": contacts,
        "last_coordinates": last_coord,
        "health_reading": latest_reading
    }


@router.post("/sessions/{session_id}/alert-logs", status_code=status.HTTP_201_CREATED)
def create_alert_log(
    session_id: UUID,
    channel: str,
    alert_status: str,
    contact_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Endpoint for the mobile client to report and log alert dispatches (e.g. native SMS, push)
    to the database for auditing.
    """
    session = db.query(EmergencySession).filter(EmergencySession.id == session_id, EmergencySession.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Active emergency session not found")
        
    new_log = AlertLog(
        session_id=session.id,
        contact_id=contact_id,
        channel=channel,
        status=alert_status,
        sent_at=datetime.now()
    )
    db.add(new_log)
    db.commit()
    db.refresh(new_log)
    return {"status": "logged", "id": new_log.id}


@router.post("/sessions/sync", status_code=status.HTTP_201_CREATED)
def sync_offline_emergency_session(
    sync_data: OfflineEmergencySessionSync,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Syncs an emergency session that occurred while the client device was offline.
    Batch creates the session, readings, GPS coordinates, and alert logs.
    """
    # 1. Create the EmergencySession
    # Ensure any existing active sessions are resolved
    db.query(EmergencySession)\
      .filter(EmergencySession.user_id == current_user.id, EmergencySession.status == "active")\
      .update({
          EmergencySession.status: "resolved", 
          EmergencySession.ended_at: datetime.now(), 
          EmergencySession.resolution_notes: "Auto-resolved to sync offline session"
      })

    session = EmergencySession(
        id=sync_data.session_id,
        user_id=current_user.id,
        status="resolved",
        started_at=sync_data.started_at,
        ended_at=sync_data.ended_at,
        resolution_notes=sync_data.resolution_notes
    )
    db.add(session)
    
    # 2. Add Health Readings
    for hr in sync_data.health_readings:
        reading = HealthReading(
            user_id=current_user.id,
            heart_rate=hr.heart_rate,
            systolic_bp=hr.systolic_bp,
            diastolic_bp=hr.diastolic_bp,
            spo2=hr.spo2,
            steps=hr.steps,
            sleep_hours=hr.sleep_hours,
            recorded_at=hr.recorded_at or datetime.now()
        )
        db.add(reading)
        
    # 3. Add GPS Coordinates
    for gps in sync_data.gps_coordinates:
        coord = GPSCoordinate(
            session_id=sync_data.session_id,
            latitude=gps.latitude,
            longitude=gps.longitude,
            recorded_at=gps.recorded_at
        )
        db.add(coord)
        
    # 4. Add Alert Logs
    for al in sync_data.alert_logs:
        log = AlertLog(
            session_id=sync_data.session_id,
            contact_id=al.contact_id,
            channel=al.channel,
            status=al.status,
            sent_at=al.sent_at
        )
        db.add(log)
        
    db.commit()
    db.refresh(session)
    return {"status": "synced", "session_id": session.id}


