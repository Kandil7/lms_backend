"""
Firebase Service Module for LMS Backend.

This module provides integration with Firebase Admin SDK for authentication
and Firebase Cloud Functions for email sending capabilities.

Configuration (via environment variables):
- FIREBASE_ENABLED: Enable/disable Firebase integration (default: False)
- FIREBASE_PROJECT_ID: Firebase project ID
- FIREBASE_PRIVATE_KEY: Firebase service account private key
- FIREBASE_CLIENT_EMAIL: Firebase service account client email
- FIREBASE_AUTH_EMULATOR_HOST: Firebase Auth emulator host (for development)
- FIREBASE_FUNCTIONS_URL: Base URL for Firebase Cloud Functions email transport
- FIREBASE_FUNCTIONS_API_KEY: API key for Firebase Cloud Functions
"""

import logging
import os
import importlib
from datetime import datetime, UTC
from typing import Any
from urllib.parse import quote

import httpx

from app.core.config import settings

# Configure module logger
logger = logging.getLogger(__name__)

# Firebase Admin SDK imports
firebase_admin: Any = None
auth: Any = None
credentials: Any = None

try:
    firebase_admin = importlib.import_module("firebase_admin")
    auth = importlib.import_module("firebase_admin.auth")
    credentials = importlib.import_module("firebase_admin.credentials")
except ImportError:
    if settings.FIREBASE_ENABLED:
        logger.warning(
            "firebase-admin package not installed while FIREBASE_ENABLED=true"
        )
    else:
        logger.debug("firebase-admin package not installed; Firebase Auth is disabled")


class FirebaseError(Exception):
    """Base exception for Firebase-related errors."""

    def __init__(self, message: str, original_error: Exception | None = None):
        self.message = message
        self.original_error = original_error
        super().__init__(message)


class FirebaseAuthError(FirebaseError):
    """Exception raised for Firebase authentication errors."""

    def __init__(
        self,
        message: str,
        original_error: Exception | None = None,
        error_code: str | None = None,
    ):
        self.error_code = error_code
        super().__init__(message, original_error)


class FirebaseFunctionsError(FirebaseError):
    """Exception raised for Firebase Cloud Functions errors."""

    def __init__(
        self,
        message: str,
        original_error: Exception | None = None,
        status_code: int | None = None,
    ):
        self.status_code = status_code
        super().__init__(message, original_error)


class FirebaseInitializationError(FirebaseError):
    """Exception raised when Firebase fails to initialize."""

    pass


class FirebaseNotEnabledError(Exception):
    """Exception raised when Firebase is not enabled but service is accessed."""

    pass


# Global state for Firebase app
_firebase_app_initialized = False
_firebase_auth_service: "FirebaseAuthService | None" = None
_firebase_functions_service: "FirebaseFunctionsService | None" = None


def _initialize_firebase() -> bool:
    """
    Initialize Firebase Admin SDK.

    Returns:
        True if Firebase was initialized successfully, False otherwise.

    Raises:
        FirebaseInitializationError: If Firebase is enabled but fails to initialize.
    """
    global _firebase_app_initialized

    if not settings.FIREBASE_ENABLED:
        logger.debug("Firebase is disabled, skipping initialization")
        return False

    if _firebase_app_initialized:
        logger.debug("Firebase app already initialized")
        return True

    firebase_admin_module = _get_firebase_admin_module()
    credentials_module = _get_credentials_module()

    # Check for required credentials
    if not settings.FIREBASE_PROJECT_ID:
        error_msg = "FIREBASE_PROJECT_ID is required when FIREBASE_ENABLED=True"
        logger.error(error_msg)
        raise FirebaseInitializationError(error_msg)

    # Handle Firebase Auth emulator for development
    emulator_host = settings.FIREBASE_AUTH_EMULATOR_HOST
    if emulator_host:
        os.environ["FIREBASE_AUTH_EMULATOR_HOST"] = emulator_host
        logger.info(f"Firebase Auth emulator enabled: {emulator_host}")

    try:
        # Initialize credentials
        if settings.FIREBASE_PRIVATE_KEY and settings.FIREBASE_CLIENT_EMAIL:
            # Use service account credentials
            private_key = settings.FIREBASE_PRIVATE_KEY

            # Handle private key formatting (replace escaped newlines)
            if "\\n" in private_key:
                private_key = private_key.replace("\\n", "\n")

            service_account_config = {
                "type": "service_account",
                "project_id": settings.FIREBASE_PROJECT_ID,
                "private_key": private_key,
                "client_email": settings.FIREBASE_CLIENT_EMAIL,
            }

            cred = credentials_module.Certificate(service_account_config)
            logger.info(
                f"Initializing Firebase Admin SDK with service account for project: "
                f"{settings.FIREBASE_PROJECT_ID}"
            )
        else:
            # Use default credentials (e.g., from GOOGLE_APPLICATION_CREDENTIALS)
            logger.info(
                f"Initializing Firebase Admin SDK with default credentials for project: "
                f"{settings.FIREBASE_PROJECT_ID}"
            )
            cred = credentials_module.ApplicationDefault()

        # Initialize Firebase app
        firebase_admin_module.initialize_app(cred)
        _firebase_app_initialized = True
        logger.info(
            f"Firebase Admin SDK initialized successfully for project: "
            f"{settings.FIREBASE_PROJECT_ID}"
        )

        return True

    except Exception as e:
        error_msg = f"Failed to initialize Firebase Admin SDK: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise FirebaseInitializationError(error_msg, e)


def _ensure_firebase_initialized() -> None:
    """Ensure Firebase is initialized before use."""
    if not settings.FIREBASE_ENABLED:
        raise FirebaseNotEnabledError(
            "Firebase is not enabled. Set FIREBASE_ENABLED=True to use Firebase services."
        )
    if not _firebase_app_initialized:
        _initialize_firebase()


def _ensure_firebase_auth_available() -> None:
    """Ensure Firebase Auth is available."""
    if not settings.FIREBASE_ENABLED:
        raise FirebaseNotEnabledError(
            "Firebase is not enabled. Set FIREBASE_ENABLED=True to use Firebase Auth."
        )
    _get_auth_module()
    _ensure_firebase_initialized()


def _get_firebase_admin_module() -> Any:
    """Return firebase_admin module or raise an explicit initialization error."""
    if firebase_admin is None:
        raise FirebaseInitializationError(
            "Firebase Admin SDK not available. Install firebase-admin package."
        )
    return firebase_admin


def _get_credentials_module() -> Any:
    """Return firebase_admin.credentials module or raise an explicit initialization error."""
    if credentials is None:
        raise FirebaseInitializationError(
            "Firebase credentials module not available. Install firebase-admin package."
        )
    return credentials


def _get_auth_module() -> Any:
    """Return firebase_admin.auth module or raise an explicit initialization error."""
    if auth is None:
        raise FirebaseInitializationError(
            "Firebase Auth module not available. Install firebase-admin package."
        )
    return auth


def _to_iso_timestamp(value: Any) -> str | None:
    """Normalize Firebase timestamps (datetime/ms/sec) to ISO-8601."""
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC).isoformat()
        return value.isoformat()
    if isinstance(value, (int, float)):
        # Firebase metadata is commonly milliseconds since epoch.
        ts = float(value)
        if ts > 1e11:
            ts /= 1000.0
        return datetime.fromtimestamp(ts, tz=UTC).isoformat()
    return str(value)


class FirebaseAuthService:
    """
    Service for Firebase Authentication operations.

    Provides methods for:
    - Generating email verification links
    - Generating password reset links
    - Getting user information by email
    - Verifying Firebase ID tokens
    """

    def __init__(self):
        """Initialize Firebase Auth service."""
        logger.debug("FirebaseAuthService initialized")

    def generate_email_verification_link(self, email: str) -> str:
        """
        Generate an email verification link for the given email address.

        Args:
            email: The email address to send the verification link to.

        Returns:
            The generated verification link URL.

        Raises:
            FirebaseAuthError: If the link generation fails.
            FirebaseNotEnabledError: If Firebase is not enabled.
        """
        _ensure_firebase_auth_available()
        auth_module = _get_auth_module()

        logger.info(f"Generating email verification link for: {email}")

        try:
            # Check if running against emulator
            if settings.FIREBASE_AUTH_EMULATOR_HOST:
                # In emulator mode, return a mock link
                mock_link = (
                    f"http://localhost:3000/verify-email?"
                    f"emulator=true&email={quote(email)}"
                )
                logger.debug(f"Generated emulator verification link: {mock_link}")
                return mock_link

            # Generate the verification link using Firebase Admin SDK
            link = auth_module.generate_email_verification_link(email)
            logger.info(f"Successfully generated email verification link for: {email}")
            return link

        except Exception as e:
            error_msg = f"Failed to generate email verification link: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise FirebaseAuthError(
                error_msg,
                original_error=e,
                error_code="EMAIL_VERIFICATION_LINK_FAILED",
            )

    def generate_password_reset_link(self, email: str) -> str:
        """
        Generate a password reset link for the given email address.

        Args:
            email: The email address to send the password reset link to.

        Returns:
            The generated password reset link URL.

        Raises:
            FirebaseAuthError: If the link generation fails.
            FirebaseNotEnabledError: If Firebase is not enabled.
        """
        _ensure_firebase_auth_available()
        auth_module = _get_auth_module()

        logger.info(f"Generating password reset link for: {email}")

        try:
            # Check if running against emulator
            if settings.FIREBASE_AUTH_EMULATOR_HOST:
                # In emulator mode, return a mock link
                mock_link = (
                    f"http://localhost:3000/reset-password?"
                    f"emulator=true&email={quote(email)}"
                )
                logger.debug(f"Generated emulator password reset link: {mock_link}")
                return mock_link

            # Generate the password reset link using Firebase Admin SDK
            link = auth_module.generate_password_reset_link(email)
            logger.info(f"Successfully generated password reset link for: {email}")
            return link

        except Exception as e:
            error_msg = f"Failed to generate password reset link: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise FirebaseAuthError(
                error_msg,
                original_error=e,
                error_code="PASSWORD_RESET_LINK_FAILED",
            )

    def get_user_by_email(self, email: str) -> dict:
        """
        Get user information by email address.

        Args:
            email: The email address to look up.

        Returns:
            A dictionary containing user information:
            - uid: The user's unique ID
            - email: The user's email address
            - email_verified: Whether the email is verified
            - display_name: The user's display name
            - photo_url: The user's photo URL
            - disabled: Whether the user is disabled
            - metadata: Creation and last sign-in timestamps
            - provider_data: List of identity providers

        Raises:
            FirebaseAuthError: If the user is not found or lookup fails.
            FirebaseNotEnabledError: If Firebase is not enabled.
        """
        _ensure_firebase_auth_available()
        auth_module = _get_auth_module()

        logger.info(f"Looking up user by email: {email}")

        try:
            # Check if running against emulator
            if settings.FIREBASE_AUTH_EMULATOR_HOST:
                # In emulator mode, return mock user data
                mock_user = {
                    "uid": f"mock-user-{hash(email) % 10000}",
                    "email": email,
                    "email_verified": False,
                    "display_name": None,
                    "photo_url": None,
                    "disabled": False,
                    "metadata": {
                        "created_at": "2024-01-01T00:00:00Z",
                        "last_signed_in_at": None,
                    },
                    "provider_data": [],
                }
                logger.debug(f"Generated emulator user data for: {email}")
                return mock_user

            # Get user from Firebase Auth
            user = auth_module.get_user_by_email(email)

            # Convert user record to dictionary
            user_data = {
                "uid": user.uid,
                "email": user.email,
                "email_verified": user.email_verified,
                "display_name": user.display_name,
                "photo_url": user.photo_url,
                "disabled": user.disabled,
                "metadata": {
                    "created_at": _to_iso_timestamp(
                        user.user_metadata.creation_timestamp
                    ),
                    "last_signed_in_at": _to_iso_timestamp(
                        user.user_metadata.last_sign_in_timestamp
                    ),
                },
                "provider_data": [
                    {
                        "provider_id": provider.provider_id,
                        "uid": provider.uid,
                        "display_name": provider.display_name,
                        "email": provider.email,
                        "photo_url": provider.photo_url,
                    }
                    for provider in user.provider_data
                ],
            }

            logger.info(f"Successfully retrieved user data for: {email}")
            return user_data

        except Exception as e:
            error_text = str(e)
            if "not found" in error_text.lower():
                error_msg = f"User not found with email: {email}"
                logger.warning(error_msg)
                raise FirebaseAuthError(
                    error_msg,
                    original_error=e,
                    error_code="USER_NOT_FOUND",
                )

            error_msg = f"Failed to get user by email: {error_text}"
            logger.error(error_msg, exc_info=True)
            raise FirebaseAuthError(
                error_msg,
                original_error=e,
                error_code="GET_USER_FAILED",
            )

    def verify_id_token(self, id_token: str) -> dict:
        """
        Verify a Firebase ID token.

        Args:
            id_token: The Firebase ID token to verify.

        Returns:
            A dictionary containing the decoded token claims:
            - uid: The user's unique ID
            - email: The user's email address
            - email_verified: Whether the email is verified
            - auth_time: Authentication timestamp
            - iat: Token issuance timestamp
            - exp: Token expiration timestamp
            - Other custom claims

        Raises:
            FirebaseAuthError: If the token is invalid or expired.
            FirebaseNotEnabledError: If Firebase is not enabled.
        """
        _ensure_firebase_auth_available()
        auth_module = _get_auth_module()

        logger.debug("Verifying Firebase ID token")

        try:
            # Check if running against emulator
            if settings.FIREBASE_AUTH_EMULATOR_HOST:
                # In emulator mode, return mock decoded token
                mock_decoded = {
                    "uid": "mock-user-12345",
                    "email": "test@example.com",
                    "email_verified": True,
                    "auth_time": 1704067200,
                    "iat": 1704067200,
                    "exp": 1704153600,
                    "iss": f"https://securetoken.google.com/{settings.FIREBASE_PROJECT_ID}",
                    "aud": settings.FIREBASE_PROJECT_ID,
                    "sub": "mock-user-12345",
                }
                logger.debug("Returning emulator ID token verification result")
                return mock_decoded

            # Verify the ID token
            decoded_token = auth_module.verify_id_token(id_token)

            logger.info(
                f"Successfully verified ID token for user: {decoded_token.get('uid')}"
            )
            return decoded_token

        except Exception as e:
            error_text = str(e)
            lowered = error_text.lower()
            if "expired" in lowered:
                error_msg = "Firebase ID token has expired"
                logger.warning(error_msg)
                raise FirebaseAuthError(
                    error_msg,
                    original_error=e,
                    error_code="TOKEN_EXPIRED",
                )
            if "invalid" in lowered:
                error_msg = f"Invalid Firebase ID token: {error_text}"
                logger.warning(error_msg)
                raise FirebaseAuthError(
                    error_msg,
                    original_error=e,
                    error_code="INVALID_TOKEN",
                )

            error_msg = f"Failed to verify ID token: {error_text}"
            logger.error(error_msg, exc_info=True)
            raise FirebaseAuthError(
                error_msg,
                original_error=e,
                error_code="VERIFY_TOKEN_FAILED",
            )

    def create_custom_token(
        self, uid: str, additional_claims: dict | None = None
    ) -> str:
        """
        Create a custom Firebase token for the given user UID.

        This can be used to authenticate with Firebase from a backend service.

        Args:
            uid: The user's unique ID.
            additional_claims: Optional custom claims to include in the token.

        Returns:
            The generated custom token string.

        Raises:
            FirebaseAuthError: If token creation fails.
            FirebaseNotEnabledError: If Firebase is not enabled.
        """
        _ensure_firebase_auth_available()
        auth_module = _get_auth_module()

        logger.info(f"Creating custom token for user: {uid}")

        try:
            custom_token = auth_module.create_custom_token(uid, additional_claims)
            # Convert bytes to string if needed
            token_str = (
                custom_token.decode("utf-8")
                if isinstance(custom_token, bytes)
                else custom_token
            )
            logger.info(f"Successfully created custom token for user: {uid}")
            return token_str

        except Exception as e:
            error_msg = f"Failed to create custom token: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise FirebaseAuthError(
                error_msg,
                original_error=e,
                error_code="CREATE_CUSTOM_TOKEN_FAILED",
            )


class FirebaseFunctionsService:
    """
    Service for calling Firebase Cloud Functions.

    Provides methods for invoking Firebase Cloud Functions, particularly
    for sending emails via a deployed function.
    """

    def __init__(self):
        """Initialize Firebase Functions service."""
        self._base_url = settings.FIREBASE_FUNCTIONS_URL
        self._api_key = settings.FIREBASE_FUNCTIONS_API_KEY
        self._timeout = 30  # seconds

        if self._base_url:
            # Ensure base URL doesn't have trailing slash
            self._base_url = self._base_url.rstrip("/")

        logger.debug(
            f"FirebaseFunctionsService initialized with base URL: {self._base_url}"
        )

    def _get_headers(self) -> dict[str, str]:
        """Get headers for Firebase Functions API requests."""
        headers = {
            "Content-Type": "application/json",
        }

        if self._api_key:
            headers["X-API-Key"] = self._api_key

        return headers

    def send_email_via_function(
        self,
        to_email: str,
        subject: str,
        body: str,
        template: str | None = None,
    ) -> dict:
        """
        Send an email using Firebase Cloud Functions.

        Calls the /sendEmail endpoint of the configured Firebase Functions URL.

        Args:
            to_email: Recipient email address.
            subject: Email subject.
            body: Email body content.
            template: Optional template name to use for the email.

        Returns:
            A dictionary containing the response from the Cloud Function:
            - success: Whether the email was sent successfully
            - message_id: Optional message ID if available
            - response: Full response from the function

        Raises:
            FirebaseFunctionsError: If the function call fails.
        """
        if not self._base_url:
            raise FirebaseFunctionsError(
                "FIREBASE_FUNCTIONS_URL is not configured. "
                "Set FIREBASE_FUNCTIONS_URL to use Firebase Functions for email."
            )

        logger.info(f"Sending email via Firebase Functions to: {to_email}")

        # Prepare the request payload
        payload = {
            "to": to_email,
            "subject": subject,
            "body": body,
        }

        if template:
            payload["template"] = template

        # Build the full URL
        url = f"{self._base_url}/sendEmail"

        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.post(
                    url,
                    json=payload,
                    headers=self._get_headers(),
                )
                response.raise_for_status()
                result = response.json() if response.content else {}

            logger.info(
                f"Successfully sent email via Firebase Functions to: {to_email}"
            )
            return {
                "success": True,
                "message_id": result.get("messageId") or result.get("message_id"),
                "response": result,
            }

        except httpx.HTTPStatusError as e:
            error_msg = f"Failed to send email via Firebase Functions: {str(e)}"
            logger.error(error_msg, exc_info=True)

            raise FirebaseFunctionsError(
                error_msg,
                original_error=e,
                status_code=e.response.status_code,
            )
        except httpx.RequestError as e:
            error_msg = f"Failed to send email via Firebase Functions: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise FirebaseFunctionsError(
                error_msg,
                original_error=e,
            )

        except Exception as e:
            error_msg = f"Unexpected error calling Firebase Functions: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise FirebaseFunctionsError(error_msg, original_error=e)

    def call_function(
        self,
        function_name: str,
        method: str = "POST",
        data: dict | None = None,
    ) -> dict:
        """
        Call a generic Firebase Cloud Function.

        Args:
            function_name: Name of the Cloud Function to call (without leading slash).
            method: HTTP method to use (GET, POST, PUT, DELETE).
            data: Optional data to send with the request.

        Returns:
            A dictionary containing the response from the Cloud Function.

        Raises:
            FirebaseFunctionsError: If the function call fails.
        """
        if not self._base_url:
            raise FirebaseFunctionsError("FIREBASE_FUNCTIONS_URL is not configured.")

        logger.info(f"Calling Firebase Cloud Function: {function_name} ({method})")

        # Build the full URL
        url = f"{self._base_url}/{function_name.lstrip('/')}"

        try:
            method_upper = method.upper()
            if method_upper not in {"GET", "POST", "PUT", "DELETE"}:
                raise FirebaseFunctionsError(f"Unsupported HTTP method: {method}")

            request_kwargs: dict[str, Any] = {
                "headers": self._get_headers(),
            }
            if method_upper == "GET":
                request_kwargs["params"] = data
            elif data is not None:
                request_kwargs["json"] = data

            with httpx.Client(timeout=self._timeout) as client:
                response = client.request(method_upper, url, **request_kwargs)
                response.raise_for_status()
                result = response.json() if response.content else {}

            logger.info(f"Successfully called Cloud Function: {function_name}")
            return result

        except httpx.HTTPStatusError as e:
            error_msg = f"Failed to call Firebase Cloud Function: {str(e)}"
            logger.error(error_msg, exc_info=True)

            raise FirebaseFunctionsError(
                error_msg,
                original_error=e,
                status_code=e.response.status_code,
            )
        except httpx.RequestError as e:
            error_msg = f"Failed to call Firebase Cloud Function: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise FirebaseFunctionsError(
                error_msg,
                original_error=e,
            )


def get_firebase_auth_service() -> FirebaseAuthService | None:
    """
    Get the Firebase Auth service instance.

    Returns:
        FirebaseAuthService instance if Firebase is enabled, None otherwise.

    Note:
        The service will attempt to initialize Firebase on first use.
    """
    global _firebase_auth_service

    if not settings.FIREBASE_ENABLED:
        logger.debug("Firebase not enabled, returning None for auth service")
        return None

    if _firebase_auth_service is None:
        _firebase_auth_service = FirebaseAuthService()

    return _firebase_auth_service


def get_firebase_functions_service() -> FirebaseFunctionsService | None:
    """
    Get the Firebase Functions service instance.

    Returns:
        FirebaseFunctionsService instance if FIREBASE_FUNCTIONS_URL is configured,
        None otherwise.
    """
    global _firebase_functions_service

    if not settings.FIREBASE_FUNCTIONS_URL:
        logger.debug("Firebase Functions URL not set, returning None for functions service")
        return None

    if _firebase_functions_service is None:
        _firebase_functions_service = FirebaseFunctionsService()

    return _firebase_functions_service


def initialize_firebase_on_startup() -> bool:
    """
    Initialize Firebase during application startup.

    This function should be called during application startup to ensure
    Firebase is properly initialized before handling requests.

    Returns:
        True if Firebase was initialized successfully or is not enabled,
        False if Firebase is enabled but failed to initialize.
    """
    if not settings.FIREBASE_ENABLED:
        logger.info("Firebase is disabled, skipping initialization")
        return True

    try:
        _initialize_firebase()
        logger.info("Firebase initialized successfully during startup")
        return True
    except FirebaseInitializationError as e:
        logger.error(f"Failed to initialize Firebase during startup: {e.message}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during Firebase initialization: {str(e)}")
        return False


def is_firebase_enabled() -> bool:
    """
    Check if Firebase is enabled and configured.

    Returns:
        True if Firebase is enabled, False otherwise.
    """
    return settings.FIREBASE_ENABLED


def get_firebase_project_id() -> str | None:
    """
    Get the configured Firebase project ID.

    Returns:
        Firebase project ID if configured, None otherwise.
    """
    return settings.FIREBASE_PROJECT_ID


def is_firebase_initialized() -> bool:
    """
    Check if Firebase Admin SDK has been initialized.

    Returns:
        True if Firebase is initialized, False otherwise.
    """
    return _firebase_app_initialized
