import uuid
from sqlalchemy import Column, String, Integer, Numeric, Float, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship as rel
from app.db.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), default="user")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    contacts = rel("EmergencyContact", back_populates="user", cascade="all, delete-orphan")
    readings = rel("HealthReading", back_populates="user", cascade="all, delete-orphan")
    sessions = rel("EmergencySession", back_populates="user", cascade="all, delete-orphan")


class EmergencyContact(Base):
    __tablename__ = "emergency_contacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    relationship = Column(String(100), nullable=False) # Bound to Column, masks global 'relationship'
    mobile_number = Column(String(50), nullable=False)
    priority = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = rel("User", back_populates="contacts")
    alert_logs = rel("AlertLog", back_populates="contact")


class HealthReading(Base):
    __tablename__ = "health_readings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    heart_rate = Column(Numeric(5, 2))
    systolic_bp = Column(Numeric(5, 2))
    diastolic_bp = Column(Numeric(5, 2))
    spo2 = Column(Numeric(5, 2))
    steps = Column(Integer, default=0)
    sleep_hours = Column(Numeric(4, 2), default=0.0)
    recorded_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    user = rel("User", back_populates="readings")


class EmergencySession(Base):
    __tablename__ = "emergency_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(50), default="active", index=True)  # 'active', 'resolved', 'cancelled'
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)
    resolution_notes = Column(Text, nullable=True)

    # Relationships
    user = rel("User", back_populates="sessions")
    coordinates = rel("GPSCoordinate", back_populates="session", cascade="all, delete-orphan")
    alert_logs = rel("AlertLog", back_populates="session", cascade="all, delete-orphan")


class GPSCoordinate(Base):
    __tablename__ = "gps_coordinates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("emergency_sessions.id", ondelete="CASCADE"), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    session = rel("EmergencySession", back_populates="coordinates")


class AlertLog(Base):
    __tablename__ = "alert_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("emergency_sessions.id", ondelete="CASCADE"), nullable=False)
    contact_id = Column(UUID(as_uuid=True), ForeignKey("emergency_contacts.id", ondelete="SET NULL"), nullable=True)
    channel = Column(String(50), nullable=False)  # 'sms', 'push', 'call'
    status = Column(String(50), nullable=False)   # 'sent', 'failed'
    sent_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    session = rel("EmergencySession", back_populates="alert_logs")
    contact = rel("EmergencyContact", back_populates="alert_logs")
