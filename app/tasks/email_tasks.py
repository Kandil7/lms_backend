import logging
import smtplib
from email.message import EmailMessage

from app.core.config import settings
from app.tasks.celery_app import celery_app

logger = logging.getLogger("app.tasks.email")
EMAIL_AUTORETRY_EXCEPTIONS = (smtplib.SMTPException, TimeoutError, OSError)


def _send_email(*, to_email: str, subject: str, body: str) -> str:
    message = EmailMessage()
    message["From"] = settings.EMAIL_FROM
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)

    if not settings.SMTP_HOST:
        log_message = f"email processed in dry-run mode for <{to_email}> with subject '{subject}'"
        logger.info(log_message)
        return log_message

    smtp_client: smtplib.SMTP | smtplib.SMTP_SSL
    if settings.SMTP_USE_SSL:
        smtp_client = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15)
    else:
        smtp_client = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15)

    with smtp_client as client:
        client.ehlo()
        if settings.SMTP_USE_TLS and not settings.SMTP_USE_SSL:
            client.starttls()
            client.ehlo()
        if settings.SMTP_USERNAME:
            client.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD or "")
        client.send_message(message)

    sent_message = f"email sent to <{to_email}> with subject '{subject}'"
    logger.info(sent_message)
    return sent_message


@celery_app.task(
    name="app.tasks.email_tasks.send_welcome_email",
    autoretry_for=EMAIL_AUTORETRY_EXCEPTIONS,
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 5},
)
def send_welcome_email(email: str, full_name: str) -> str:
    subject = "Welcome to LMS"
    body = (
        f"Hello {full_name},\n\n"
        "Welcome to LMS. Your account is ready.\n\n"
        "Best regards,\nLMS Team"
    )
    return _send_email(to_email=email, subject=subject, body=body)


@celery_app.task(
    name="app.tasks.email_tasks.send_password_reset_email",
    autoretry_for=EMAIL_AUTORETRY_EXCEPTIONS,
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 5},
)
def send_password_reset_email(email: str, full_name: str, reset_token: str, reset_url: str) -> str:
    subject = "Reset your LMS password"
    body = (
        f"Hello {full_name},\n\n"
        "We received a request to reset your password.\n"
        f"Reset link: {reset_url}\n"
        f"Token: {reset_token}\n\n"
        "If you did not request this, you can ignore this email.\n\n"
        "Best regards,\nLMS Team"
    )
    return _send_email(to_email=email, subject=subject, body=body)


@celery_app.task(
    name="app.tasks.email_tasks.send_email_verification_email",
    autoretry_for=EMAIL_AUTORETRY_EXCEPTIONS,
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 5},
)
def send_email_verification_email(email: str, full_name: str, verification_token: str, verification_url: str) -> str:
    subject = "Verify your LMS email"
    body = (
        f"Hello {full_name},\n\n"
        "Please verify your email address to activate full access.\n"
        f"Verification link: {verification_url}\n"
        f"Token: {verification_token}\n\n"
        "If you did not create this account, you can ignore this email.\n\n"
        "Best regards,\nLMS Team"
    )
    return _send_email(to_email=email, subject=subject, body=body)


@celery_app.task(
    name="app.tasks.email_tasks.send_mfa_login_code_email",
    autoretry_for=EMAIL_AUTORETRY_EXCEPTIONS,
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 5},
)
def send_mfa_login_code_email(email: str, full_name: str, code: str, expires_minutes: int) -> str:
    subject = "Your LMS login verification code"
    body = (
        f"Hello {full_name},\n\n"
        "Use the following code to complete your login:\n"
        f"{code}\n\n"
        f"This code expires in {expires_minutes} minutes.\n"
        "If this was not you, please reset your password immediately.\n\n"
        "Best regards,\nLMS Team"
    )
    return _send_email(to_email=email, subject=subject, body=body)


@celery_app.task(
    name="app.tasks.email_tasks.send_mfa_setup_code_email",
    autoretry_for=EMAIL_AUTORETRY_EXCEPTIONS,
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 5},
)
def send_mfa_setup_code_email(email: str, full_name: str, code: str, expires_minutes: int) -> str:
    subject = "Your LMS MFA setup code"
    body = (
        f"Hello {full_name},\n\n"
        "Use the following code to enable MFA on your account:\n"
        f"{code}\n\n"
        f"This code expires in {expires_minutes} minutes.\n\n"
        "Best regards,\nLMS Team"
    )
    return _send_email(to_email=email, subject=subject, body=body)
