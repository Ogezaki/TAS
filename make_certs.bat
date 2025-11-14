@echo on
setlocal enabledelayedexpansion

where mkcert >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
  echo [ERR] mkcert introuvable.
  echo Installe mkcert puis relance :
  echo   choco install mkcert
  exit /b 2
)

for /f "usebackq delims=" %%A in (`py -3 get_ip.py 2^>nul`) do set SERVER_IP=%%A
if "%SERVER_IP%"=="" set SERVER_IP=127.0.0.1
echo [INFO] IP LAN : %SERVER_IP%

echo [CERT] mkcert -install
mkcert -install

echo [CERT] Generation cert.pem/key.pem pour %SERVER_IP% %COMPUTERNAME% localhost 127.0.0.1
mkcert -cert-file cert.pem -key-file key.pem %SERVER_IP% %COMPUTERNAME% localhost 127.0.0.1

if exist cert.pem if exist key.pem (
  echo [OK] Certificats crees.
  exit /b 0
) else (
  echo [ERR] Echec generation certificats.
  exit /b 1
)
