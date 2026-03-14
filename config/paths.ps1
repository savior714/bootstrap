# config/paths.ps1 — 경로 및 버전 상수 정의 (Single Source of Truth)
# Encoding: UTF-8 no BOM | PowerShell 5 호환
#
# 수정 지침:
#   - 패키지 버전 업그레이드 시 이 파일의 해당 상수만 수정한다.
#   - 환경 변수가 주입된 경우 환경 변수가 우선 적용된다 (Override 가능).

# -------------------------------------------------------
# Java
# -------------------------------------------------------
# JDK 설치 기준 디렉터리. JAVA_INSTALL_BASE 환경 변수로 재정의 가능.
if ($env:JAVA_INSTALL_BASE) {
    $Script:JAVA_INSTALL_BASE = $env:JAVA_INSTALL_BASE
} else {
    $Script:JAVA_INSTALL_BASE = "C:\Program Files\Eclipse Adoptium"
}
# 버전 업 시 이 줄만 수정 (예: "jdk-21*")
$Script:JAVA_VERSION_GLOB = "jdk-17*"

# -------------------------------------------------------
# Android
# -------------------------------------------------------
$Script:ANDROID_SDK_BASE = "$env:LOCALAPPDATA\Android\Sdk"

# -------------------------------------------------------
# Rust
# -------------------------------------------------------
$Script:RUST_CARGO_BIN = Join-Path $env:USERPROFILE ".cargo\bin\rustup.exe"

# -------------------------------------------------------
# VS Build Tools
# -------------------------------------------------------
# Windows SDK 버전. WINDOWS_SDK_VER 환경 변수로 재정의 가능.
if ($env:WINDOWS_SDK_VER) {
    $Script:WINDOWS_SDK_VER = $env:WINDOWS_SDK_VER
} else {
    $Script:WINDOWS_SDK_VER = "26100"
}

# -------------------------------------------------------
# PowerShell Profile
# -------------------------------------------------------
# Profile 주입 여부 확인용 마커 키. 변경 시 기존 Profile과 중복 주입될 수 있으므로 주의.
$Script:PROFILE_MARKER_KEY = "Antigravity Terminal Initialization"

# -------------------------------------------------------
# UI
# -------------------------------------------------------
$Script:MENU_BORDER_WIDTH = 50
$Script:APP_TITLE         = "Antigravity Dev Environment"

# -------------------------------------------------------
# Winget
# -------------------------------------------------------
# winget이 "이미 설치됨"으로 반환하는 Exit Code
$Script:WINGET_ALREADY_INSTALLED_CODE = -1978335189
