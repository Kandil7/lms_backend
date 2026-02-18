# Module Design Decisions - Why We Chose This

This document explains the key design decisions made for each module in the LMS Backend, the alternatives considered, and why we chose the current implementation.

---

## Table of Contents

1. [Auth Module Decisions](#1-auth-module-decisions)
2. [Users Module Decisions](#2-users-module-decisions)
3. [Courses Module Decisions](#3-courses-module-decisions)
4. [Enrollments Module Decisions](#4-enrollments-module-decisions)
5. [Quizzes Module Decisions](#5-quizzes-module-decisions)
6. [Certificates Module Decisions](#6-certificates-module-decisions)
7. [Files Module Decisions](#7-files-module-decisions)
8. [Analytics Module Decisions](#8-analytics-module-decisions)

---

## 1. Auth Module Decisions

### Decision: JWT Token Strategy

**Question:** Why use JWT tokens instead of server-side sessions?

**Options Considered:**

| Option | Pros | Cons |
|--------|------|------|
| Server Sessions | Simple, secure | Not scalable, requires sticky sessions |
| JWT Tokens | Stateless, scalable | Token management complexity |
| OAuth2 | Industry standard | Overkill for single app |

**Our Choice:** JWT Tokens

**Reasoning:**
- **Scalability**: JWT is stateless, works across multiple API servers
- **Mobile Support**: Easier to integrate with mobile apps
- **Industry Standard**: Widely accepted pattern
- **Redis Blacklist**: Solves the revocation problem

### Decision: Dual Token System

**Question:** Why separate access and refresh tokens?

**Our Choice:** Access token (15 min) + Refresh token (30 days)

**Reasoning:**
- **Security**: Short-lived access tokens limit damage if compromised
- **UX**: Users stay logged in with refresh tokens
- **Revocation**: Can revoke refresh token to force re-login

### Decision: MFA Implementation

**Question:** Why use numeric codes instead of TOTP apps?

**Our Choice:** Numeric codes (sent to user during MFA flow)

**Reasoning:**
- **Simplicity**: No QR code scanning required
- **Fallback**: Codes work without smartphone
- **Flexibility**: Can be extended to TOTP later

### Decision: Token Blacklisting

**Question:** How to handle logout and token revocation?

**Implementation:**
- Store blacklisted JWT IDs (jti) in Redis
- Check blacklist on each authenticated request

**Reasoning:**
- JWTs are inherently stateless
- Redis provides fast lookups
- TTL matches token expiration

---

## 2. Users Module Decisions

### Decision: UUID Primary Keys

**Question:** Why use UUID instead of auto-increment integers?

**Options Considered:**

| Option | Pros | Cons |
|--------|------|------|
| Auto-increment | Simple, small | Predictable, hard to merge |
| UUID4 | Random, distributed | Larger, random order |
| ULID | Sortable, random | Additional dependency |

**Our Choice:** UUID4

**Reasoning:**
- **Security**: Not guessable IDs
- **Distributed Systems**: No central ID generation
- **PostgreSQL Support**: Native UUID type

### Decision: JSON Metadata Column

**Question:** How to handle flexible user profile data?

**Options Considered:**

| Option | Pros | Cons |
|--------|------|------|
| Fixed Columns | Fast, indexed | Inflexible |
| EAV Tables | Flexible | Slow, complex |
| JSONB Column | Flexible, fast | Limited indexing |

**Our Choice:** JSONB metadata column

**Reasoning:**
- **Flexibility**: Add fields without migrations
- **Performance**: JSONB is optimized in PostgreSQL
- **Type Safety**: Still typed in Python

### Decision: Role Constraint

**Question:** How to enforce valid roles?

**Implementation:** Check constraint in database

```sql
CHECK (role IN ('admin','instructor','student'))
```

**Reasoning:**
- **Data Integrity**: No invalid roles in database
- **Defense in Depth**: Database-level protection

---

## 3. Courses Module Decisions

### Decision: Course-Lesson Hierarchy

**Question:** How to structure course content?

**Options Considered:**

| Option | Pros | Cons |
|--------|------|------|
| Flat (all lessons) | Simple | No organization |
| Nested (folders) | Organized | Complex queries |
| Linear (ordered list) | Simple + organized | Default choice |

**Our Choice:** Linear ordered list with optional parent-child

**Reasoning:**
- **Simplicity**: Most courses are linear
- **Flexibility**: Parent-child for modules/units
- **Ordering**: Explicit order_index, not dependent on ID

### Decision: Slug-Based URLs

**Question:** How to identify courses in URLs?

**Options Considered:**

| Option | Pros | Cons |
|--------|------|------|
| `/courses/123` | Simple | Not SEO friendly |
| `/courses/python-basics` | SEO friendly | Requires uniqueness |
| `/courses/123-python-basics` | Both | Complex |

**Our Choice:** Slug-based (`/courses/python-basics`)

**Reasoning:**
- **SEO**: Human-readable URLs
- **Bookmarks**: Easy to remember
- **Uniqueness**: Unique constraint enforced

### Decision: Publish Workflow

**Question:** How to handle course visibility?

**Implementation:** Boolean `is_published` flag

**Reasoning:**
- **Draft/Published**: Standard CMS pattern
- **Preview**: Instructors can preview before publishing
- **Simple**: No complex states

### Decision: RESTRICT Delete for Instructor

**Question:** What happens when instructor is deleted?

**Implementation:** `FOREIGN KEY ... ON DELETE RESTRICT`

**Reasoning:**
- **Data Integrity**: Can't delete instructor with courses
- **Warning**: Clear error message
- **Alternative**: Admin must reassign courses first

---

## 4. Enrollments Module Decisions

### Decision: Separate Progress Table

**Question:** Why not store progress directly in Enrollment?

**Options Considered:**

| Option | Pros | Cons |
|--------|------|------|
| Single Table | Simple | Can't track per-lesson |
| Separate Table | Granular tracking | More complex |

**Our Choice:** Separate LessonProgress table

**Reasoning:**
- **Granularity**: Track each lesson individually
- **Resume**: Students can resume from specific lesson
- **Analytics**: Detailed progress data
- **Video**: Track video position

### Decision: Progress Calculation

**Question:** How to calculate overall progress?

**Formula:**
```
progress_percentage = (completed_lessons / total_lessons) * 100
```

**Reasoning:**
- **Simple**: Easy to understand
- **Fair**: Equal weight per lesson
- **Alternative**: Could use time-based (future enhancement)

### Decision: Unique Constraint

**Question:** Can a student enroll in the same course twice?

**Implementation:** `UNIQUE (student_id, course_id)`

**Reasoning:**
- **Data Integrity**: One enrollment per student per course
- **Alternative**: Could allow retakes (future enhancement)

### Decision: Decimal for Percentages

**Question:** Why use DECIMAL instead of FLOAT?

**Reasoning:**
- **Precision**: FLOAT can have rounding errors
- **Money**: Same reason we don't use FLOAT for money
- **Example**: 33.3333333... vs 33.33

---

## 5. Quizzes Module Decisions

### Decision: One Quiz Per Lesson

**Question:** Why limit to one quiz per lesson?

**Reasoning:**
- **Simplicity**: Clear association
- **UX**: Students know what comes after lesson
- **Extension**: Can be extended later if needed

### Decision: JSON for Answers

**Question:** How to store question options and answers?

**Options Considered:**

| Option | Pros | Cons |
|--------|------|------|
| Separate Tables | Normalized, queryable | Complex joins |
| JSON Column | Flexible, simple | Less queryable |

**Our Choice:** JSON columns for options and answers

**Reasoning:**
- **Flexibility**: Different question types have different structures
- **Simplicity**: No complex schema changes
- **Performance**: Acceptable for this use case

### Decision: Auto-Grading

**Question:** How to grade quiz attempts?

**Implementation:** Automatic grading for objective questions

**Question Types:**
- `multiple_choice`: Match answer to correct option
- `true_false`: Exact match
- `short_answer`: Case-insensitive match (keyword)

**Reasoning:**
- **Scale**: Manual grading doesn't scale
- **Objectivity**: Consistent scoring
- **Future**: Essay questions can be manually graded

### Decision: Attempt Tracking

**Question:** How to track multiple attempts?

**Implementation:**
- Attempt number per enrollment/quiz
- Status: in_progress → submitted → graded

**Reasoning:**
- **Audit**: Complete history of attempts
- **Limits**: Respects max_attempts setting
- **Time Tracking**: Time taken per attempt

---

## 6. Certificates Module Decisions

### Decision: Certificate Per Enrollment

**Question:** Why only one certificate per enrollment?

**Implementation:** `UNIQUE (enrollment_id)`

**Reasoning:**
- **Simplicity**: One completion = one certificate
- **Verification**: Unique certificate number
- **Alternative**: Could allow reissuance (future enhancement)

### Decision: Unique Certificate Numbers

**Question:** How to generate verifiable certificates?

**Format:** `CERT-YYYYMMDD-XXXXXX`

**Reasoning:**
- **Uniqueness**: Extremely low collision probability
- **Verification**: Public API to verify by number
- **Date**: Contains issue date information

### Decision: PDF Storage

**Question:** Why store PDF files rather than generate on-demand?

**Reasoning:**
- **Performance**: Serve static files, not generate each time
- **Consistency**: Certificate won't change
- **Cost**: Generation is CPU-intensive

---

## 7. Files Module Decisions

### Decision: Storage Abstraction

**Question:** How to support multiple storage providers?

**Implementation:** Abstract base class with implementations

```python
class FileStorage(ABC):
    @abstractmethod
    async def upload(self, file, path) -> str: pass

class LocalStorage(FileStorage): ...
class S3Storage(FileStorage): ...
```

**Reasoning:**
- **Flexibility**: Easy to switch providers
- **Testing**: Can mock for tests
- **Extensibility**: Add GCS, Azure, etc.

### Decision: Unique Filenames

**Question:** How to handle file naming?

**Implementation:** UUID-based filenames with original filename stored

**Reasoning:**
- **Uniqueness**: No filename conflicts
- **Security**: Prevent path traversal
- **Reference**: Original filename for display

### Decision: File Type Validation

**Question:** How to prevent malicious uploads?

**Implementation:**
- MIME type validation
- Extension whitelist
- File size limits

**Reasoning:**
- **Security**: Prevent executable uploads
- **Storage**: Prevent abuse
- **Type Safety**: Expected file types only

---

## 8. Analytics Module Decisions

### Decision: No Separate Analytics Tables

**Question:** Why not store analytics data separately?

**Reasoning:**
- **Simplicity**: Calculate from existing data
- **Accuracy**: Always current
- **Storage**: No duplicate data
- **Trade-off**: Slower for complex queries (acceptable)

### Decision: Different Endpoints for Different Roles

**Question:** How to organize analytics endpoints?

**Implementation:**
- `/analytics/my-*` → Student view
- `/analytics/courses/{id}` → Course view
- `/analytics/instructors/{id}` → Instructor view
- `/analytics/system/*` → Admin view

**Reasoning:**
- **Role-based**: Each role sees relevant data
- **Security**: Permissions enforced per endpoint
- **Simplicity**: No complex query parameters

---

## Summary Table

| Decision | Our Choice | Alternative | Reason |
|----------|------------|-------------|--------|
| Auth Tokens | JWT | Sessions | Scalability |
| User IDs | UUID | Auto-increment | Security |
| User Profiles | JSONB | Fixed columns | Flexibility |
| Course URLs | Slug | ID-based | SEO |
| Lesson Order | order_index | ID-based | Explicit |
| Progress | Separate table | Single record | Granularity |
| Quiz Answers | JSON | Normalized tables | Flexibility |
| Certificates | PDF storage | Generate on-demand | Performance |
| File Storage | Abstract class | Single implementation | Extensibility |
| Analytics | On-the-fly | Pre-aggregated | Accuracy |

This documentation explains the reasoning behind key architectural decisions for each module in the LMS Backend.
