from __future__ import annotations

import logging

from backend.notifications.base import NotificationPayload

logger = logging.getLogger("maslobox.notifications.email")


class EmailStubNotifier:
    """Fake email sender — logs intended message, no network I/O."""

    name = "email"

    def __init__(self) -> None:
        self.outbox: list[dict] = []

    def notify_new_booking(self, payload: NotificationPayload) -> None:
        to = payload.admin_email or "admin@maslobox.local"
        subject = f"Новая заявка #{payload.booking_id} — МаслоБокс"
        body = (
            f"Клиент: {payload.name}\n"
            f"Телефон: {payload.phone}\n"
            f"Авто: {payload.car_model}\n"
            f"Точка: {payload.point_name or 'не указана'}\n"
            f"Желаемое время: {payload.desired_datetime_raw or '—'}\n"
            f"Комментарий: {payload.comment or '—'}\n"
        )
        mail = {"to": to, "subject": subject, "body": body}
        self.outbox.append(mail)
        logger.info("EMAIL STUB to=%s subject=%s", to, subject)
