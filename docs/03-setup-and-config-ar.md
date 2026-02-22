# التشغيل والإعداد (Setup and Configuration)

## 1. المتطلبات

- Docker Desktop (أو Docker Engine + Compose).
- Python 3.11 (للتشغيل المحلي بدون Docker).
- Git.

## 2. التشغيل السريع عبر Docker

## 2.1 أوامر مباشرة

```bash
docker compose up -d --build
docker compose exec -T api alembic upgrade head
```

## 2.2 سكربتات التشغيل (Windows)

PowerShell:

```powershell
.\scripts\run_project.ps1
```

Batch:

```bat
scripts\run_project.bat
```

خيارات مفيدة:

- `-NoBuild`: تشغيل بدون إعادة build.
- `-NoMigrate`: تخطي migrations.
- `-CreateAdmin`: إنشاء admin.
- `-SeedDemoData`: إدخال بيانات تجريبية.
- `-FollowLogs`: متابعة logs مباشرة.

## 3. التشغيل المحلي بدون Docker

```bash
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

## 4. ملفات الإعداد

## 4.1 `.env`

هذا الملف هو المصدر الأساسي لقيم runtime.

إذا غير موجود:

```bash
cp .env.example .env
```

## 4.2 `app/core/config.py`

كل الإعدادات معرفة في `Settings` class وتتحمل تلقائيًا.

ملاحظة مهمة:

- الحقول التي تمثل lists مثل `CORS_ORIGINS` تقرأ من CSV.

## 5. الإعدادات الأساسية المهمة

## 5.1 Application

- `PROJECT_NAME`
- `ENVIRONMENT`
- `API_V1_PREFIX`
- `DEBUG`

## 5.2 Database

- `DATABASE_URL`
- `SQLALCHEMY_ECHO`
- `DB_POOL_SIZE`
- `DB_MAX_OVERFLOW`

## 5.3 Security

- `SECRET_KEY`
- `ALGORITHM`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `REFRESH_TOKEN_EXPIRE_DAYS`

## 5.4 CORS / Hosts

- `CORS_ORIGINS`
- `TRUSTED_HOSTS`

## 5.5 Redis / Celery / Rate-limit

- `REDIS_URL`
- `CELERY_BROKER_URL`
- `CELERY_RESULT_BACKEND`
- `RATE_LIMIT_USE_REDIS`
- `RATE_LIMIT_REQUESTS_PER_MINUTE`
- `RATE_LIMIT_WINDOW_SECONDS`
- `RATE_LIMIT_REDIS_PREFIX`
- `RATE_LIMIT_EXCLUDED_PATHS`

## 5.6 File handling

- `UPLOAD_DIR`
- `CERTIFICATES_DIR`
- `MAX_UPLOAD_MB`
- `ALLOWED_UPLOAD_EXTENSIONS`
- `FILE_STORAGE_PROVIDER` (`local` أو `azure`)
- `FILE_DOWNLOAD_URL_EXPIRE_SECONDS`

## 6. الفرق بين Local وDocker Networking

داخل Docker services:

- استخدم `db` بدل `localhost` لقاعدة البيانات.
- استخدم `redis` بدل `localhost` لـ Redis.

خارج Docker (local tooling على جهازك):

- غالبًا ستستخدم `localhost`.

## 7. بعد التشغيل

تحقق سريع:

- `http://localhost:8000/api/v1/health`
- `http://localhost:8000/docs`

## 8. البيانات التجريبية

### إنشاء Admin

```bash
python scripts/create_admin.py
```

### Seed Demo Data

```bash
python scripts/seed_demo_data.py
```

## 9. أهم المشاكل الشائعة في الإعداد

1. `.env` غير موجود.
2. migration غير مطبقة.
3. DATABASE_URL أو REDIS_URL غير مناسبين لطريقة التشغيل.
4. SECRET_KEY ضعيف أو placeholder.
