from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.config import Settings, get_settings
from backend.database import get_db
from backend.deps import get_client_ip, get_notifier
from backend.models.entities import Point, Review, ReviewModerationStatus, Service
from backend.notifications.base import CompositeNotifier
from backend.schemas.booking import BookingCreate, BookingCreateResult, validation_errors_from_pydantic
from backend.schemas.point import PointOut
from backend.schemas.review import ReviewOut
from backend.schemas.service import ServiceOut
from backend.services.bookings import FieldValidationError, create_booking
from backend.services.rate_limit import rate_limiter

router = APIRouter(tags=["public"])


@router.get("/points", response_model=list[PointOut])
def list_points(db: Session = Depends(get_db)) -> list[Point]:
    return list(
        db.scalars(select(Point).where(Point.is_active.is_(True)).order_by(Point.id))
    )


@router.get("/services", response_model=list[ServiceOut])
def list_services(db: Session = Depends(get_db)) -> list[Service]:
    return list(
        db.scalars(
            select(Service).where(Service.is_active.is_(True)).order_by(Service.sort_order, Service.id)
        )
    )


@router.get("/reviews", response_model=list[ReviewOut])
def list_reviews(db: Session = Depends(get_db)) -> list[Review]:
    return list(
        db.scalars(
            select(Review)
            .where(Review.status == ReviewModerationStatus.published)
            .order_by(Review.created_at.desc())
        )
    )


@router.post("/bookings", response_model=BookingCreateResult, status_code=201)
def post_booking(
    request: Request,
    body: dict,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    notifier: CompositeNotifier = Depends(get_notifier),
):
    try:
        payload = BookingCreate.model_validate(body)
    except ValidationError as exc:
        return JSONResponse(
            status_code=422,
            content={"detail": validation_errors_from_pydantic(exc)},
        )

    try:
        booking = create_booking(
            db,
            payload,
            settings=settings,
            rate_limiter=rate_limiter,
            notifier=notifier,
            client_ip=get_client_ip(request),
        )
    except FieldValidationError as exc:
        return JSONResponse(status_code=422, content={"detail": exc.errors})

    return BookingCreateResult(id=booking.id, status=booking.status)
