# Module Guide: Course Content & Assets

This guide explores the modules that manage the core learning material.

---

## 📚 Courses Module (`app/modules/courses`)
**Purpose**: Structure and delivery of educational content.

### Data Model Hierarchy:
1. **Course**:
   - `id`, `title`, `slug`, `instructor_id`.
   - `status`: `draft`, `published`, `archived`.
2. **Lesson**:
   - `id`, `course_id`, `parent_lesson_id` (for sections).
   - `type`: `video`, `text`, `quiz`, `assignment`.
   - `order_index`: Determines the sequence.

### Recursive Structure:
We use a **Self-Referencing Adjacency List** for sections.
- A "Module" is just a Lesson where `type=section`.
- A "Lesson" inside that module has `parent_lesson_id = module_id`.
- **Querying**: We use a Recursive CTE (Common Table Expression) in `repository.py` to fetch the full tree in one query.

---

## 📁 Files Module (`app/modules/files`)
**Purpose**: Securely handle user-uploaded content.

### The Problem:
Allowing direct file uploads is risky (malware, storage exhaustion).

### The Solution:
1. **Validation**: `service.py` uses `python-magic` to verify the *actual* file type (not just the extension).
2. **Storage**:
   - **Local**: `uploads/` (Dev).
   - **S3/Blob**: (Prod) The service abstracts this via a `StorageProvider` interface.
3. **Access Control**:
   - Files are private by default.
   - `GET /files/{id}` checks if the `current_user` has access (e.g., enrolled in the course that owns the file).

### Flow:
1. Client `POST /files/upload` -> Server validates & saves -> Returns `File` object.
2. Client `POST /courses/{id}/lessons` -> Payload includes `file_id`.
