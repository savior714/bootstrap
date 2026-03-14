# scripts/fix-encoding.ps1
# Fix file encoding to UTF-8 (no BOM by default, with BOM if requested)
# Usage: ./fix-encoding.ps1 <file_path> [--add-bom]

param(
    [string]$FilePath,
    [switch]$AddBom,
    [switch]$Ansi
)

if (-not (Test-Path $FilePath)) {
    Write-Error "File not found: $FilePath"
    exit 1
}

try {
    $content = Get-Content $FilePath -Raw
    if ($Ansi) {
        # ANSI (System Default, e.g., CP949)
        [System.IO.File]::WriteAllText($FilePath, $content, [System.Text.Encoding]::Default)
        Write-Host "Successfully converted $FilePath to ANSI" -ForegroundColor Green
    } elseif ($AddBom) {
        # UTF-8 with BOM (C# Default)
        [System.IO.File]::WriteAllText($FilePath, $content, [System.Text.Encoding]::UTF8)
        Write-Host "Successfully converted $FilePath to UTF-8 with BOM" -ForegroundColor Green
    } else {
        # UTF-8 no BOM
        $utf8NoBom = New-Object System.Text.UTF8Encoding $false
        [System.IO.File]::WriteAllText($FilePath, $content, $utf8NoBom)
        Write-Host "Successfully converted $FilePath to UTF-8 no BOM" -ForegroundColor Green
    }
}
catch {
    Write-Error "Failed to fix encoding for ${FilePath}: $($_.Exception.Message)"
    exit 1
}
