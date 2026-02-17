# شرح المعمارية بالتفصيل

## 1. الصورة العامة

المشروع مبني كـ `Modular Monolith`:

- تطبيق واحد.
- قاعدة بيانات واحدة.
- Modules متعددة مفصولة منطقيًا.

هذا الأسلوب مناسب جدًا للمرحلة الحالية لأنه يعطيك:

- سرعة تطوير.
- سهولة debugging.
- قابلية نقل Module لاحقًا إلى خدمة منفصلة إذا احتجت.

## 2. هيكل المجلدات

```text
app/
  api/
    v1/
      api.py
  core/
    config.py
    database.py
    security.py
    dependencies.py
    permissions.py
    exceptions.py
    middleware/
  modules/
    <module_name>/
      models.py / models/
      schemas.py / schemas/
      repositories/
      services/
      router.py / routers/
  tasks/
  utils/
```

## 3. دور كل طبقة

## 3.1 core

- `config.py`: تحميل وإدارة كل الإعدادات من `.env`.
- `database.py`: engine/session/base + health check.
- `security.py`: hashing + JWT create/decode.
- `dependencies.py`: dependencies جاهزة للـ routers (current user, pagination, permissions).
- `permissions.py`: تعريف الأدوار والصلاحيات.
- `middleware/*`: logging + rate-limit.
- `exceptions.py`: توحيد شكل الأخطاء.

## 3.2 modules

كل Module يحتوي منطقه الخاص ولا يعتمد على تفاصيل داخل Module آخر إلا عبر service/repository منظم.

## 3.3 api aggregation

الملف `app/api/v1/api.py` يقوم بتجميع routers باستخدام `_safe_include`.

ميزة `_safe_include`:

- في حال Module فشل تحميله، التطبيق لا ينهار بالكامل.
- يسجل warning فقط.

## 4. middleware stack

في `app/main.py` ترتيب middleware مهم:

1. `CORSMiddleware`
2. `GZipMiddleware`
3. `TrustedHostMiddleware`
4. `RequestLoggingMiddleware`
5. `RateLimitMiddleware`

## 4.1 Rate limiting

- يدعم Redis backend.
- يوجد fallback إلى in-memory عند مشاكل Redis أو مشاكل event loop.
- يضيف headers:
  - `X-RateLimit-Limit`
  - `X-RateLimit-Remaining`
  - `X-RateLimit-Reset`

## 5. نمط العمل داخل endpoint

المسار المعتاد لأي endpoint:

1. Router يستقبل ويعمل validation أولي عبر schema.
2. Dependency تتحقق من التوكن/الدور.
3. Service ينفذ business logic.
4. Repository ينفذ DB IO.
5. Router يرجع response model واضح.

## 6. إدارة الجلسات في SQLAlchemy

- `SessionLocal` معرف مركزيًا في `app/core/database.py`.
- `get_db()` dependency تستخدم في الراوترات.
- النمط المستخدم يقلل تسريب الجلسات ويضمن close بعد كل request.

## 7. تصميم الصلاحيات

الأدوار:

- `admin`
- `instructor`
- `student`

الصلاحيات معرفة كـ Permissions منفصلة (مثل `course:create`, `analytics:view`) ويتم التحقق منها عبر:

- `require_roles(...)`
- `require_permissions(...)`

هذا يعطي مرونة أعلى من checks صلبة داخل كل endpoint.

## 8. background processing architecture

المهام الخلفية مع Celery:

- broker/result backend على Redis.
- routing حسب نوع المهمة:
  - emails
  - progress
  - certificates

ملفات المهام:

- `app/tasks/email_tasks.py`
- `app/tasks/progress_tasks.py`
- `app/tasks/certificate_tasks.py`

## 9. static/files serving

التطبيق يركب static mounts:

- `/uploads` للملفات المحلية.
- `/certificates-static` للشهادات.

هذا يبسط التطوير المحلي، ويمكن لاحقًا نقل التقديم إلى CDN/S3 في الإنتاج.

## 10. نقاط تصميم مهمة

- API versioning عبر `API_V1_PREFIX` (`/api/v1`).
- فصل واضح بين concerns.
- استخدام Pydantic schemas لتثبيت contracts.
- اعتماد migrations بدل create-all المباشر في التشغيل الحقيقي.

