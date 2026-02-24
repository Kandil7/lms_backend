# Frontend Integration Guide

This guide is designed for frontend developers building client applications (Web, Mobile, etc.) that consume the EduConnect Pro LMS API.

---

## 📋 Table of Contents
1. [API Connectivity](#1-api-connectivity)
2. [Authentication Flow](#2-authentication-flow)
3. [Error Handling](#3-error-handling)
4. [Pagination & Filtering](#4-pagination--filtering)
5. [File Uploads](#5-file-uploads)
6. [WebSocket Integration](#6-websocket-integration)

---

## 1. API Connectivity
- **Base URL**: `https://egylms.duckdns.org/api/v1` (Production) or `http://localhost:8000/api/v1` (Development).
- **Format**: All requests and responses use **JSON**.
- **CORS**: Ensure your frontend domain is added to the `CORS_ORIGINS` list in the backend `.env`.

---

## 2. Authentication Flow
We support two modes of authentication. The backend determines which one to use based on the `ENVIRONMENT` setting.

### JWT Mode (Development/Mobile)
1. **Login**: `POST /auth/login` returns an `access_token` and `refresh_token`.
2. **Usage**: Include the token in every request header:
   `Authorization: Bearer <your_access_token>`
3. **Refresh**: When the access token expires (401 error), call `POST /auth/refresh` with the refresh token.

### Cookie Mode (Production Web)
1. **Login**: `POST /auth/login-cookie` sets `HttpOnly` cookies automatically.
2. **CSRF**: Fetch the CSRF token from the initial handshake and include it in the `X-CSRF-Token` header for all state-changing requests (POST, PUT, DELETE).
3. **Logout**: `POST /auth/logout-cookie` clears the cookies.

---

## 3. Error Handling
The backend uses a standard error format:
```json
{
  "detail": "Error message string"
}
```
Or for validation errors (422):
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "invalid email format",
      "type": "value_error.email"
    }
  ]
}
```

### Common Status Codes:
- `401 Unauthorized`: Token expired or invalid.
- `403 Forbidden`: User role does not have permission.
- `404 Not Found`: Resource ID does not exist.
- `422 Unprocessable Entity`: Validation failed (check the `detail` array).
- `429 Too Many Requests`: Rate limit hit.

---

## 4. Pagination & Filtering
For list endpoints (e.g., `GET /courses`), use query parameters:
- `page`: Page number (starting from 1).
- `page_size`: Items per page (default 10).
- `search`: Search query string.
- `sort`: Field name to sort by.

---

## 5. File Uploads
- **Endpoint**: `POST /files/upload`
- **Method**: `multipart/form-data`
- **Field Name**: `file`
- **Response**: Returns a `file_id` and `file_url`. Store the `file_id` to link it to courses or user profiles.

---

## 6. WebSocket Integration
For real-time progress or notifications:
- **URL**: `wss://egylms.duckdns.org/api/v1/ws`
- **Auth**: Pass the token in the query string: `?token=<jwt_token>`.
- **Message Format**:
  ```json
  {
    "type": "progress_update",
    "data": {
      "course_id": "uuid",
      "percentage": 85.5
    }
  }
  ```

---

## 🛠️ Tools & Tips
- **Swagger UI**: Visit `/docs` on the backend to test endpoints interactively.
- **Postman**: Import our collection from `postman/` for a pre-configured testing environment.
- **TypeScript**: We recommend generating types from the backend's `openapi.json` to ensure contract synchronization.
