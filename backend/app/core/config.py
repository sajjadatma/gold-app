import warnings
from pathlib import Path
from typing import Literal, Self

from pydantic import (
    EmailStr,
    HttpUrl,
    PostgresDsn,
    computed_field,
    field_validator,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Use top level .env file (one level above ./backend/)
        env_file="../.env",
        env_ignore_empty=True,
        extra="ignore",
    )
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str
    # 60 minutes * 24 hours * 8 days = 8 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    FRONTEND_HOST: str = "http://localhost:5173"
    FASTAPI_ENV: Literal["development"] | None = None

    PROJECT_NAME: str
    SENTRY_DSN: HttpUrl | None = None
    DATABASE_URL: PostgresDsn

    # Background jobs (arq). Eager mode keeps tests and local demos deterministic.
    REDIS_URL: str = "redis://localhost:6379"
    TASKS_EAGER: bool = True

    # Storage
    STORAGE_BACKEND: Literal["local", "s3"] = "local"
    STORAGE_LOCAL_DIR: str = str(
        Path(__file__).resolve().parents[2] / "storage"
    )
    S3_ENDPOINT_URL: str | None = None
    S3_BUCKET: str | None = None
    S3_ACCESS_KEY_ID: str | None = None
    S3_SECRET_ACCESS_KEY: str | None = None
    S3_REGION: str = "us-east-1"

    # AI providers. Fake by default; missing credentials never block work.
    AI_PROVIDER: Literal["fake", "openai"] = "fake"
    AI_API_BASE: str = "https://api.openai.com/v1"
    AI_API_KEY: str | None = None
    AI_TEXT_MODEL: str = "gpt-4.1-mini"
    AI_VISION_MODEL: str = "gpt-4.1-mini"
    AI_IMAGE_MODEL: str = "gpt-image-1"

    # Instagram
    INSTAGRAM_PROVIDER: Literal["fake", "graph"] = "fake"
    INSTAGRAM_GRAPH_BASE: str = "https://graph.facebook.com/v21.0"

    # Upload limits (bytes / counts)
    MAX_PDF_BYTES: int = 50 * 1024 * 1024
    MAX_IMAGE_BYTES: int = 25 * 1024 * 1024
    MAX_FONT_BYTES: int = 20 * 1024 * 1024
    MAX_DESIGN_SOURCE_BYTES: int = 150 * 1024 * 1024
    MAX_ZIP_BYTES: int = 250 * 1024 * 1024
    MAX_ARCHIVE_FILES: int = 500
    MAX_UPLOAD_FILES: int = 100
    MAX_ARCHIVE_EXPANDED_BYTES: int = 500 * 1024 * 1024
    MAX_IMAGE_PIXELS: int = 80_000_000

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def _use_psycopg_driver(cls, value: str | PostgresDsn) -> str:
        database_url = str(value)
        for scheme in ("postgres://", "postgresql://"):
            if database_url.startswith(scheme):
                return database_url.replace(scheme, "postgresql+psycopg://", 1)
        return database_url

    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    SMTP_PORT: int = 587
    SMTP_HOST: str | None = None
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    EMAILS_FROM_EMAIL: EmailStr | None = None
    EMAILS_FROM_NAME: str | None = None

    @model_validator(mode="after")
    def _set_default_emails_from(self) -> Self:
        if not self.EMAILS_FROM_NAME:
            self.EMAILS_FROM_NAME = self.PROJECT_NAME
        return self

    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int = 48

    @computed_field  # type: ignore[prop-decorator]
    @property
    def emails_enabled(self) -> bool:
        return bool(self.SMTP_HOST and self.EMAILS_FROM_EMAIL)

    EMAIL_TEST_USER: EmailStr = "test@example.com"
    FIRST_SUPERUSER: EmailStr
    FIRST_SUPERUSER_PASSWORD: str

    def _check_default_secret(self, var_name: str, value: str | None) -> None:
        if value == "changethis":
            message = (
                f'The value of {var_name} is "changethis", '
                "for security, please change it, at least for deployments."
            )
            if self.FASTAPI_ENV == "development":
                warnings.warn(message, stacklevel=1)
            else:
                raise ValueError(message)

    @model_validator(mode="after")
    def _enforce_non_default_secrets(self) -> Self:
        self._check_default_secret("SECRET_KEY", self.SECRET_KEY)
        for host in self.DATABASE_URL.hosts():
            self._check_default_secret("DATABASE_URL password", host["password"])
        self._check_default_secret(
            "FIRST_SUPERUSER_PASSWORD", self.FIRST_SUPERUSER_PASSWORD
        )

        return self


settings = Settings()  # type: ignore # ty: ignore[unused-ignore-comment]
