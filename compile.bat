@echo off
setlocal
pushd "%~dp0"
if errorlevel 1 exit /b 1

java -jar .\KickAss.jar .\main.asm
if errorlevel 1 (
    echo Error de compilacion. No se iniciara VICE.
    popd
    exit /b 1
)

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0run-vice.ps1"
set "viceResult=%ERRORLEVEL%"
popd
exit /b %viceResult%
