# Swagger Authorization Fix for FastAPI

## Problem
FastAPI Swagger UI doesn't automatically handle JWT or cookie-based authentication, making it difficult to test protected endpoints.

## Solution Implemented
I have implemented a comprehensive fix that adds proper OpenAPI security schemes and configuration.

## Changes Made

### 1. Updated `app/main.py`
Added `custom_openapi()` function that:
- Defines security schemes for both JWT (development) and cookie-based (production) authentication
- Automatically applies security to protected endpoints
- Uses environment-aware configuration (production vs development)

### 2. Security Schemes Added
- **OAuth2PasswordBearer**: For JWT token authentication in development
- **AccessTokenCookie**: For HttpOnly cookie authentication in production
- **RefreshTokenCookie**: For refresh token cookies in production

### 3. Protected Endpoints Configuration
The following endpoint patterns now have automatic security configuration:
- `/auth/login-cookie`, `/auth/refresh-cookie`, `/auth/logout-cookie`
- `/users/me`
- `/instructors/` (all instructor endpoints)
- `/admin/` (all admin endpoints)
- `/courses/`, `/enrollments/`, `/quizzes/`, `/assignments/`, `/analytics/`, `/certificates/`, `/payments/`, `/files/`

## How to Use After Implementation

### For Development Environment
1. Start your FastAPI application
2. Go to `http://localhost:8000/docs`
3. Click the **"Authorize"** button (top right corner)
4. Enter: `Bearer <your_jwt_token>`
5. Click **"Authorize"**
6. All protected endpoints will now include the Authorization header

### For Production Environment (Cookie-Based)
1. The Swagger UI will automatically look for `access_token` cookie
2. You can manually set cookies using browser developer tools:
   - `access_token`: Your JWT access token
   - `refresh_token`: Your JWT refresh token
3. Or use the "Authorize" button and enter cookie values

## Verification Steps

### Test 1: Check OpenAPI Schema
```bash
curl http://localhost:8000/openapi.json | grep -A 10 "securitySchemes"
```

Expected output should include:
- `"OAuth2PasswordBearer"`
- `"AccessTokenCookie"`
- `"RefreshTokenCookie"`

### Test 2: Verify Swagger UI
1. Access `/docs`
2. Look for "Authorize" button in top right
3. Click it and verify the security schemes are available

## Additional Notes

### Environment Configuration
- **Development**: Uses JWT token authentication (`OAuth2PasswordBearer`)
- **Production**: Uses cookie-based authentication (`AccessTokenCookie`)
- The configuration is environment-aware based on `settings.ENVIRONMENT`

### Security Best Practices
- HttpOnly cookies are properly configured for production
- CSP policy remains intact
- Rate limiting still applies
- JWT blacklist fail-closed behavior preserved

## Troubleshooting

### If "Authorize" button doesn't appear:
1. Ensure `ENABLE_API_DOCS=true` in your environment file
2. Restart the FastAPI application
3. Clear browser cache

### If authorization doesn't work:
1. Verify your token is valid
2. Check that the endpoint path matches the protected patterns
3. Ensure you're using the correct security scheme (JWT vs cookies)

## Files Modified
- `app/main.py` - Added custom OpenAPI configuration
- `docs/swagger_authorization_fix.md` - This documentation
- `scripts/test_swagger_auth.py` - Verification script

The implementation is now complete and ready for use. Swagger UI will now properly handle authorization for all protected endpoints.