# SMTP Provider Selection (Supabase vs Firebase)

## Recommendation
- Use a dedicated SMTP provider for the backend (`Resend`, `SES`, `Postmark`, or `SendGrid`).
- Keep backend email delivery controlled by:
  - `SMTP_HOST`
  - `SMTP_PORT`
  - `SMTP_USERNAME`
  - `SMTP_PASSWORD`
  - `EMAIL_FROM`

## Supabase
- Supabase built-in SMTP is for testing. Their auth SMTP guide documents team-only delivery and a very low send limit for default SMTP.
- If you use Supabase Auth, configure **custom SMTP** there using the same SMTP provider credentials used by this backend.
- This keeps auth emails and backend-triggered emails aligned.

## Firebase
- Firebase custom SMTP is tied to Identity Platform configuration.
- Standard Firebase Auth setup is not a drop-in SMTP relay for backend app email tasks.
- If you already run Identity Platform, you can configure SMTP there; otherwise keep backend SMTP direct.

## Backend Default (Resend Example)
```env
SMTP_HOST=smtp.resend.com
SMTP_PORT=587
SMTP_USERNAME=resend
SMTP_PASSWORD=re_xxxxxxxxxxxxxxxxxxxxx
SMTP_USE_TLS=true
SMTP_USE_SSL=false
EMAIL_FROM=no-reply@your-domain.com
```

## Validation
```bash
python scripts/test_smtp_connection.py
python scripts/test_smtp_connection.py --to your-email@example.com
```

## References
- Supabase Auth SMTP guide: https://supabase.com/docs/guides/auth/auth-smtp
- Resend SMTP guide: https://resend.com/docs/knowledge-base/smtp
- Identity Platform config API (`smtp` fields): https://cloud.google.com/identity-platform/docs/reference/rest/v2/Config
