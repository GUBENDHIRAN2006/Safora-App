import os
from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    # Application settings
    APP_NAME: str = "Safora Backend"
    
    # Supabase Credentials (defaults supplied from user parameters)
    SUPABASE_URL: str = "https://wocwjmikitjzyytuczhw.supabase.co"
    SUPABASE_ANON_KEY: str = "sb_publishable_Jqh1FPi_xSayoMg48m1Pzw_IVP_GQJn"
    
    # Database URL: loaded from .env (DATABASE_URL variable)
    DATABASE_URL: str = "postgresql://postgres.wocwjmikitjzyytuczhw:gubendhiran123@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres"
    
    # Google Maps API Key
    GOOGLE_MAPS_API_KEY: str = "AIzaSyCQygp5l4GAc46JyOHZYEcWBu3-IbDTwtQ"
    
    # JWT Secrets
    JWT_SECRET_KEY: str = "9a37e19572d4d8ef8cf496cfc3c8617887383a1b02534f31da63309a475d691e"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 11520  # 8 days for mobile sessions
    
    # Firebase Cloud Messaging
    FCM_SERVER_KEY: str = ""
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

# Instantiate settings
settings = Settings()
