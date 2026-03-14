@echo off
setlocal
title DevTools Installer Setup 2026
set "SCRIPT_DIR=%~dp0"

echo ========================================
echo   DevTools Installer Setup 2026
echo ========================================
echo.

:: [1] Check Admin
echo [Step 1] Checking Admin...
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Not running as Admin.
) else (
    echo [OK] Admin confirmed.
)
echo.

:: [2] Check winget
echo [Step 2] Checking winget...
winget --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] winget not found.
    pause
    exit /b 1
)
echo [OK] winget is available.
echo.

:: [3] Check Python 3.14
echo [Step 3] Checking Python 3.14...
python --version 2>nul | findstr "3.14" >nul
if %errorlevel% neq 0 (
    echo [INFO] Python 3.14 not found. Installing...
    winget install --id Python.Python.3.14 --silent --accept-package-agreements --accept-source-agreements
    if %errorlevel% neq 0 (
        echo [ERROR] Python installation failed.
        pause
        exit /b 1
    )
) else (
    echo [OK] Python 3.14 found.
)
echo.

:: [4] Dependencies
echo [Step 4] Installing dependencies...
cd /d "%SCRIPT_DIR%"

:: Check Internet
ping -n 1 pypi.org >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] No internet connection detected to pypi.org. 
    echo Installation might fail or hang.
)

:: Check Pip
echo [INFO] Checking pip...
python -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] pip not found, trying to initialize...
    python -m ensurepip --upgrade >nul 2>&1
)

echo [INFO] Installing from requirements.txt (Verbose mode)...
:: Using -v for visibility and removing --user if it causes issues for some
python -m pip install -r requirements.txt -v --no-input
if %errorlevel% neq 0 (
    echo.
    echo [WARNING] Some dependencies failed. Trying with --user flag...
    python -m pip install -r requirements.txt --user --no-input
)
echo [OK] Step 4 completed.
echo.

:: [5] Shortcut
echo [Step 5] Creating Desktop Shortcut...
powershell -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut('%USERPROFILE%\Desktop\DevTools Installer.lnk');$s.TargetPath='python.exe';$s.Arguments='\"%SCRIPT_DIR%DevToolsInstaller.py\"';$s.WorkingDirectory='%SCRIPT_DIR%';$s.IconLocation='%SCRIPT_DIR%devtools_icon.png';$s.Save()"
echo.

echo ========================================
echo   Setup Complete!
echo ========================================
echo.
echo [INFO] Launching app...
python "%SCRIPT_DIR%DevToolsInstaller.py"

echo.
echo If the app closed, check the terminal above for errors.
pause
exit /b 0
