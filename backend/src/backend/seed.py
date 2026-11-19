from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models.entities import Point, Review, ReviewModerationStatus, Service


def weekdays_full(open_t: str, close_t: str) -> list[dict]:
    return [{"days": [0, 1, 2, 3, 4, 5, 6], "open": open_t, "close": close_t}]


def weekdays_mon_sat(open_t: str, close_t: str) -> list[dict]:
    return [{"days": [0, 1, 2, 3, 4, 5], "open": open_t, "close": close_t}]


POINTS = [
    {
        "slug": "south",
        "name": "МаслоТочка · Юг",
        "address": "ул. Каширское шоссе, 61к1",
        "schedule": weekdays_full("09:00", "21:00"),
        "schedule_label": "Пн–Вс 9:00–21:00",
        "phone": "+74951203001",
        "admin_email": "south@maslotocheka.ru",
        "telegram_chat_id": "tg-south",
    },
    {
        "slug": "north",
        "name": "МаслоТочка · Север",
        "address": "ул. Дмитровское шоссе, 107",
        "schedule": weekdays_full("09:00", "21:00"),
        "schedule_label": "Пн–Вс 9:00–21:00",
        "phone": "+74951203002",
        "admin_email": "north@maslotocheka.ru",
        "telegram_chat_id": "tg-north",
    },
    {
        "slug": "center",
        "name": "МаслоТочка · Запад",
        "address": "Кутузовский проспект, 36",
        "schedule": weekdays_mon_sat("09:00", "20:00"),
        "schedule_label": "Пн–Сб 9:00–20:00",
        "phone": "+74951203003",
        "admin_email": "west@maslotocheka.ru",
        "telegram_chat_id": "tg-west",
    },
]

SERVICES = [
    {
        "slug": "engine-oil",
        "name": "Замена масла ДВС + фильтр",
        "price_from": 1490,
        "price_label": "от 1 490 ₽",
        "description": "Слив, замена фильтра, заливка по регламенту производителя.",
        "sort_order": 1,
    },
    {
        "slug": "atf",
        "name": "Замена масла АКПП",
        "price_from": 2900,
        "price_label": "от 2 900 ₽",
        "description": "Частичная или аппаратная замена масла АКПП.",
        "sort_order": 2,
    },
    {
        "slug": "psf",
        "name": "Замена масла ГУР",
        "price_from": 1200,
        "price_label": "от 1 200 ₽",
        "description": "Замена жидкости гидроусилителя руля с проверкой уровня.",
        "sort_order": 3,
    },
    {
        "slug": "brake-fluid",
        "name": "Замена тормозной жидкости",
        "price_from": 1800,
        "price_label": "от 1 800 ₽",
        "description": "Прокачка контура и замена тормозной жидкости.",
        "sort_order": 4,
    },
    {
        "slug": "flush",
        "name": "Промывка масляной системы",
        "price_from": 990,
        "price_label": "от 990 ₽",
        "description": "Промывка перед заменой масла при сильных загрязнениях.",
        "sort_order": 5,
    },
]

POINT_FIELDS = (
    "name",
    "address",
    "schedule",
    "schedule_label",
    "phone",
    "admin_email",
    "telegram_chat_id",
)

SERVICE_FIELDS = (
    "name",
    "price_from",
    "price_label",
    "description",
    "sort_order",
)


def _upsert_points(db: Session) -> dict[str, Point]:
    existing = {p.slug: p for p in db.scalars(select(Point)).all()}
    by_slug: dict[str, Point] = {}
    for data in POINTS:
        point = existing.get(data["slug"])
        if point is None:
            point = Point(**data, is_active=True)
            db.add(point)
        else:
            for field in POINT_FIELDS:
                setattr(point, field, data[field])
            point.is_active = True
        by_slug[data["slug"]] = point
    db.flush()
    return by_slug


def _upsert_services(db: Session) -> None:
    existing = {s.slug: s for s in db.scalars(select(Service)).all()}
    for data in SERVICES:
        service = existing.get(data["slug"])
        if service is None:
            db.add(Service(**data, is_active=True))
        else:
            for field in SERVICE_FIELDS:
                setattr(service, field, data[field])
            service.is_active = True
    db.flush()


def _seed_reviews_if_empty(db: Session, by_slug: dict[str, Point]) -> None:
    if db.scalar(select(Review.id).limit(1)) is not None:
        return

    reviews = [
        Review(
            client_name="Алексей М.",
            car_model="Киа Sportage",
            text="Сделали за 25 минут, масло подобрали по VIN. Диагностику ходовой правда сделали бесплатно.",
            point_id=by_slug["south"].id,
            status=ReviewModerationStatus.published,
        ),
        Review(
            client_name="Марина К.",
            car_model="VW Polo",
            text="Чистый бокс, всё по чеку. Вернули старый фильтр — приятно, что без уговоров.",
            point_id=by_slug["north"].id,
            status=ReviewModerationStatus.published,
        ),
        Review(
            client_name="Игорь С.",
            car_model="Toyota Camry",
            text="Езжу уже третий раз. Цены как на сайте, очередь живая, но ждал недолго.",
            point_id=by_slug["center"].id,
            status=ReviewModerationStatus.published,
        ),
        Review(
            client_name="Ольга В.",
            car_model="Hyundai Creta",
            text="Записалась онлайн, приехала к нужному слоту. Мастера вежливые, объяснили по регламенту.",
            point_id=by_slug["south"].id,
            status=ReviewModerationStatus.published,
        ),
        Review(
            client_name="Скрытый",
            car_model="Test",
            text="Не должен отображаться на сайте",
            point_id=by_slug["north"].id,
            status=ReviewModerationStatus.pending,
        ),
    ]
    db.add_all(reviews)


def seed_if_empty(db: Session) -> None:
    """Backward-compatible entrypoint: sync catalog and seed reviews once. """
    sync_catalog(db)


def sync_catalog(db: Session) -> None:
    """Create or update points/services to match the landing content."""
    by_slug = _upsert_points(db)
    _upsert_services(db)
    _seed_reviews_if_empty(db, by_slug)
    db.commit()
