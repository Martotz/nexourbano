@echo off
rem Sube el repo a GitHub (Martotz/nexourbano). Doble clic. Si Git pide iniciar sesion, se abre el navegador.
cd /d "%~dp0\.."
set GIT="C:\Program Files\Git\cmd\git.exe"
if not exist evidence\_consola mkdir evidence\_consola
title NexoUrbano - subir a GitHub
(
  echo === %date% %time%
  %GIT% -c safe.directory=* remote remove origin 2>nul
  %GIT% -c safe.directory=* remote add origin https://github.com/Martotz/nexourbano.git
  %GIT% -c safe.directory=* push -u origin main
  if errorlevel 1 (echo PUSH_FALLO) else (echo PUSH_OK)
  %GIT% -c safe.directory=* ls-remote origin
) > evidence\_consola\github.log 2>&1
type evidence\_consola\github.log
echo.
echo ===== Terminado =====
pause
