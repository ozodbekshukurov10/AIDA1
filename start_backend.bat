@echo off
cd /d "%~dp0"
echo Activating virtual environment...
call .venv\Scripts\activate.bat
echo Starting Django backend on http://127.0.0.1:8001 ...
python manage.py runserver 127.0.0.1:8001
pause
