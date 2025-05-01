import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load .env file from the project root (one level up from 'api')
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
load_dotenv(dotenv_path=dotenv_path)

class Settings(BaseSettings):
    PROJECT_NAME: str = "Task Manager API"
    API_V1_STR: str = "/api/v1"

    # Database settings loaded from .env file
    DATABASE_URL: str | None = os.getenv("DATABASE_URL")

    # JWT Settings (replace with strong, unique secrets in production)
    SECRET_KEY: str = "YOUR_VERY_SECRET_KEY_CHANGE_THIS" # KEEP SECRET
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        case_sensitive = True
        # If you want to load directly from a .env file using BaseSettings (alternative):
        # env_file = "../../../.env" # Relative path from this file to .env
        # env_file_encoding = 'utf-8'


settings = Settings()

# Simple check to ensure DATABASE_URL is loaded
if settings.DATABASE_URL is None:
    print("Warning: DATABASE_URL is not set in the environment variables or .env file.")
    # You might want to raise an error or provide a default fallback for local dev
    # raise ValueError("DATABASE_URL not set")
else:
    # Mask password for printing
    from urllib.parse import urlparse, urlunparse
    parsed_url = urlparse(settings.DATABASE_URL)
    if parsed_url.password:
        safe_url = parsed_url._replace(netloc=f"{parsed_url.username}:*****@{parsed_url.hostname}:{parsed_url.port}")
        print(f"Database URL loaded: {urlunparse(safe_url)}")
    else:
        print(f"Database URL loaded: {settings.DATABASE_URL}")
