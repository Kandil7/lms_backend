# Module Guide: The Student Learning Journey

This guide covers the modules that track student progress and assessment.

---

## 🤝 Enrollments Module (`app/modules/enrollments`)
**Purpose**: Represents the "Active Learning State".

### Data Model:
- `user_id`, `course_id`.
- `progress_percentage`: 0-100 (Denormalized for performance).
- `last_accessed_at`: For "Resume Learning" features.

### Progress Calculation:
We use an **Event-Driven** approach.
1. Student completes a lesson (`POST /complete`).
2. API updates `LessonProgress` table.
3. API fires a background task `calculate_course_progress(enrollment_id)`.
4. Task counts total lessons vs. completed lessons and updates `enrollment.progress`.

---

## 📝 Quizzes Module (`app/modules/quizzes`)
**Purpose**: Assessment engine.

### Components:
- **Quiz**: Container with settings (`time_limit`, `pass_score`).
- **Question**: The actual content. Stored in `quiz_questions`.
  - `options` (JSONB): Stores choices `[{ "text": "A", "is_correct": true }]`.
- **QuizAttempt**: A student's specific session.
  - `answers` (JSONB): Stores the student's selections.

### Grading Logic (`service.py`):
- **Auto-Grading**: For MCQs, the service compares `attempt.answers` against `question.options` immediately upon submission.
- **Manual Grading**: For Essay questions, the attempt state is set to `pending_review`.

---

## 🎓 Certificates Module (`app/modules/certificates`)
**Purpose**: Reward completion.

### Trigger:
Listens for the `enrollment_completed` event (when progress hits 100%).

### PDF Generation:
- Uses `ReportLab` or `WeasyPrint`.
- **Template**: HTML/CSS template populated with student name and course date.
- **Security**: Generates a UUID `verify_id` and QR code linking to the verification page.
