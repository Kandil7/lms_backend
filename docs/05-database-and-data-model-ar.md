# قاعدة البيانات ونموذج البيانات

## 1. نظرة عامة

المشروع يستخدم PostgreSQL كقاعدة البيانات الأساسية، وإدارة schema تتم عبر Alembic.

الموديلات معرفة في modules المختلفة، ويتم تجميع metadata عبر SQLAlchemy.

## 2. الجداول الأساسية

## 2.1 users

يمثل كل حساب مستخدم:

- `email`, `password_hash`, `full_name`, `role`, `is_active`
- metadata وتواريخ الإنشاء/التحديث

## 2.2 refresh_tokens

تخزين refresh token records:

- `user_id`
- `token_jti`
- `expires_at`
- `revoked_at`

## 2.3 courses

يمثل الكورسات:

- `title`, `slug`, `description`
- `instructor_id`
- `difficulty_level`, `is_published`

## 2.4 lessons

يمثل دروس الكورس:

- `course_id`
- `title`, `slug`
- `lesson_type`
- `order_index`
- optional parent lesson (hierarchy)

## 2.5 enrollments

ربط الطالب بالكورس:

- `student_id`, `course_id`
- `status`
- `progress_percentage`
- counters (`completed_lessons_count`, `total_lessons_count`, `total_time_spent_seconds`)
- rating/review fields

## 2.6 lesson_progress

progress على مستوى كل درس لكل enrollment:

- `enrollment_id`, `lesson_id`
- `status`
- `completion_percentage`
- `time_spent_seconds`

## 2.7 quizzes

اختبارات مرتبطة بالدروس:

- `lesson_id`
- إعدادات النجاح/المحاولات/الخلط
- publish state

## 2.8 quiz_questions

أسئلة الاختبارات:

- `quiz_id`
- question text/type
- points
- options/correct answer

## 2.9 quiz_attempts

محاولات الطلاب:

- `enrollment_id`, `quiz_id`
- `attempt_number`
- status/timing
- score/percentage/pass
- answers payload

## 2.10 uploaded_files

Metadata ملفات الرفع:

- uploader
- filename/original name
- storage path/provider
- mime/file size

## 2.11 certificates

سجلات الشهادات:

- enrollment/student/course refs
- certificate number
- pdf path
- revoked state

## 3. العلاقات (Foreign Keys)

علاقات رئيسية:

- `courses.instructor_id -> users.id`
- `lessons.course_id -> courses.id`
- `enrollments.student_id -> users.id`
- `enrollments.course_id -> courses.id`
- `lesson_progress.enrollment_id -> enrollments.id`
- `lesson_progress.lesson_id -> lessons.id`
- `quizzes.lesson_id -> lessons.id`
- `quiz_questions.quiz_id -> quizzes.id`
- `quiz_attempts.enrollment_id -> enrollments.id`
- `quiz_attempts.quiz_id -> quizzes.id`
- `uploaded_files.uploader_id -> users.id`
- `certificates.enrollment_id -> enrollments.id`
- `certificates.student_id -> users.id`
- `certificates.course_id -> courses.id`

## 4. أنواع البيانات

من SQLAlchemy metadata الحالية:

- IDs تظهر كـ `CHAR(32)` (UUID hex).
- timestamps غالبًا `DATETIME`.
- النسب/الدرجات `NUMERIC`.
- payload المرن مثل options/answers/metadata في `JSON`.

## 5. إدارة migrations

Alembic baseline:

- `0001_initial_schema`

أوامر مهمة:

```bash
alembic upgrade head
alembic current
alembic downgrade -1
```

داخل Docker:

```bash
docker compose exec -T api alembic upgrade head
```

## 6. نمط التعامل مع قاعدة البيانات

- جلسات DB عبر `SessionLocal` في `app/core/database.py`.
- أي endpoint يأخذ session عبر dependency `get_db()`.
- service/repository layers مسؤولة عن commit/flush حسب سياق العملية.

## 7. ملاحظات تصميمية مهمة

1. وجود حقول denormalized داخل `enrollments` لتحسين قراءة dashboards.
2. حفظ answers/options بصيغة JSON يقلل تعقيد schema في الأسئلة والمحاولات.
3. الفصل بين enrollments وlesson_progress يسمح بتفصيل أدق للتتبع.

## 8. تحسينات مستقبلية مقترحة

1. إضافة migrations incremental بدل الاعتماد على create-all logic داخل revision واحد.
2. إضافة indexes إضافية حسب query patterns الحقيقية من production.
3. partitioning أو archiving لجدول `quiz_attempts` لو الحجم كبر.

