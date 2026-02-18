# Code Examples

This document provides practical code examples for common LMS operations.

---

## 1. User Registration and Authentication

### Register a New User

from app.modules.users.schemas import UserCreate
from app.modules.users.services.user_service import UserService
from app.core.database import SessionLocal

db = SessionLocal()
try:
    service = UserService(db)
    user = service.create_user(
        payload=UserCreate(
            email="student@example.com",
            full_name="John Student",
            password="securepassword123",
            role="student"
        )
    )
    print(f"Created user: {user.id}")
finally:
    db.close()

### Login

from app.modules.users.services.user_service import UserService, InvalidCredentialsError

db = SessionLocal()
try:
    service = UserService(db)
    try:
        user = service.authenticate(
            email="student@example.com",
            password="securepassword123"
        )
        print(f"Logged in: {user.email}")
    except InvalidCredentialsError:
        print("Invalid credentials")
finally:
    db.close()

---

## 2. Creating a Course

### Create Course

from app.modules.courses.schemas.course import CourseCreate
from app.modules.courses.services.course_service import CourseService
from app.core.database import SessionLocal

db = SessionLocal()
try:
    service = CourseService(db)
    course = service.create_course(
        payload=CourseCreate(
            title="Python Programming Basics",
            slug="python-basics",
            description="Learn Python from scratch",
            category="programming",
            difficulty_level="beginner",
            estimated_duration_minutes=120
        ),
        current_user=instructor
    )
    print(f"Created course: {course.id}")
finally:
    db.close()

---

## 3. Enrolling a Student

from app.modules.enrollments.service import EnrollmentService
from app.core.database import SessionLocal

db = SessionLocal()
try:
    service = EnrollmentService(db)
    enrollment = service.enroll(
        student_id=student.id,
        course_id=course.id
    )
    print(f"Enrolled: {enrollment.id}")
finally:
    db.close()

---

## 4. Taking a Quiz

### Start Quiz Attempt

from app.modules.quizzes.services.attempt_service import AttemptService

db = SessionLocal()
try:
    service = AttemptService(db)
    attempt = service.start_attempt(
        quiz_id=quiz.id,
        current_user=student
    )
    print(f"Attempt started: {attempt.id}")
finally:
    db.close()

### Submit Quiz

from app.modules.quizzes.schemas.attempt import AttemptSubmitRequest, AnswerSubmission

attempt = service.submit_attempt(
    quiz_id=quiz.id,
    attempt_id=attempt.id,
    payload=AttemptSubmitRequest(
        answers=[
            AnswerSubmission(
                question_id=q1.id,
                selected_option_id="option_1"
            )
        ]
    ),
    current_user=student
)

print(f"Score: {attempt.score}/{attempt.max_score}")
print(f"Passed: {attempt.is_passed}")

---

## 5. Generating a Certificate

from app.modules.certificates.service import CertificateService

service = CertificateService(db)
certificates = service.get_my_certificates(student.id)

if certificates:
    cert = certificates[0]
    print(f"Certificate: {cert.certificate_number}")

# Verify
result = service.verify_certificate("CERT-20240115-ABC123")
if result:
    print(f"Valid for: {result.student.full_name}")

---

## 6. Progress Tracking

from app.modules.enrollments.schemas import LessonProgressUpdate

progress = service.update_lesson_progress(
    enrollment_id=enrollment.id,
    lesson_id=lesson.id,
    payload=LessonProgressUpdate(
        status="completed",
        completion_percentage=100.00
    ),
    current_user=student
)

print(f"Progress: {progress.completion_percentage}%")

---

## Summary

This guide covers:
1. User Authentication
2. Course Creation
3. Student Enrollment
4. Quiz Taking
5. Certificate Generation
6. Progress Tracking
