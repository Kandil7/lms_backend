# المهام الخلفية والتشغيل والصيانة

## 1. المهام الخلفية (Celery)

## 1.1 التعريف

إعداد Celery في:

- `app/tasks/celery_app.py`

ويستخدم:

- Broker: `CELERY_BROKER_URL`
- Result backend: `CELERY_RESULT_BACKEND`

## 1.2 توزيع الـ queues

- `emails` لمهام البريد.
- `progress` لمهام التقدم.
- `certificates` لمهام الشهادات.

## 1.3 المهام الحالية

- `app.tasks.email_tasks.send_welcome_email`
- `app.tasks.progress_tasks.recalculate_course_progress`
- `app.tasks.certificate_tasks.generate_certificate`

> ملاحظة: المهام الحالية base stubs ويمكن توسيعها بسهولة.

## 2. التشغيل اليومي (Operations)

## 2.1 تشغيل الخدمات

```bash
docker compose up -d --build
```

## 2.2 فحص الحالة

```bash
docker compose ps
curl http://localhost:8000/api/v1/health
```

## 2.3 logs

```bash
docker compose logs --tail=200 api
docker compose logs --tail=200 celery-worker
docker compose logs --tail=200 celery-beat
```

## 2.4 migrations

```bash
docker compose exec -T api alembic upgrade head
docker compose exec -T api alembic current
```

## 3. rate limiting behavior

الـ middleware:

- يحاول Redis أولًا.
- لو Redis فشل أو حصل `Event loop is closed` يعمل fallback إلى in-memory.
- لا يكسر الطلبات عند عطل Redis transient.

## 4. إدارة الملفات والشهادات

- الملفات المحلية في `uploads/`.
- ملفات الشهادات في `certificates/`.
- المسارات متاحة عبر static mounts:
  - `/uploads`
  - `/certificates-static`

## 5. التشغيل في الإنتاج (Production Notes)

1. اجعل `DEBUG=false`.
2. استخدم `SECRET_KEY` قوية بطول كبير.
3. قيد `CORS_ORIGINS` و`TRUSTED_HOSTS` بدقة.
4. استخدم PostgreSQL/Redis managed.
5. فعّل monitoring للـ API + worker + db.
6. حافظ على backup policy للبيانات والملفات.
7. استخدم TLS termination عبر reverse proxy.

## 6. Troubleshooting سريع

## 6.1 API لا يقلع

- تحقق من `.env`.
- تحقق من `DATABASE_URL`.
- افحص `docker compose logs api`.

## 6.2 DB health down

- تأكد أن `db` container up.
- شغل migrations.
- تحقق من network host (`db` داخل docker).

## 6.3 Celery لا يتصل بـ Redis

- تأكد أن URLs تستخدم host `redis` داخل containers.
- افحص logs worker/beat.

## 6.4 أخطاء auth hashing

- تأكد من نسخة `bcrypt` المتوافقة (`<5.0.0`).
- أعد build بعد تعديل requirements.

## 7. checklist قبل release

1. كل الاختبارات خضراء.
2. migrations مطبقة.
3. health endpoint يعمل.
4. secrets ليست placeholders.
5. branch محدث وPR راجعه فريقك.

