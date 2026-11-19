from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from backend.config import Settings, get_settings
from backend.database import get_db
from backend.notifications.base import CompositeNotifier
from backend.notifications.factory import build_notifier

_notifier: CompositeNotifier | None = None


def get_notifier() -> CompositeNotifier:
    global _notifier
    if _notifier is None:
        _notifier = build_notifier()
    return _notifier


def reset_notifier(notifier: CompositeNotifier | None = None) -> CompositeNotifier:
    global _notifier
    _notifier = notifier or build_notifier()
    return _notifier


@dataclass(slots=True)
class AdminPrincipal:
    is_superadmin: bool
    point_slug: str | None = None


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def require_admin(
    authorization: str | None = Header(default=None),
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
    settings: Settings = Depends(get_settings),
) -> AdminPrincipal:
    token = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    elif x_admin_token:
        token = x_admin_token.strip()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется токен администратора",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if token == settings.admin_token:
        return AdminPrincipal(is_superadmin=True)

    point_slug = settings.admin_point_tokens.get(token)
    if point_slug:
        return AdminPrincipal(is_superadmin=False, point_slug=point_slug)

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Неверный токен администратора",
        headers={"WWW-Authenticate": "Bearer"},
    )


DbSession = Session
DbDep = Depends(get_db)
