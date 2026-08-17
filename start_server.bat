@echo off
title CCI Skill Academy Backend Server
echo ========================================================
echo        CCI SKILL ACADEMY - BACKEND & ADMIN SERVER
echo ========================================================
echo Starting server on http://localhost:8000 ...
echo.
echo Admin Portal:        http://localhost:8000/admin
echo Certificate Verify:  http://localhost:8000/verify
echo API Documentation:   http://localhost:8000/docs
echo ========================================================
echo.
..\.venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
pause
