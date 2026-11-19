import re


def normalize_phone(raw: str) -> str:
    """Normalize RU phone to +7XXXXXXXXXX."""
    if raw is None or not str(raw).strip():
        raise ValueError("Укажите телефон")

    digits = re.sub(r"\D", "", str(raw))
    if not digits:
        raise ValueError("Укажите корректный российский телефон")

    if len(digits) == 11 and digits.startswith("8"):
        digits = "7" + digits[1:]
    elif len(digits) == 10:
        digits = "7" + digits
    elif len(digits) == 11 and digits.startswith("7"):
        pass
    else:
        raise ValueError("Укажите корректный российский телефон в формате +7XXXXXXXXXX")

    if len(digits) != 11 or not digits.startswith("7"):
        raise ValueError("Укажите корректный российский телефон в формате +7XXXXXXXXXX")

    return f"+{digits}"
