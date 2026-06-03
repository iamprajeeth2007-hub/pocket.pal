import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # Credentials come from .env or environment; defaults kept for local dev convenience.
    SUPABASE_URL: str = "https://zgnnxujzbjohaovsfuhj.supabase.co"
    SUPABASE_ANON_KEY: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inpnbm54dWp6YmpvaGFvdnNmdWhqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzk2MjA1NzUsImV4cCI6MjA5NTE5NjU3NX0.srCWZrPVScAmd02zAJCmuypsS2aRaZGHLiW7L-kbqks"
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None

    PORT: int = 8000
    HOST: str = "0.0.0.0"
    ENV: str = "development"

    # CORS: comma-separated allowed origins e.g. "https://myapp.vercel.app,http://localhost:3000"
    ALLOWED_ORIGINS: str = "*"

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(__file__), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
