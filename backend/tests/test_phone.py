import pytest

from backend.services.phone import normalize_phone


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("8 (912) 345-67-89", "+79123456789"),
        ("89123456789", "+79123456789"),
        ("+7 912 345 67 89", "+79123456789"),
        ("79123456789", "+79123456789"),
        ("9123456789", "+79123456789"),
    ],
)
def test_normalize_phone_ok(raw, expected):
    assert normalize_phone(raw) == expected


@pytest.mark.parametrize("raw", ["", "123", "12345", "+1 202 555 0100", "abc"])
def test_normalize_phone_bad(raw):
    with pytest.raises(ValueError):
        normalize_phone(raw)
