@echo off
rem Lanzador para doble clic: corre el paso escrito en tools\paso.txt (ej. "s1") y graba la consola
rem en evidence\_consola\<paso>.log. Equivale a abrir PowerShell y escribir .\run.ps1 <paso>.
cd /d "%~dp0\.."
set /p PASO=<tools\paso.txt
if "%PASO%"=="" set PASO=help
if not exist evidence\_consola mkdir evidence\_consola
title NexoUrbano - run.ps1 %PASO%
powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Transcript -Path 'evidence\_consola\%PASO%.log' -Force | Out-Null; try { .\run.ps1 %PASO% } catch { Write-Host ('ERROR: ' + $_) -ForegroundColor Red }; Stop-Transcript | Out-Null"
echo.
echo ===== Terminado: %PASO% =====
pause
