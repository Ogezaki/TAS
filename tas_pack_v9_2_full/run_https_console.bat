@echo on
setlocal enabledelayedexpansion
set PYTHONUNBUFFERED=1

if not exist ".venv" (
  py -3 -m venv .venv
)
call .venv\Scripts\activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

for /f "usebackq delims=" %%A in (`python get_ip.py`) do set SERVER_IP=%%A
if "%SERVER_IP%"=="" set SERVER_IP=127.0.0.1
echo [SETUP] IP LAN : %SERVER_IP%

set FLASK_APP=timer_app.py
set FLASK_ENV=production

if not exist cert.pem (
  echo [WARN] cert.pem / key.pem absents -> tentative HTTPS 'adhoc' (necessite 'cryptography')
)

echo [RUN] Lancement TAS (HTTPS 8443 prioritaire, fallback HTTP 8080 si besoin)...
python timer_app.py --host 0.0.0.0 --port 8080 --https 1 --https-port 8443 --cert cert.pem --key key.pem

echo.
echo ========= FIN (ExitCode=%ERRORLEVEL%) =========
pause
