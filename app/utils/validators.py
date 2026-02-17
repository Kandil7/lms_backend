import re
from pathlib import Path


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9\s-]", "", value)
    value = re.sub(r"[\s-]+", "-", value)
    return value.strip("-")


def ensure_allowed_extension(filename: str, allowed_extensions: list[str]) -> str:
    ext = Path(filename).suffix.lower().lstrip(".")
    if ext not in allowed_extensions:
        raise ValueError(f"File extension '.{ext}' is not allowed")
    return ext
