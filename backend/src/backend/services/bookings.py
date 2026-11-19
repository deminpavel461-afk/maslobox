from __future__ import annotations

from datetime import date, datetime, time, timezone

from fastapi import HTTPException
from starlette import status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from backend.config import Settings
from backend.deps import AdminPrincipal
from backend.models.entities import (
    Booking,
    BookingSource,
    BookingStatus,
    Point,
    Service,
)
from backend.notifications.base import NotificationPayload, Notifier
from backend.schemas.booking import AdminBookingUpdate, BookingCreate
from backend.services.datetime_parse import is_within_schedule, parse_desired_datetime
from backend.services.rate_limit import RateLimiter


class FieldValidationError(Exception):
    def __init__(self, errors: list[dict[str, str]]) -> None:
        self.errors = errors
        super().__init__("validation failed")


def create_booking(
    db: Session,
    payload: BookingCreate,
    *,
    settings: Settings,
    rate_limiter: RateLimiter,
    notifier: Notifier,
    client_ip: str,
) -> Booking:
    # honeypot: pretend success without persisting
    if payload.website:
        fake = Booking(
            id=0,
            name=payload.name,
            phone=payload.phone,
            car_model=payload.car_model,
            desired_datetime_raw=payload.desired_datetime,
            status=BookingStatus.new,
            source=payload.source,
            consent=True,
        )
        return fake

    errors: list[dict[str, str]] = []

    if not rate_limiter.hit(
        f"phone:{payload.phone}",
        limit=settings.rate_limit_phone_max,
        window_seconds=settings.rate_limit_phone_window_seconds,
    ):
        errors.append(
            {
                "field": "phone",
                "message": "Слишком много заявок с этого номера. Попробуйте позже.",
            }
        )

    if not rate_limiter.hit(
        f"ip:{client_ip}",
        limit=settings.rate_limit_ip_max,
        window_seconds=settings.rate_limit_ip_window_seconds,
    ):
        errors.append(
            {
                "field": "body",
                "message": "Слишком много заявок с вашего адреса. Попробуйте позже.",
            }
        )

    point: Point | None = None
    if payload.point_id is not None:
        point = db.get(Point, payload.point_id)
        if point is None or not point.is_active:
            errors.append({"field": "point_id", "message": "Выбранная точка недоступна"})

    services: list[Service] = []
    if payload.service_ids:
        services = list(
            db.scalars(
                select(Service).where(
                    Service.id.in_(payload.service_ids),
                    Service.is_active.is_(True),
                )
            )
        )
        found = {s.id for s in services}
        missing = [sid for sid in payload.service_ids if sid not in found]
        if missing:
            errors.append(
                {
                    "field": "service_ids",
                    "message": f"Неизвестные услуги: {', '.join(map(str, missing))}",
                }
            )

    desired_dt = parse_desired_datetime(payload.desired_datetime)
    if desired_dt is not None and point is not None:
        if not is_within_schedule(desired_dt, point.schedule):
            errors.append(
                {
                    "field": "desired_datetime",
                    "message": (
                        f"Выбранное время вне режима работы точки «{point.name}» "
                        f"({point.schedule_label})"
                    ),
                }
            )

    if errors:
        raise FieldValidationError(errors)

    booking = Booking(
        name=payload.name,
        phone=payload.phone,
        car_model=payload.car_model,
        desired_datetime_raw=payload.desired_datetime,
        desired_datetime=desired_dt,
        comment=payload.comment,
        point_id=point.id if point else None,
        status=BookingStatus.new,
        source=payload.source or BookingSource.landing,
        consent=True,
        services=services,
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    booking = db.scalar(
        select(Booking)
        .options(selectinload(Booking.point), selectinload(Booking.services))
        .where(Booking.id == booking.id)
    )

    notifier.notify_new_booking(
        NotificationPayload(
            booking_id=booking.id,
            name=booking.name,
            phone=booking.phone,
            car_model=booking.car_model,
            point_name=booking.point.name if booking.point else None,
            desired_datetime_raw=booking.desired_datetime_raw,
            comment=booking.comment,
            admin_email=booking.point.admin_email if booking.point else None,
            telegram_chat_id=booking.point.telegram_chat_id if booking.point else None,
        )
    )
    return booking


def list_bookings(
    db: Session,
    admin: AdminPrincipal,
    *,
    point_id: int | None = None,
    status_filter: BookingStatus | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    q: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Booking], int]:
    query = select(Booking).options(selectinload(Booking.point), selectinload(Booking.services))

    if not admin.is_superadmin:
        point = db.scalar(select(Point).where(Point.slug == admin.point_slug))
        if point is None:
            return [], 0
        query = query.where(Booking.point_id == point.id)
    elif point_id is not None:
        query = query.where(Booking.point_id == point_id)

    if status_filter is not None:
        query = query.where(Booking.status == status_filter)

    if date_from is not None:
        start = datetime.combine(date_from, time.min, tzinfo=timezone.utc)
        query = query.where(Booking.created_at >= start)
    if date_to is not None:
        end = datetime.combine(date_to, time.max, tzinfo=timezone.utc)
        query = query.where(Booking.created_at <= end)

    if q:
        like = f"%{q.strip()}%"
        query = query.where(or_(Booking.name.ilike(like), Booking.phone.ilike(like)))

    count_query = select(func.count()).select_from(query.order_by(None).subquery())
    total = db.scalar(count_query) or 0

    items = list(
        db.scalars(
            query.order_by(Booking.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    )
    return items, total


ALLOWED_TRANSITIONS: dict[BookingStatus, set[BookingStatus]] = {
    BookingStatus.new: {BookingStatus.confirmed, BookingStatus.canceled},
    BookingStatus.confirmed: {BookingStatus.done, BookingStatus.canceled},
    BookingStatus.done: set(),
    BookingStatus.canceled: set(),
}


def update_booking(
    db: Session,
    admin: AdminPrincipal,
    booking_id: int,
    payload: AdminBookingUpdate,
) -> Booking:
    booking = db.scalar(
        select(Booking)
        .options(selectinload(Booking.point), selectinload(Booking.services))
        .where(Booking.id == booking_id)
    )
    if booking is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Заявка не найдена")

    if not admin.is_superadmin:
        point = db.scalar(select(Point).where(Point.slug == admin.point_slug))
        if point is None or booking.point_id != point.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Заявка не найдена")

    if payload.status is not None and payload.status != booking.status:
        allowed = ALLOWED_TRANSITIONS.get(booking.status, set())
        if payload.status not in allowed:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=[
                    {
                        "field": "status",
                        "message": (
                            f"Нельзя сменить статус {booking.status.value} → {payload.status.value}. "
                            f"Допустимо: {', '.join(s.value for s in allowed) or 'нет'}"
                        ),
                    }
                ],
            )
        booking.status = payload.status

    if payload.admin_comment is not None:
        booking.admin_comment = payload.admin_comment.strip() or None

    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking
