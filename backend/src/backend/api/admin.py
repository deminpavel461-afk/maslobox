from __future__ import annotations

import math
from datetime import date

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.deps import AdminPrincipal, require_admin
from backend.models.entities import BookingStatus
from backend.schemas.booking import (
    AdminBookingUpdate,
    BookingListResponse,
    BookingOut,
    validation_errors_from_pydantic,
)
from backend.schemas.common import PaginatedMeta
from backend.services.bookings import list_bookings, update_booking

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/bookings", response_model=BookingListResponse)
def admin_list_bookings(
    point_id: int | None = None,
    status: BookingStatus | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    q: str | None = Query(default=None, description="Поиск по имени или телефону"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: AdminPrincipal = Depends(require_admin),
) -> BookingListResponse:
    items, total = list_bookings(
        db,
        admin,
        point_id=point_id,
        status_filter=status,
        date_from=date_from,
        date_to=date_to,
        q=q,
        page=page,
        page_size=page_size,
    )
    pages = math.ceil(total / page_size) if page_size else 0
    return BookingListResponse(
        items=[BookingOut.model_validate(item) for item in items],
        meta=PaginatedMeta(page=page, page_size=page_size, total=total, pages=pages),
    )


@router.patch("/bookings/{booking_id}", response_model=BookingOut)
def admin_patch_booking(
    booking_id: int,
    body: dict,
    db: Session = Depends(get_db),
    admin: AdminPrincipal = Depends(require_admin),
):
    try:
        payload = AdminBookingUpdate.model_validate(body)
    except ValidationError as exc:
        return JSONResponse(
            status_code=422,
            content={"detail": validation_errors_from_pydantic(exc)},
        )

    booking = update_booking(db, admin, booking_id, payload)
    return BookingOut.model_validate(booking)
