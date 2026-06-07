from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from decimal import Decimal

# --- Auth Schemas ---

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: str = Field(..., min_length=1)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    role: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[str] = None


# --- Emergency Contact Schemas ---

class EmergencyContactCreate(BaseModel):
    name: str = Field(..., min_length=1)
    relationship: str = Field(..., min_length=1)
    mobile_number: str = Field(..., min_length=5)
    priority: int = 1

class EmergencyContactUpdate(BaseModel):
    name: Optional[str] = None
    relationship: Optional[str] = None
    mobile_number: Optional[str] = None
    priority: Optional[int] = None

class EmergencyContactResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    relationship: str
    mobile_number: str
    priority: int
    created_at: datetime

    class Config:
        from_attributes = True


# --- Health Reading Schemas ---

class HealthReadingCreate(BaseModel):
    heart_rate: Decimal
    systolic_bp: Decimal
    diastolic_bp: Decimal
    spo2: Decimal
    steps: Optional[int] = 0
    sleep_hours: Optional[Decimal] = Decimal("0.0")
    recorded_at: Optional[datetime] = None

class HealthReadingResponse(BaseModel):
    id: UUID
    user_id: UUID
    heart_rate: Decimal
    systolic_bp: Decimal
    diastolic_bp: Decimal
    spo2: Decimal
    steps: int
    sleep_hours: Decimal
    recorded_at: datetime

    class Config:
        from_attributes = True


# --- Live Location Schemas ---

class GPSCoordinateCreate(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)

class GPSCoordinateResponse(BaseModel):
    id: UUID
    session_id: UUID
    latitude: float
    longitude: float
    recorded_at: datetime

    class Config:
        from_attributes = True


# --- Emergency Session Schemas ---

class EmergencySessionCreate(BaseModel):
    trigger_reason: Optional[str] = "Manual Trigger"

class EmergencySessionResolve(BaseModel):
    resolution_notes: str = Field(..., min_length=5)

class EmergencySessionResponse(BaseModel):
    id: UUID
    user_id: UUID
    status: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None

    class Config:
        from_attributes = True

class EmergencyDetailsResponse(BaseModel):
    session: EmergencySessionResponse
    user_name: str
    contacts: List[EmergencyContactResponse]
    last_coordinates: Optional[GPSCoordinateResponse] = None
    health_reading: Optional[HealthReadingResponse] = None


# --- AI Risk Analysis Schemas ---

class RiskAnalysisRequest(BaseModel):
    heart_rate: float
    systolic_bp: float
    diastolic_bp: float
    spo2: float
    sleep_hours: float
    steps: int

class RiskAnalysisResponse(BaseModel):
    risk_level: str  # 'Low', 'Medium', 'High'
    rf_confidence: float
    xgb_confidence: float
    timestamp: datetime


# --- Offline Emergency Sync Schemas ---

class GPSCoordinateSync(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    recorded_at: datetime

class AlertLogSync(BaseModel):
    contact_id: Optional[UUID] = None
    channel: str # 'sms', 'push', 'call'
    status: str # 'sent', 'failed'
    sent_at: datetime

class OfflineEmergencySessionSync(BaseModel):
    session_id: UUID
    started_at: datetime
    ended_at: datetime
    resolution_notes: str
    health_readings: List[HealthReadingCreate]
    gps_coordinates: List[GPSCoordinateSync]
    alert_logs: List[AlertLogSync]

