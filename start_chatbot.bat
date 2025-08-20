@echo off
REM One-click launcher for your chatbot (backend + frontend)

REM Activate Python venv and start backend
start "Backend" cmd /k "cd /d %~dp0 && D:\chatbot\.venv\Scripts\python.exe -m uvicorn main:app --reload"

REM Start frontend React app
start "Frontend" cmd /k "cd /d %~dp0\frontend && npm start"

REM Wait a few seconds, then open browser
ping 127.0.0.1 -n 6 > nul
start http://localhost:3000

echo Chatbot is starting! You can close this window.
pause
