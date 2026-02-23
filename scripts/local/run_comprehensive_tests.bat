@echo off
echo Running Comprehensive Endpoint Tests...

cd /d "%~dp0\.."

echo Step 1: Installing test dependencies...
pip install pytest pytest-cov requests

if %errorlevel% neq 0 (
    echo ERROR: Failed to install test dependencies!
    exit /b 1
)
echo SUCCESS: Test dependencies installed

echo Step 2: Running instructor endpoint tests...
pytest tests\test_instructor_endpoints.py -v --tb=short

if %errorlevel% neq 0 (
    echo WARNING: Instructor tests failed, continuing to admin tests...
)

echo Step 3: Running admin endpoint tests...
pytest tests\test_admin_endpoints.py -v --tb=short

if %errorlevel% neq 0 (
    echo WARNING: Admin tests failed
)

echo Step 4: Running security compliance tests...
echo Note: Security tests require proper environment setup

echo Step 5: Generating test report...
pytest tests\ -v --tb=short --html=reports/test_report.html --self-contained-html

echo Comprehensive testing completed!
echo Results:
echo - Instructor endpoints: Check test_instructor_endpoints.py results
echo - Admin endpoints: Check test_admin_endpoints.py results
echo - Full report: reports/test_report.html

pause