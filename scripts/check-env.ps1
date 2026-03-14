param(
    [switch]$Fix = $false
)

# scripts/diagnose_env.ps1
# Antigravity Environment Integrity Check Script
# Encoding: UTF-8 no BOM

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$allReportItems = @()

# --- Helper Functions ---

function Update-VSCodeSetting {
    param($Key, $Value)
    $path = "$PSScriptRoot\..\.vscode\settings.json"
    $dir = Split-Path $path
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    if (-not (Test-Path $path)) { Set-Content -Path $path -Value "{}" -Encoding utf8 }
    
    $config = Get-Content $path -Raw | ConvertFrom-Json
    $config | Add-Member -MemberType NoteProperty -Name $Key -Value $Value -Force
    $config | ConvertTo-Json | Set-Content -Path $path -Encoding utf8
    Write-Host "Updated VSCode setting: ${Key} = ${Value}" -ForegroundColor Cyan
}

function Invoke-EslintConfigUpdate {
    param($Rules)
    Write-Host "Please manually update eslint.config.js with rules: ${Rules}" -ForegroundColor Yellow
}

function Add-ReportItem {
    param($Category, $Item, $Status, $Message, $FixCommand = "")
    $statusStr = if ($Status) { "PASS" } else { "FAIL" }
    $ts = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    
    $obj = New-Object PSObject
    $obj | Add-Member -MemberType NoteProperty -Name "Category" -Value $Category
    $obj | Add-Member -MemberType NoteProperty -Name "Item" -Value $Item
    $obj | Add-Member -MemberType NoteProperty -Name "Status" -Value $statusStr
    $obj | Add-Member -MemberType NoteProperty -Name "Message" -Value $Message
    $obj | Add-Member -MemberType NoteProperty -Name "FixCommand" -Value $FixCommand
    $obj | Add-Member -MemberType NoteProperty -Name "Timestamp" -Value $ts
    $script:allReportItems += $obj

    if ($Status) {
        Write-Host ("[PASS] [{0}] ${Item}: {1}" -f $Category, $Message) -ForegroundColor Green
    } else {
        Write-Host ("[FAIL] [{0}] ${Item}: {1}" -f $Category, $Message) -ForegroundColor Red
        if ($FixCommand) {
            Write-Host ("  -> FIX: ${FixCommand}") -ForegroundColor Yellow
            if ($script:Fix) {
                Write-Host "  -> Attempting Auto-Fix..." -ForegroundColor Cyan
                try {
                    Invoke-Expression $FixCommand
                    Write-Host "  -> Auto-Fix Success!" -ForegroundColor Green
                } catch {
                    Write-Host "  -> Auto-Fix Failed: $($_.Exception.Message)" -ForegroundColor Red
                }
            }
        }
    }
}

# --- Validation Functions ---

function Test-ToolPresence {
    param(
        [string]$Name,
        [string]$Command,
        [string]$VersionArg = "--version",
        [bool]$IsOptional = $false,
        [string]$Category = "Toolchain"
    )

    try {
        $toolPath = Get-Command $Command -ErrorAction SilentlyContinue
        if (-not $toolPath) {
            if ($IsOptional) {
                Add-ReportItem -Category $Category -Item $Name -Status $true -Message "Optional tool ${Command} is missing (Skipped)"
                return $true
            }
            Add-ReportItem -Category $Category -Item $Name -Status $false -Message "${Command} is not in PATH" -FixCommand "winget install ${Command}"
            return $false
        }

        $out = & $Command $VersionArg 2>&1
        $exitCode = $LASTEXITCODE
        $versionRaw = ($out | Select-Object -First 1 | Out-String).Trim()
        
        if ($exitCode -ne 0 -and $exitCode -ne -1) {
            Add-ReportItem -Category $Category -Item $Name -Status $false -Message "Error running ${Command} (ExitCode: $exitCode) - ${versionRaw}"
            return $false
        }

        Add-ReportItem -Category $Category -Item $Name -Status $true -Message "$($toolPath.Source) - ${versionRaw}"
        return $true
    }
    catch {
        Add-ReportItem -Category $Category -Item $Name -Status $false -Message "Exception during ${Name} check: $($_.Exception.Message)"
        return $false
    }
}

function Test-GitConfigSetting {
    param([string]$Key, [string]$DisplayName, [string]$ExpectedValue = $null, [string]$Category = "GitConfig")
    try {
        $val = (git config --get $Key 2>$null)
        if ($null -eq $val) { $val = "" } else { $val = $val.Trim() }
        
        if ([string]::IsNullOrWhiteSpace($val)) {
            Add-ReportItem -Category $Category -Item $DisplayName -Status $false -Message "Missing Git config '${Key}'" -FixCommand "git config --global ${Key} <your_value>"
            return $false
        }
        
        if ($ExpectedValue -and $val -ne $ExpectedValue) {
            Add-ReportItem -Category $Category -Item $DisplayName -Status $false -Message "Value mismatch: ${val} (Expected: ${ExpectedValue})" -FixCommand "git config --global ${Key} ${ExpectedValue}"
            return $false
        }

        Add-ReportItem -Category $Category -Item $DisplayName -Status $true -Message $val
        return $true
    }
    catch {
        Add-ReportItem -Category $Category -Item $DisplayName -Status $false -Message "Error checking Git config '${Key}': $($_.Exception.Message)"
        return $false
    }
}

function Test-NpmConfigSetting {
    param([string]$Key, [string]$DisplayName, [string]$Category = "NpmConfig")
    try {
        $val = (npm config get $Key 2>$null)
        if ($null -eq $val) { $val = "" } else { $val = $val.Trim() }

        if ([string]::IsNullOrWhiteSpace($val) -or $val -eq "undefined") {
            Add-ReportItem -Category $Category -Item $DisplayName -Status $false -Message "Missing NPM config '${Key}'" -FixCommand "npm config set ${Key} <your_value>"
            return $false
        }
        Add-ReportItem -Category $Category -Item $DisplayName -Status $true -Message $val
        return $true
    }
    catch {
        Add-ReportItem -Category $Category -Item $DisplayName -Status $false -Message "Error checking NPM config '${Key}': $($_.Exception.Message)"
        return $false
    }
}

function Test-FileEncoding {
    param([string]$Path, [string]$Category = "Encoding")
    $fileName = Split-Path $Path -Leaf
    try {
        if (-not (Test-Path $Path)) {
            Add-ReportItem -Category $Category -Item $fileName -Status $false -Message "File not found"
            return $false
        }

        $bytes = [System.IO.File]::ReadAllBytes($Path)
        
        if ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) {
            Add-ReportItem -Category $Category -Item $fileName -Status $false -Message "BOM detected (UTF-8 with BOM)" -FixCommand "powershell -File $PSScriptRoot/fix-encoding.ps1 $Path"
            return $false
        }

        Add-ReportItem -Category $Category -Item $fileName -Status $true -Message "UTF-8 no BOM"
        return $true
    }
    catch {
        Add-ReportItem -Category $Category -Item $fileName -Status $false -Message "Error checking encoding: $($_.Exception.Message)"
        return $false
    }
}

function Test-VSCodeSettingsIntegrity {
    param([string]$Path, [string]$Category = "IDE")
    try {
        if (-not (Test-Path $Path)) {
            Add-ReportItem -Category $Category -Item "settings.json" -Status $false -Message "Missing .vscode/settings.json" -FixCommand "Update-VSCodeSetting -Key 'files.encoding' -Value 'utf8'"
            return $false
        }

        $content = Get-Content $Path -Raw | ConvertFrom-Json
        $success = $true

        $expected = @{
            "files.encoding"          = "utf8"
            "files.insertFinalNewline" = $true
            "editor.tabSize"           = 2
            "editor.formatOnSave"      = $true
        }

        foreach ($key in $expected.Keys) {
            $val = $content.$key
            if ($null -eq $val) {
                Add-ReportItem -Category $Category -Item $key -Status $false -Message "Missing setting '${key}'" -FixCommand "Update-VSCodeSetting -Key ${key} -Value $($expected[$key])"
                $success = $false
            } elseif ($val -ne $expected[$key]) {
                Add-ReportItem -Category $Category -Item $key -Status $false -Message "Mismatch: ${val} (Expected: $($expected[$key]))" -FixCommand "Update-VSCodeSetting -Key ${key} -Value $($expected[$key])"
                $success = $false
            }
        }
        if ($success) {
            Add-ReportItem -Category $Category -Item "settings.json" -Status $true -Message "All essential rules OK"
        }
        return $success
    }
    catch {
        Add-ReportItem -Category $Category -Item "settings.json" -Status $false -Message "Error checking VSCode settings: $($_.Exception.Message)"
        return $false
    }
}

function Test-NpxToolHealth {
    param(
        [string]$Name,
        [string]$Command,
        [bool]$IsOptional = $false,
        [string]$Category = "TechStack"
    )
    try {
        $out = & npx -y --silent $Command --version 2>&1
        $exitCode = $LASTEXITCODE
        $versionRaw = ($out | Select-Object -First 1 | Out-String).Trim()
        
        if ($exitCode -ne 0 -or [string]::IsNullOrWhiteSpace($versionRaw)) {
            if ($IsOptional) {
                Add-ReportItem -Category $Category -Item $Name -Status $true -Message "Optional tool ${Command} is missing (Skipped)"
                return $true
            }
            Add-ReportItem -Category $Category -Item $Name -Status $false -Message "npx ${Command} failed or not installed" -FixCommand "npm install --silent --save-dev ${Command}"
            return $false
        }

        Add-ReportItem -Category $Category -Item $Name -Status $true -Message "version ${versionRaw}"
        return $true
    }
    catch {
        Add-ReportItem -Category $Category -Item $Name -Status $false -Message "Exception: $($_.Exception.Message)"
        return $false
    }
}

function Test-RegistryConnectivity {
    param(
        [string]$Name,
        [string]$RegistryUrl,
        [bool]$CheckAuth = $false,
        [string]$Category = "Network"
    )
    try {
        if ([string]::IsNullOrWhiteSpace($RegistryUrl) -or $RegistryUrl -eq "undefined") {
            Add-ReportItem -Category $Category -Item $Name -Status $false -Message "Registry URL not defined"
            return $false
        }

        $uri = [Uri]$RegistryUrl
        $hostName = $uri.Host

        $ping = Test-NetConnection -ComputerName $hostName -Port 443 -InformationLevel Quiet
        if (-not $ping) {
            Add-ReportItem -Category $Category -Item $Name -Status $false -Message "Cannot connect to ${hostName} (Port 443)"
            return $false
        }

        if ($CheckAuth) {
            $whoami = & npm whoami --registry $RegistryUrl 2>$null | Out-String
            $whoami = $whoami.Trim()
            if ($LASTEXITCODE -ne 0) {
                Add-ReportItem -Category $Category -Item $Name -Status $false -Message "Auth failed for ${Name}" -FixCommand "npm login --registry ${RegistryUrl}"
                return $false
            }
            Add-ReportItem -Category $Category -Item $Name -Status $true -Message "Connected and Authenticated ($whoami)"
        } else {
            Add-ReportItem -Category $Category -Item $Name -Status $true -Message "Connected to ${hostName}"
        }
        return $true
    }
    catch {
        Add-ReportItem -Category $Category -Item $Name -Status $false -Message "Exception: $($_.Exception.Message)"
        return $false
    }
}

function Test-SharedLintPolicy {
    param(
        [string]$PolicyPath,
        [string]$LocalConfigPath,
        [string]$Category = "Policy"
    )
    try {
        if (-not (Test-Path $PolicyPath)) {
            Add-ReportItem -Category $Category -Item "LintPolicy" -Status $true -Message "Optional shared_lint_rules.json missing (Skipped)"
            return $true
        }
        if (-not (Test-Path $LocalConfigPath)) {
            Add-ReportItem -Category $Category -Item "LintPolicy" -Status $false -Message "Missing eslint.config.js" -FixCommand "npx eslint --init"
            return $false
        }

        $policy = Get-Content $PolicyPath -Raw | ConvertFrom-Json
        $localContent = Get-Content $LocalConfigPath -Raw
        
        $missingRules = @()
        foreach ($rule in $policy.rules.PSObject.Properties) {
            $ruleName = $rule.Name
            if ($localContent -notlike "*$ruleName*") {
                $missingRules += $ruleName
            }
        }

        if ($missingRules.Count -gt 0) {
            $msg = "Missing rules: " + ($missingRules -join ", ")
            Add-ReportItem -Category $Category -Item "LintPolicy" -Status $false -Message $msg
            return $false
        }

        Add-ReportItem -Category $Category -Item "LintPolicy" -Status $true -Message "All shared rules present"
        return $true
    }
    catch {
        Add-ReportItem -Category $Category -Item "LintPolicy" -Status $false -Message "Error: $($_.Exception.Message)"
        return $false
    }
}

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
    (Test-ToolPresence -Name "yarn"    -Command "yarn" -VersionArg "v" -IsOptional $true)
)
foreach ($res in $results) { if ($null -ne $res -and -not $res) { $allPassed = $false } }

# 2. Config Integrity
Write-Host "`n[2] Configuration Integrity" -ForegroundColor Gray
$configResults = @(
    (Test-GitConfigSetting -Key "user.name"     -DisplayName "User Name"),
    (Test-GitConfigSetting -Key "user.email"    -DisplayName "User Email"),
    (Test-GitConfigSetting -Key "core.autocrlf" -DisplayName "Auto CRLF" -ExpectedValue "true"),
    (Test-NpmConfigSetting -Key "registry"      -DisplayName "Registry URL")
)
foreach ($res in $configResults) { if ($null -ne $res -and -not $res) { $allPassed = $false } }

# 3. Encoding Integrity
Write-Host "`n[3] File System & Encoding Integrity" -ForegroundColor Gray
$filesToCheck = @(
    "$PSScriptRoot\..\README.md",
    "$PSScriptRoot\..\Bootstrap-DevEnv.ps1",
    "$PSScriptRoot\check-env.ps1",
    "$PSScriptRoot\..\package.json",
    "$PSScriptRoot\..\tsconfig.json"
)
foreach ($f in $filesToCheck) {
    if (Test-Path $f) {
        if (-not (Test-FileEncoding -Path $f)) { $allPassed = $false }
    } else {
        Add-ReportItem -Category "Encoding" -Item (Split-Path $f -Leaf) -Status $false -Message "Required file missing"
        $allPassed = $false
    }
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
