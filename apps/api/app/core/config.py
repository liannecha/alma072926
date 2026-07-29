import os
from pathlib import Path
from typing import Any

from dotenv import dotenv_values
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict


def parse_cors_origins(value: Any) -> list[str]:
    if isinstance(value, str):
        return [origin.strip() for origin in value.split(",") if origin.strip()]
    if isinstance(value, list):
        return [str(origin).strip() for origin in value if str(origin).strip()]
    return ["http://localhost:3000"]


class CustomSettingsSource:
    def __init__(self, settings_cls: type[BaseSettings]) -> None:
        self.settings_cls = settings_cls

    def __call__(self) -> dict[str, Any]:
        env_values: dict[str, str | None] = {}
        env_file = Path(__file__).resolve().parents[2] / ".env"
        if env_file.exists():
            env_values.update(dotenv_values(env_file))

        for key, value in os.environ.items():
            env_values[key] = value

        data: dict[str, Any] = {}
        for field_name in self.settings_cls.model_fields:
            env_name = field_name.upper()
            if env_name in env_values and env_values[env_name] is not None:
                if field_name == "cors_origins":
                    data[field_name] = parse_cors_origins(env_values[env_name])
                else:
                    data[field_name] = env_values[env_name]
        return data


class Settings(BaseSettings):
    app_name: str = "Alma Lead Intake API"
    environment: str = "development"
    cors_origins: list[str] = ["http://localhost:3000"]
    database_url: str = "sqlite:///./alma_leads.db"
    resume_storage_dir: str = "./storage/resumes"
    internal_auth_token: str = "change-me"
    google_client_id: str = ""
    internal_allowed_emails: str = ""
    internal_allowed_email_domain: str = ""
    internal_notification_email: str = "lianne.cha@gmail.com"
    email_provider: str = "console"
    email_from: str = "no-reply@example.com"
    resend_api_key: str = ""
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (init_settings, CustomSettingsSource(settings_cls), file_secret_settings)


settings = Settings()
