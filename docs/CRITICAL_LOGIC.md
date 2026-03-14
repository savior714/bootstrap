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

## 6. 전역 규칙 관리 표준 (AI & Quality)

프로젝트 간 개발 경험을 통일하고 동일한 에러의 재발을 방지하기 위한 전역 관리 시스템입니다.

### 행동 및 품질 규칙 구성
1. **AI 행동 지침 (Behavioral)**: `templates/AI_GUIDELINES.md`
   - AI(Antigravity)가 코드를 작성하거나 디버깅할 때 반드시 준수해야 하는 행동 원칙.
   - 인코딩, Micro-task, 안정성 중심의 단계별 실행 지침 포함.
2. **기술 린트 정책 (Technical)**: `shared_lint_rules.json`
   - ESLint 등 도구가 프로젝트 소스 코드를 기계적으로 검증하는 규칙 모음.
   - 플랫폼 호환성 및 인코딩 사고 방지를 위한 엄격한 규칙 적용.

### 타 프로젝트 이식 및 참조 프로세스
- **배포**: 신규 프로젝트 생성 시 `bootstrap.bat` 또는 동기화 스크립트에서 해당 파일들을 타겟 프로젝트 루트로 복사합니다.
- **검증**: `scripts/check-env.ps1`을 통해 각 프로젝트의 로컬 지침이 `bootstrap` 저장소의 템플릿과 일치하는지 상시 확인합니다.
- **동기화**: `bootstrap` 저장소의 규칙이 업데이트되면, `check-env.ps1`의 self-healing 기능을 통해 타겟 프로젝트의 지침을 갱신합니다.

---

## 7. 별도 설치 도구 (스크립트 외)

- Antigravity IDE
- VS Code / Cursor AI

---

## 8. Terminal Interaction Protocol

Antigravity 에이전트와 터미널 간의 안정적인 상호작용을 위한 프로토콜입니다.

| 항목 | 내용 |
|------|-----------|
| **세션 초기화** | `scripts/init-terminal.ps1`을 호출하여 세션의 인코딩을 UTF-8로 고정하고 ANSI 시퀀스를 억제 |
| **명령어 파일화** | 100자 이상의 복잡한 명령이나 중첩 따옴표가 포함된 경우 임시 스크립트(`.ps1`)를 생성하여 실행 |
| **인코딩 원칙** | 터미널 출력 및 파싱은 UTF-8을 기본으로 하며, 결과물 파일 생성 시에도 UTF-8 no BOM 준수 |
| **전역 규칙** | `.antigravityrules`에 명시된 터미널 상호작용 지침을 최우선으로 준수 |

### 위반 시 대응
- 파싱 에러 발생 시 즉시 `init-terminal.ps1` 재실행 및 세션 상태 확인
- 명령어가 너무 길어 파싱 지연이 예상될 경우 자동으로 Micro-task로 분할하여 수행


---

## 9. Zero-Config Automation

사용자의 수동 개입 없이 `bootstrap.bat` 실행만으로 모든 환경을 전역 최적화하는 매커니즘입니다.

| 항목 | 구현 내용 |
|------|-----------|
| **전역 경로 등록** | `ANTIGRAVITY_BOOTSTRAP_PATH` 시스템 환경 변수를 현재 레포지토리 경로로 등록 |
| **터미널 영구 안정화** | 사용자 `$PROFILE`에 `init-terminal.ps1` 호출 코드를 자동 주입하여 모든 터미널 세션의 인코딩을 UTF-8로 고정 |
| **전역 도구 표준화** | `git config --global core.autocrlf false`, `init.defaultBranch main` 등의 설정을 강제 적용 |
| **무설정 에이전트 지침** | 에이전트가 `ANTIGRAVITY_BOOTSTRAP_PATH`를 감지하면 자동으로 해당 경로의 전역 지침을 로드하도록 설계 |
