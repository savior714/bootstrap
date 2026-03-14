# CRITICAL_LOGIC.md — Bootstrap DevEnv 규칙 SSOT

> 이 파일은 bootstrap_repo의 모든 설계 결정과 규칙의 유일한 기준(Single Source of Truth)입니다.

---

## 1. 실행 환경 표준

| 항목 | 결정 | 이유 |
|------|------|------|
| 런처 | `bootstrap.bat` 우클릭 → **관리자 권한으로 실행** | 스크립트 내 admin self-elevation 시 원본 창이 닫히는 현상 방지 |
| PowerShell | **`powershell.exe` (PS5) 고정** | PS7 미사용 환경. pwsh 감지 로직 제거됨 |
| PS1 인코딩 | **UTF-8 with BOM** | PS5가 BOM 없는 UTF-8을 ANSI(CP949)로 읽어 파싱 오류 발생 → BOM 필수 |
| bat 인코딩 | **ANSI (CP949)** | Windows cmd 호환성 |

---

## 2. 패키지 그룹 구성 (현행)

| # | 항목 | 기본 선택 |
|---|------|:---:|
| 1 | Core — Git, Python 3.14, Node.js LTS, Rust (rustup), uv | ✅ |
| 2 | VS Build Tools 2022 (MSVC + Windows SDK 26100) | ✅ |
| 3 | Windows Terminal | ✅ |
| 4 | Go | ⬜ |
| 5 | Java (Temurin JDK 17 LTS) | ⬜ |
| 6 | Android Studio | ⬜ |
| 7 | Docker Desktop | ⬜ |
| 8 | Supabase CLI | ⬜ |

**제거된 항목:**
- ~~PowerShell 7 (pwsh)~~ — PS7 미사용 환경이므로 제거 (그룹 #2였음)

---

## 3. 설계 결정 사항

### Admin 자동 승격 구조
- `Bootstrap-DevEnv.ps1` 실행 시 admin 아닐 경우 `Start-Process powershell -Verb RunAs`로 재실행 후 `exit 0`
- 이로 인해 **원본 bat 창이 닫히고 UAC 창 + 새 창이 열리는 것은 정상 동작**
- 해결책: bat 파일을 처음부터 관리자 권한으로 실행

### 메뉴 UI
- `$Host.UI.RawUI.ReadKey` 기반 인터랙티브 메뉴
- 숫자 키로 토글, `A`/`N`으로 전체 선택/해제, `Enter`로 설치 시작
- 그룹별 설명(Desc) 라인은 불필요하여 제거됨

### Post-install 자동화

`Add-ToUserPath` 헬퍼 함수: 경로 존재 확인 후 User PATH 중복 없이 등록, 현재 세션 즉시 반영

| 항목 | 자동화 내용 |
|------|------------|
| **Rust** | rustup stable toolchain 설치 및 default 설정 |
| **Java** | `JAVA_HOME` 설정 (`C:\Program Files\Eclipse Adoptium\jdk-17*`) + `\bin` PATH 자동 추가 |
| **Android** | `ANDROID_HOME` 설정 (`%LOCALAPPDATA%\Android\Sdk`) + `platform-tools`, `emulator` PATH 자동 추가 |

---

## 5. 환경 무결성 검증 엔진 (Integrity Engine)

개발 환경의 일관성을 유지하고 "Ghost Bug"를 방지하기 위한 검증 시스템입니다.

| 항목 | 검증 내용 |
|------|-----------|
| **Core CLI** | Node.js, Git, npm, pnpm, yarn의 설치 및 최소 버전 확인 |
| **Config** | `.npmrc` (Registry), `.gitconfig` (User Info, autocrlf) 무결성 확인 |
| **File System** | 주요 설정 파일(`package.json` 등)의 인코딩(UTF-8 no BOM) 검증 |
| **IDE Sync** | VSCode `settings.json`의 일관성 확인 및 자동 생성 지원 |
| **Tech Stack** | `tsc`, `eslint`, `prettier` 바이너리 가용성 Dry-Run |
| **Shared Lint** | `shared_lint_rules.json`을 통한 프로젝트 간 동일 린트 정책 강제 |

### 검증 결과 보고
- `scripts/check-env.ps1` 실행 시 `env_report.json` 생성
- IDE와의 연동을 위해 표준 JSON 스키마를 따름
- 위반 사항 발견 시 구체적인 복구 제안 제공

---

## 6. 별도 설치 도구 (스크립트 외)

- Antigravity IDE
- VS Code / Cursor AI
