@echo off
cd /d %~dp0
if not exist .venv\Scripts\python.exe (
  echo Creating virtual environment...
  py -m venv .venv
  call .venv\Scripts\activate
  python -m pip install -r requirements.txt
) else (
  call .venv\Scripts\activate
)
start "MarketPulse" cmd /c "python app.py"
timeout /t 2 /nobreak >nul
start "" http://127.0.0.1:5000
