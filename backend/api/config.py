from pydantic_settings import BaseSettings
from typing import Optional, List
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # PROJECT_NAME: str = "DocMind"
    # API_V1_STR: str = "/api/v1"
    # FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:8501")
    
    #Database Configuration
    POSTGRES_USER: str = os.getenv("POSTGRES_USER")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", 5432))

    DATABASE_URL: str = (
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
        f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )

    GROBID_HOST: str = os.getenv("GROBID_HOST", "localhost")
    GROBID_PORT: int = int(os.getenv("GROBID_PORT", 8070))
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
        
    class Config:
        env_file = ".env"
        case_sensitive = True
        env_file_encoding = 'utf-8'
        extra = "allow"

settings = Settings()