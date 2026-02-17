# الاختبارات والجودة وطريقة العمل

## 1. إطار الاختبارات

المشروع يستخدم:

- `pytest`
- `fastapi.testclient`

ملفات الاختبار موجودة في `tests/`.

## 2. تغطية الاختبارات الحالية

الاختبارات تغطي تدفقات أساسية لموديولات:

- auth
- courses
- enrollments
- quizzes
- analytics
- files
- certificates
- permissions

تشغيل الاختبارات:

```bash
pytest -q
```

داخل Docker:

```bash
docker compose exec -T api pytest -q
```

## 3. فلسفة كتابة الاختبارات في هذا المشروع

### 3.1 ما الذي نختبره

1. Success path.
2. Authorization boundaries.
3. Validation failures.
4. Regression-sensitive business rules.

### 3.2 ما الذي نضيفه عند إضافة feature جديدة

1. اختبار endpoint الأساسي.
2. اختبار access control.
3. اختبار edge cases الأساسية.
4. اختبار failure mode واضح.

## 4. CI / Quality Gates

المشروع يحتوي workflow CI في:

- `.github/workflows/ci.yml`

الهدف أن أي PR يمر على:

- install
- tests
- fail fast عند أي كسر

## 5. أسلوب العمل الموصى به (Senior Workflow)

1. أنشئ branch مخصص:
   - `feature/...`
   - `fix/...`
   - `chore/...`
2. نفذ تغييرات صغيرة ومركزة.
3. اكتب commits واضحة.
4. شغّل الاختبارات قبل push.
5. افتح PR مع وصف تقني واضح.

## 6. نمط رسائل commit المقترح

- `feat(module): add ...`
- `fix(module): resolve ...`
- `chore(dev): improve ...`
- `docs(project): add ...`
- `test(module): cover ...`

## 7. مراجعة الكود (Review Checklist)

1. هل التغيير يحافظ على contracts الحالية؟
2. هل فيه كسر backward compatibility؟
3. هل authorization checks سليمة؟
4. هل error handling واضح؟
5. هل الاختبارات كافية لحالة التغيير؟

## 8. متطلبات الجودة قبل الدمج

1. جميع الاختبارات خضراء.
2. لا يوجد secrets hardcoded.
3. docs محدثة إذا تغير سلوك API أو setup.
4. migration موجودة إذا schema تغيرت.
5. PR description يشرح:
   - ماذا تغير؟
   - لماذا؟
   - كيف تم التحقق؟

