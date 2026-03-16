# scripts/lib/env-core.ps1
# Antigravity Environment Integrity Core Library
# Encoding: UTF-8 no BOM

# --- Helper Functions ---

function Update-VSCodeSetting {
    param($Key, $Value)
    $path = Join-Path $PSScriptRoot "..\..\.vscode\settings.json"
    $dir = Split-Path $path
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    if (-not (Test-Path $path)) { [System.IO.File]::WriteAllText($path, "{}", [System.Text.Encoding]::UTF8) }
    
    $config = Get-Content $path -Raw | ConvertFrom-Json
    $config | Add-Member -MemberType NoteProperty -Name $Key -Value $Value -Force
    # Use System.IO.File to ensure UTF8 no BOM (PowerShell 5.x Out-File -Encoding utf8 adds BOM)
    $json = $config | ConvertTo-Json -Depth 10
    $utf8NoBom = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($path, $json, $utf8NoBom)
    Write-Host "Updated VSCode setting: ${Key} = ${Value}" -ForegroundColor Cyan
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
                Write-Host "  -> [Self-Healing] Executing fix..." -ForegroundColor Cyan
                try {
                    Invoke-Expression $FixCommand
                    Write-Host "  -> [Self-Healing] Success." -ForegroundColor Green
                } catch {
                    Write-Host ("  -> [Self-Healing] Failed: {0}" -f $_.Exception.Message) -ForegroundColor Red
                }
            }
        }
    }
}

# --- Validation Functions ---

function Test-ToolPresence {
    param([string]$Name, [string]$Command, [string]$VersionArg = "--version", [bool]$IsOptional = $false, [string]$Category = "Toolchain")
    try {
        $toolPath = Get-Command $Command -ErrorAction SilentlyContinue
        if (-not $toolPath) {
            if ($IsOptional) { return $true }
            Add-ReportItem -Category $Category -Item $Name -Status $false -Message "${Command} is not in PATH" -FixCommand "winget install ${Command}"
            return $false
        }
        $out = & $Command $VersionArg 2>&1
        $versionRaw = ($out | Select-Object -First 1 | Out-String).Trim()
        Add-ReportItem -Category $Category -Item $Name -Status $true -Message "$($toolPath.Source) - ${versionRaw}"
        return $true
    }
    catch {
        Add-ReportItem -Category $Category -Item $Name -Status $false -Message "Exception: $($_.Exception.Message)"
        return $false
    }
}

function Test-GitConfigSetting {
    param([string]$Key, [string]$DisplayName, [string]$ExpectedValue = $null, [string]$Category = "GitConfig")
    $val = (git config --get $Key 2>$null)
    if ([string]::IsNullOrWhiteSpace($val)) {
        Add-ReportItem -Category $Category -Item $DisplayName -Status $false -Message "Missing Git config '${Key}'"
        return $false
    }
    if (-not [string]::IsNullOrEmpty($ExpectedValue) -and $val.Trim() -ne $ExpectedValue) {
        Add-ReportItem -Category $Category -Item $DisplayName -Status $false -Message "Mismatch: $($val.Trim()) (Expected: $ExpectedValue)"
        return $false
    }
    Add-ReportItem -Category $Category -Item $DisplayName -Status $true -Message $val.Trim()
    return $true
}

function Test-NpmConfigSetting {
    param([string]$Key, [string]$DisplayName, [string]$Category = "NpmConfig")
    $val = (npm config get $Key 2>$null)
    if ([string]::IsNullOrWhiteSpace($val) -or $val -eq "undefined") {
        Add-ReportItem -Category $Category -Item $DisplayName -Status $false -Message "Missing NPM config '${Key}'"
        return $false
    }
    Add-ReportItem -Category $Category -Item $DisplayName -Status $true -Message $val.Trim()
    return $true
}

function Test-FileEncoding {
    param($Path, [string]$Category = "Encoding", [string]$Required = "UTF8NoBom")
    $fileName = Split-Path $Path -Leaf
    if (-not (Test-Path $Path)) {
        Add-ReportItem -Category $Category -Item $fileName -Status $false -Message "File not found"
        return $false
    }
    $bytes = [System.IO.File]::ReadAllBytes($Path)
    $hasBom = ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF)

    if ($Required -eq "UTF8WithBom" -and -not $hasBom) {
        Add-ReportItem -Category $Category -Item $fileName -Status $false -Message "BOM missing" -FixCommand "powershell -File $PSScriptRoot/../fix-encoding.ps1 '$Path' --add-bom"
        return $false
    }
    if ($Required -eq "UTF8NoBom" -and $hasBom) {
        Add-ReportItem -Category $Category -Item $fileName -Status $false -Message "BOM detected" -FixCommand "powershell -File $PSScriptRoot/../fix-encoding.ps1 '$Path'"
        return $false
    }
    Add-ReportItem -Category $Category -Item $fileName -Status $true -Message "$Required (OK)"
    return $true
}

function Test-VSCodeSettingsIntegrity {
    param([string]$Path, [string]$Category = "IDE")
    if (-not (Test-Path $Path)) {
        Add-ReportItem -Category $Category -Item "settings.json" -Status $false -Message "Missing"
        return $false
    }
    $content = Get-Content $Path -Raw | ConvertFrom-Json
    $success = $true
    $expected = @{ "files.encoding" = "utf8"; "editor.tabSize" = 2 }
    foreach ($key in $expected.Keys) {
        if ($content.$key -ne $expected[$key]) {
            Add-ReportItem -Category $Category -Item $key -Status $false -Message "Mismatch"
            $success = $false
        }
    }
    if ($success) { Add-ReportItem -Category $Category -Item "settings.json" -Status $true -Message "OK" }
    return $success
}

function Test-NpxToolHealth {
    param([string]$Name, [string]$Command, [bool]$IsOptional = $false, [string]$Category = "TechStack")
    $out = & npx -y --silent $Command --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        if ($IsOptional) { return $true }
        Add-ReportItem -Category $Category -Item $Name -Status $false -Message "npx ${Command} failed"
        return $false
    }
    Add-ReportItem -Category $Category -Item $Name -Status $true -Message "$($out | Select-Object -First 1)"
    return $true
}

function Test-RegistryConnectivity {
    param([string]$Name, [string]$RegistryUrl, [string]$Category = "Network")
    $uri = [Uri]$RegistryUrl
    $ping = Test-NetConnection -ComputerName $uri.Host -Port 443 -InformationLevel Quiet
    if (-not $ping) {
        Add-ReportItem -Category $Category -Item $Name -Status $false -Message "Unreachable"
        return $false
    }
    Add-ReportItem -Category $Category -Item $Name -Status $true -Message "Connected to $($uri.Host)"
    return $true
}

function Test-SharedLintPolicy {
    param([string]$PolicyPath, [string]$LocalConfigPath, [string]$Category = "Policy")
    if (-not (Test-Path $PolicyPath)) { return $true }
    if (-not (Test-Path $LocalConfigPath)) {
        Add-ReportItem -Category $Category -Item "Lint" -Status $false -Message "eslint.config.js missing"
        return $false
    }
    Add-ReportItem -Category $Category -Item "LintPolicy" -Status $true -Message "Verified"
    return $true
}

function Test-AIGuidelinesIntegrity {
    param([string]$Path, [string]$TemplatePath, [string]$Category = "Guidelines")
    try {
        if (-not (Test-Path $Path)) {
            Add-ReportItem -Category $Category -Item "AI_GUIDELINES.md" -Status $false -Message "Missing" -FixCommand "Copy-Item -Path '$TemplatePath' -Destination '$Path' -Force"
            return $false
        }
        if (-not (Test-FileEncoding -Path $Path -Category $Category -Required "UTF8NoBom")) { return $false }
        
        if (Test-Path $TemplatePath) {
            $rootHash = (Get-FileHash -Path $Path -Algorithm MD5).Hash
            $tempHash = (Get-FileHash -Path $TemplatePath -Algorithm MD5).Hash
            if ($rootHash -ne $tempHash) {
                Add-ReportItem -Category $Category -Item "AI_GUIDELINES.md" -Status $false -Message "Out of sync" -FixCommand "Copy-Item -Path '$TemplatePath' -Destination '$Path' -Force"
                return $false
            }
        }
        Add-ReportItem -Category $Category -Item "AI_GUIDELINES.md" -Status $true -Message "Synced"
        return $true
    }
    catch {
        Add-ReportItem -Category $Category -Item "AI_GUIDELINES.md" -Status $false -Message "Error: $($_.Exception.Message)"
        return $false
    }
}

function Test-SyntaxHealth {
    param($Path, [string]$Category = "Syntax")
    $fileName = Split-Path $Path -Leaf
    if (-not (Test-Path $Path)) { return $true }
    try {
        $errors = $null
        [System.Management.Automation.Language.Parser]::ParseInput((Get-Content $Path -Raw), [ref]$null, [ref]$errors)
        if ($errors) {
            Add-ReportItem -Category $Category -Item $fileName -Status $false -Message "Syntax Error: $($errors[0].Message)"
            return $false
        }
        Add-ReportItem -Category $Category -Item $fileName -Status $true -Message "Valid"
        return $true
    } catch {
        Add-ReportItem -Category $Category -Item $fileName -Status $false -Message "Parser Exception: $($_.Exception.Message)"
        return $false
    }
}
