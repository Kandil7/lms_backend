#!/bin/bash
# Environment file security validator
# Usage: ./validate_env.sh <environment_file>

set -e

FILE="$1"

if [ -z "$FILE" ]; then
    echo "Usage: $0 <environment_file>"
    echo "Example: $0 .env.production"
    exit 1
fi

if [ ! -f "$FILE" ]; then
    echo "Error: File '$FILE' not found"
    exit 1
fi

echo "🔍 Validating environment file: $FILE"
echo "====================================="

# Check for hardcoded secrets (CRITICAL)
CRITICAL_ISSUES=0
WARNING_ISSUES=0

# Hardcoded database passwords
if grep -q "change-strong-db-password" "$FILE"; then
    echo "❌ CRITICAL: Hardcoded database password detected"
    echo "   Line: $(grep -n "change-strong-db-password" "$FILE")"
    CRITICAL_ISSUES=$((CRITICAL_ISSUES + 1))
fi

# Hardcoded secret keys
if grep -q "replace-with-a-strong-random-secret" "$FILE" || grep -q "change-me" "$FILE"; then
    echo "❌ CRITICAL: Hardcoded secret key detected"
    echo "   Line: $(grep -n -E "replace-with-a-strong-random-secret|change-me" "$FILE")"
    CRITICAL_ISSUES=$((CRITICAL_ISSUES + 1))
fi

# Weak default values
if grep -q "admin" "$FILE" | grep -q "password"; then
    echo "⚠️  WARNING: Admin credentials pattern detected"
    WARNING_ISSUES=$((WARNING_ISSUES + 1))
fi

# Missing required variables
REQUIRED_VARS=("POSTGRES_USER" "POSTGRES_PASSWORD" "SECRET_KEY")
for VAR in "${REQUIRED_VARS[@]}"; do
    if ! grep -q "^$VAR=" "$FILE"; then
        echo "⚠️  WARNING: Required variable '$VAR' not found"
        WARNING_ISSUES=$((WARNING_ISSUES + 1))
    fi
done

# Check for sensitive data in git (security best practice)
if git status --porcelain | grep -q "\.env"; then
    echo "❌ CRITICAL: Environment file appears to be tracked by git"
    echo "   This is a severe security risk - environment files should NEVER be committed"
    CRITICAL_ISSUES=$((CRITICAL_ISSUES + 1))
fi

# Summary
echo ""
echo "📊 Validation Summary:"
echo "Critical issues: $CRITICAL_ISSUES"
echo "Warning issues: $WARNING_ISSUES"

if [ "$CRITICAL_ISSUES" -gt 0 ]; then
    echo ""
    echo "❌ FAILED: $CRITICAL_ISSUES critical security issues found"
    echo "Environment file is NOT secure for production deployment"
    exit 1
elif [ "$WARNING_ISSUES" -gt 0 ]; then
    echo ""
    echo "⚠️  WARNING: $WARNING_ISSUES warning issues found"
    echo "Environment file requires review before production deployment"
    exit 2
else
    echo ""
    echo "✅ PASSED: No critical security issues found"
    echo "Environment file is secure for production deployment"
    exit 0
fi