# UAT and Bug Bash Plan

## 1. Goal
- Validate real user journeys before launch.
- Catch blocking defects that automated tests do not cover.

## 2. UAT Scope
- Audience:
  - 3-5 instructors
  - 10-20 students
  - 1-2 admins/support users
- Test window:
  - UAT Week: `T-14` to `T-7` days before launch
  - Bug bash: `T-6` to `T-4` days before launch
- Environment:
  - Staging with production-like configuration and seed data.

## 3. Entry Criteria
- Staging checklist is complete:
  - `docs/ops/02-staging-release-checklist.md`
- Security workflow is green:
  - `.github/workflows/security.yml`
- Observability stack is running and alerts are connected.

## 4. Exit Criteria
- No open `P0` or `P1` bugs.
- `P2` bugs have approved mitigation or deferred release ticket.
- UAT sign-off is approved by Product Owner + Engineering Lead.

## 5. Bug Bash Workflow
1. Assign participants and ownership per module.
2. Use `docs/templates/bug-bash-report-template.md`.
3. Log each finding with:
   - severity (`P0`, `P1`, `P2`, `P3`)
   - reproducibility
   - affected role
   - impact on launch
4. Triage in same day and decide:
   - fix before launch
   - workaround + post-launch ticket
   - reject (not reproducible / low impact)

## 6. Mandatory UAT Journeys
1. Student registration/login, enroll course, finish lesson, attempt quiz.
2. Instructor course creation, lesson update, quiz publish, analytics view.
3. Admin user management and platform overview.
4. File upload/download and certificate generation flow.
5. Password reset and email verification flow.

## 7. Evidence and Artifacts
- UAT scenarios: `docs/templates/uat-scenario-template.md`
- Bug bash report: `docs/templates/bug-bash-report-template.md`
- Final sign-off note attached to release tag/PR.

