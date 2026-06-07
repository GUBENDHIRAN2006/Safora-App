from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from uuid import UUID
from app.db.database import get_db
from app.models.models import User, EmergencySession, AlertLog, HealthReading
from app.schemas.schemas import UserResponse, EmergencySessionResponse
from app.routes.auth import get_current_admin

router = APIRouter(prefix="/admin", tags=["Admin Panel"])

@router.get("/users", response_model=List[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """Admin-only: Retrieve all registered user accounts."""
    return db.query(User).order_by(User.created_at.desc()).all()


@router.put("/users/{target_user_id}/role", response_model=UserResponse)
def update_user_role(
    target_user_id: UUID,
    role: str,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """Admin-only: Updates the role (e.g., 'user', 'admin') of a target user."""
    if role not in ["user", "admin"]:
        raise HTTPException(status_code=400, detail="Invalid role type. Must be 'user' or 'admin'.")
        
    user = db.query(User).filter(User.id == target_user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User account not found.")
        
    user.role = role
    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{target_user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    target_user_id: UUID,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """Admin-only: Deletes a user profile and cascades delete to all associated contacts, health readings, etc."""
    user = db.query(User).filter(User.id == target_user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User account not found.")
        
    if user.id == admin_user.id:
        raise HTTPException(status_code=400, detail="Cannot self-delete the currently active admin session.")
        
    db.delete(user)
    db.commit()
    return


@router.get("/emergencies", response_model=List[EmergencySessionResponse])
def list_emergency_logs(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """Admin-only: Retreive a list of all historical emergency alert sessions."""
    return db.query(EmergencySession).order_by(EmergencySession.started_at.desc()).all()


@router.get("/alerts")
def list_alert_logs(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """Admin-only: Fetches system-wide emergency alert dispatch logs (SMS, Push, Calls)."""
    logs = db.query(
        AlertLog.id,
        AlertLog.session_id,
        AlertLog.channel,
        AlertLog.status,
        AlertLog.sent_at,
        User.full_name.label("user_name")
    ).join(
        EmergencySession, AlertLog.session_id == EmergencySession.id
    ).join(
        User, EmergencySession.user_id == User.id
    ).order_by(
        AlertLog.sent_at.desc()
    ).all()
    
    return [
        {
            "id": log.id,
            "session_id": log.session_id,
            "channel": log.channel,
            "status": log.status,
            "sent_at": log.sent_at.isoformat(),
            "user_name": log.user_name
        }
        for log in logs
    ]


@router.get("/statistics")
def get_system_statistics(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """Admin-only: Calculates aggregate metrics of user base, active alerts, and overall system load."""
    total_users = db.query(User).count()
    total_emergencies = db.query(EmergencySession).count()
    active_emergencies = db.query(EmergencySession).filter(EmergencySession.status == "active").count()
    
    # SMS vs Push dispatch counts
    alert_distribution = db.query(
        AlertLog.channel,
        func.count(AlertLog.id).label("count")
    ).group_by(
        AlertLog.channel
    ).all()
    
    distribution_dict = {"sms": 0, "push": 0, "call": 0}
    for item in alert_distribution:
        if item.channel in distribution_dict:
            distribution_dict[item.channel] = item.count
            
    # System health parameters average
    avg_metrics = db.query(
        func.avg(HealthReading.heart_rate).label("avg_hr"),
        func.avg(HealthReading.spo2).label("avg_spo2")
    ).first()
    
    return {
        "total_users": total_users,
        "total_emergencies": total_emergencies,
        "active_emergencies": active_emergencies,
        "alert_dispatch_summary": distribution_dict,
        "system_health_averages": {
            "heart_rate": round(float(avg_metrics.avg_hr), 1) if avg_metrics.avg_hr else 0.0,
            "spo2": round(float(avg_metrics.avg_spo2), 1) if avg_metrics.avg_spo2 else 0.0
        }
    }
