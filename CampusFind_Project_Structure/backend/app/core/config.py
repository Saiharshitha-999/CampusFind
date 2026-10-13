from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "CampusFind"
    api_prefix: str = "/api/v1"
    frontend_origin: str = "http://localhost:5173"
    database_url: str = "postgresql+psycopg://campusfind_user:change_me@localhost:5432/campusfind"
    secret_key: str = "local-development-only-change-this"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
