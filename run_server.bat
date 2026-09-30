@echo off
cd %~dp0
call venv\Scripts\activate.bat
uvicorn main:app --reload