@echo off
REM One-click launcher for Windows
if not exist venv (
    python -m venv venv
)
call venv\Scripts\activate
python -m pip install --upgrade pip
pip install PySide6 matplotlib
python main.py
pause
