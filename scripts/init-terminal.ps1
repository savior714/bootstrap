<#
.SYNOPSIS
    터미널 세션 초기화 스크립트 (Refined).
.DESCRIPTION
    Antigravity 에이전트의 안정적인 작동을 위해 터미널 인코딩을 UTF-8로 고정하고,
    ANSI 시퀀스, 컬러 출력, 진행 표시줄 등 불필요한 시스템 출력을 억제합니다.
#>

# 1. 시스템 인코딩 고정 (UTF-8 SSOT)
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# 2. PowerShell 명령어 자동 인코딩 설정
$PSDefaultParameterValues['Out-File:Encoding'] = 'utf8'
$PSDefaultParameterValues['*:Encoding'] = 'utf8'

# 3. 진행률 표시줄 억제 (Terminal Stability)
$ProgressPreference = 'SilentlyContinue'

# 4. 환경 변수 최적화 (Agent Compatibility)
$env:TERM = 'dumb'       # 복잡한 터미널 기능 억제
$env:NO_COLOR = '1'      # ANSI 컬러 코드 제거
$env:POWERSHELL_TELEMETRY_OPTOUT = '1' # 원격 분석 비활성화

Write-Host ">>> Terminal Protocol Refined: UTF-8 Static Mode Active." -ForegroundColor Cyan
