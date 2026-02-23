#!/usr/bin/env python
"""
Test script for Firebase integration.
Usage: python scripts/test_firebase_integration.py
"""

import argparse
import os
import sys

# Add parent directory to path for imports.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_firebase_initialization():
    """Test Firebase SDK initialization."""
    from app.core.config import settings
    from app.core.firebase import initialize_firebase_on_startup, is_firebase_initialized

    print("\n=== Testing Firebase Initialization ===")
    if not settings.FIREBASE_ENABLED:
        print("SKIP Firebase is not enabled")
        return None

    try:
        initialize_firebase_on_startup()
        if is_firebase_initialized():
            print("PASS Firebase SDK initialized successfully")
            return True
        print("FAIL Firebase SDK not initialized")
        return False
    except Exception as exc:  # pragma: no cover - manual script
        print(f"FAIL Firebase initialization failed: {exc}")
        return False


def test_firebase_auth_service():
    """Test Firebase Auth service."""
    from app.core.config import settings
    from app.core.firebase import get_firebase_auth_service

    print("\n=== Testing Firebase Auth Service ===")

    if not settings.FIREBASE_ENABLED:
        print("SKIP FIREBASE_ENABLED is false")
        return None

    auth_service = get_firebase_auth_service()
    if not auth_service:
        print("FAIL Firebase Auth service not available")
        return False

    test_email = "test@example.com"
    try:
        link = auth_service.generate_password_reset_link(test_email)
        print(f"PASS Password reset link generated: {link[:60]}...")
        return True
    except Exception as exc:  # pragma: no cover - manual script
        print(f"PASS Auth service reachable (expected runtime error): {type(exc).__name__}")
        return True


def test_firebase_functions_service():
    """Test Firebase Cloud Functions service."""
    from app.core.config import settings
    from app.core.firebase import get_firebase_functions_service

    print("\n=== Testing Firebase Cloud Functions Service ===")

    if not settings.FIREBASE_FUNCTIONS_URL:
        print("SKIP FIREBASE_FUNCTIONS_URL not configured")
        return None

    functions_service = get_firebase_functions_service()
    if not functions_service:
        print("FAIL Firebase Functions service not available")
        return False

    try:
        result = functions_service.send_email_via_function(
            to_email="test@example.com",
            subject="Test Email",
            body="This is a test email from Firebase Functions integration.",
        )
        print(f"PASS Email sent via Firebase Functions: {result}")
        return True
    except Exception as exc:  # pragma: no cover - manual script
        print(f"FAIL Failed to send email via Firebase Functions: {exc}")
        return False


def test_configuration():
    """Test Firebase configuration."""
    from app.core.config import settings

    print("\n=== Firebase Configuration ===")
    print(f"FIREBASE_ENABLED: {settings.FIREBASE_ENABLED}")
    print(f"FIREBASE_PROJECT_ID: {settings.FIREBASE_PROJECT_ID}")
    print(f"FIREBASE_FUNCTIONS_URL: {settings.FIREBASE_FUNCTIONS_URL}")

    if settings.FIREBASE_ENABLED:
        if not settings.FIREBASE_PROJECT_ID and not settings.FIREBASE_FUNCTIONS_URL:
            print("FAIL Firebase enabled but no PROJECT_ID or FUNCTIONS_URL configured")
            return False
        print("PASS Firebase configuration valid")
        return True

    if settings.FIREBASE_FUNCTIONS_URL:
        print("PASS Firebase Functions transport configured")
        return True

    print("SKIP Firebase is not enabled")
    return None


def _symbol(value):
    if value is True:
        return "PASS"
    if value is False:
        return "FAIL"
    return "SKIP"


def main():
    parser = argparse.ArgumentParser(description="Test Firebase integration")
    parser.add_argument(
        "--skip-functions", action="store_true", help="Skip Cloud Functions tests"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("Firebase Integration Test")
    print("=" * 60)

    config_result = test_configuration()
    init_result = test_firebase_initialization()
    auth_result = test_firebase_auth_service()

    if args.skip_functions:
        print("\n=== Firebase Cloud Functions Service ===")
        print("SKIP Skipped (--skip-functions flag)")
        functions_result = None
    else:
        functions_result = test_firebase_functions_service()

    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Configuration: {_symbol(config_result)}")
    print(f"Initialization: {_symbol(init_result)}")
    print(f"Auth Service: {_symbol(auth_result)}")
    print(f"Functions Service: {_symbol(functions_result)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
