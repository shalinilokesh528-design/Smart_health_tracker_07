@echo off
echo Starting Django Development Server...
echo.
echo Please wait while the server starts...
echo.
cd /d "%~dp0"
python manage.py runserver 127.0.0.1:8000
pause

