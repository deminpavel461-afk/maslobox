from __future__ import annotations

import logging

from backend.notifications.base import NotificationPayload

logger = logging.getLogger("maslobox.notifications.telegram")


class TelegramMockNotifier:
    """Mock Telegram bot — stores messages instead of calling Telegram API."""

    name = "telegram"

    def __init__(self) -> None:
        self.messages: list[dict] = []

    def notify_new_booking(self, payload: NotificationPayload) -> None:
        chat_id = payload.telegram_chat_id or "mock-admin-chat"
        text = (
            f"🛢 Новая заявка #{payload.booking_id}\n"
            f"{payload.name} · {payload.phone}\n"
            f"{payload.car_model}\n"
            f"Точка: {payload.point_name or 'не указана'}\n"
            f"Время: {payload.desired_datetime_raw or '—'}"
        )
        message = {"chat_id": chat_id, "text": text, "booking_id": payload.booking_id}
        self.messages.append(message)
        logger.info("TELEGRAM MOCK chat_id=%s booking_id=%s", chat_id, payload.booking_id)
