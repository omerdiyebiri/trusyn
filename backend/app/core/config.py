from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Trusyn"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "YOUR_SUPER_SECRET_KEY_CHANGE_THIS" # In production, use a secure env var
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8 # 8 days
    DATABASE_URL: Optional[str] = "sqlite+aiosqlite:///./trusyn.db"
    REDIS_URL: Optional[str] = "redis://localhost:6379/0"

    # SMTP Settings
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = 587
    SMTP_HOST: Optional[str] = "smtp.gmail.com"
    SMTP_USER: Optional[str] = "takedowns@trusyn.io"
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = "takedowns@trusyn.io"
    EMAILS_FROM_NAME: Optional[str] = "Trusyn Brand Protection"

    # IMAP Settings (For tracking replies)
    IMAP_HOST: str = "imap.gmail.com"
    IMAP_PORT: int = 993
    IMAP_USER: str = "takedowns@trusyn.io"
    IMAP_PASSWORD: Optional[str] = None # Same as SMTP password usually

    # External threat intel APIs
    URLSCAN_API_KEY: Optional[str] = None
    ABUSE_CH_AUTH_KEY: Optional[str] = None  # used by ThreatFox / URLhaus
    URLSCAN_VISIBILITY: str = "public"  # public | unlisted | private
    # Google PageSpeed Insights — used as a screenshot fallback when our
    # Playwright probe lands on a Cloudflare challenge page. Optional;
    # works without a key at low rate (~25 req/day shared pool).
    GOOGLE_PAGESPEED_API_KEY: Optional[str] = None

    # Cloudflare Abuse Reports API — primary takedown channel for
    # CF-fronted phishing. Submitting via API uses the same triage
    # pipeline as the web form but skips Turnstile (Bearer auth).
    # Email to abuse@cloudflare.com is documented as decorative; CF
    # auto-bounces it back to the form. We keep the audit Report row
    # but the actual dispatch goes through these endpoints.
    CF_API_EMAIL: Optional[str] = None
    CF_API_KEY: Optional[str] = None  # Global API Key (legacy auth)
    CF_API_TOKEN: Optional[str] = None  # Modern Bearer token
    CF_ACCOUNT_ID: Optional[str] = None

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        extra="ignore"
    )

settings = Settings()
