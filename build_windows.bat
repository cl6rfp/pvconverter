@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  set "PYEXE=.venv\Scripts\python.exe"
) else (
  set "PYEXE=py -3.12"
)
%PYEXE% -m pip install -r requirements.txt pyinstaller
if errorlevel 1 goto :error
%PYEXE% -m PyInstaller --noconfirm --clean --windowed --name PV_Converter --collect-all zstandard pv_converter_gui.py
if errorlevel 1 goto :error
echo.
echo Build complete: dist\PV_Converter\PV_Converter.exe
echo Copy the complete dist\PV_Converter folder to the target PC.
pause
exit /b 0
:error
echo Build failed. Review the error above.
pause
exit /b 1
