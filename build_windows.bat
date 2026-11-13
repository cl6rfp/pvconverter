@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title PV Converter - Windows build

echo [1/5] Checking Python 3.12 (64-bit)...
py -3.12 -c "import sys; assert sys.maxsize > 2**32, 'Python de 32 bits no es compatible'" >nul 2>&1
if errorlevel 1 goto :python_error

if not exist ".venv-build\Scripts\python.exe" (
  py -3.12 -m venv ".venv-build"
  if errorlevel 1 goto :error
)
set "PYEXE=%CD%\.venv-build\Scripts\python.exe"

echo [2/5] Installing dependencies in isolated environment...
"%PYEXE%" -m pip install --disable-pip-version-check -r requirements.txt -r requirements-build.txt
if errorlevel 1 goto :error

echo [3/5] Checking source and dependencies...
"%PYEXE%" -m unittest -q test_gencad_parser test_pv_validation test_pvf_security test_route_audit test_connectivity_audit test_contact_audit test_layer_preview test_artwork_audit test_component_transform test_gencad_roundtrip_audit test_cad_coverage_audit test_source_features_audit
if errorlevel 1 goto :error
"%PYEXE%" test_arc_direction.py
if errorlevel 1 goto :error

echo [4/5] Building Windows distribution...
"%PYEXE%" -m PyInstaller --noconfirm --clean --windowed --onedir --name PV_Converter --collect-all zstandard --exclude-module matplotlib --exclude-module pandas pv_converter_gui.py
if errorlevel 1 goto :error

if not exist "dist\PV_Converter\PV_Converter.exe" goto :error

echo [5/5] Packaging portable distribution...
"%PYEXE%" scripts\package_windows.py
if errorlevel 1 goto :error

echo.
echo OK: dist\PV_Converter\PV_Converter.exe
echo ZIP: dist\PV_Converter_0.001.0010_Windows_x64.zip
echo.
echo IMPORTANTE: Verifica la GUI y la conversion en Windows antes de distribuir.
pause
exit /b 0

:python_error
echo ERROR: Instala Python 3.12 de 64 bits desde python.org.
echo Verifica que el lanzador "py" funcione.
pause
exit /b 1

:error
echo ERROR: La compilacion o alguna comprobacion ha fallado. Revisa el mensaje anterior.
pause
exit /b 1
