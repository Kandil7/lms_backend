# Complete Utilities and Helpers Documentation

This document provides comprehensive documentation for all utility functions and helper modules in the LMS Backend system.

---

## Table of Contents

1. [Pagination Utilities](#1-pagination-utilities)
2. [Validators](#2-validators)
3. [Constants](#3-constants)

---

## 1. Pagination Utilities

**Location:** `app/utils/pagination.py`

The pagination module provides utilities for paginating database query results.

### PageParams

```python
from app.utils.pagination import PageParams

# Create pagination parameters
params = PageParams(page=1, page_size=20)

# Access properties
params.page        # 1
params.page_size   # 20
params.offset      # 0 (calculated)
```

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `page` | int | Current page number (1-indexed) |
| `page_size` | int | Number of items per page |
| `offset` | int | SQL OFFSET value |

### paginate Function

```python
from app.utils.pagination import paginate, PageParams

# Usage with database query
params = PageParams(page=1, page_size=20)

# Get total count
total = await db.execute(select(User).count())

# Get items
offset = params.offset
users = await db.execute(
    select(User).offset(offset).limit(params.page_size)
)

# Create paginated response
result = paginate(users, total, params)
```

### Response Format

```python
{
    "items": [...],           # List of items
    "total": 150,            # Total number of items
    "page": 1,               # Current page
    "page_size": 20,         # Items per page
    "total_pages": 8          # Total number of pages
}
```

### Pagination Examples

```python
# Example 1: Simple pagination
params = PageParams(page=1, page_size=10)
query = query.offset(params.offset).limit(params.page_size)

# Example 2: With search
search_term = "python"
params = PageParams(page=2, page_size=15)
query = query.filter(User.name.ilike(f"%{search_term}%"))
query = query.offset(params.offset).limit(params.page_size)

# Example 3: With sorting
params = PageParams(page=1, page_size=20)
query = query.order_by(User.created_at.desc())
query = query.offset(params.offset).limit(params.page_size)
```

---

## 2. Validators

**Location:** `app/utils/validators.py`

### slugify

Converts a string to a URL-friendly slug.

```python
from app.utils.validators import slugify

# Convert course title to slug
slug = slugify("Introduction to Python Programming")
# Result: "introduction-to-python-programming"

slug = slugify("  Python 101   ")
# Result: "python-101"

slug = slugify("Learn Python! @home")
# Result: "learn-python-home"
```

### Algorithm

1. Trim whitespace
2. Convert to lowercase
3. Remove special characters (keep only a-z, 0-9, spaces, hyphens)
4. Replace multiple spaces/hyphens with single hyphen
5. Trim leading/trailing hyphens

### ensure_allowedExtension

Validates file extension against allowed list.

```python
from app.utils.validators import ensure_allowed_extension

# Validate extension
try:
    ext = ensure_allowed_extension(
        "document.pdf",
        allowed_extensions=["pdf", "doc", "docx"]
    )
    # ext = "pdf"
except ValueError as e:
    # Handle invalid extension
    print(e)  # "File extension '.exe' is not allowed"
```

### normalize_storageFolder

Normalizes and validates storage folder paths.

```python
from app.utils.validators import normalize_storage_folder

# Valid paths
normalize_storage_folder("uploads")           # "uploads"
normalize_storage_folder("uploads/images")     # "uploads/images"
normalize_storage_folder("uploads/videos/2024") # "uploads/videos/2024"

# Invalid paths (raises ValueError)
normalize_storage_folder("/etc")               # ValueError: Invalid folder path
normalize_storage_folder("../../../etc")        # ValueError: Invalid folder path
normalize_storage_folder("uploads/../etc")     # ValueError: Invalid folder path
```

### Validation Rules

1. Cannot start with `/`
2. Cannot contain `..` (directory traversal)
3. Each segment must match `[A-Za-z0-9_-]+`

---

## 3. Constants

**Location:** `app/utils/constants.py`

This file contains application-wide constants.

```python
from app.utils.constants import (
    # Pagination
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    
    # File uploads
    MAX_UPLOAD_SIZE,
    ALLOWED_EXTENSIONS,
    
    # User roles
    ROLE_ADMIN,
    ROLE_INSTRUCTOR,
    ROLE_STUDENT,
)
```

### Common Constants

| Constant | Value | Description |
|----------|-------|-------------|
| DEFAULT_PAGE_SIZE | 20 | Default pagination size |
| MAX_PAGE_SIZE | 100 | Maximum items per page |
| ROLE_ADMIN | "admin" | Administrator role |
| ROLE_INSTRUCTOR | "instructor" | Instructor role |
| ROLE_STUDENT | "student" | Student role |

---

## Summary

The utilities module provides:

1. **Pagination** - Easy pagination for database queries
2. **Validators** - Input validation for slugs, files, paths
3. **Constants** - Centralized constant definitions

These utilities help maintain consistency across the application.
