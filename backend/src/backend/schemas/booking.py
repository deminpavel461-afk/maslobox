from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from backend.models.entities import BookingSource, BookingStatus
from backend.schemas.common import PaginatedMeta
from backend.schemas.point import PointOut
from backend.schemas.service import ServiceOut
from backend.services.phone import normalize_phone


class BookingCreate(BaseModel):
    name: str = Field(min_length=2, max_length=50)
    phone: str
    car_model: str = Field(min_length=1, max_length=120)
    desired_datetime: str | None = Field(default=None, max_length=255)
    comment: str | None = Field(default=None, max_length=2000)
    point_id: int | None = None
    service_ids: list[int] = Field(default_factory=list)
    consent: bool
    source: BookingSource = BookingSource.landing
    # honeypot — должно оставаться пустым
    website: str | None = Field(default="", max_length=200)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not (2 <= len(cleaned) <= 50):
            raise ValueError("Имя должно содержать от 2 до 50 символов")
        return cleaned

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        try:
            return normalize_phone(value)
        except ValueError as exc:
            raise ValueError(str(exc)) from exc

    @field_validator("car_model")
    @classmethod
    def validate_car(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Укажите марку и модель автомобиля")
        return cleaned

    @field_validator("desired_datetime")
    @classmethod
    def strip_desired(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @field_validator("comment")
    @classmethod
    def strip_comment(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @field_validator("consent")
    @classmethod
    def require_consent(cls, value: bool) -> bool:
        if value is not True:
            raise ValueError("Необходимо согласие на обработку персональных данных")
        return value


class BookingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    phone: str
    car_model: str
    desired_datetime_raw: str | None
    desired_datetime: datetime | None
    comment: str | None
    point_id: int | None
    status: BookingStatus
    source: BookingSource
    admin_comment: str | None
    created_at: datetime
    updated_at: datetime
    point: PointOut | None = None
    services: list[ServiceOut] = Field(default_factory=list)


class BookingListResponse(BaseModel):
    items: list[BookingOut]
    meta: PaginatedMeta


class AdminBookingUpdate(BaseModel):
    status: BookingStatus | None = None
    admin_comment: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def at_least_one_field(self) -> "AdminBookingUpdate":
        if self.status is None and self.admin_comment is None:
            raise ValueError("Укажите status и/или admin_comment")
        return self


class BookingCreateResult(BaseModel):
    id: int
    status: BookingStatus
    message: str = "Заявка принята. Мы перезвоним в ближайшее время."


def validation_errors_from_pydantic(exc: Any) -> list[dict[str, str]]:
    """Convert pydantic ValidationError to field/message pairs."""
    errors: list[dict[str, str]] = []
    for err in exc.errors():
        loc = err.get("loc", ())
        field = ".".join(str(part) for part in loc if part != "body") or "body"
        msg = err.get("msg", "Некорректное значение")
        if msg.startswith("Value error, "):
            msg = msg.removeprefix("Value error, ")
        lower = msg.lower()
        if (
            field in {"", "body", "__root__"}
            or field.endswith("require_consent")
            or "соглас" in lower
            or "consent" in lower
        ) and "соглас" in lower:
            field = "consent"
        if "string_too_short" in err.get("type", "") and field == "name":
            msg = "Имя должно содержать от 2 до 50 символов"
        if "string_too_short" in err.get("type", "") and field == "car_model":
            msg = "Укажите марку и модель автомобиля"
        errors.append({"field": field, "message": msg})
    return errors
