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
        "slug": "north",
        "name": "Север",
        "address": "ул. Ленина, 48",
        "schedule": weekdays_full("09:00", "21:00"),
        "schedule_label": "Пн–Вс 9:00–21:00",
        "phone": "+74951204501",
        "admin_email": "north@maslobox.ru",
        "telegram_chat_id": "tg-north",
    },
    {
        "slug": "center",
        "name": "Центр",
        "address": "пр. Мира, 112",
        "schedule": weekdays_full("08:00", "22:00"),
        "schedule_label": "Пн–Вс 8:00–22:00",
        "phone": "+74951204502",
        "admin_email": "center@maslobox.ru",
        "telegram_chat_id": "tg-center",
    },
    {
        "slug": "south",
        "name": "Юг",
        "address": "ул. Садовая, 7",
        "schedule": weekdays_mon_sat("09:00", "20:00"),
        "schedule_label": "Пн–Сб 9:00–20:00",
        "phone": "+74951204503",
        "admin_email": "south@maslobox.ru",
        "telegram_chat_id": "tg-south",
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
        "price_from": 2990,
        "price_label": "от 2 990 ₽",
        "description": "Частичная или аппаратная замена масла АКПП.",
        "sort_order": 2,
    },
    {
        "slug": "psf",
        "name": "Замена жидкости ГУР",
        "price_from": 1890,
        "price_label": "от 1 890 ₽",
        "description": "Замена жидкости гидроусилителя руля.",
        "sort_order": 3,
    },
    {
        "slug": "brake-fluid",
        "name": "Замена тормозной жидкости",
        "price_from": 1690,
        "price_label": "от 1 690 ₽",
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


def seed_if_empty(db: Session) -> None:
    if db.scalar(select(Point.id).limit(1)) is not None:
        return

    points = [Point(**data, is_active=True) for data in POINTS]
    db.add_all(points)
    db.flush()

    services = [Service(**data, is_active=True) for data in SERVICES]
    db.add_all(services)
    db.flush()

    by_slug = {p.slug: p for p in points}
    reviews = [
        Review(
            client_name="Андрей К.",
            car_model="Toyota Camry",
            text="Заехал без записи — через 25 минут уже уехал. Масло Castrol, фильтр оригинал. Рекомендую точку на Мира.",
            point_id=by_slug["center"].id,
            status=ReviewModerationStatus.published,
        ),
        Review(
            client_name="Мария С.",
            car_model="Kia Rio",
            text="Прозрачные цены, показали старый фильтр. Диагностику ходовой сделали бесплатно — нашли люфт.",
            point_id=by_slug["north"].id,
            status=ReviewModerationStatus.published,
        ),
        Review(
            client_name="Игорь В.",
            car_model="VW Tiguan",
            text="Меняю масло здесь уже третий раз. Всегда по регламенту, чек и рекомендации на руках.",
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
    db.commit()
