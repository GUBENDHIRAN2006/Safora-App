-- Safora Database Schema
-- To be run in Supabase SQL Editor

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Users Table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'user',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index for user email lookup
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- 2. Emergency Contacts Table
CREATE TABLE IF NOT EXISTS emergency_contacts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    relationship VARCHAR(100) NOT NULL, -- 'parent', 'spouse', 'friend', 'doctor', etc.
    mobile_number VARCHAR(50) NOT NULL,
    priority INT DEFAULT 1, -- 1 is primary
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_emergency_contacts_user ON emergency_contacts(user_id);

-- 3. Health Readings Table
CREATE TABLE IF NOT EXISTS health_readings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    heart_rate DECIMAL(5,2),
    systolic_bp DECIMAL(5,2),
    diastolic_bp DECIMAL(5,2),
    spo2 DECIMAL(5,2),
    steps INT DEFAULT 0,
    sleep_hours DECIMAL(4,2) DEFAULT 0.0,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_health_readings_user ON health_readings(user_id);
CREATE INDEX IF NOT EXISTS idx_health_readings_recorded_at ON health_readings(recorded_at DESC);

-- 4. Emergency Sessions Table
CREATE TABLE IF NOT EXISTS emergency_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(50) DEFAULT 'active', -- 'active', 'resolved', 'cancelled'
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP WITH TIME ZONE,
    resolution_notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_emergency_sessions_user ON emergency_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_emergency_sessions_status ON emergency_sessions(status);

-- 5. GPS Coordinates Table for Live Tracking
CREATE TABLE IF NOT EXISTS gps_coordinates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES emergency_sessions(id) ON DELETE CASCADE,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_gps_coordinates_session ON gps_coordinates(session_id);
CREATE INDEX IF NOT EXISTS idx_gps_coordinates_recorded_at ON gps_coordinates(recorded_at ASC);

-- 6. Alert Logs Table
CREATE TABLE IF NOT EXISTS alert_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES emergency_sessions(id) ON DELETE CASCADE,
    contact_id UUID REFERENCES emergency_contacts(id) ON DELETE SET NULL,
    channel VARCHAR(50) NOT NULL, -- 'sms', 'push', 'call'
    status VARCHAR(50) NOT NULL, -- 'sent', 'failed'
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_alert_logs_session ON alert_logs(session_id);
