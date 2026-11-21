import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    APP_NAME: str = "SocialPlus.ai"
    APP_ENV: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "127.0.0.1"

    # Database
    DATABASE_URL: str = "sqlite:///./socialplus.db"

    # YouTube API
    YOUTUBE_API_KEY: Optional[str] = None

    # Meta Graph API (Instagram & Facebook)
    META_APP_ID: Optional[str] = None
    META_APP_SECRET: Optional[str] = None
    META_REDIRECT_URI: str = "http://localhost:8000/auth/meta/callback"
    META_API_VERSION: str = "v20.0"

    # AI/NLP
    MODEL_NAME: str = "local-multilingual-ensemble"
    MAX_COMMENTS_DEFAULT: int = 500
    MAX_UPLOAD_SIZE_MB: int = 25

    # Directory Paths
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    UPLOADS_DIR: str = os.path.join(BASE_DIR, "uploads")
    REPORTS_DIR: str = os.path.join(BASE_DIR, "reports")
    FRONTEND_DIR: str = os.path.join(BASE_DIR, "frontend")

    @property
    def is_youtube_configured(self) -> bool:
        return bool(self.YOUTUBE_API_KEY and self.YOUTUBE_API_KEY.strip() and not self.YOUTUBE_API_KEY.startswith("YOUR_"))

    @property
    def is_meta_configured(self) -> bool:
        return bool(
            self.META_APP_ID and not self.META_APP_ID.startswith("YOUR_") and
            self.META_APP_SECRET and not self.META_APP_SECRET.startswith("YOUR_")
        )


settings = Settings()
os.makedirs(settings.UPLOADS_DIR, exist_ok=True)
os.makedirs(settings.REPORTS_DIR, exist_ok=True)
