# Database Architecture & Migrations

This guide covers the data layer of the LMS, including schema design principles, key relationships, and the migration workflow.

---

## 📋 Table of Contents
1. [Schema Design Principles](#1-schema-design-principles)
2. [Core Entity Relationships](#2-core-entity-relationships)
3. [JSONB for Flexibility](#3-jsonb-for-flexibility)
4. [Indexing Strategy](#4-indexing-strategy)
5. [Alembic Migration Workflow](#5-alembic-migration-workflow)

---

## 1. Schema Design Principles
Our database design prioritizes **security, performance, and flexibility**:

- **Primary Keys**: We use `UUID` (Universally Unique Identifiers) for all tables. This prevents "Enumeration Attacks" where attackers guess IDs by incrementing numbers.
- **Timestamps**: Every table includes `created_at` and `updated_at` for auditing and data synchronization.
- **Strict Typing**: We use PostgreSQL-specific types like `JSONB`, `INET` (for IP addresses), and custom `ENUMs` to ensure data integrity at the storage level.

---

## 2. Core Entity Relationships
Understanding how data connects is crucial for building new features.

### The "Golden Triangle" of Learning
1. **Users**: The actors (Students, Instructors, Admins).
2. **Courses**: The learning material (contains Lessons and Quizzes).
3. **Enrollments**: The junction that connects a User to a Course, tracking their specific journey.

### Data Flow Example
- A `User` (student) creates an `Enrollment` for a `Course`.
- As the student views `Lessons`, we create `LessonProgress` records.
- When the student finishes a `Quiz`, a `QuizAttempt` is linked to their `Enrollment`.

---

## 3. JSONB for Flexibility
While we prefer structured tables, some data is inherently dynamic. We use `JSONB` for:
- **Quiz Options**: Stores questions and their multiple-choice options in a single field.
- **Metadata**: User preferences, social links, or course prerequisites.
- **Audit Logs**: Storing snapshots of "before" and "after" states for changes.

---

## 4. Indexing Strategy
To maintain low latency as the database grows, we apply strategic indexes:
- **B-Tree**: On all primary and foreign keys.
- **Unique**: On `email`, `slug`, and combined fields (e.g., `user_id` + `course_id` in enrollments).
- **GIN (Generalized Inverted Index)**: For searching within `JSONB` fields.
- **Partial Indexes**: For frequently queried subsets (e.g., `WHERE is_published = TRUE`).

---

## 5. Alembic Migration Workflow
We use **Alembic** to manage schema changes safely.

### How to add a new column/table:
1. **Modify the Model**: Update your SQLAlchemy model in `app/modules/*/models.py`.
2. **Auto-generate Migration**:
   ```bash
   alembic revision --autogenerate -m "Add description to courses"
   ```
3. **Review**: Open the generated file in `alembic/versions/` and verify the `upgrade()` and `downgrade()` functions.
4. **Apply**:
   ```bash
   alembic upgrade head
   ```

### Best Practices:
- **Never delete migration files** that have been pushed to production.
- **Always provide a downgrade path** in your migration scripts.
- **Avoid complex logic** in migrations; keep them strictly for schema changes.

---

## 🛠️ DB Debugging Tips
- **View Schema**: Use `\d+ table_name` in `psql`.
- **Check Migrations**: `alembic current` shows the latest applied migration.
- **Query JSONB**:
  ```sql
  SELECT * FROM quizzes WHERE options->>'type' = 'multiple_choice';
  ```
