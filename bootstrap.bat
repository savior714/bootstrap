@chcp 65001 > nul
@echo off
setlocal

echo.
echo  ==========================================
echo    ECO Dev Environment Bootstrap
echo  ==========================================
echo.
echo  Installs development tools via winget.
echo  You will be able to select which to install.
echo.
echo  Tools available:
echo    [Core]  Git, Python 3.14, Node.js LTS, Rust, uv
echo    [Build] VS Build Tools 2022 (MSVC + Windows SDK)
echo    [Shell] PowerShell 7 (pwsh)
echo    [Extra] Go, Java 17, Android Studio, Docker, Supabase CLI
echo    [UI]    Windows Terminal
echo.
echo  Antigravity, VS Code, Cursor AI: install separately.
echo.
pause

REM Detect pwsh (PS7) or fallback to powershell (PS5)
set "PS_CMD=pwsh.exe"
where %PS_CMD% >nul 2>nul
if %ERRORLEVEL% neq 0 set "PS_CMD=powershell.exe"

%PS_CMD% -NoProfile -ExecutionPolicy Bypass -File "%~dp0Bootstrap-DevEnv.ps1"

endlocal
