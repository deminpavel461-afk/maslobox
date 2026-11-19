from __future__ import annotations

import logging

from backend.notifications.base import NotificationPayload

logger = logging.getLogger("maslobox.notifications.console")


class ConsoleNotifier:
    name = "console"

    def __init__(self) -> None:
        self.messages: list[str] = []

    def notify_new_booking(self, payload: NotificationPayload) -> None:
        message = (
            f"[NEW BOOKING #{payload.booking_id}] {payload.name} {payload.phone} | "
            f"{payload.car_model} | точка: {payload.point_name or 'не указана'} | "
            f"время: {payload.desired_datetime_raw or '—'} | "
            f"коммент: {payload.comment or '—'}"
        )
        self.messages.append(message)
        logger.info(message)
        print(message, flush=True)
