from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):  # type: ignore[misc]
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )
    SECRET_KEY: str = Field(..., min_length=32)
    APP_NAME: str
    DATABASE_URL: str
    TEST_DATABASE_URL: str
    DEBUG: bool
    LOG_LEVEL: str
    LOG_FILE: str | None = None


settings = Settings()
