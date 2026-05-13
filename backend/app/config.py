"""
Configuration management for the Conversational AI Backend
Uses environment variables for sensitive data
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # API Configuration
    API_TITLE: str = "Conversational AI Agent"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = "Production-grade conversational voice AI for Indian market"
    DEBUG: bool = False
    
    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = True
    
    # Sarvam AI Configuration
    SARVAM_API_KEY: str = ""
    SARVAM_LLM_MODEL: str = "Sarvam-30B"
    SARVAM_STT_MODEL: str = "saaras:v3"
    SARVAM_TTS_MODEL: str = "Bulbul v3"
    SARVAM_API_BASE_URL: str = "https://api.sarvam.ai"
    
    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_TTL: int = 3600  # 1 hour
    
    # PostgreSQL Configuration
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/conversational_ai"
    
    # WebSocket Configuration
    WS_HEARTBEAT_INTERVAL: int = 30
    WS_MAX_CONNECTIONS: int = 1000
    
    # Exotel Telephony Configuration
    EXOTEL_SID: str = ""
    EXOTEL_API_KEY: str = ""
    EXOTEL_API_TOKEN: str = ""
    EXOTEL_CALLER_ID: str = ""
    EXOTEL_WS_URL: str = ""  # Your public WSS URL for Exotel to connect to
    
    # Audio Configuration
    SAMPLE_RATE: int = 16000
    CHANNELS: int = 1
    CHUNK_SIZE: int = 1024
    MAX_AUDIO_LENGTH: int = 300  # 5 minutes in seconds
    
    # Response Configuration
    STREAMING_ENABLED: bool = True
    RESPONSE_TIMEOUT: int = 30
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    class Config:
        env_file = ("../.env", ".env")
        extra = "ignore"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
