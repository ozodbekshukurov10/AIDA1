@echo off
cd /d "%~dp0frontend"
echo Installing dependencies if needed...
call npm install --silent
echo Starting Vite frontend on http://localhost:3000 ...
echo Make sure the backend is running on http://127.0.0.1:8001
npm run dev:vite
pause
