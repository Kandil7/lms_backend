# Demo Branch Guide

هذا الدليل يشرح طريقة تشغيل نسخة `demo` بحيث تكون:

- المشروع شغال بالكامل.
- قاعدة البيانات متطبقة عليها migrations.
- بيانات Demo موجودة وجاهزة للاستخدام.

## 1. الهدف من demo branch

فرع `demo` مخصص للعروض والتجارب السريعة، لذلك يعتمد على:

- تشغيل كامل عبر Docker.
- Seed data جاهزة (users + course + lessons + enrollment + quiz + graded attempt).

## 2. أسرع طريقة تشغيل

### PowerShell

```powershell
.\scripts\run_demo.ps1
```

### Batch

```bat
scripts\run_demo.bat
```

## 3. ماذا يفعل run_demo

1. يتأكد من وجود `.env` (وينسخه من `.env.example` إذا لزم).
2. يشغل Docker Compose.
3. يطبق `alembic upgrade head`.
4. يشغل:

```bash
python scripts/seed_demo_data.py --reset-passwords
```

5. ينتظر `/api/v1/health` حتى تصبح `ok`.

## 4. بيانات الدخول التجريبية

- `admin.demo@example.com / AdminPass123`
- `instructor.demo@example.com / InstructorPass123`
- `student.demo@example.com / StudentPass123`

## 5. روابط مفيدة بعد التشغيل

- Swagger: `http://localhost:8000/docs`
- Health: `http://localhost:8000/api/v1/health`

## 6. خيارات السكربت

### run_demo.ps1

- `-NoBuild`
- `-SkipMigrate`
- `-SkipSeed`
- `-FollowLogs`

### run_demo.bat

- `-NoBuild` / `--no-build`
- `-SkipMigrate` / `--skip-migrate`
- `-SkipSeed` / `--skip-seed`
- `-FollowLogs` / `--follow-logs`

## 7. إعادة ضبط بيانات demo

إذا أردت إعادة ضبط كلمات المرور والبيانات الأساسية:

```bash
docker compose exec -T api python scripts/seed_demo_data.py --reset-passwords
```

## 8. ملاحظات

- هذا الفرع مناسب للـ demo وليس بديلاً عن إعدادات production.
- قبل أي Demo مهم، يفضل تشغيل:

```bash
docker compose ps
docker compose exec -T api pytest -q
```
