from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(slots=True)
class NotificationPayload:
    booking_id: int
    name: str
    phone: str
    car_model: str
    point_name: str | None
    desired_datetime_raw: str | None
    comment: str | None
    admin_email: str | None = None
    telegram_chat_id: str | None = None


class Notifier(Protocol):
    name: str

    def notify_new_booking(self, payload: NotificationPayload) -> None: ...


class CompositeNotifier:
    name = "composite"

    def __init__(self, notifiers: list[Notifier]) -> None:
        self._notifiers = notifiers
        self.sent: list[tuple[str, NotificationPayload]] = []

    def notify_new_booking(self, payload: NotificationPayload) -> None:
        for notifier in self._notifiers:
            notifier.notify_new_booking(payload)
            self.sent.append((notifier.name, payload))
