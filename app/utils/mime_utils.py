import importlib
import mimetypes
from typing import Protocol, cast


class _MagicModule(Protocol):
    def from_buffer(self, buffer: bytes, *, mime: bool = False) -> str: ...


def _load_magic_module() -> _MagicModule | None:
    """Load python-magic dynamically so static analysis doesn't require local install."""
    try:
        module = importlib.import_module("magic")
        return cast(_MagicModule, module)
    except Exception:
        return None


_MAGIC = _load_magic_module()

def detect_mime_type_from_content(content: bytes) -> tuple[str, str]:
    """
    Detect MIME type from file content using libmagic (file signature analysis).
    
    Args:
        content: File content as bytes
        
    Returns:
        Tuple of (mime_type, extension)
    """
    try:
        # Use python-magic for accurate MIME type detection when available.
        if _MAGIC is None:
            raise RuntimeError("python-magic is unavailable")
        mime_type = _MAGIC.from_buffer(content, mime=True)

        extension = mimetypes.guess_extension(mime_type) or ""
        if extension.startswith("."):
            extension = extension[1:]

        return mime_type, extension
    except Exception:
        return "application/octet-stream", "bin"


def validate_file_content_type(content: bytes, expected_extension: str, allowed_extensions: list[str]) -> bool:
    """
    Validate file content against expected extension and allowed extensions.
    
    Args:
        content: File content as bytes
        expected_extension: Extension from filename
        allowed_extensions: List of allowed extensions
        
    Returns:
        bool: True if valid, False if invalid
    """
    try:
        # Detect MIME type from content
        mime_type, detected_extension = detect_mime_type_from_content(content)
        expected_extension = expected_extension.lower()
        normalized_allowed = [ext.lower() for ext in allowed_extensions]

        # If libmagic is unavailable we get a generic fallback; keep extension-only validation.
        is_generic_detection = mime_type == "application/octet-stream" and detected_extension == "bin"
        if is_generic_detection:
            return expected_extension in normalized_allowed
        
        # Check if detected extension matches expected extension
        if expected_extension and detected_extension and expected_extension != detected_extension.lower():
            # Allow some common mismatches (e.g., .jpg vs .jpeg)
            if not _is_extension_mismatch_allowed(expected_extension, detected_extension):
                return False
        
        # Check if MIME type is allowed based on extensions
        if not _is_mime_type_allowed(mime_type, normalized_allowed):
            return False
            
        return True
    except Exception:
        # If detection fails, fall back to extension-only validation
        return expected_extension.lower() in [ext.lower() for ext in allowed_extensions]


def _is_extension_mismatch_allowed(ext1: str, ext2: str) -> bool:
    """Check if extension mismatch is acceptable."""
    # Common acceptable mismatches
    acceptable_pairs = [
        ("jpg", "jpeg"),
        ("jpeg", "jpg"),
        ("png", "PNG"),
        ("pdf", "PDF"),
        ("doc", "docx"),
        ("docx", "doc"),
    ]
    return (ext1.lower(), ext2.lower()) in acceptable_pairs or (ext2.lower(), ext1.lower()) in acceptable_pairs


def _is_mime_type_allowed(mime_type: str, allowed_extensions: list[str]) -> bool:
    """Check if MIME type is allowed based on allowed extensions."""
    # Map common MIME types to extensions
    mime_to_ext = {
        "image/jpeg": ["jpg", "jpeg"],
        "image/png": ["png"],
        "image/gif": ["gif"],
        "video/mp4": ["mp4"],
        "video/avi": ["avi"],
        "video/mov": ["mov"],
        "application/pdf": ["pdf"],
        "application/msword": ["doc"],
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ["docx"],
        "text/plain": ["txt"],
        "application/octet-stream": ["bin"],
    }

    normalized_allowed = {ext.lower() for ext in allowed_extensions}
    normalized_mime = mime_type.lower()

    # Exact mapping first.
    detected_extensions = mime_to_ext.get(normalized_mime, [])
    if any(ext in normalized_allowed for ext in detected_extensions):
        return True

    # Pattern fallback with explicit extension allow-list checks.
    if normalized_mime.startswith("image/"):
        return bool({"jpg", "jpeg", "png", "gif"} & normalized_allowed)
    if normalized_mime.startswith("video/"):
        return bool({"mp4", "avi", "mov"} & normalized_allowed)
    if normalized_mime.startswith("application/"):
        return bool({"pdf", "doc", "docx", "bin"} & normalized_allowed)

    return False
