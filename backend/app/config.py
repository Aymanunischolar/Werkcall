"""Central configuration. Free-tier provider limits live here so they can be
re-checked in one place before any cost claim is published (see blueprint §4)."""
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: str = "development"
    log_level: str = "INFO"

    # Voice provider selection: gemini_live (free-first default) | openai_realtime (optional paid) | mock (tests/offline demo)
    voice_provider: str = "mock"
    gemini_api_key: str | None = None
    gemini_live_model: str = "gemini-live-2.5-flash-preview"
    openai_api_key: str | None = None
    openai_realtime_model: str = "gpt-4o-realtime-preview"

    # Supabase
    supabase_url: str | None = None
    supabase_service_role_key: str | None = None
    supabase_anon_key: str | None = None

    # Google Calendar
    google_oauth_client_id: str | None = None
    google_oauth_client_secret: str | None = None
    google_calendar_id: str = "primary"

    # HubSpot
    hubspot_private_app_token: str | None = None

    # Gmail
    gmail_sender_address: str | None = None

    # n8n
    n8n_webhook_base_url: str | None = None
    n8n_webhook_signing_secret: str | None = None

    # Twilio (optional telephone adapter)
    twilio_account_sid: str | None = None
    twilio_auth_token: str | None = None
    twilio_trial_number: str | None = None

    # Security
    allowed_origins: str = "http://localhost:5173"
    session_rate_limit_per_minute: int = 20
    demo_data_retention_days: int = 7
    store_raw_audio: bool = False

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
