# Client Application Implementation Plan (Detailed)

Date: 2026-02-21
Audience: Product, Engineering, QA, Design, DevOps
Backend Reference: `app/api/v1/api.py`, `docs/08-api-documentation.md`

## 1. Objective

Build a production-ready LMS client application that consumes the existing backend APIs and supports complete role-based workflows for:

- student
- instructor
- admin

The client app should be web-first, responsive (desktop + mobile web), secure, and testable end to end.

## 2. Scope

### In Scope (V1)

- Authentication and session management (register, login, MFA challenge, refresh, logout).
- Role-based access and route protection.
- Student flows:
  - browse courses
  - course details + lesson list
  - enrollment
  - lesson progress updates
  - quiz taking and results
  - personal dashboard and progress analytics
  - certificates list/download/verify
- Instructor flows:
  - course CRUD and publish
  - lesson CRUD
  - quiz and question authoring
  - enrollment list and course stats
  - course-level analytics
- Admin flows:
  - users management
  - system overview analytics
- File uploads and file management for authenticated users.
- Frontend observability, CI, QA automation, and staged rollout.

### Out of Scope (V1)

- Native mobile apps.
- Real-time classroom/chat/live streaming.
- Offline-first video synchronization.
- Payments checkout UX (no active payments router is wired in `app/api/v1/api.py` as of 2026-02-21).

## 3. Constraints and Assumptions

- API base path is `/api/v1`.
- Auth uses JWT access token + refresh token API flow.
- Access token expiry is short (`ACCESS_TOKEN_EXPIRE_MINUTES` default 15).
- MFA may be enabled per user, so login may return challenge response instead of tokens.
- Response envelope may be enabled/disabled by environment (`API_RESPONSE_ENVELOPE_ENABLED`).
- API is rate-limited and returns standard rate-limit headers.
- CORS is expected to include client origin (`CORS_ORIGINS`).

## 4. Recommended Client Stack

- Framework: Next.js (App Router) + TypeScript.
- UI: Tailwind CSS + headless component primitives.
- Server state: TanStack Query.
- Forms/validation: React Hook Form + Zod.
- Charts: Recharts or ECharts.
- E2E: Playwright.
- Unit/component tests: Vitest + React Testing Library.
- Error tracking: Sentry browser SDK.

Reasoning:
- Next.js enables secure token handling via server routes if needed and supports SSR/CSR hybrid rendering.
- TanStack Query matches this API-heavy LMS domain with cache invalidation and optimistic updates.

## 5. Architecture

### 5.1 Layers

- `app` (routes, layouts, route groups).
- `modules` (feature modules by domain).
- `lib/api` (typed API client + auth refresh logic + envelope unwrapping).
- `lib/auth` (session, route guard, role checks).
- `lib/ui` (design system primitives).
- `lib/telemetry` (frontend metrics/events/logging hooks).

### 5.2 Proposed Directory Structure

```text
client/
  src/
    app/
      (public)/
      (auth)/
      (student)/
      (instructor)/
      (admin)/
    modules/
      auth/
      users/
      courses/
      lessons/
      enrollments/
      quizzes/
      analytics/
      files/
      certificates/
    lib/
      api/
      auth/
      config/
      utils/
      telemetry/
    components/
      ui/
      shared/
  tests/
    e2e/
    integration/
```

### 5.3 Core Technical Decisions

- Build a single API client wrapper that:
  - injects `Authorization` header.
  - unwraps envelope responses when enabled.
  - normalizes API errors (`detail` array/string).
  - retries on network/transient failures with bounded backoff.
- Use a refresh-token mutex to prevent parallel refresh storms.
- Keep role checks centralized (`canAccessRoute`, `canPerformAction`).
- Throttle lesson progress updates (debounce + flush on visibility change/unload).

## 6. Backend API to Screen Mapping

### 6.1 Authentication

- `POST /auth/register`: Register page.
- `POST /auth/login`: Login page.
- `POST /auth/login/mfa`: MFA challenge page.
- `POST /auth/refresh`: Silent session refresh.
- `POST /auth/logout`: Logout action.
- `POST /auth/forgot-password`: Forgot password page.
- `POST /auth/reset-password`: Reset password page.
- `POST /auth/verify-email/request`: Verification resend.
- `POST /auth/verify-email/confirm`: Email verification page.
- `GET /auth/me`: session bootstrap.

### 6.2 Courses and Lessons

- `GET /courses`: Catalog, Instructor "My Courses" (with `mine=true`), filters.
- `POST /courses`: Instructor/Admin create course.
- `GET /courses/{course_id}`: Course details.
- `PATCH /courses/{course_id}`: Edit course.
- `POST /courses/{course_id}/publish`: Publish action.
- `DELETE /courses/{course_id}`: Delete action.
- `GET /courses/{course_id}/lessons`: Course curriculum.
- `POST /courses/{course_id}/lessons`: Create lesson.
- `GET /lessons/{lesson_id}`: Lesson player/detail.
- `PATCH /lessons/{lesson_id}`: Edit lesson.
- `DELETE /lessons/{lesson_id}`: Delete lesson.

### 6.3 Enrollments and Progress

- `POST /enrollments`: Enroll button on course page.
- `GET /enrollments/my-courses`: Student learning dashboard list.
- `GET /enrollments/{enrollment_id}`: Enrollment detail and completion state.
- `PUT /enrollments/{enrollment_id}/lessons/{lesson_id}/progress`: Progress sync.
- `POST /enrollments/{enrollment_id}/lessons/{lesson_id}/complete`: Explicit completion.
- `POST /enrollments/{enrollment_id}/review`: Course review modal.
- `GET /enrollments/courses/{course_id}`: Instructor enrolled students list.
- `GET /enrollments/courses/{course_id}/stats`: Instructor course stats cards.

### 6.4 Quizzes

- `GET /courses/{course_id}/quizzes`: Quiz list in course context.
- `POST /courses/{course_id}/quizzes`: Instructor create quiz.
- `GET /courses/{course_id}/quizzes/{quiz_id}`: Quiz settings/details.
- `PATCH /courses/{course_id}/quizzes/{quiz_id}`: Edit quiz.
- `POST /courses/{course_id}/quizzes/{quiz_id}/publish`: Publish quiz.
- `GET /courses/{course_id}/quizzes/{quiz_id}/questions`: Student quiz question view.
- `GET /courses/{course_id}/quizzes/{quiz_id}/questions/manage`: Instructor question management view.
- `POST /courses/{course_id}/quizzes/{quiz_id}/questions`: Create question.
- `PATCH /courses/{course_id}/quizzes/{quiz_id}/questions/{question_id}`: Edit question.
- `POST /quizzes/{quiz_id}/attempts`: Start attempt.
- `GET /quizzes/{quiz_id}/attempts/start`: Fetch quiz payload for taking.
- `POST /quizzes/{quiz_id}/attempts/{attempt_id}/submit`: Submit answers.
- `GET /quizzes/{quiz_id}/attempts/my-attempts`: Attempts history.
- `GET /quizzes/{quiz_id}/attempts/{attempt_id}`: Attempt result page.

### 6.5 Analytics

- `GET /analytics/my-progress`: Student summary metrics.
- `GET /analytics/my-dashboard`: Student dashboard page.
- `GET /analytics/courses/{course_id}`: Instructor course analytics page.
- `GET /analytics/instructors/{instructor_id}/overview`: Instructor overview page.
- `GET /analytics/system/overview`: Admin dashboard.

### 6.6 Files and Certificates

- `POST /files/upload`: File uploader component.
- `GET /files/my-files`: My files manager.
- `GET /files/download/{file_id}`: Download action.
- `POST /certificates/enrollments/{enrollment_id}/generate`: Generate certificate action.
- `GET /certificates/my-certificates`: Student certificate center.
- `GET /certificates/{certificate_id}/download`: Download certificate.
- `POST /certificates/{certificate_id}/revoke`: Admin/instructor revoke action.
- `GET /certificates/verify/{certificate_number}`: Public certificate verification page.

## 7. Role-Based UX and Authorization Matrix

- Student:
  - can browse published courses, enroll, learn, attempt quizzes, view personal analytics, view/download certificates.
  - cannot create/update course content.
- Instructor:
  - can manage own courses/lessons/quizzes/questions.
  - can view course enrollments/stats and course analytics.
  - cannot access admin-only user/system pages.
- Admin:
  - full access including users listing and system analytics.

Client enforcement:
- route-level guards.
- component/action-level guards (hide or disable restricted actions).
- hard fail handling for 403 responses with clear UI messages.

## 8. Detailed Implementation Phases

### 8.1 Phase 0 - Foundation (Week 1)

Deliverables:
- frontend repo scaffold.
- baseline layout and navigation shell.
- environment config (`NEXT_PUBLIC_API_BASE_URL`, app env tags).
- CI pipeline skeleton.

Tasks:
- initialize Next.js + TypeScript + ESLint + Prettier.
- configure absolute imports and module boundaries.
- set up shared UI primitives and theme tokens.
- create HTTP client with error normalization.
- add global loading/error boundary patterns.
- add Sentry initialization hooks (disabled in local).

Acceptance:
- app boots in local and staging.
- health check call to `/api/v1/health` works.
- lint + typecheck pass in CI.

### 8.2 Phase 1 - Auth and Session (Week 2)

Deliverables:
- full auth screens and session lifecycle.

Tasks:
- register, login, forgot/reset password forms.
- MFA challenge screen for login fallback response.
- email verification request/confirm UX.
- token persistence strategy + silent refresh service.
- protected route middleware and role-aware redirects.
- logout and forced re-auth flow.

Acceptance:
- handles both auth response variants:
  - `AuthResponse`
  - `MfaChallengeResponse`
- auto-refresh works across tab refresh and expired access token.
- protected pages redirect anonymous users.

### 8.3 Phase 2 - Student Learning Experience (Weeks 3-5)

Deliverables:
- complete student learning workflows.

Tasks:
- course catalog with filters, pagination, and empty states.
- course detail page with lesson outline and enroll action.
- "My Courses" dashboard using enrollments APIs.
- lesson player page:
  - video/text/assignment/quiz lesson handling
  - progress tracker with debounced sync
  - continue-learning behavior from last position
- quiz-taking flow:
  - start attempt
  - load shuffled questions/options
  - submit and result summary
  - attempt history view
- review submission UI with validation.
- student analytics dashboard (`my-progress`, `my-dashboard`).
- certificate center + download + public verify page.

Acceptance:
- student can complete end-to-end flow:
  course discovery -> enrollment -> lesson completion -> quiz submission -> certificate visibility.
- progress aggregation from backend is reflected accurately in UI.

### 8.4 Phase 3 - Instructor Authoring and Management (Weeks 6-8)

Deliverables:
- instructor control plane.

Tasks:
- "My Courses" management list (`GET /courses?mine=true`).
- create/edit/publish/delete course.
- lesson authoring:
  - hierarchy via `parent_lesson_id`
  - ordering and type-specific validation
  - preview flags
- quiz authoring:
  - create/edit/publish quiz
  - question CRUD for multiple types
  - answer options and scoring inputs
- enrolled students table and course stats cards.
- instructor course analytics page.
- file upload integration for course assets.

Acceptance:
- instructor can build and publish a complete course with lessons and quiz.
- authorization is enforced for non-owner instructor accounts.

### 8.5 Phase 4 - Admin Console (Week 9)

Deliverables:
- admin-only management pages.

Tasks:
- users table with pagination/search filters.
- user detail page and edit form (role, active state).
- system overview dashboard (users, courses, enrollments).
- role switch and audit-friendly UI labels.

Acceptance:
- admin-only routes blocked for non-admin users.
- all user CRUD interactions function against `/users` APIs.

### 8.6 Phase 5 - Hardening and Release (Weeks 10-11)

Deliverables:
- production readiness package.

Tasks:
- unified error taxonomy and UX copy.
- rate-limit aware UX (429 handling with cooldown hints).
- loading skeletons and optimistic updates where safe.
- accessibility remediation (keyboard paths, semantic labels, contrast).
- performance optimization (route-level code split, image strategy, caching).
- E2E smoke pack for all roles.
- release checklist and rollback playbook.

Acceptance:
- Lighthouse and Web Vitals within target thresholds.
- critical E2E scenarios pass in staging.
- Sentry and frontend logs verified in staging.

### 8.7 Phase 6 - Post-Launch Enhancements (Week 12+)

Possible additions:
- notifications center.
- advanced analytics filtering and date ranges.
- multi-language support.
- payments module UI if backend router is activated.

## 9. Detailed Module Backlog

### 9.1 Auth Module

- session provider + hooks (`useSession`, `useRequireRole`).
- token refresh interceptor with single-flight locking.
- MFA login branch handling.
- auth-specific error mapping (invalid credentials, expired challenge, unverified email).

### 9.2 Course Module

- query keys:
  - `courses.list`
  - `courses.detail`
  - `courses.mine`
- mutations invalidate course + lesson dependent keys.
- filter state in URL for shareable views.

### 9.3 Lesson Module

- render strategy by `lesson_type`.
- progress sync policy:
  - debounce every 15-30 seconds
  - flush on tab hidden/unload
  - retry queue with max attempts

### 9.4 Quiz Module

- schema-driven question editor for all supported question types.
- timed quiz UX for `time_limit_minutes`.
- attempt state persistence until submit.
- results visibility aligned with `show_correct_answers`.

### 9.5 Analytics Module

- summary cards + trend widgets.
- precision-safe formatting for decimals.
- guarded dashboard routes by role.

### 9.6 Files and Certificates

- uploader with progress bar and type/size pre-checks.
- list/download views with fallback handling for redirect downloads.
- public certificate verification screen with no auth requirement.

## 10. Data and API Contract Strategy

- Generate TypeScript types from OpenAPI at build time.
- Maintain a thin hand-written service layer for query params and endpoint composition.
- Add contract tests that compare mocked payloads to generated types.

Critical handling rules:
- Support both payload shapes:
  - wrapped: `{ success, data, message }`
  - plain: direct object/array
- Parse FastAPI validation errors (`detail[]`) into field-level form errors.
- Parse and surface 401, 403, 404, 409, 422, 429 consistently.

## 11. UX and UI Requirements

- Responsive breakpoints:
  - mobile: 360px+
  - tablet: 768px+
  - desktop: 1024px+
- Navigation:
  - top app bar + role-aware side navigation on dashboard routes.
- Empty/loading/error states for every data-fetching screen.
- Form behavior:
  - client-side validation first
  - server error reconciliation per field
- Accessibility baseline:
  - keyboard navigation across all key journeys
  - ARIA labels for controls
  - visible focus and contrast compliance

## 12. Testing Strategy

### 12.1 Unit Tests

- API client utilities (envelope unwrap, error parser, refresh lock).
- role guard utilities.
- pure data formatting and analytics transforms.

### 12.2 Component Tests

- auth forms, course filters, lesson progress widgets, quiz question renderer.
- mutation side effects and invalidation behaviors.

### 12.3 Integration Tests

- module-level tests with API mock server.
- auth lifecycle including MFA branch.

### 12.4 E2E Tests (Playwright)

- student end-to-end learning path.
- instructor authoring and publish path.
- admin user management path.
- certificate verification public path.

### 12.5 Non-Functional Tests

- performance smoke on key pages.
- accessibility checks on major templates.

## 13. CI/CD Plan

Pipeline stages:
- install dependencies.
- lint.
- typecheck.
- unit + component tests.
- build.
- E2E smoke (staging-gated).

Deployment:
- preview deployments per PR.
- staged release to staging, then production.
- release tags with changelog entries.

## 14. Security Plan

- never log tokens or sensitive PII in client logs.
- strict CSP and secure headers on client host.
- sanitize all rich text rendering from lesson content.
- enforce role checks in both route guards and action buttons.
- centralized handling of 401/403 to avoid leaking privileged data.

## 15. Performance Targets

- initial load JS budget: <= 250KB gzipped for public/auth routes.
- Time to Interactive on broadband desktop: < 3s for main dashboards.
- API call deduplication via query caching.
- virtualization for long tables/lists.

## 16. Observability and Product Telemetry

- frontend error tracking via Sentry.
- business events:
  - `course_enrolled`
  - `lesson_completed`
  - `quiz_submitted`
  - `certificate_downloaded`
- correlate client request IDs with backend logs when possible.

## 17. Delivery Timeline and Milestones

- Week 1: Foundation ready.
- Week 2: Auth complete.
- Weeks 3-5: Student flows complete.
- Weeks 6-8: Instructor flows complete.
- Week 9: Admin console complete.
- Weeks 10-11: Hardening + release prep.
- Week 12: Production launch and stabilization.

## 18. Team Plan

Minimum team:
- 1 frontend lead.
- 2 frontend engineers.
- 1 QA automation engineer.
- 1 UI/UX designer (shared).
- 1 DevOps engineer (shared).

## 19. Definition of Done (Per Feature)

- API integration complete and typed.
- happy path + edge cases handled.
- loading/empty/error states implemented.
- unit/component/E2E coverage added.
- accessibility checks pass.
- telemetry events emitted where applicable.
- reviewed and accepted in staging.

## 20. Immediate Next Execution Steps

1. Approve stack and timeline in this document.
2. Create `client` repository with Phase 0 scaffold.
3. Implement Phase 1 auth/session before any feature module.
4. Run weekly demos at phase boundaries (Weeks 2, 5, 8, 9, 11).
