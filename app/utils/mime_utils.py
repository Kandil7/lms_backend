import mimetypes
import magic
from typing import Optional, Tuple

def detect_mime_type_from_content(content: bytes) -> Tuple[str, str]:
    """
    Detect MIME type from file content using libmagic (file signature analysis).
    
    Args:
        content: File content as bytes
        
    Returns:
        Tuple of (mime_type, extension)
    """
    try:
        # Use python-magic for accurate MIME type detection
        mime_type = magic.from_buffer(content, mime=True)
        
        # Get extension from MIME type
        extension = mimetypes.guess_extension(mime_type) or ""
        if extension.startswith("."):
            extension = extension[1:]
            
        return mime_type, extension
    except Exception:
        # Fallback to basic detection
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
        
        # Check if detected extension matches expected extension
        if expected_extension and detected_extension and expected_extension.lower() != detected_extension.lower():
            # Allow some common mismatches (e.g., .jpg vs .jpeg)
            if not _is_extension_mismatch_allowed(expected_extension, detected_extension):
                return False
        
        # Check if MIME type is allowed based on extensions
        if not _is_mime_type_allowed(mime_type, allowed_extensions):
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
    
    # Check if MIME type matches any allowed extension
    for allowed_ext in allowed_extensions:
        if mime_type in mime_to_ext.get(allowed_ext, []):
            return True
    
    # Check if MIME type starts with common patterns
    if any(mime_type.startswith(prefix) for prefix in ["image/", "video/", "application/"]):
        # For security, only allow if the extension is explicitly allowed
        return any(
            mime_type.startswith("image/") and "jpg" in allowed_extensions or "jpeg" in allowed_extensions or "png" in allowed_extensions,
            mime_type.startswith("video/") and "mp4" in allowed_extensions or "avi" in allowed_extensions or "mov" in allowed_extensions,
            mime_type.startswith("application/") and "pdf" in allowed_extensions or "doc" in allowed_extensions or "docx" in allowed_extensions,
        )
    
    return False