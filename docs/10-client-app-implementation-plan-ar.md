# Full Client App Implementation Plan (تفصيلي)

## 1. هدف الخطة

الهدف هو تنفيذ Frontend كامل فوق الـ LMS backend الحالي مع:

- تجربة مستخدم واضحة حسب الدور (Student/Instructor/Admin).
- إدارة حالة قوية وآمنة.
- تكامل API منظم وقابل للصيانة.
- اختبارات جيدة وقابلية نشر Production.

الخطة دي عملية وقابلة للتنفيذ Sprint by Sprint.

## 2. نطاق المنتج (Scope)

## 2.1 Primary Personas

- زائر (Guest)
- طالب (Student)
- مدرب (Instructor)
- مشرف نظام (Admin)

## 2.2 الوظائف الأساسية المطلوبة

- Auth: register/login/logout/refresh/session restore.
- Course catalog + course details + lesson viewing.
- Enrollment + progress tracking.
- Quiz taking + attempt history.
- Student dashboard + analytics.
- Instructor dashboards لإدارة المحتوى والتحليلات.
- Admin dashboards للمستخدمين والنظام.
- File uploads.
- Certificates view/download/verify.

## 2.3 خارج نطاق النسخة الأولى (Optional Later)

- Real-time notifications.
- Chat/live classroom.
- Offline-first synchronization.

## 3. Stack مقترح للتنفيذ

## 3.1 الأساس

- Framework: Next.js (App Router) + TypeScript.
- Styling: Tailwind CSS + component primitives.
- Data fetching/cache: TanStack Query.
- Forms: React Hook Form + Zod.
- HTTP client: Axios.
- Charts: Recharts أو ECharts.
- Testing:
  - Unit: Vitest + Testing Library
  - E2E: Playwright

## 3.2 سبب الاختيار

- App Router مناسب routing/layouts/SSR المختلط.
- TanStack Query يقلل تعقيد cache/invalidation.
- RHF + Zod يوفر validation موحد وقابل لإعادة الاستخدام.
- Axios interceptor يسهل refresh-token flow.

## 4. هيكل المشروع المقترح (Client)

```text
client/
  src/
    app/
      (public)/
      (auth)/
      (student)/
      (instructor)/
      (admin)/
      certificates/verify/[number]/
    modules/
      auth/
      courses/
      lessons/
      enrollments/
      quizzes/
      analytics/
      files/
      certificates/
      users/
    shared/
      api/
      components/
      hooks/
      stores/
      utils/
      types/
    middleware.ts
```

مبدأ التقسيم:

- `modules/*`: feature-centric.
- `shared/*`: reusable cross-cutting logic.
- كل feature فيها:
  - `api.ts`
  - `types.ts`
  - `hooks.ts`
  - `components/*`

## 5. تكامل الـ API (Backend Contract Mapping)

## 5.1 Auth Contract

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`

Client rules:

- حفظ `access_token` في memory/store.
- حفظ `refresh_token` في httpOnly cookie (أفضل) أو secure storage.
- عند 401:
  - محاولة refresh مرة واحدة.
  - إعادة الطلب.
  - لو فشل: logout + redirect login.

## 5.2 Routing حسب الدور

### Guest

- `/`
- `/auth/login`
- `/auth/register`
- `/courses`
- `/courses/[id]`
- `/certificates/verify/[number]`

### Student

- `/student/dashboard`
- `/student/my-courses`
- `/student/enrollments/[id]`
- `/student/quizzes/[quizId]/start`
- `/student/certificates`
- `/student/files`

### Instructor

- `/instructor/dashboard`
- `/instructor/courses`
- `/instructor/courses/new`
- `/instructor/courses/[id]/edit`
- `/instructor/courses/[id]/lessons`
- `/instructor/courses/[id]/quizzes`
- `/instructor/analytics/courses/[id]`

### Admin

- `/admin/dashboard`
- `/admin/users`
- `/admin/courses`
- `/admin/analytics/system`
- `/admin/certificates`

## 6. Auth and Session Architecture

## 6.1 Session bootstrap

عند تحميل التطبيق:

1. اقرأ session snapshot.
2. لو فيه token: استدعاء `/auth/me`.
3. لو فشل بسبب expiry: `refresh`.
4. لو فشل refresh: clear session.

## 6.2 Axios layer

ملفين رئيسيين:

- `shared/api/client.ts`
- `shared/api/interceptors.ts`

Interceptors:

- Request interceptor يضيف `Authorization`.
- Response interceptor يعالج `401` ويحاول refresh.
- منع refresh-loop عبر flag داخلي.

## 6.3 Route protection

- Server middleware: فحص بسيط للوجود.
- Client guard: فحص role + redirect.
- حماية granular على مستوى الصفحات الحساسة.

## 7. UX Flows (End-to-End)

## 7.1 Student Flow

1. Register/Login.
2. Browse courses.
3. Open course details.
4. Enroll.
5. Open lesson + update progress.
6. Start quiz + submit.
7. View dashboard analytics.
8. Download certificate بعد الإكمال.

## 7.2 Instructor Flow

1. Login.
2. Create course.
3. Add lessons.
4. Add quizzes/questions.
5. Publish.
6. Track enrollments/stats.

## 7.3 Admin Flow

1. Login.
2. Manage users.
3. View system overview analytics.
4. Revoke certificate إذا لزم.

## 8. UI Information Architecture

## 8.1 Shared Layouts

- Public layout.
- Auth layout.
- Dashboard layout (role-aware sidebar + topbar).

## 8.2 Shared Components

- `AppTable`
- `AppPagination`
- `MetricCard`
- `RoleBadge`
- `StatusBadge`
- `ConfirmDialog`
- `FileUploader`
- `ProgressBar`
- `QuizTimer`

## 8.3 Empty/Error/Loading states

- Skeletons لكل list/detail page.
- Empty states واضحة مع CTA.
- Error boundary على مستوى route segment.
- Retry actions عند أخطاء الشبكة.

## 9. State Management Strategy

## 9.1 Server State (TanStack Query)

- كل endpoint hook:
  - `useCoursesQuery`
  - `useMyEnrollmentsQuery`
  - `useMyDashboardQuery`
  - ...

Policy:

- staleTime مختلف حسب نوع البيانات.
- invalidation بعد mutations.

## 9.2 Client State

- Auth/session state.
- UI state (dialogs, filters المحلية).
- Form state داخل RHF.

## 9.3 Caching Keys Convention

أمثلة:

- `["auth", "me"]`
- `["courses", { page, pageSize, category, mine }]`
- `["enrollments", "mine", { page, pageSize }]`
- `["analytics", "my-dashboard"]`

## 10. Validation and Data Contracts

## 10.1 Type safety

- DTO types في `modules/*/types.ts`.
- Zod schemas للـ forms.
- mapper functions من API DTO إلى UI models عند الحاجة.

## 10.2 Error handling

تصنيف الأخطاء:

- Validation errors (422/400): تظهر تحت الحقول.
- Auth errors (401/403): redirect أو toast حسب السياق.
- Not found (404): route-level not found UI.
- Server errors (500): generic fallback + trace id لو متاح.

## 11. Performance Plan

- Lazy load للموديولات الثقيلة (charts, rich editors).
- Virtualized tables للقوائم الطويلة.
- Debounce للبحث.
- تجنب over-fetching (paginated endpoints فقط).
- image optimization + caching headers.

## 12. Security Plan (Client-side)

- تجنب تخزين refresh token في localStorage.
- حماية XSS عبر sanitize لأي HTML محتوى.
- لا تستخدم `dangerouslySetInnerHTML` إلا عند الضرورة ومع sanitize.
- CSRF strategy إذا استخدمت cookie-based refresh.
- إخفاء عناصر UI غير المسموح بها حسب role (مع الاعتماد الأساسي على backend authorization).

## 13. الاختبارات

## 13.1 Unit Tests

- hooks.
- pure mappers/formatters.
- auth utilities.

## 13.2 Component Tests

- forms validation.
- table interactions.
- guards behavior.

## 13.3 E2E (Playwright)

Scenarios أساسية:

1. Student login -> enroll -> progress -> quiz submit -> dashboard.
2. Instructor creates and publishes course.
3. Admin views system analytics and user list.

## 14. CI/CD لخدمة العميل

Pipeline مقترح:

1. Install + typecheck.
2. Lint + unit tests.
3. Build.
4. E2E smoke على بيئة staging.
5. Deploy.

Quality gates:

- لا merge بدون passing checks.
- حماية branch `main`.

## 15. بيئات التشغيل

- Local:
  - `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1`
- Stage:
  - endpoint stage backend
- Production:
  - endpoint prod backend

يفضل فصل secrets عن build artifacts واستخدام environment-specific configs.

## 16. خطة التنفيذ المرحلية (Milestones)

## Milestone 0 - Bootstrap (1-2 يوم)

- إعداد Next.js + TS + Tailwind + Query + RHF.
- إعداد ESLint/Prettier/Husky.
- base layouts + routing skeleton.

Deliverable:

- App shell يعمل + CI ابتدائي.

## Milestone 1 - Auth Foundation (2-3 أيام)

- صفحات login/register.
- session store + interceptors + refresh flow.
- route guards.

Deliverable:

- login/logout/session restore شغال.

## Milestone 2 - Public Catalog (2-3 أيام)

- قائمة الكورسات + تفاصيل كورس.
- filters + pagination.

Deliverable:

- Guest browsing كامل.

## Milestone 3 - Student Learning Flow (4-5 أيام)

- enrollments list/details.
- lesson progress updates.
- my-dashboard.

Deliverable:

- رحلة الطالب الأساسية كاملة.

## Milestone 4 - Quizzes (3-4 أيام)

- start attempt.
- quiz-taking UI + timer.
- submit + results.

Deliverable:

- quiz flow كامل.

## Milestone 5 - Instructor Workspace (5-6 أيام)

- CRUD courses.
- lessons management.
- quizzes/questions management.
- course analytics.

Deliverable:

- instructor dashboard usable end-to-end.

## Milestone 6 - Admin Workspace (3-4 أيام)

- users management.
- system overview.
- certificate revoke actions.

Deliverable:

- admin operations الأساسية مكتملة.

## Milestone 7 - Files + Certificates UX (2-3 أيام)

- upload/list/download files.
- certificates list/download.
- public certificate verify page.

## Milestone 8 - Hardening & QA (3-5 أيام)

- E2E scenarios.
- performance pass.
- accessibility pass.
- bug fixing.

## 17. Branch Strategy (Client)

بما إن الريبو عنده `main`, `dev`, `stage`, `demo`:

- `dev`: development integration branch.
- `stage`: pre-production stabilization.
- `main`: production-ready.
- `demo`: demo-specific data/config snapshots.

Feature branching:

- `feature/client-auth`
- `feature/client-student-dashboard`
- `feature/client-instructor-courses`
- ...

Merge flow:

1. feature -> `dev`
2. `dev` -> `stage`
3. `stage` -> `main`
4. cherry-pick أو merge انتقائي إلى `demo` حسب سيناريو العرض

## 18. Commit Strategy (Senior Style)

معايير:

- Commits صغيرة وواضحة.
- كل commit يبني ويختبر.
- رسالة commit semantic.

أمثلة:

- `feat(client-auth): implement token refresh interceptor`
- `feat(client-student): add my-dashboard page with analytics cards`
- `fix(client-quizzes): prevent duplicate submit on slow network`
- `test(client-auth): add session restore unit tests`
- `docs(client): add routing and module map`

## 19. Definition of Done (لكل Feature)

- UI مكتمل وفق acceptance criteria.
- API integration بدون mock.
- Loading/empty/error states موجودة.
- Unit tests مضافة للمنطق الجديد.
- review + lint + typecheck pass.
- docs محدثة إذا حصل تغيير في السلوك.

## 20. Risks and Mitigations

## Risk 1: Token refresh loops

Mitigation:

- refresh-once guard + central error fallback.

## Risk 2: Overfetching and slow dashboards

Mitigation:

- pagination + query caching + selective fetching.

## Risk 3: Role leakage in UI

Mitigation:

- central auth/permissions helpers + route guards.

## Risk 4: Divergence بين backend changes وfrontend assumptions

Mitigation:

- generated API types (OpenAPI) أو contracts versioning.

## 21. أول Backlog مقترح قابل للتنفيذ فورًا

1. Bootstrap frontend repo + CI + base layout.
2. Implement auth flow end-to-end.
3. Build courses list/details pages.
4. Implement student enrollments/dashboard.
5. Implement quiz-taking flow.
6. Implement instructor course management.
7. Implement admin analytics and users pages.
8. Finish e2e and release checklist.

