from __future__ import annotations

from backend.config import Settings, get_settings
from backend.notifications.base import CompositeNotifier, Notifier
from backend.notifications.console import ConsoleNotifier
from backend.notifications.email_stub import EmailStubNotifier
from backend.notifications.telegram_mock import TelegramMockNotifier

_CHANNEL_MAP = {
    "console": ConsoleNotifier,
    "email": EmailStubNotifier,
    "telegram": TelegramMockNotifier,
}


def build_notifier(settings: Settings | None = None) -> CompositeNotifier:
    settings = settings or get_settings()
    notifiers: list[Notifier] = []
    for channel in settings.notification_channel_list:
        cls = _CHANNEL_MAP.get(channel)
        if cls is None:
            continue
        notifiers.append(cls())
    if not notifiers:
        notifiers.append(ConsoleNotifier())
    return CompositeNotifier(notifiers)
