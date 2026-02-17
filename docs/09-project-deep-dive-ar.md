# شرح المشروع بالكامل (Deep Dive)

## 1. الهدف من المشروع

المشروع ده هو Backend كامل لمنصة Learning Management System (LMS) مبني بـ FastAPI.
الفكرة الأساسية: توفير API موحد يدير رحلة التعلم من أول إنشاء الحساب لحد استلام الشهادة.

المنصة تغطي:

- إدارة المستخدمين والأدوار.
- إدارة الكورسات والدروس.
- التسجيل في الكورسات وتتبع التقدم.
- الاختبارات (Quiz) والتصحيح وتقييم الأداء.
- التحليلات للطالب والمدرب والإدارة.
- رفع الملفات وتنزيلها.
- إصدار الشهادات والتحقق منها.
- مهام خلفية باستخدام Celery.

## 2. المعمارية العامة

المشروع مبني كأسلوب Modular Monolith:

- كود واحد وDeployment واحد.
- كل Domain في Module منفصل.
- Core مشتركة لكل الموديولات.

ليه الاختيار ده مناسب؟

- أسرع في التنفيذ والصيانة من microservices في المرحلة الحالية.
- أسهل في الـ debugging والـ testing.
- يسمح بالفصل المنطقي للكود مع قابلية التطوير مستقبلًا.

## 3. بنية المجلدات

```text
app/
  api/v1/api.py                 # تجميع الراوترات + health
  core/                         # config, db, auth deps, permissions, middleware
  modules/                      # business modules (auth, courses, quizzes, ...)
  tasks/                        # celery app + tasks
alembic/                        # migrations
scripts/                        # أوامر التشغيل والبذور والأدوات
tests/                          # الاختبارات
docs/                           # التوثيق
postman/                        # collections + environments
```

## 4. دورة الطلب داخل النظام

أي Request بيمر تقريبًا بالترتيب التالي:

1. يدخل `FastAPI` من `app/main.py`.
2. يمر عبر Middleware:
   - CORS
   - GZip
   - TrustedHost
   - Request Logging
   - Rate Limit
3. يتوجه للراوتر المناسب من `app/api/v1/api.py`.
4. Dependencies تتحقق من الهوية والصلاحيات.
5. Service layer تنفذ business logic.
6. Repository/ORM تتعامل مع قاعدة البيانات.
7. Response ترجع للعميل.

## 5. Core Layer بالتفصيل

## 5.1 الإعدادات `app/core/config.py`

- تحميل الإعدادات من `.env` عبر `pydantic-settings`.
- دعم CSV parsing لقيم زي:
  - `CORS_ORIGINS`
  - `TRUSTED_HOSTS`
  - `RATE_LIMIT_EXCLUDED_PATHS`
  - `ALLOWED_UPLOAD_EXTENSIONS`

أهم المتغيرات:

- `DATABASE_URL`
- `SECRET_KEY`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `REFRESH_TOKEN_EXPIRE_DAYS`
- `REDIS_URL`
- `CELERY_BROKER_URL`
- `CELERY_RESULT_BACKEND`

## 5.2 قاعدة البيانات `app/core/database.py`

- SQLAlchemy 2.x.
- Session لكل request عن طريق dependency `get_db`.
- Health check موجود ويُستخدم في `/api/v1/health`.

## 5.3 المصادقة والصلاحيات

- التوكنات JWT في `app/core/security.py`.
- Access token يحتوي `sub`, `role`, `typ=access`.
- Refresh token يحتوي `sub`, `typ=refresh`.
- Password hashing باستخدام `passlib` + `bcrypt`.

الصلاحيات:

- Roles: `admin`, `instructor`, `student`.
- Permissions mapping موجود في `app/core/permissions.py`.
- Dependencies مهمة:
  - `get_current_user`
  - `require_roles`
  - `require_permissions`

## 5.4 Middleware

### Request Logging

- يسجل method + path + status + latency.

### Rate Limit

- يعتمد Redis backend.
- عند فشل Redis يحصل fallback إلى in-memory بدل كسر الطلبات.
- يدعم `X-RateLimit-*` headers.

## 6. شرح الموديولات

## 6.1 Auth

المسؤوليات:

- Register
- Login
- Refresh tokens
- Logout
- Current user profile

نقاط مهمة:

- Refresh tokens متخزنة في جدول `refresh_tokens`.
- عند refresh يتم revoke للتوكن القديم وإصدار جديد (rotation).

## 6.2 Users

المسؤوليات:

- إدارة المستخدمين (خصوصًا من admin).
- قراءة وتحديث البيانات.

قواعد وصول:

- `admin` فقط للوصول لقوائم المستخدمين وتعديلهم.
- المستخدم العادي يستخدم `/users/me` و`/auth/me`.

## 6.3 Courses + Lessons

المسؤوليات:

- إنشاء الكورس وتعديله ونشره.
- إدارة الدروس داخل الكورس.
- عرض الكورسات مع pagination/filtering.

قواعد مهمة:

- إنشاء/تعديل/نشر غالبًا `instructor` أو `admin`.
- الطالب يشوف الكورسات المنشورة.
- `mine=true` لتصفية كورسات المستخدم الحالي.

## 6.4 Enrollments + Progress

المسؤوليات:

- تسجيل الطالب في الكورس.
- حفظ تقدم كل درس (status, completion %, time spent).
- تحديث summary fields على enrollment:
  - `progress_percentage`
  - `completed_lessons_count`
  - `total_time_spent_seconds`
- مراجعات وتقييمات الكورس.

قواعد مهمة:

- التسجيل في كورس غير منشور مرفوض.
- الطالب لا يستطيع review قبل 20% تقدم.
- عند اكتمال كل الدروس يتحول enrollment إلى `completed`.
- يتم محاولة إصدار شهادة تلقائيًا بعد الإكمال.

## 6.5 Quizzes

المسؤوليات:

- إدارة Quiz.
- إدارة الأسئلة.
- إدارة المحاولات والتصحيح.

تدفق المحاولة:

1. `POST /quizzes/{quiz_id}/attempts` لبدء محاولة.
2. `GET /quizzes/{quiz_id}/attempts/start` لجلب الأسئلة (بدون إجابات صحيحة).
3. `POST /submit` لإرسال الإجابات والحصول على النتيجة.

## 6.6 Analytics

مستويات التحليلات:

- Student: `my-progress`, `my-dashboard`
- Instructor/Admin: Course analytics
- Instructor/Admin: Instructor overview
- Admin فقط: System overview

نقطة فنية مهمة:

- استعلامات aggregation لازم تكون متوافقة مع PostgreSQL (`GROUP BY` كامل للحقول المستخدمة في `ORDER BY`).

## 6.7 Files

المسؤوليات:

- رفع الملفات مع validation للامتداد والحجم.
- تخزين metadata في جدول `uploaded_files`.
- تنزيل الملفات من Local أو S3.

providers:

- `local` (افتراضي)
- `s3` (اختياري)

## 6.8 Certificates

المسؤوليات:

- إصدار شهادة PDF عند اكتمال Enrollment.
- تنزيل الشهادة.
- التحقق العام من رقم الشهادة.
- إلغاء الشهادة (`admin` فقط).

طريقة الإصدار:

- توليد `certificate_number`.
- توليد ملف PDF داخل `CERTIFICATES_DIR`.
- حفظ record في جدول `certificates`.

## 7. قاعدة البيانات (Data Model)

الجداول الأساسية:

- `users`
- `refresh_tokens`
- `courses`
- `lessons`
- `enrollments`
- `lesson_progress`
- `quizzes`
- `quiz_questions`
- `quiz_attempts`
- `uploaded_files`
- `certificates`

العلاقات الأساسية:

- كورس يتبع Instructor.
- الدروس تتبع الكورس.
- enrollment يربط الطالب بالكورس.
- progress يربط enrollment بكل درس.
- quiz يتبع lesson.
- attempts تتبع quiz + enrollment.
- certificate تتبع enrollment + student + course.

## 8. Background Jobs

المكان:

- `app/tasks/celery_app.py`
- tasks:
  - `email_tasks.py`
  - `progress_tasks.py`
  - `certificate_tasks.py`

Queues:

- `emails`
- `progress`
- `certificates`

تشغيل runtime:

- `celery-worker`
- `celery-beat`

## 9. التشغيل المحلي والـ Docker

الطريقة المفضلة:

```bash
docker compose up -d --build
docker compose exec -T api alembic upgrade head
```

سكريبتات جاهزة:

- `scripts/run_project.ps1`
- `scripts/run_project.bat`
- `scripts/run_demo.ps1`
- `scripts/run_demo.bat`

## 10. الاختبارات والجودة

الاختبارات في `tests/` وتشمل:

- auth
- permissions
- courses
- enrollments
- quizzes
- analytics
- files
- certificates

CI في `.github/workflows/ci.yml`:

- Python 3.11 و3.12
- compile sanity
- Postman generation sanity
- pytest

## 11. الوثائق وPostman

Swagger/ReDoc:

- `/docs`
- `/redoc`

Postman:

- `postman/LMS Backend.postman_collection.json`
- `postman/LMS Backend.postman_environment.json`
- Demo artifacts:
  - `postman/LMS Backend DEMO.postman_collection.json`
  - `postman/LMS Backend DEMO.postman_environment.json`
  - `postman/LMS Backend DEMO.postman_runner_data.json`

## 12. نقاط قوة حالية

- بنية واضحة وفصل modules محترم.
- RBAC فعلي.
- تغطية اختبار جيدة.
- Seed + demo flow جاهز للعرض.
- تكامل جيد بين progress/certificates/analytics.

## 13. نقاط تحتاج تطوير مستقبلًا

- إضافة refresh token blacklist cleanup job دوري.
- تحسين observability (metrics + tracing).
- توسيع tasks الفعلية بدل stubs.
- تحسين pagination/filtering لبعض endpoints.
- تقليل deprecation warnings (مثل fpdf API القديمة).

## 14. كيف تضيف Feature جديدة بشكل صحيح

الترتيب العملي:

1. تعريف schema (request/response).
2. كتابة business logic في service.
3. إضافة repository query عند الحاجة.
4. إضافة endpoint بالـ dependencies الصحيحة.
5. إضافة tests (success + auth + validation).
6. تحديث docs + postman إن لزم.

Branch/commit style المقترح:

- Branch: `feature/<module>-<short-topic>`
- Commits صغيرة ومركزة:
  - `feat(module): ...`
  - `fix(module): ...`
  - `test(module): ...`
  - `docs(module): ...`

