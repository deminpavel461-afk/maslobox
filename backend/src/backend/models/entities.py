from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class BookingStatus(str, enum.Enum):
    new = "new"
    confirmed = "confirmed"
    done = "done"
    canceled = "canceled"


class BookingSource(str, enum.Enum):
    landing = "landing"
    call = "call"


class ReviewModerationStatus(str, enum.Enum):
    pending = "pending"
    published = "published"
    rejected = "rejected"


booking_services = Table(
    "booking_services",
    Base.metadata,
    Column("booking_id", ForeignKey("bookings.id", ondelete="CASCADE"), primary_key=True),
    Column("service_id", ForeignKey("services.id", ondelete="CASCADE"), primary_key=True),
)


class Point(Base):
    __tablename__ = "points"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    address: Mapped[str] = mapped_column(String(255))
    # [{"days":[0..6], "open":"09:00", "close":"21:00"}] 0=Monday
    schedule: Mapped[list] = mapped_column(JSON)
    schedule_label: Mapped[str] = mapped_column(String(120))
    phone: Mapped[str] = mapped_column(String(20))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    admin_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    telegram_chat_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    bookings: Mapped[list[Booking]] = relationship(back_populates="point")
    reviews: Mapped[list[Review]] = relationship(back_populates="point")


class Service(Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    price_from: Mapped[int] = mapped_column(Integer)
    price_label: Mapped[str] = mapped_column(String(64))
    description: Mapped[str] = mapped_column(Text, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    bookings: Mapped[list[Booking]] = relationship(
        secondary=booking_services,
        back_populates="services",
    )


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    phone: Mapped[str] = mapped_column(String(16), index=True)
    car_model: Mapped[str] = mapped_column(String(120))
    desired_datetime_raw: Mapped[str | None] = mapped_column(String(255), nullable=True)
    desired_datetime: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    point_id: Mapped[int | None] = mapped_column(ForeignKey("points.id"), nullable=True, index=True)
    status: Mapped[BookingStatus] = mapped_column(
        Enum(BookingStatus), default=BookingStatus.new, index=True
    )
    source: Mapped[BookingSource] = mapped_column(Enum(BookingSource), default=BookingSource.landing)
    admin_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    consent: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    point: Mapped[Point | None] = relationship(back_populates="bookings")
    services: Mapped[list[Service]] = relationship(
        secondary=booking_services,
        back_populates="bookings",
    )


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    client_name: Mapped[str] = mapped_column(String(100))
    car_model: Mapped[str] = mapped_column(String(120))
    text: Mapped[str] = mapped_column(Text)
    point_id: Mapped[int | None] = mapped_column(ForeignKey("points.id"), nullable=True)
    status: Mapped[ReviewModerationStatus] = mapped_column(
        Enum(ReviewModerationStatus), default=ReviewModerationStatus.pending, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    point: Mapped[Point | None] = relationship(back_populates="reviews")
