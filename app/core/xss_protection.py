"""
XSS Protection Utilities

This module provides HTML sanitization for user-generated content to prevent XSS attacks.
Uses the bleach library to sanitize HTML input while allowing safe tags and attributes.
"""

import bleach
import logging
from typing import Optional, Union

logger = logging.getLogger("app.xss_protection")

# Safe HTML tags and attributes for user-generated content
SAFE_TAGS = [
    "p", "br", "strong", "em", "u", "i", "b", "ul", "ol", "li", "a", "h1", "h2", "h3", 
    "h4", "h5", "h6", "blockquote", "code", "pre", "hr", "img", "span", "div"
]

SAFE_ATTRIBUTES = {
    "a": ["href", "title", "target"],
    "img": ["src", "alt", "title", "width", "height"],
    "div": ["class", "style"],
    "span": ["class", "style"],
    "p": ["class", "style"],
    "h1": ["class", "style"],
    "h2": ["class", "style"],
    "h3": ["class", "style"],
    "h4": ["class", "style"],
    "h5": ["class", "style"],
    "h6": ["class", "style"],
    "ul": ["class", "style"],
    "ol": ["class", "style"],
    "li": ["class", "style"],
    "blockquote": ["class", "style"],
    "code": ["class", "style"],
    "pre": ["class", "style"],
}

SAFE_STYLES = [
    "color", "background-color", "font-size", "font-family", "text-align", 
    "margin", "padding", "border", "width", "height", "display", "float"
]

def sanitize_html(content: Optional[str]) -> Optional[str]:
    """
    Sanitize HTML content to prevent XSS attacks.
    
    Args:
        content: The HTML content to sanitize
        
    Returns:
        Sanitized HTML content or None if input is None
    """
    if content is None:
        return None
    
    try:
        # Strip all HTML tags first, then re-allow safe ones
        sanitized = bleach.clean(
            content,
            tags=SAFE_TAGS,
            attributes=SAFE_ATTRIBUTES,
            styles=SAFE_STYLES,
            strip=True,
            protocols=["http", "https", "mailto"]
        )
        return sanitized
    except Exception as e:
        logger.error(f"Error sanitizing HTML content: {e}")
        # If sanitization fails, return the original content but log the error
        return content

def sanitize_text(content: Optional[str]) -> Optional[str]:
    """
    Sanitize plain text content by escaping HTML entities.
    
    Args:
        content: The text content to sanitize
        
    Returns:
        Sanitized text content or None if input is None
    """
    if content is None:
        return None
    
    try:
        # Escape HTML entities for plain text
        sanitized = bleach.clean(content, tags=[], strip=True)
        return sanitized
    except Exception as e:
        logger.error(f"Error sanitizing text content: {e}")
        return content

def sanitize_user_content(content: Optional[str], content_type: str = "html") -> Optional[str]:
    """
    Sanitize user-generated content based on content type.
    
    Args:
        content: The content to sanitize
        content_type: Type of content ("html", "text", "description")
        
    Returns:
        Sanitized content
    """
    if content is None:
        return None
    
    if content_type == "html":
        return sanitize_html(content)
    elif content_type in ["text", "description", "instructions"]:
        return sanitize_text(content)
    else:
        # Default to text sanitization
        return sanitize_text(content)

# Helper function to sanitize multiple fields
def sanitize_fields(data: dict, field_map: dict) -> dict:
    """
    Sanitize multiple fields in a dictionary based on field mapping.
    
    Args:
        data: Dictionary containing fields to sanitize
        field_map: Dictionary mapping field names to content types
        
    Returns:
        Dictionary with sanitized fields
    """
    sanitized_data = data.copy()
    
    for field_name, content_type in field_map.items():
        if field_name in sanitized_data:
            sanitized_data[field_name] = sanitize_user_content(
                sanitized_data[field_name], content_type
            )
    
    return sanitized_data