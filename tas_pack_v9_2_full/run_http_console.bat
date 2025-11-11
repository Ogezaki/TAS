@echo on
setlocal enabledelayedexpansion
set PYTHONUNBUFFERED=1

if not exist ".venv" (
  py -3 -m venv .venv
)
call .venv\Scripts\activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

set FLASK_APP=timer_app.py
set FLASK_ENV=production

python timer_app.py --host 0.0.0.0 --port 8080

echo.
echo ========= FIN (ExitCode=%ERRORLEVEL%) =========
pause
