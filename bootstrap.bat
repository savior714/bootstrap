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
echo    [Extra] Go, Java 17, Android Studio, Docker, Supabase CLI
echo    [UI]    Windows Terminal
echo.
echo  Antigravity, VS Code, Cursor AI: install separately.
echo.
pause

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Bootstrap-DevEnv.ps1"

endlocal
