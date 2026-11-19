from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "sqlite:///./maslobox.db"
    admin_token: str = "change-me-admin-token"
    # token -> point slug; point admins only see their bookings
    admin_point_tokens: dict[str, str] = Field(
        default_factory=lambda: {
            "north-token": "north",
            "center-token": "center",
            "south-token": "south",
        }
    )
    notification_channels: str = "console,email,telegram"
    rate_limit_phone_max: int = 3
    rate_limit_phone_window_seconds: int = 600
    rate_limit_ip_max: int = 5
    rate_limit_ip_window_seconds: int = 600
    cors_origins: list[str] = Field(default_factory=lambda: ["*"])

    @property
    def notification_channel_list(self) -> list[str]:
        return [item.strip().lower() for item in self.notification_channels.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
