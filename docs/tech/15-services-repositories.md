# Services and Repositories Documentation

This document provides a comprehensive reference for all service and repository classes in the LMS Backend system.

---

## Table of Contents

1. User Services and Repositories
2. Authentication Services
3. Course Services and Repositories
4. Lesson Services and Repositories
5. Enrollment Services and Repositories
6. Quiz Services and Repositories
7. Question Services
8. Attempt Services
9. Certificate Services
10. File Services

---

## 1. User Services and Repositories

### UserRepository

Location: app/modules/users/repositories/user_repository.py

#### Methods

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| get_by_id | user_id: UUID | User or None | Get user by UUID |
| get_by_email | email: str | User or None | Get user by email |
| list | page: int, page_size: int | tuple | List users |
| create | **fields | User | Create new user |
| update | user: User, **fields | User | Update user |

### UserService

Location: app/modules/users/services/user_service.py

#### Methods

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| create_user | payload: UserCreate | User | Create new user |
| authenticate | email, password | User | Authenticate user |
| update_user | user_id, payload | User | Update user |
| list_users | page, page_size | tuple | List users |
| get_user | user_id | User | Get user |

---

## 2. Authentication Services

### AuthService

Location: app/modules/auth/service.py

#### Methods

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| login | email, password | tuple | Login + MFA challenge |
| refresh_tokens | refresh_token | TokenResponse | Refresh tokens |
| logout | refresh_token, access_token | None | Logout |
| request_password_reset | email | tuple | Request reset |
| request_email_verification | email | tuple | Request verification |
| confirm_email_verification | token | None | Confirm verification |
| reset_password | token, new_password | None | Reset password |
| request_enable_mfa | user, password | tuple | Request MFA |
| confirm_enable_mfa | user, code | None | Confirm MFA |
| disable_mfa | user, password | None | Disable MFA |
| verify_mfa_login | challenge_token, code | tuple | Verify MFA |

---

## 3. Course Services and Repositories

### CourseRepository

| Method | Description |
|--------|-------------|
| get_by_id | Get course by ID |
| get_by_slug | Get course by slug |
| list | List courses with filters |
| create | Create course |
| update | Update course |
| delete | Delete course |

### CourseService

| Method | Description |
|--------|-------------|
| list_courses | List courses |
| get_course | Get course |
| create_course | Create course |
| update_course | Update course |
| publish_course | Publish course |
| delete_course | Delete course |

---

## 4. Lesson Services and Repositories

### LessonRepository

| Method | Description |
|--------|-------------|
| get_by_id | Get lesson |
| list_by_course | List lessons |
| count_by_course | Count lessons |
| get_next_order_index | Get next order |
| create | Create lesson |
| update | Update lesson |
| delete | Delete lesson |

### LessonService

| Method | Description |
|--------|-------------|
| list_lessons | List lessons |
| get_lesson | Get lesson |
| create_lesson | Create lesson |
| update_lesson | Update lesson |
| delete_lesson | Delete lesson |

---

## 5. Enrollment Services and Repositories

### EnrollmentRepository

| Method | Description |
|--------|-------------|
| get_by_id | Get enrollment |
| get_by_student_and_course | Get by student/course |
| list_by_student | List student enrollments |
| list_by_course | List course enrollments |
| create | Create enrollment |
| update | Update enrollment |
| get_lesson_progress | Get progress |
| upsert_lesson_progress | Upsert progress |
| get_enrollment_progress_stats | Get stats |
| get_course_stats | Get course stats |

### EnrollmentService

| Method | Description |
|--------|-------------|
| enroll | Enroll student |
| list_my_enrollments | List my enrollments |
| list_course_enrollments | List course enrollments |
| get_enrollment | Get enrollment |
| update_lesson_progress | Update progress |
| mark_lesson_completed | Mark completed |
| add_review | Add review |
| get_course_stats | Get stats |
| recalculate_enrollment_summary | Recalculate |

---

## 6. Quiz Services and Repositories

### QuizRepository

| Method | Description |
|--------|-------------|
| get_by_id | Get quiz |
| get_by_lesson | Get by lesson |
| list_by_course | List quizzes |
| list_by_course_with_stats | List with stats |
| create | Create quiz |
| update | Update quiz |
| count_questions | Count questions |
| total_points | Total points |

### QuizService

| Method | Description |
|--------|-------------|
| list_course_quizzes | List quizzes |
| list_course_quiz_items | List with stats |
| get_quiz | Get quiz |
| create_quiz | Create quiz |
| update_quiz | Update quiz |
| publish_quiz | Publish quiz |

---

## 7. Question Services

### QuestionRepository

| Method | Description |
|--------|-------------|
| get_by_id | Get question |
| list_by_quiz | List questions |
| get_next_order_index | Next order |
| create | Create question |
| update | Update question |
| delete | Delete question |

### QuestionService

| Method | Description |
|--------|-------------|
| add_question | Add question |
| update_question | Update question |
| list_quiz_questions | List questions |
| list_quiz_questions_for_management | List for management |

---

## 8. Attempt Services

### AttemptRepository

| Method | Description |
|--------|-------------|
| get_by_id | Get attempt |
| list_by_enrollment | List attempts |
| get_latest_attempt_number | Latest number |
| get_in_progress | In-progress attempt |
| create | Create attempt |
| update | Update attempt |
| calculate_percentage | Calculate score |

### AttemptService

| Method | Description |
|--------|-------------|
| start_attempt | Start attempt |
| get_quiz_for_taking | Get quiz |
| submit_attempt | Submit attempt |
| list_my_attempts | List attempts |
| get_attempt | Get attempt |
| build_attempt_result_answers | Build result |

---

## 9. Certificate Services

### CertificateService

| Method | Description |
|--------|-------------|
| issue_for_enrollment | Issue certificate |
| get_my_certificates | Get certificates |
| get_certificate_for_user | Get certificate |
| verify_certificate | Verify certificate |
| revoke_certificate | Revoke certificate |

---

## 10. File Services

### FileService

| Method | Description |
|--------|-------------|
| upload_file | Upload file |
| list_user_files | List files |
| get_file_for_user | Get file |
| get_download_target | Get download target |

---

## Summary

| Module | Repository | Service |
|--------|------------|---------|
| Users | UserRepository | UserService |
| Auth | - | AuthService |
| Courses | CourseRepository | CourseService |
| Lessons | LessonRepository | LessonService |
| Enrollments | EnrollmentRepository | EnrollmentService |
| Quizzes | QuizRepository | QuizService |
| Questions | QuestionRepository | QuestionService |
| Attempts | AttemptRepository | AttemptService |
| Certificates | - | CertificateService |
| Files | - | FileService |
