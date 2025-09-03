# File: config.py
import os
from pydantic_settings import BaseSettings
from typing import List, Optional, Union
from dotenv import load_dotenv
from pydantic import field_validator

load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "RodeCeview"

    # Database Configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    
    # Supabase Configuration
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30  # 30 days
    
    # Vector Database - Pinecone
    PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY", "")
    PINECONE_ENVIRONMENT: str = os.getenv("PINECONE_ENVIRONMENT", "")
    PINECONE_INDEX_NAME: str = os.getenv("PINECONE_INDEX_NAME", "code-review-index")

    # Gemini API Key
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    # Embedding Model
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

    # Git Configuration
    MAX_COMMIT_HISTORY: int = int(os.getenv("MAX_COMMIT_HISTORY", 1000))
    REPOSITORY_BASE_PATH: str = os.getenv("REPOSITORY_BASE_PATH", "./repositories")

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
    "http://localhost:3000", 
    "http://localhost:8000", 
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000", 
    "https://rodeceview.vercel.app"
]


    # Email Configuration (for notifications)
    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", 587))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", "noreply@rodeceview.com")

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    def parse_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    class Config:
        case_sensitive = True

settings = Settings()