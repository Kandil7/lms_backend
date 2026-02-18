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


def normalize_storage_folder(folder: str) -> str:
    value = (folder or "").strip().replace("\\", "/")
    if not value:
        return "uploads"

    if value.startswith("/"):
        raise ValueError("Invalid folder path")

    raw_parts = [part for part in value.split("/") if part and part != "."]
    if not raw_parts:
        return "uploads"

    safe_parts: list[str] = []
    for part in raw_parts:
        if part == "..":
            raise ValueError("Invalid folder path")
        if not re.fullmatch(r"[A-Za-z0-9_-]+", part):
            raise ValueError("Folder path contains unsupported characters")
        safe_parts.append(part)

    return "/".join(safe_parts)
