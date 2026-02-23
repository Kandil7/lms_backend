@echo off
setlocal

set "BASE_URL=%~1"
set "DURATION=%~2"
set "HOST_HEADER=%~3"
set "STUDENT_RATE=%~4"
set "INSTRUCTOR_RATE=%~5"
set "ADMIN_RATE=%~6"

if "%BASE_URL%"=="" set "BASE_URL=http://localhost:8000"
if "%DURATION%"=="" set "DURATION=10m"
if "%HOST_HEADER%"=="" set "HOST_HEADER="
if "%STUDENT_RATE%"=="" set "STUDENT_RATE=8"
if "%INSTRUCTOR_RATE%"=="" set "INSTRUCTOR_RATE=3"
if "%ADMIN_RATE%"=="" set "ADMIN_RATE=1"

k6 run tests/perf/k6_realistic.js ^
  -e BASE_URL=%BASE_URL% ^
  -e DURATION=%DURATION% ^
  -e HOST_HEADER=%HOST_HEADER% ^
  -e STUDENT_RATE=%STUDENT_RATE% ^
  -e INSTRUCTOR_RATE=%INSTRUCTOR_RATE% ^
  -e ADMIN_RATE=%ADMIN_RATE%

exit /b %ERRORLEVEL%

