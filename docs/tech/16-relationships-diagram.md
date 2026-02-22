# Entity Relationships Diagram

This document provides a complete entity relationship diagram for the LMS Backend.

## Entity Relationship Diagram

```
USERS (id, email, password_hash, full_name, role, is_active, mfa_enabled, metadata, created_at, updated_at, last_login_at, email_verified_at)
  |
  +-- courses (1:N) --> COURSES (id, title, slug, description, instructor_id FK, category, difficulty_level, is_published, thumbnail_url, estimated_duration_minutes, metadata, created_at, updated_at)
  |     |
  |     +-- lessons (1:N) --> LESSONS (id, course_id FK, title, slug, description, content, lesson_type, order_index, parent_lesson_id FK, duration_minutes, video_url, is_preview, metadata, created_at, updated_at)
  |     |     |
  |     |     +-- quiz (1:1) --> QUIZZES (id, lesson_id FK unique, title, description, quiz_type, passing_score, time_limit_minutes, max_attempts, shuffle_questions, shuffle_options, show_correct_answers, is_published, created_at, updated_at)
  |     |     |     |
  |     |     |     +-- questions (1:N) --> QUIZ_QUESTIONS (id, quiz_id FK, question_text, question_type, points, order_index, explanation, options, correct_answer, metadata)
  |     |     |     |
  |     |     |     +-- attempts (1:N) --> QUIZ_ATTEMPTS (id, enrollment_id FK, quiz_id FK, attempt_number, status, started_at, submitted_at, graded_at, score, max_score, percentage, is_passed, time_taken_seconds, answers)
  |     |     |
  |     |     +-- lesson_progress (1:N) --> LESSON_PROGRESS (id, enrollment_id FK, lesson_id FK, status, started_at, completed_at, time_spent_seconds, last_position_seconds, completion_percentage, attempts_count, metadata)
  |     |
  |     +-- enrollments (1:N) --> ENROLLMENTS (id, student_id FK, course_id FK, enrolled_at, started_at, completed_at, status, progress_percentage, completed_lessons_count, total_lessons_count, total_time_spent_seconds, last_accessed_at, certificate_issued_at, rating, review)
  |           |
  |           +-- certificates (1:1) --> CERTIFICATES (id, enrollment_id FK unique, student_id FK, course_id FK, certificate_number unique, pdf_path, completion_date, issued_at, is_revoked, revoked_at)
  |
  +-- enrollments (1:N) --> ENROLLMENTS
  |
  +-- certificates (1:N) --> CERTIFICATES
  |
  +-- uploaded_files (1:N) --> UPLOADED_FILES (id, uploader_id FK, filename, original_filename, file_url, storage_path, file_type, mime_type, file_size, folder, storage_provider, is_public, created_at)
  |
  +-- refresh_tokens (1:N) --> REFRESH_TOKENS (id, user_id FK, token_jti, expires_at, revoked_at, created_at)
```

## Foreign Key Constraints

| Table | Column | References | On Delete |
|-------|--------|------------|-----------|
| courses | instructor_id | users.id | RESTRICT |
| lessons | course_id | courses.id | CASCADE |
| lessons | parent_lesson_id | lessons.id | SET NULL |
| quizzes | lesson_id | lessons.id | CASCADE |
| quiz_questions | quiz_id | quizzes.id | CASCADE |
| enrollments | student_id | users.id | CASCADE |
| enrollments | course_id | courses.id | CASCADE |
| lesson_progress | enrollment_id | enrollments.id | CASCADE |
| lesson_progress | lesson_id | lessons.id | CASCADE |
| quiz_attempts | enrollment_id | enrollments.id | CASCADE |
| quiz_attempts | quiz_id | quizzes.id | CASCADE |
| certificates | enrollment_id | enrollments.id | CASCADE |
| certificates | student_id | users.id | CASCADE |
| certificates | course_id | courses.id | CASCADE |
| refresh_tokens | user_id | users.id | CASCADE |
| uploaded_files | uploader_id | users.id | CASCADE |

## Cascade Behaviors

- CASCADE: Delete propagates to child records
- RESTRICT: Prevents delete if children exist
- SET NULL: Sets foreign key to NULL on parent delete

## Indexes Summary

- users: email (unique), role, created_at, email_verified_at
- courses: slug (unique), category, difficulty, is_published, instructor_id
- lessons: course_id, (course_id, lesson_type, order_index)
- enrollments: student_id, course_id, status, (student_id, enrolled_at)
- quizzes: lesson_id (unique)
- quiz_attempts: enrollment_id, quiz_id, submitted_at
- certificates: enrollment_id (unique), certificate_number (unique)
- refresh_tokens: user_id, token_jti (unique)

## Check Constraints

- users.role: admin|instructor|student
- courses.difficulty_level: beginner|intermediate|advanced|NULL
- lessons.lesson_type: video|text|quiz|assignment
- enrollments.status: active|completed|dropped|expired
- lesson_progress.status: not_started|in_progress|completed
- quizzes.quiz_type: practice|graded
- quiz_questions.question_type: multiple_choice|true_false|short_answer|essay
- quiz_attempts.status: in_progress|submitted|graded
