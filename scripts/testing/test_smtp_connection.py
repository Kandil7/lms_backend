import argparse
import os
import smtplib
from email.message import EmailMessage


def _as_bool(value: str, *, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify SMTP connectivity and optionally send a test email.")
    parser.add_argument("--to", help="Recipient email for an optional test message.")
    parser.add_argument("--subject", default="LMS SMTP Test")
    parser.add_argument("--body", default="SMTP test message from LMS backend.")
    args = parser.parse_args()

    smtp_host = os.getenv("SMTP_HOST", "").strip()
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_username = os.getenv("SMTP_USERNAME", "").strip()
    smtp_password = os.getenv("SMTP_PASSWORD", "")
    smtp_use_tls = _as_bool(os.getenv("SMTP_USE_TLS", "true"), default=True)
    smtp_use_ssl = _as_bool(os.getenv("SMTP_USE_SSL", "false"), default=False)
    email_from = os.getenv("EMAIL_FROM", "").strip()

    if not smtp_host:
        raise SystemExit("SMTP_HOST is required.")
    if smtp_use_tls and smtp_use_ssl:
        raise SystemExit("SMTP_USE_TLS and SMTP_USE_SSL cannot both be true.")
    if args.to and not email_from:
        raise SystemExit("EMAIL_FROM is required when sending a test message.")

    client: smtplib.SMTP | smtplib.SMTP_SSL
    if smtp_use_ssl:
        client = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=15)
    else:
        client = smtplib.SMTP(smtp_host, smtp_port, timeout=15)

    with client as smtp:
        smtp.ehlo()
        if smtp_use_tls and not smtp_use_ssl:
            smtp.starttls()
            smtp.ehlo()
        if smtp_username:
            smtp.login(smtp_username, smtp_password)

        if args.to:
            message = EmailMessage()
            message["From"] = email_from
            message["To"] = args.to
            message["Subject"] = args.subject
            message.set_content(args.body)
            smtp.send_message(message)
            print(f"SMTP connection OK and test email sent to {args.to}.")
        else:
            print("SMTP connection OK (login succeeded).")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
