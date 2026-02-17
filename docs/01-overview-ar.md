# نظرة عامة على المشروع (LMS Backend)

## 1. الهدف من المشروع

هذا المشروع هو Backend كامل لمنصة تعليمية (Learning Management System) مبني باستخدام `FastAPI` بأسلوب `Modular Monolith`.

المشروع مصمم ليغطي دورة التعلم كاملة:

- إدارة المستخدمين (Admin / Instructor / Student).
- إدارة الكورسات والدروس.
- التسجيل في الكورسات وتتبع التقدم.
- بناء الاختبارات وتصحيحها.
- التحليلات (Dashboard/Stats).
- رفع الملفات.
- إصدار شهادات إتمام.
- تنفيذ مهام خلفية عبر Celery.

## 2. الفكرة المعمارية

بدل ما يكون الكود "ملف كبير" أو "microservices كثيرة من البداية"، المشروع مقسوم Modules مستقلة داخل نفس التطبيق:

- `auth`
- `users`
- `courses`
- `enrollments`
- `quizzes`
- `analytics`
- `files`
- `certificates`

كل Module فيه طبقات واضحة:

- `models`: جداول قاعدة البيانات.
- `schemas`: نماذج الطلب/الاستجابة.
- `repositories`: استعلامات وعمليات DB.
- `services`: منطق العمل (Business Logic).
- `routers`: API endpoints.

## 3. المسار العام لأي Request

1. الطلب يدخل من `app/main.py`.
2. يمر على Middleware:
   - CORS
   - GZip
   - Trusted Host
   - Request Logging
   - Rate Limiting
3. يتم توجيهه إلى Router مناسب تحت `/api/v1`.
4. Dependencies تتحقق من:
   - المستخدم الحالي
   - الصلاحيات
   - Session قاعدة البيانات
5. Service + Repository ينفذوا المنطق والاستعلامات.
6. ترجع الاستجابة مع headers مثل rate-limit headers.

## 4. نقاط القوة في التصميم الحالي

- هيكل واضح وسهل التوسع.
- وجود طبقة Service يقلل منطق العمل داخل الراوتر.
- وجود طبقة Repository يجعل تغيير طريقة التخزين أسهل.
- إعدادات مركزية عبر `pydantic-settings`.
- جاهز للتشغيل المحلي وDocker.
- فيه اختبارات API تغطي تدفقات أساسية.

## 5. التقنيات الأساسية

- `FastAPI` (API framework)
- `SQLAlchemy 2.x` (ORM)
- `Alembic` (migrations)
- `PostgreSQL` (primary database)
- `Redis` (rate-limit + celery broker/backend)
- `Celery` (background jobs)
- `passlib + bcrypt` (password hashing)
- `python-jose` (JWT tokens)
- `pytest` (testing)

## 6. حالة المشروع التشغيلية

النسخة الحالية تدعم:

- تشغيل كامل عبر Docker Compose.
- Health endpoint للتحقق السريع.
- Migration baseline (`0001_initial_schema`).
- اختبار API ناجح محليًا (`pytest`).

## 7. قراءة مقترحة لباقي التوثيق

1. `docs/02-architecture-ar.md` لفهم الهيكل الداخلي بالتفصيل.
2. `docs/03-setup-and-config-ar.md` للتشغيل والإعداد.
3. `docs/04-modules-and-api-ar.md` لمعرفة كل Module والـ Endpoints.
4. `docs/05-database-and-data-model-ar.md` لفهم قاعدة البيانات.
5. `docs/06-background-jobs-and-ops-ar.md` للتشغيل والصيانة.
6. `docs/07-testing-and-quality-ar.md` للاختبارات والجودة.

