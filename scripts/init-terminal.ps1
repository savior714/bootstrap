<#
.SYNOPSIS
    터미널 세션 초기화 스크립트.
.DESCRIPTION
    Antigravity 에이전트의 안정적인 작동을 위해 터미널 인코딩을 UTF-8로 고정하고,
    ANSI 시퀀스 및 컬러 출력을 억제합니다.
#>

# 1. 인코딩 고정 (UTF-8)
$OutputEncoding = [Console]::InputEncoding = [Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# 2. 파일 출력 기본값 설정
$PSDefaultParameterValues['Out-File:Encoding'] = 'utf8'
$PSDefaultParameterValues['*:Encoding'] = 'utf8'

# 3. 환경 변수 설정 (에이전트 최적화)
$env:TERM = 'dumb'   # 복잡한 터미널 기능 억제
$env:NO_COLOR = '1'  # 컬러 제어 문자 제거 (파싱 안정성 확보)

Write-Output "Terminal environment initialized with UTF-8 and static mode."
