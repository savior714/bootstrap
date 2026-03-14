# scripts/fix-encoding.ps1
# Fix file encoding to UTF-8 no BOM
# Usage: ./fix-encoding.ps1 <file_path>

param([string]$FilePath)

if (-not (Test-Path $FilePath)) {
    Write-Error "File not found: $FilePath"
    exit 1
}

try {
    $content = Get-Content $FilePath -Raw
    $utf8NoBom = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($FilePath, $content, $utf8NoBom)
    Write-Host "Successfully converted $FilePath to UTF-8 no BOM" -ForegroundColor Green
}
catch {
    Write-Error "Failed to fix encoding for ${FilePath}: $($_.Exception.Message)"
    exit 1
}
