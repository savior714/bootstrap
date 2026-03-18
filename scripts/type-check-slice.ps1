# =============================================================================
# type-check-slice.ps1
# 목적: tsc --noEmit 결과에서 LLM 최소 컨텍스트(Error-Only)만 추출
# 전략: docs/TS_TYPE_VALIDATION.md Section 1 참조
#
# 사용법:
#   powershell -NoProfile -File scripts/type-check-slice.ps1
#   powershell -NoProfile -File scripts/type-check-slice.ps1 -ProjectPath "c:\other-project"
#   powershell -NoProfile -File scripts/type-check-slice.ps1 -MaxErrors 10 -ContextLines 3
# =============================================================================

param(
    [string]$ProjectPath = $PSScriptRoot | Split-Path -Parent,
    [int]$MaxErrors = 20,
    [int]$ContextLines = 5,
    [switch]$RawOutput
)

$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# ── 1. tsc 실행 및 결과 캡처 ─────────────────────────────────────────────────
$tscOutput = powershell -NoProfile -Command "
    Set-Location -LiteralPath '$ProjectPath'
    npx -p typescript tsc --noEmit 2>&1
"

# ── 2. 에러 라인 필터링 ───────────────────────────────────────────────────────
$errorLines = $tscOutput | Where-Object { $_ -match 'error TS\d+' }
$errorCount = $errorLines.Count

if ($errorCount -eq 0) {
    Write-Host '✅ Type Check PASSED — 에러 없음. LLM 개입 불필요.' -ForegroundColor Green
    exit 0
}

# ── 3. 에러 요약 출력 ─────────────────────────────────────────────────────────
Write-Host ''
Write-Host "🔴 Type Errors: $errorCount 개 발견" -ForegroundColor Red
Write-Host '── LLM에 전달할 최소 컨텍스트 (Error-Only) ──────────────────────' -ForegroundColor DarkGray

if ($RawOutput) {
    # 에이전트 자동 처리용: 순수 에러 텍스트만 출력
    $errorLines | Select-Object -First $MaxErrors | ForEach-Object { Write-Output $_ }
} else {
    # 사람이 읽는 형식: 에러 코드별 그룹화
    $errorLines | Select-Object -First $MaxErrors | ForEach-Object {
        $line = $_

        # 파일명:라인:열 — 에러 코드: 메시지 패턴 파싱
        if ($line -match "^(.+)\((\d+),(\d+)\): error (TS\d+): (.+)$") {
            $file    = $Matches[1].Trim()
            $lineNo  = [int]$Matches[2]
            $errCode = $Matches[4]
            $errMsg  = $Matches[5]

            Write-Host ''
            Write-Host "  📄 $file : $lineNo" -ForegroundColor Cyan
            Write-Host "  ❌ [$errCode] $errMsg" -ForegroundColor Yellow

            # ContextLines 범위의 소스 코드 출력
            $absPath = Join-Path $ProjectPath $file
            if (Test-Path -LiteralPath $absPath) {
                $srcLines  = [System.IO.File]::ReadAllLines($absPath)
                $startIdx  = [Math]::Max(0, $lineNo - $ContextLines - 1)
                $endIdx    = [Math]::Min($srcLines.Count - 1, $lineNo + $ContextLines - 1)

                Write-Host "  ── 소스 컨텍스트 (라인 $($startIdx+1)~$($endIdx+1)) ──" -ForegroundColor DarkGray
                for ($i = $startIdx; $i -le $endIdx; $i++) {
                    $prefix = if ($i -eq $lineNo - 1) { "  >" } else { "   " }
                    $color  = if ($i -eq $lineNo - 1) { 'Red' } else { 'Gray' }
                    Write-Host "$prefix $($i+1): $($srcLines[$i])" -ForegroundColor $color
                }
            }
        } else {
            Write-Host "  $line" -ForegroundColor Yellow
        }
    }

    if ($errorCount -gt $MaxErrors) {
        Write-Host ''
        Write-Host "  ... 외 $($errorCount - $MaxErrors)개 에러 생략 (MaxErrors=$MaxErrors)" -ForegroundColor DarkGray
    }
}

# ── 4. 사용 가이드 출력 ───────────────────────────────────────────────────────
if (-not $RawOutput) {
    Write-Host ''
    Write-Host '── LLM 활용 가이드 ──────────────────────────────────────────────' -ForegroundColor DarkGray
    Write-Host '  1. 위 에러 라인과 소스 컨텍스트만 LLM에 전달하세요.' -ForegroundColor DarkGray
    Write-Host '  2. 전체 파일 주입은 금지입니다. (docs/TS_TYPE_VALIDATION.md §2)' -ForegroundColor DarkGray
    Write-Host '  3. 수정 후 이 스크립트를 재실행하여 0개 확인하세요.' -ForegroundColor DarkGray
    Write-Host ''
}

exit $errorCount
