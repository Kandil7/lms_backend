
# Data Flows Documentation

This document describes the complete data flows for key operations in the LMS Backend system.

---

## Table of Contents

1. User Registration Flow
2. Authentication and Login Flow
3. Course Creation Flow
4. Course Enrollment Flow
5. Lesson Progress Flow
6. Quiz Taking Flow
7. Certificate Generation Flow
8. File Upload Flow
9. Password Reset Flow
10. MFA Setup Flow

---

## 1. User Registration Flow

### Steps

1. User submits registration request
2. System validates email and password
3. System checks if email already exists
4. System creates user record with hashed password
5. System generates JWT tokens
6. System sends welcome email (async)
7. System sends email verification email (async)
8. Returns tokens to client

### Database Changes
- INSERT into users table

---

## 2. Authentication and Login Flow

### Steps

1. User submits credentials
2. System validates email format
3. System looks up user by email
4. System verifies password
5. If MFA enabled: Generate MFA challenge
6. If MFA disabled: Issue tokens directly
7. If MFA: Send code via email
8. User submits MFA code
9. System verifies MFA code
10. Issue tokens

### MFA Challenge Flow
- Challenge Token: JWT with type=mfa_challenge
- Code: 6-digit random number stored in Redis
- Timeout: 10 minutes

---

## 3. Course Creation Flow

### Steps

1. Authenticated instructor submits course data
2. System validates permissions (instructor or admin)
3. System generates slug if not provided
4. System checks slug uniqueness
5. System creates course record
6. System invalidates course cache
7. Returns created course

### Cache Invalidation
- Delete: courses:*
- Delete: lessons:*

---

## 4. Course Enrollment Flow

### Steps

1. Student submits enrollment request
2. System validates course exists
3. System checks course is published
4. System checks no existing enrollment
5. System creates enrollment record
6. System calculates initial progress
7. System commits to database
8. Returns enrollment

### Initial Values
- status: active
- progress_percentage: 0.00
- completed_lessons_count: 0

---

## 5. Lesson Progress Flow

### Steps

1. Student updates lesson progress
2. System validates enrollment ownership
3. System validates lesson belongs to course
4. System gets or creates progress record
5. System updates progress values
6. System recalculates enrollment summary
7. If completed: Trigger certificate check
8. System commits changes
9. Async: Recalculate progress task

### Progress Status Transitions
- not_started -> in_progress (on any activity)
- in_progress -> completed (when 100%)
- completed -> cannot downgrade (enforced)

---

## 6. Quiz Taking Flow

### Start Attempt

1. Student requests to start quiz
2. System validates quiz is published
3. System validates enrollment
4. Check for existing in-progress attempt
5. Check time limit
6. Check max attempts not exceeded
7. Create new attempt record
8. Return attempt

### Submit Quiz

1. Student submits answers
2. System validates attempt belongs to student
3. System validates attempt is in_progress
4. Validate all answers against questions
5. Grade each question
6. Calculate total score and percentage
7. Determine pass/fail
8. If passed: Mark lesson as complete
9. Commit changes

### Question Grading
- Multiple choice: Match option_id
- True/False: Case-insensitive string match
- Short answer: Case-insensitive string match
- Essay: Always 0 points

---

## 7. Certificate Generation Flow

### Automatic Generation

1. Progress service marks lesson complete
2. Enrollment recalculated: completed >= total
3. Enrollment status changes to completed
4. System detects: certificate_issued_at is NULL
5. Task queued: generate_certificate

### Manual Generation

1. Admin requests certificate generation
2. System validates enrollment exists
3. System validates enrollment is completed
4. Generate certificate number
5. Generate PDF
6. Create certificate record
7. Update enrollment

### Certificate Number Format
CERT-YYYYMMDD-XXXXXX
Example: CERT-20240115-A1B2C3

---

## 8. File Upload Flow

### Steps

1. User uploads file
2. System validates file size
3. System validates file extension
4. System generates safe filename
5. System determines storage backend
6. Backend saves file
7. System creates file record
8. System returns file info

### Storage Backends
- Local: Save to filesystem
- S3: Upload to AWS S3

---

## 9. Password Reset Flow

### Request Reset

1. User submits email
2. System looks up user
3. If user exists and active: Generate token
4. Send reset email
5. Return generic message

### Reset Password

1. User submits token and new password
2. System validates token
3. System updates password hash
4. System revokes all active refresh tokens
5. System blacklists old access tokens
6. Commit changes

---

## 10. MFA Setup Flow

### Request Enable MFA

1. User submits password
2. System verifies password
3. System generates MFA code
4. System stores code in cache
5. System sends code via email

### Confirm Enable MFA

1. User submits MFA code
2. System retrieves cached code
3. System compares codes
4. System sets user.mfa_enabled = true
5. System deletes cached code
6. Commit changes

---

## Summary

| Flow | Key Components | Async Tasks |
|------|----------------|--------------|
| Registration | UserService, AuthService | Welcome email |
| Login | AuthService, Token blacklist | MFA code email |
| Course Creation | CourseService | - |
| Enrollment | EnrollmentService | - |
| Progress | EnrollmentService | Recalculate progress |
| Quiz | AttemptService, QuizService | - |
| Certificate | CertificateService | Generate PDF |
| File Upload | FileService | - |
| Password Reset | AuthService | Reset email |
| MFA | AuthService, Cache | MFA code email |

Each flow follows the pattern:
1. Validate input
2. Check permissions
3. Database operations
4. Additional actions
5. Commit transaction
6. Return response
