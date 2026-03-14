$content = Get-Content "c:\develop\bootstrap\scripts\diagnose_env.ps1" -Raw
$open = ($content.ToCharArray() | Where-Object { $_ -eq '{' }).Count
$close = ($content.ToCharArray() | Where-Object { $_ -eq '}' }).Count
Write-Host "Open: $open, Close: $close"
