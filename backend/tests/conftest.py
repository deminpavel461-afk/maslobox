from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["ADMIN_TOKEN"] = "test-admin-token"
os.environ["ADMIN_POINT_TOKENS"] = '{"north-token":"north","center-token":"center","south-token":"south"}'
os.environ["NOTIFICATION_CHANNELS"] = "console,email,telegram"
os.environ["RATE_LIMIT_PHONE_MAX"] = "3"
os.environ["RATE_LIMIT_PHONE_WINDOW_SECONDS"] = "600"
os.environ["RATE_LIMIT_IP_MAX"] = "5"
os.environ["RATE_LIMIT_IP_WINDOW_SECONDS"] = "600"

from backend import database
from backend.config import get_settings
from backend.deps import reset_notifier
from backend.main import create_app
from backend.notifications.factory import build_notifier
from backend.services.rate_limit import rate_limiter


@pytest.fixture()
def notifier():
    get_settings.cache_clear()
    return reset_notifier(build_notifier(get_settings()))


@pytest.fixture()
def client(notifier):
    get_settings.cache_clear()
    database.reset_engine("sqlite:///:memory:")
    rate_limiter.clear()
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def db_session(client) -> Session:
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()
