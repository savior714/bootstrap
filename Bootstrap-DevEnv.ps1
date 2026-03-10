# Bootstrap-DevEnv.ps1
# Fresh Windows 11 Dev Environment Bootstrap (winget-based, interactive)
# Projects: eco_pediatrics, cheonggu, law, golf_scoring, stock_vercel, blog, fmkorea, mail, myllm
# UTF-8 with BOM - PS5 (powershell.exe) compatible

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

#region --- 0. Admin self-elevation ---
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "[ECO] Admin privileges required. Re-launching as Administrator..." -ForegroundColor Yellow
    Start-Process powershell -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs
    exit 0
}
#endregion

#region --- Helper functions ---
function Write-Header {
    param([string]$Msg)
    Write-Host ""
    Write-Host ("=" * 50) -ForegroundColor Cyan
    Write-Host "  $Msg" -ForegroundColor Cyan
    Write-Host ("=" * 50) -ForegroundColor Cyan
}
function Write-OK   { param([string]$Msg) Write-Host "  [OK]   $Msg" -ForegroundColor Green }
function Write-WARN { param([string]$Msg) Write-Host "  [WARN] $Msg" -ForegroundColor Yellow }
function Write-FAIL { param([string]$Msg) Write-Host "  [FAIL] $Msg" -ForegroundColor Red }
function Write-INFO { param([string]$Msg) Write-Host "  [....] $Msg" -ForegroundColor Gray }

function Install-Pkg {
    param(
        [string]$Id,
        [string]$Name,
        [string]$Override = "",
        [string]$Source = "winget"
    )
    Write-INFO "Installing $Name..."
    # Check if already installed
    $check = winget list --id $Id --exact -e 2>$null | Select-String $Id
    if ($check) {
        Write-OK "$Name already installed. Skipping."
        return $true
    }
    $wingetArgs = @("install", "--id", $Id, "--exact", "--silent",
                    "--accept-package-agreements", "--accept-source-agreements")
    if ($Override) { $wingetArgs += @("--override", $Override) }
    winget @wingetArgs 2>&1 | Out-Null
    # Exit code -1978335189 = WINGET_ALREADY_INSTALLED (also OK)
    if ($LASTEXITCODE -eq 0 -or $LASTEXITCODE -eq -1978335189) {
        Write-OK "$Name installed."
        return $true
    } else {
        Write-FAIL "$Name failed (exit $LASTEXITCODE). Install manually if needed."
        return $false
    }
}

function Refresh-EnvPath {
    $m = [System.Environment]::GetEnvironmentVariable("PATH", "Machine")
    $u = [System.Environment]::GetEnvironmentVariable("PATH", "User")
    $env:PATH = "$m;$u"
}

function Show-CheckMark {
    param([bool]$Selected)
    if ($Selected) { return "[X]" } else { return "[ ]" }
}
#endregion

#region --- 1. winget check ---
Write-Header "ECO Dev Environment Bootstrap"
Write-Host ""
try {
    $wgVer = (winget --version 2>&1)
    Write-OK "winget found: $wgVer"
} catch {
    Write-FAIL "winget not found. Update Windows 11 or install 'App Installer' from Microsoft Store."
    pause; exit 1
}
winget source update --disable-interactivity 2>$null | Out-Null
#endregion

#region --- 2. Package groups definition ---
# Each group: Name, Description, list of packages { Id, Name, [Override] }
$groups = [ordered]@{

    "1" = @{
        Label   = "Core (Git, Python 3.14, Node.js LTS, Rust, uv)"
        Default = $true
        Pkgs    = @(
            @{ Id = "Git.Git";              Name = "Git" },
            @{ Id = "Python.Python.3.14";   Name = "Python 3.14" },
            @{ Id = "OpenJS.NodeJS.LTS";    Name = "Node.js LTS" },
            @{ Id = "Rustlang.Rustup";      Name = "Rust (rustup)" },
            @{ Id = "astral-sh.uv";         Name = "uv (Python pkg manager)" }
        )
    }

    "3" = @{
        Label   = "VS Build Tools 2022 (MSVC + Windows SDK)"
        Default = $true
        Pkgs    = @(
            @{
                Id       = "Microsoft.VisualStudio.2022.BuildTools"
                Name     = "VS Build Tools 2022"
                Override = "--quiet --add Microsoft.VisualStudio.Workload.VCTools --add Microsoft.VisualStudio.Component.Windows11SDK.26100 --includeRecommended"
            }
        )
    }

    "4" = @{
        Label   = "Windows Terminal"
        Default = $true
        Pkgs    = @(
            @{ Id = "Microsoft.WindowsTerminal"; Name = "Windows Terminal" }
        )
    }

    "5" = @{
        Label   = "Go"
        Default = $false
        Pkgs    = @(
            @{ Id = "GoLang.Go"; Name = "Go" }
        )
    }

    "6" = @{
        Label   = "Java (Temurin JDK 17 LTS)"
        Default = $false
        Pkgs    = @(
            @{ Id = "EclipseAdoptium.Temurin.17.JDK"; Name = "Temurin JDK 17" }
        )
    }

    "7" = @{
        Label   = "Android Studio"
        Default = $false
        Pkgs    = @(
            @{ Id = "Google.AndroidStudio"; Name = "Android Studio" }
        )
    }

    "8" = @{
        Label   = "Docker Desktop"
        Default = $false
        Pkgs    = @(
            @{ Id = "Docker.DockerDesktop"; Name = "Docker Desktop" }
        )
    }

    "9" = @{
        Label   = "Supabase CLI"
        Default = $false
        Pkgs    = @(
            @{ Id = "Supabase.CLI"; Name = "Supabase CLI" }
        )
    }
}
#endregion

#region --- 3. Interactive selection menu ---
# Build selection state (default values)
$selected = @{}
foreach ($key in $groups.Keys) {
    $selected[$key] = $groups[$key].Default
}

function Draw-Menu {
    Clear-Host
    Write-Host ""
    Write-Host "  ╔══════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "  ║       ECO Dev Environment - Package Selector     ║" -ForegroundColor Cyan
    Write-Host "  ╠══════════════════════════════════════════════════╣" -ForegroundColor Cyan
    Write-Host "  ║  Toggle: press number key  |  Install: [Enter]   ║" -ForegroundColor DarkCyan
    Write-Host "  ║  Select all: [A]           |  Deselect all: [N]  ║" -ForegroundColor DarkCyan
    Write-Host "  ╚══════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    foreach ($key in $groups.Keys) {
        $g   = $groups[$key]
        $chk = if ($selected[$key]) { "[X]" } else { "[ ]" }
        $col = if ($selected[$key]) { "Green" } else { "Gray" }
        Write-Host ("  [{0}] {1} {2}" -f $key, $chk, $g.Label) -ForegroundColor $col
    }
    Write-Host ""
}

# Menu loop
while ($true) {
    Draw-Menu
    $key = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    $ch  = $key.Character.ToString().ToUpper()

    if ($ch -eq "`r" -or $key.VirtualKeyCode -eq 13) { break }  # Enter
    if ($ch -eq "A") { foreach ($k in $groups.Keys) { $selected[$k] = $true } }
    if ($ch -eq "N") { foreach ($k in $groups.Keys) { $selected[$k] = $false } }
    if ($groups.ContainsKey($ch)) { $selected[$ch] = -not $selected[$ch] }
}
#endregion

#region --- 4. Installation ---
Clear-Host
Write-Header "Installing selected packages..."

$installResults = @{}

foreach ($key in $groups.Keys) {
    if (-not $selected[$key]) { continue }
    $g = $groups[$key]
    Write-Host ""
    Write-Host "  >>> $($g.Label)" -ForegroundColor Cyan

    $allOk = $true
    foreach ($pkg in $g.Pkgs) {
        $override = if ($pkg.ContainsKey("Override")) { $pkg.Override } else { "" }
        $ok = Install-Pkg -Id $pkg.Id -Name $pkg.Name -Override $override
        if (-not $ok) { $allOk = $false }
    }
    $installResults[$key] = $allOk
}
#endregion

#region --- 5. Post-install steps ---
Write-Header "Post-install configuration"
Refresh-EnvPath

# Rust: stable toolchain & shim generation
if ($selected["1"]) {
    Write-INFO "Configuring Rust stable toolchain..."
    $rustupExe = "$env:USERPROFILE\.cargo\bin\rustup.exe"
    if (Test-Path $rustupExe) {
        & $rustupExe toolchain install stable --no-self-update 2>&1 | Out-Null
        & $rustupExe default stable 2>&1 | Out-Null
        Write-OK "Rust stable toolchain ready."
    } else {
        Write-WARN "rustup.exe not found. Open a new terminal and run: rustup toolchain install stable"
    }
}

# Java: JAVA_HOME 설정
if ($selected["6"]) {
    $javaPath = "C:\Program Files\Eclipse Adoptium\jdk-17*"
    $found = Get-ChildItem $javaPath -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($found) {
        [System.Environment]::SetEnvironmentVariable("JAVA_HOME", $found.FullName, "Machine")
        $env:JAVA_HOME = $found.FullName
        Write-OK "JAVA_HOME set to: $($found.FullName)"
    } else {
        Write-WARN "JAVA_HOME not set automatically - set it manually after installation."
    }
}

# Android Studio: ANDROID_HOME hint
if ($selected["7"]) {
    Write-WARN "Android Studio installed. After first launch:"
    Write-WARN "  Set ANDROID_HOME = C:\Users\$env:USERNAME\AppData\Local\Android\Sdk"
    Write-WARN "  Add to PATH: %ANDROID_HOME%\platform-tools"
}
#endregion

#region --- 6. Final summary ---
Write-Header "Installation Summary"
Refresh-EnvPath

$verChecks = @(
    @{ Name = "git";     Cmd = "git";     Args = @("--version") },
    @{ Name = "python";  Cmd = "python";  Args = @("--version") },
    @{ Name = "node";    Cmd = "node";    Args = @("-v") },
    @{ Name = "npm";     Cmd = "npm";     Args = @("-v") },
    @{ Name = "uv";      Cmd = "uv";      Args = @("--version") },
    @{ Name = "pwsh";    Cmd = "pwsh";    Args = @("--version") },
    @{ Name = "cargo";   Cmd = "$env:USERPROFILE\.cargo\bin\cargo.exe"; Args = @("--version") },
    @{ Name = "rustup";  Cmd = "$env:USERPROFILE\.cargo\bin\rustup.exe"; Args = @("--version") },
    @{ Name = "go";      Cmd = "go";      Args = @("version") },
    @{ Name = "java";    Cmd = "java";    Args = @("-version") },
    @{ Name = "docker";  Cmd = "docker";  Args = @("--version") },
    @{ Name = "supabase";Cmd = "supabase";Args = @("--version") }
)

Write-Host ""
foreach ($c in $verChecks) {
    try {
        $out = & $c.Cmd @($c.Args) 2>&1 | Select-Object -First 1
        if ($out) { Write-OK "$($c.Name.PadRight(12)) $out" }
    } catch { <# not installed / not selected - silently skip #> }
}

Write-Host ""
Write-Host "  [NEXT STEPS]" -ForegroundColor Cyan
Write-Host "  1. Open a NEW terminal (apply PATH changes)" -ForegroundColor White
Write-Host "  2. Clone/navigate to project directory" -ForegroundColor White
Write-Host "  3. Run: eco.bat -> [2] Environment Setup" -ForegroundColor White
if ($selected["3"]) {
    Write-Host ""
    Write-Host "  NOTE: VS Build Tools may still be installing in background." -ForegroundColor Yellow
    Write-Host "        Wait for it before running native builds (Tauri, pyiceberg)." -ForegroundColor Yellow
}
Write-Host ""
pause
#endregion
