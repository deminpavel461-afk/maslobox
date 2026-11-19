from __future__ import annotations

from datetime import datetime

from backend.deps import get_notifier
from backend.services.datetime_parse import MOSCOW


def test_list_points(client):
    response = client.get("/api/v1/points")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert {p["slug"] for p in data} == {"north", "center", "south"}
    assert data[0]["schedule_label"]


def test_list_services(client):
    response = client.get("/api/v1/services")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5
    assert data[0]["price_label"].startswith("от")


def test_list_reviews_only_published(client):
    response = client.get("/api/v1/reviews")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 4
    assert all(item["client_name"] != "Скрытый" for item in data)


def test_create_booking_ok(client):
    points = client.get("/api/v1/points").json()
    services = client.get("/api/v1/services").json()
    response = client.post(
        "/api/v1/bookings",
        json={
            "name": "Алексей",
            "phone": "8 (912) 345-67-89",
            "car_model": "Kia Rio 2019",
            "desired_datetime": "как удобно",
            "comment": "Нужен Castrol",
            "point_id": points[0]["id"],
            "service_ids": [services[0]["id"]],
            "consent": True,
        },
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["id"] > 0
    assert body["status"] == "new"

    notifier = get_notifier()
    assert len(notifier.sent) >= 1


def test_create_booking_validation_errors(client):
    response = client.post(
        "/api/v1/bookings",
        json={
            "name": "А",
            "phone": "123",
            "car_model": "",
            "consent": False,
        },
    )
    assert response.status_code == 422
    detail = response.json()["detail"]
    fields = {item["field"] for item in detail}
    assert "name" in fields or any("name" in f for f in fields)
    assert "phone" in fields
    assert "car_model" in fields
    assert "consent" in fields
    assert all("message" in item for item in detail)


def test_create_booking_outside_hours(client):
    points = {p["slug"]: p for p in client.get("/api/v1/points").json()}
    west = points["center"]
    # Sunday — west (МаслоТочка · Запад) is closed
    sunday = datetime(2026, 11, 22, 12, 0, tzinfo=MOSCOW)
    response = client.post(
        "/api/v1/bookings",
        json={
            "name": "Иван Иванов",
            "phone": "+79120001122",
            "car_model": "VW Polo",
            "desired_datetime": sunday.strftime("%Y-%m-%d %H:%M"),
            "point_id": west["id"],
            "consent": True,
        },
    )
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert any(item["field"] == "desired_datetime" for item in detail)


def test_create_booking_unparsed_time_saved(client):
    response = client.post(
        "/api/v1/bookings",
        json={
            "name": "Пётр",
            "phone": "89120003344",
            "car_model": "Toyota Camry",
            "desired_datetime": "когда получится на днях",
            "consent": True,
        },
    )
    assert response.status_code == 201, response.text


def test_honeypot_does_not_persist(client, db_session):
    from sqlalchemy import func, select

    from backend.models.entities import Booking

    before = db_session.scalar(select(func.count()).select_from(Booking)) or 0
    response = client.post(
        "/api/v1/bookings",
        json={
            "name": "Bot",
            "phone": "89120005566",
            "car_model": "Spam Car",
            "consent": True,
            "website": "http://spam.test",
        },
    )
    assert response.status_code == 201
    after = db_session.scalar(select(func.count()).select_from(Booking)) or 0
    assert after == before


def test_rate_limit_by_phone(client):
    payload = {
        "name": "Лимит",
        "phone": "89121112233",
        "car_model": "Kia Rio",
        "consent": True,
    }
    for _ in range(3):
        assert client.post("/api/v1/bookings", json=payload).status_code == 201
    response = client.post("/api/v1/bookings", json=payload)
    assert response.status_code == 422
    assert any(item["field"] == "phone" for item in response.json()["detail"])
