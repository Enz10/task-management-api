import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Settings definitions - required from environment
    PROJECT_NAME: str
    API_V1_STR: str

    # Database settings loaded from environment - required
    DATABASE_URL: str

    # JWT Settings loaded from environment - required
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    class Config:
        case_sensitive = True


settings = Settings()

if settings.DATABASE_URL is None:
    print("Warning: DATABASE_URL is not set in the environment variables or .env file.")
    # You might want to raise an error or provide a default fallback for local dev
    # raise ValueError("DATABASE_URL not set")
else:
    from urllib.parse import urlparse, urlunparse
    parsed_url = urlparse(settings.DATABASE_URL)
    if parsed_url.password:
        safe_url = parsed_url._replace(netloc=f"{parsed_url.username}:*****@{parsed_url.hostname}:{parsed_url.port}")
        print(f"Database URL loaded: {urlunparse(safe_url)}")
    else:
        print(f"Database URL loaded: {settings.DATABASE_URL}")
