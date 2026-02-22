# شرح الموديولات والـ API بالتفصيل

## 1. ملاحظة عامة

كل المسارات تعمل تحت prefix:

`/api/v1`

صيغة التوثيق التالية تعرض:

- وظيفة كل Module
- أهم قواعد العمل
- قائمة الـ endpoints الحالية

## 2. Module: Auth (`app/modules/auth`)

المسؤوليات:

- تسجيل مستخدم جديد.
- تسجيل الدخول.
- تدوير refresh token.
- تسجيل الخروج.
- جلب بيانات المستخدم الحالي.

Endpoints:

- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/refresh`
- `POST /auth/logout`
- `GET /auth/me`

ملاحظات:

- يتم إنشاء access + refresh tokens.
- refresh tokens يتم تخزينها/إبطالها.
- التحقق من token type موجود (`access` vs `refresh`).

## 3. Module: Users (`app/modules/users`)

المسؤوليات:

- إدارة حسابات المستخدمين.
- قراءة/تحديث بيانات المستخدم.
- إدارة المستخدمين بواسطة admin.

Endpoints:

- `GET /users/me`
- `GET /users`
- `GET /users/{user_id}`
- `POST /users`
- `PATCH /users/{user_id}`

ملاحظات:

- الوصول لبعض العمليات محكوم بالأدوار والصلاحيات.

## 4. Module: Courses + Lessons (`app/modules/courses`)

### 4.1 Courses

المسؤوليات:

- إنشاء كورسات.
- تعديل/نشر/حذف كورسات.
- عرض كورسات مع filtering/pagination.

Endpoints:

- `GET /courses`
- `POST /courses`
- `GET /courses/{course_id}`
- `PATCH /courses/{course_id}`
- `POST /courses/{course_id}/publish`
- `DELETE /courses/{course_id}`

### 4.2 Lessons

المسؤوليات:

- إضافة دروس لكل كورس.
- تعديل/قراءة/حذف درس.
- ترتيب الدروس داخل الكورس.

Endpoints:

- `GET /courses/{course_id}/lessons`
- `POST /courses/{course_id}/lessons`
- `GET /lessons/{lesson_id}`
- `PATCH /lessons/{lesson_id}`
- `DELETE /lessons/{lesson_id}`

## 5. Module: Enrollments (`app/modules/enrollments`)

المسؤوليات:

- تسجيل الطالب في الكورس.
- متابعة تقدمه داخل الكورس.
- تحديث progress على مستوى الدرس.
- حفظ التقييم والمراجعة.

Endpoints:

- `POST /enrollments`
- `GET /enrollments/my-courses`
- `GET /enrollments/{enrollment_id}`
- `PUT /enrollments/{enrollment_id}/lessons/{lesson_id}/progress`
- `POST /enrollments/{enrollment_id}/lessons/{lesson_id}/complete`
- `POST /enrollments/{enrollment_id}/review`
- `GET /enrollments/courses/{course_id}`
- `GET /enrollments/courses/{course_id}/stats`

ملاحظات:

- Enrollment يحمل حقول denormalized مثل progress والنسب والإجماليات.

## 6. Module: Quizzes (`app/modules/quizzes`)

ينقسم إلى:

- Quiz Router
- Question Router
- Attempt Router

### 6.1 Quiz management

Endpoints:

- `GET /courses/{course_id}/quizzes`
- `POST /courses/{course_id}/quizzes`
- `GET /courses/{course_id}/quizzes/{quiz_id}`
- `PATCH /courses/{course_id}/quizzes/{quiz_id}`
- `POST /courses/{course_id}/quizzes/{quiz_id}/publish`

### 6.2 Question management

Endpoints:

- `GET /courses/{course_id}/quizzes/{quiz_id}/questions`
- `POST /courses/{course_id}/quizzes/{quiz_id}/questions`
- `PATCH /courses/{course_id}/quizzes/{quiz_id}/questions/{question_id}`

### 6.3 Attempts and grading

Endpoints:

- `POST /quizzes/{quiz_id}/attempts`
- `GET /quizzes/{quiz_id}/attempts/start`
- `POST /quizzes/{quiz_id}/attempts/{attempt_id}/submit`
- `GET /quizzes/{quiz_id}/attempts/my-attempts`
- `GET /quizzes/{quiz_id}/attempts/{attempt_id}`

## 7. Module: Analytics (`app/modules/analytics`)

المسؤوليات:

- Dashboard للطالب.
- تحليلات instructor.
- نظرة عامة admin.

Endpoints:

- `GET /analytics/my-progress`
- `GET /analytics/my-dashboard`
- `GET /analytics/courses/{course_id}`
- `GET /analytics/instructors/{instructor_id}/overview`
- `GET /analytics/system/overview`

ملاحظات:

- أجزاء من analytics تحتاج صلاحيات أعلى.

## 8. Module: Files (`app/modules/files`)

المسؤوليات:

- رفع ملفات.
- عرض ملفات المستخدم.
- تنزيل ملف.

Endpoints:

- `POST /files/upload`
- `GET /files/my-files`
- `GET /files/download/{file_id}`

ملاحظات:

- يدعم Local/Azure Blob storage provider.
- metadata تحفظ في جدول `uploaded_files`.

## 9. Module: Certificates (`app/modules/certificates`)

المسؤوليات:

- إصدار شهادة.
- تنزيل شهادة PDF.
- verify certificate public.
- revoke certificate.

Endpoints:

- `GET /certificates/my-certificates`
- `GET /certificates/{certificate_id}/download`
- `GET /certificates/verify/{certificate_number}`
- `POST /certificates/{certificate_id}/revoke`
- `POST /certificates/enrollments/{enrollment_id}/generate`

## 10. System endpoints

- `GET /health`: فحص جاهزية التطبيق وقاعدة البيانات.
- `GET /`: رسالة root بسيطة.

## 11. قواعد authorization العامة

بصورة عامة:

- بعض endpoints متاح لأي مستخدم authenticated.
- endpoints إدارة الموارد غالبًا تحتاج instructor/admin.
- endpoints الإدارة الشاملة تحتاج admin.

التحقق يتم عبر dependencies في `app/core/dependencies.py` وخرائط permissions في `app/core/permissions.py`.

## 12. أفضل ممارسة عند إضافة endpoint جديد

1. أضف schema request/response.
2. أضف service function فيها business logic.
3. أضف repository method لو في استعلامات جديدة.
4. أضف endpoint في router مع dependencies المناسبة.
5. أضف tests تغطي success + authorization + validation cases.
