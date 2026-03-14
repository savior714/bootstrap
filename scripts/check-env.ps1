param(
    [switch]$Fix = $false
)

# scripts/diagnose_env.ps1
# Antigravity Environment Integrity Check Script
# Encoding: UTF-8 no BOM (Fixed to include Guidelines)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$allReportItems = @()

# --- Load Core Library ---
$coreLibPath = Join-Path $PSScriptRoot "lib\env-core.ps1"
if (Test-Path $coreLibPath) {
    . $coreLibPath
} else {
    Write-Error "Core library not found at: $coreLibPath"
    exit 1
}

# --- Validation Functions (Integration) ---
# Note: Complex validators are now in lib/env-core.ps1


# --- Main Execution ---

Write-Host "--- Antigravity Integrity Scan Start ---" -ForegroundColor Cyan

$allPassed = $true

# 1. Toolchain Verification
Write-Host "`n[1] Toolchain Verification" -ForegroundColor Gray
$results = @(
    (Test-ToolPresence -Name "Node.js" -Command "node"),
    (Test-ToolPresence -Name "Git"     -Command "git"),
    (Test-ToolPresence -Name "npm"     -Command "npm"),
    (Test-ToolPresence -Name "pnpm"    -Command "pnpm" -IsOptional $true),
    (Test-ToolPresence -Name "yarn"    -Command "yarn" -VersionArg "--version" -IsOptional $true)
)
foreach ($res in $results) { if ($null -ne $res -and -not $res) { $allPassed = $false } }

# 2. Config Integrity
Write-Host "`n[2] Configuration Integrity" -ForegroundColor Gray
$configResults = @(
    (Test-GitConfigSetting -Key "user.name"          -DisplayName "User Name"),
    (Test-GitConfigSetting -Key "user.email"         -DisplayName "User Email"),
    (Test-GitConfigSetting -Key "core.autocrlf"      -DisplayName "Auto CRLF" -ExpectedValue "false"),
    (Test-GitConfigSetting -Key "init.defaultBranch" -DisplayName "Default Branch" -ExpectedValue "main"),
    (Test-NpmConfigSetting -Key "registry"           -DisplayName "Registry URL")
)
foreach ($res in $configResults) { if ($null -ne $res -and -not $res) { $allPassed = $false } }

# 3. Encoding Integrity
Write-Host "`n[3] File System & Encoding Integrity" -ForegroundColor Gray

# ANSI Target (.bat files)
$ansiFiles = @(
    "$PSScriptRoot\..\bootstrap.bat"
)

# UTF-8 no BOM Target (Source code, Docs, Config)
$noBomFiles = @(
    "$PSScriptRoot\..\README.md",
    "$PSScriptRoot\..\package.json",
    "$PSScriptRoot\..\tsconfig.json",
    "$PSScriptRoot\..\docs\CRITICAL_LOGIC.md",
    "$PSScriptRoot\init-terminal.ps1"
)

# UTF-8 with BOM Required (Entry points for PS5)
$requireBomFiles = @(
    "$PSScriptRoot\..\Bootstrap-DevEnv.ps1",
    "$PSScriptRoot\check-env.ps1"
)

foreach ($f in $ansiFiles) {
    if (-not (Test-FileEncoding -Path $f -Required "ANSI")) { $allPassed = $false }
}
foreach ($f in $noBomFiles) {
    if (-not (Test-FileEncoding -Path $f -Required "UTF8NoBom")) { $allPassed = $false }
}
foreach ($f in $requireBomFiles) {
    if (-not (Test-FileEncoding -Path $f -Required "UTF8WithBom")) { $allPassed = $false }
}

# 4. IDE Verification
Write-Host "`n[4] IDE Settings Verification" -ForegroundColor Gray
if (-not (Test-VSCodeSettingsIntegrity -Path "$PSScriptRoot\..\.vscode\settings.json")) { $allPassed = $false }

# 5. Tech Stack dry-run
Write-Host "`n[5] Tech Stack Health Check (Dry-Run)" -ForegroundColor Gray
$techResults = @(
    (Test-NpxToolHealth -Name "TypeScript Compiler" -Command "tsc"),
    (Test-NpxToolHealth -Name "ESLint"              -Command "eslint" -IsOptional $true),
    (Test-NpxToolHealth -Name "Prettier"            -Command "prettier" -IsOptional $true)
)
foreach ($res in $techResults) { if ($null -ne $res -and -not $res) { $allPassed = $false } }

# 6. Network
Write-Host "`n[6] Network & Registry Reachability" -ForegroundColor Gray
$currentRegistry = (npm config get registry 2>$null)
if($currentRegistry) { $currentRegistry = $currentRegistry.Trim() }
if ($currentRegistry) {
    if (-not (Test-RegistryConnectivity -Name "Current NPM" -RegistryUrl $currentRegistry)) { $allPassed = $false }
}

# 7. Lint Policy
Write-Host "`n[7] Shared Lint Policy Verification" -ForegroundColor Gray
if (-not (Test-SharedLintPolicy -PolicyPath "$PSScriptRoot\..\shared_lint_rules.json" -LocalConfigPath "$PSScriptRoot\..\eslint.config.js")) { $allPassed = $false }

# 8. AI Behavioral Guidelines
Write-Host "`n[8] AI Behavioral Guidelines Verification" -ForegroundColor Gray
if (-not (Test-AIGuidelinesIntegrity -Path "$PSScriptRoot\..\AI_GUIDELINES.md" -TemplatePath "$PSScriptRoot\..\templates\AI_GUIDELINES.md")) { $allPassed = $false }

# Final Report
$reportPath = "$PSScriptRoot\env_report.json"
try {
    $reportJson = $allReportItems | ConvertTo-Json -Depth 5
    $utf8NoBom = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($reportPath, $reportJson, $utf8NoBom)
    Write-Host "`n--- Report saved to: ${reportPath} ---" -ForegroundColor Cyan
} catch {
    Write-Host "`n--- Failed to save report: $($_.Exception.Message) ---" -ForegroundColor Red
}

if (-not $allPassed) {
    Write-Host "`n--- Environment Integrity Check FAILED ---" -ForegroundColor Yellow
    $failCount = ($allReportItems | Where-Object { $_.Status -eq "FAIL" }).Count
    Write-Host "Total Failures: ${failCount}" -ForegroundColor Yellow
    exit 1
}

Write-Host "`n--- All integrity checks passed ---" -ForegroundColor Cyan
exit 0
