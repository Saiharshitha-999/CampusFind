from pathlib import Path

from sqlalchemy.engine import URL
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_env: str = "development"
    app_name: str = "CampusFind"
    api_prefix: str = "/api/v1"
    frontend_origin: str = "http://localhost:5173"
    # DATABASE_URL remains an optional override for CI and one-off environments.
    database_url: str | None = None
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "campusfind_db"
    postgres_user: str = "campusfind_user"
    postgres_password: str = ""
    secret_key: str = "local-development-only-change-this"
    upload_dir: str = "uploads"
    max_upload_bytes: int = 5242880
    match_high_threshold: int = 75
    match_medium_threshold: int = 45
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_starttls: bool = True
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[3] / ".env",
        extra="ignore",
    )

    @property
    def sqlalchemy_url(self) -> str:
        if self.database_url:
            return self.database_url
        return URL.create(
            "postgresql+psycopg",
            username=self.postgres_user,
            password=self.postgres_password,
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_db,
        ).render_as_string(hide_password=False)

    @property
    def allowed_frontend_origins(self) -> list[str]:
        # Vite may run at either default or fallback port when another dev
        # server is already using 5173. Keep both local origins available,
        # while retaining the configured origin used for generated email links.
        origins = {self.frontend_origin.rstrip("/")}
        if self.app_env.lower() != "production":
            origins.update({"http://localhost:5173", "http://localhost:5174"})
        return sorted(origins)

settings = Settings()
if settings.app_env.lower() == "production" and settings.secret_key == "local-development-only-change-this":
    raise RuntimeError("Set a unique SECRET_KEY before starting CampusFind in production")
