"""
Log Redaction Utilities

This module provides automatic redaction of PII (Personally Identifiable Information) 
from log messages to comply with privacy regulations.
"""

import re
import logging
import json
from typing import Optional, Union, Dict, Any

logger = logging.getLogger("app.log_redaction")

# Patterns for PII redaction
EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
PHONE_PATTERN = re.compile(r'\b(?:\+?1[-.\s]?)?\(?[2-9]\d{2}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b')
SSN_PATTERN = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')
CREDIT_CARD_PATTERN = re.compile(r'\b(?:\d{4}[-.\s]?){3}\d{4}\b')
PASSWORD_PATTERN = re.compile(r'(?:password|passwd|pwd|secret|token|api_key|auth_token)\s*[:=]\s*[\'"]?[^\'"\s]+', re.IGNORECASE)
PII_FIELDS = [
    'email', 'phone', 'telephone', 'mobile', 'ssn', 'social_security_number',
    'credit_card', 'card_number', 'password', 'passwd', 'pwd', 'secret', 'token',
    'api_key', 'auth_token', 'access_token', 'refresh_token', 'jwt', 'session_id'
]

def redact_pii(text: str) -> str:
    """
    Redact PII from text using regex patterns.
    
    Args:
        text: The text to redact
        
    Returns:
        Redacted text with PII replaced by [REDACTED]
    """
    if not text:
        return text
    
    # Redact email addresses
    text = EMAIL_PATTERN.sub('[REDACTED_EMAIL]', text)
    
    # Redact phone numbers
    text = PHONE_PATTERN.sub('[REDACTED_PHONE]', text)
    
    # Redact SSNs
    text = SSN_PATTERN.sub('[REDACTED_SSN]', text)
    
    # Redact credit card numbers
    text = CREDIT_CARD_PATTERN.sub('[REDACTED_CREDIT_CARD]', text)
    
    # Redact passwords and secrets
    text = PASSWORD_PATTERN.sub(r'\1: [REDACTED_SECRET]', text)
    
    return text

def redact_dict(data: Union[Dict[str, Any], str]) -> Union[Dict[str, Any], str]:
    """
    Redact PII from dictionary or JSON string.
    
    Args:
        data: Dictionary or JSON string to redact
        
    Returns:
        Redacted dictionary or string
    """
    if isinstance(data, str):
        try:
            # Try to parse as JSON
            parsed = json.loads(data)
            if isinstance(parsed, dict):
                return _redact_dict_recursive(parsed)
            else:
                return redact_pii(data)
        except json.JSONDecodeError:
            # Not valid JSON, treat as plain text
            return redact_pii(data)
    
    elif isinstance(data, dict):
        return _redact_dict_recursive(data)
    
    return data

def _redact_dict_recursive(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively redact PII from dictionary.
    """
    redacted = {}
    
    for key, value in data.items():
        # Redact keys that contain PII patterns
        redacted_key = key
        for pii_field in PII_FIELDS:
            if pii_field.lower() in key.lower():
                redacted_key = f"{key}_REDACTED"
                break
        
        # Redact values
        if isinstance(value, str):
            redacted_value = redact_pii(value)
        elif isinstance(value, dict):
            redacted_value = _redact_dict_recursive(value)
        elif isinstance(value, list):
            redacted_value = [_redact_dict_recursive(item) if isinstance(item, dict) else item for item in value]
        else:
            redacted_value = value
            
        redacted[redacted_key] = redacted_value
    
    return redacted

class PIIRedactingFilter(logging.Filter):
    """
    Logging filter that redacts PII from log records.
    """
    def __init__(self, name: str = ""):
        super().__init__(name)
        
    def filter(self, record: logging.LogRecord) -> bool:
        """Filter log records by redacting PII."""
        try:
            # Redact message
            if hasattr(record, 'msg') and record.msg:
                record.msg = redact_pii(str(record.msg))
            
            # Redact extra data
            if hasattr(record, 'extra') and record.extra:
                record.extra = redact_dict(record.extra)
                
            # Redact args
            if hasattr(record, 'args') and record.args:
                record.args = tuple(redact_pii(str(arg)) if isinstance(arg, str) else arg for arg in record.args)
                
        except Exception as e:
            logger.error(f"Error in PII redaction filter: {e}")
            
        return True

# Global redaction filter instance
pii_redaction_filter = PIIRedactingFilter()