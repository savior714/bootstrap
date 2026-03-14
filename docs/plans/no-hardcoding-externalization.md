# 🗺️ Project Blueprint: 하드코딩 금지 및 설정 외부화

> 생성 일시: 2026-03-14 | 상태: 설계 승인 대기

## 🎯 Architectural Goal

이 프로젝트(`Bootstrap-DevEnv.ps1` 기반 Windows 11 개발환경 자동화 도구)에 존재하는 하드코딩된 값들을 체계적으로 외부화하여:
- **환경 독립성**: 패키지 버전·경로 변경 시 단일 설정 파일만 수정
- **보안 기준선**: `.gitignore` 강화 및 시크릿 스캔 기반 마련
- **가독성**: 매직 넘버·스트링을 의미 있는 상수로 치환

**SSOT**: `docs/CRITICAL_LOGIC.md` Section 2 (패키지 그룹), Section 3 (Post-install 경로) 정렬 대상

---

## 🔍 현재 상태 분석 (As-Is)

### 발견된 하드코딩 항목

| 위치 | 값 | 분류 | 위험도 |
|------|----|------|:------:|
| `Bootstrap-DevEnv.ps1:283` | `"C:\Program Files\Eclipse Adoptium\jdk-17*"` | 경로 + 버전 고정 | 🔴 High |
| `Bootstrap-DevEnv.ps1:148` | `Windows11SDK.26100` (Override 문자열 내) | 버전 고정 | 🟡 Med |
| `Bootstrap-DevEnv.ps1:213` | `50` (메뉴 테두리 너비) | 매직 넘버 | 🟢 Low |
| `Bootstrap-DevEnv.ps1:113` | `"Antigravity Dev Environment Bootstrap"` (제목) | 매직 스트링 | 🟢 Low |
| `Bootstrap-DevEnv.ps1:36` | `"Antigravity Terminal Initialization"` (Profile 주석 키) | 매직 스트링 | 🟡 Med |
| `.gitignore` | `.env` 패턴 누락 | 보안 기준선 미비 | 🔴 High |
| 프로젝트 전체 | `.env.example` 미존재 | Zero-Config 온보딩 불가 | 🟡 Med |
| `Bootstrap-DevEnv.ps1:135` | `"Python.Python.3.14"`, `"EclipseAdoptium.Temurin.17.JDK"` | 패키지 버전 코드 내 고정 | 🟡 Med |

---

## 🛠️ Step-by-Step Execution Plan

> ⚠️ **각 Task는 단 하나의 도구 호출(Read / Edit / Write / Bash 중 1개)로 완료되어야 한다.**

### 📦 Task List

---

#### ✅ 보안 기준선 (Security Baseline) — 우선순위 최상

- [ ] **Task 1: `.gitignore`에 시크릿 패턴 추가**
  - **Tool**: `Edit`
  - **Target**: `.gitignore`
  - **Goal**: `.env`, `.env.local`, `.env.*.local` 등을 추가하여 실수에 의한 시크릿 Push 원천 차단
  - **Pseudocode**:
    ```
    # 기존 .gitignore 하단에 추가
    .env
    .env.local
    .env.*.local
    *.secret
    ```
  - **Dependency**: None

- [ ] **Task 2: `.env.example` 파일 생성**
  - **Tool**: `Write`
  - **Target**: `.env.example` (프로젝트 루트)
  - **Goal**: 신규 팀원이 5분 안에 로컬 환경 구동 가능하도록 Zero-Config 온보딩 기준 파일 제공. 실제 값 없이 키 이름과 설명만 포함
  - **Pseudocode**:
    ```ini
    # Bootstrap DevEnv — 환경 변수 예시 파일
    # 이 파일을 .env로 복사 후 값을 채우세요.
    # .env는 .gitignore에 등록되어 절대 커밋되지 않습니다.

    # [선택] 패키지 설치 시 사용할 Winget 소스 (기본값: winget)
    # WINGET_SOURCE=winget

    # [선택] Java 설치 경로 패턴 (기본값: C:\Program Files\Eclipse Adoptium)
    # JAVA_INSTALL_BASE=C:\Program Files\Eclipse Adoptium
    ```
  - **Dependency**: Task 1

---

#### 📦 설정 외부화 (Config Externalization)

- [ ] **Task 3: `config/packages.json` 생성 — 패키지 메타데이터 분리**
  - **Tool**: `Write`
  - **Target**: `config/packages.json`
  - **Goal**: `Bootstrap-DevEnv.ps1`에 인라인된 패키지 ID·버전 정보를 외부 JSON으로 분리. 버전 업그레이드 시 스크립트 수정 불필요
  - **Pseudocode**:
    ```json
    {
      "groups": {
        "1": {
          "label": "Core (Git, Python 3.14, Node.js LTS, Rust, uv)",
          "default": true,
          "packages": [
            { "id": "Git.Git", "name": "Git" },
            { "id": "Python.Python.3.14", "name": "Python 3.14" },
            { "id": "OpenJS.NodeJS.LTS", "name": "Node.js LTS" },
            { "id": "Rustlang.Rustup", "name": "Rust (rustup)" },
            { "id": "astral-sh.uv", "name": "uv" }
          ]
        }
        // ... 나머지 그룹
      }
    }
    ```
  - **Dependency**: None

- [ ] **Task 4: `config/paths.ps1` 생성 — 경로 상수 외부화**
  - **Tool**: `Write`
  - **Target**: `config/paths.ps1`
  - **Goal**: `Bootstrap-DevEnv.ps1`에 산재한 절대 경로 패턴과 버전 고정 문자열을 단일 상수 파일로 집중 관리. 버전 변경 시 이 파일만 수정
  - **Pseudocode**:
    ```powershell
    # config/paths.ps1 — 경로 및 버전 상수 정의
    # UTF-8 no BOM

    $Script:JAVA_INSTALL_BASE  = $env:JAVA_INSTALL_BASE `
        ?? "C:\Program Files\Eclipse Adoptium"
    $Script:JAVA_VERSION_GLOB  = "jdk-17*"       # 버전 업 시 이 줄만 수정

    $Script:WINDOWS_SDK_VER    = "26100"          # VS Build Tools Windows SDK 버전
    $Script:RUST_CARGO_BIN     = "$env:USERPROFILE\.cargo\bin\rustup.exe"
    $Script:ANDROID_SDK_BASE   = "$env:LOCALAPPDATA\Android\Sdk"
    $Script:PROFILE_MARKER_KEY = "Antigravity Terminal Initialization"
    ```
  - **Dependency**: None

---

#### 🔢 매직 값 제거 (Magic Value Elimination)

- [ ] **Task 5: `Bootstrap-DevEnv.ps1` 상단에 UI 상수 블록 추가**
  - **Tool**: `Edit`
  - **Target**: `Bootstrap-DevEnv.ps1`
  - **Goal**: 메뉴 UI에 사용된 매직 넘버·스트링을 Named Constant로 치환하여 단일 수정 지점 확보
  - **Pseudocode**:
    ```powershell
    #region --- Constants ---
    $MENU_BORDER_WIDTH   = 50
    $APP_TITLE           = "Antigravity Dev Environment"
    $WINGET_ALREADY_INSTALLED_CODE = -1978335189
    #endregion
    ```
  - **Dependency**: Task 4

- [ ] **Task 6: `Bootstrap-DevEnv.ps1` — Java 경로를 `config/paths.ps1` 상수로 교체**
  - **Tool**: `Edit`
  - **Target**: `Bootstrap-DevEnv.ps1:283`
  - **Goal**: 하드코딩된 `"C:\Program Files\Eclipse Adoptium\jdk-17*"`를 `$Script:JAVA_INSTALL_BASE + "\" + $Script:JAVA_VERSION_GLOB`로 교체
  - **Pseudocode**:
    ```powershell
    # Before
    $javaPath = "C:\Program Files\Eclipse Adoptium\jdk-17*"
    # After
    . (Join-Path $PSScriptRoot "config\paths.ps1")
    $javaPath = Join-Path $Script:JAVA_INSTALL_BASE $Script:JAVA_VERSION_GLOB
    ```
  - **Dependency**: Task 4, Task 5

- [ ] **Task 7: `Bootstrap-DevEnv.ps1` — VS SDK 버전을 상수로 교체**
  - **Tool**: `Edit`
  - **Target**: `Bootstrap-DevEnv.ps1:148`
  - **Goal**: Override 문자열 내 `Windows11SDK.26100`을 `$Script:WINDOWS_SDK_VER` 변수 삽입으로 치환
  - **Pseudocode**:
    ```powershell
    Override = "--quiet --add Microsoft.VisualStudio.Workload.VCTools " +
               "--add Microsoft.VisualStudio.Component.Windows11SDK.$($Script:WINDOWS_SDK_VER) " +
               "--includeRecommended"
    ```
  - **Dependency**: Task 4, Task 5

---

#### 📋 SSOT 및 문서 정렬

- [ ] **Task 8: `CRITICAL_LOGIC.md` Section 3 업데이트**
  - **Tool**: `Edit`
  - **Target**: `docs/CRITICAL_LOGIC.md`
  - **Goal**: Java 경로, Android SDK 경로의 관리 기준을 `config/paths.ps1`로 명시. 단일 수정 지점 문서화
  - **Dependency**: Task 6, Task 7

- [ ] **Task 9: `memory.md` 갱신 (200줄 초과 시 요약 선행)**
  - **Tool**: `Edit`
  - **Target**: `docs/memory.md`
  - **Goal**: 이번 설계 변경 사항 기록. 현재 190줄 → 200줄 도달 직전이므로 요약 후 기록
  - **Dependency**: Task 8

---

## ⚠️ 기술적 제약 및 규칙 (SSOT)

- **Encoding**: 모든 신규 파일 UTF-8 no BOM 고정. (`config/paths.ps1`, `config/packages.json`)
- **PowerShell 호환**: PS5 환경. `??` (Null-coalescing) 연산자는 PS7+에서만 동작 → PS5 대응 폴백 패턴 사용: `if ($env:VAR) { $env:VAR } else { "default" }`
- **packages.json 로딩**: `ConvertFrom-Json`으로 파싱. PS5에서는 `-AsHashtable` 미지원 → `PSCustomObject` 기반 접근
- **경로 조합**: 문자열 결합 금지, 반드시 `Join-Path` 사용
- **환경 변수 Fallback**: 주입되지 않은 경우 `Write-WARN`으로 경고 후 기본값 사용

### PS5 환경 Null-coalescing 패턴
```powershell
# PS7+: $env:JAVA_INSTALL_BASE ?? "C:\Program Files\Eclipse Adoptium"
# PS5 호환:
$Script:JAVA_INSTALL_BASE = if ($env:JAVA_INSTALL_BASE) {
    $env:JAVA_INSTALL_BASE
} else {
    Write-WARN "JAVA_INSTALL_BASE not set. Using default path."
    "C:\Program Files\Eclipse Adoptium"
}
```

---

## ✅ Definition of Done

1. [ ] `.gitignore`에 `.env*`, `*.secret` 패턴 추가됨
2. [ ] `.env.example` 파일이 루트에 존재하며 모든 설정 키를 문서화함
3. [ ] `config/packages.json`이 패키지 그룹 전체를 정의함
4. [ ] `config/paths.ps1`에 모든 경로·버전 상수가 집중됨
5. [ ] `Bootstrap-DevEnv.ps1` 내 하드코딩 경로·버전 문자열이 0개
6. [ ] `CRITICAL_LOGIC.md` Section 3이 `config/paths.ps1` 참조로 업데이트됨
7. [ ] 신규 팀원이 `.env.example`만 보고 5분 내 로컬 구동 가능한 상태

---

## 🔒 Senior 정밀도 체크리스트

- [ ] **Secret Scan**: `git log --all --full-history -- "*.env"` 로 커밋 히스토리 점검
- [ ] **Zero-Config Build**: `.env.example` → `.env` 복사 후 `bootstrap.bat` 즉시 실행 가능
- [ ] **Environment Agnostic**: `JAVA_INSTALL_BASE` 환경 변수 주입만으로 다른 드라이브 경로 대응
- [ ] **Meaningful Naming**: `WINDOWS_SDK_VER`은 값(26100)이 아닌 역할(Windows SDK 버전)을 표현
- [ ] **Single Source of Truth**: 패키지 버전은 `config/packages.json`에만 존재, `Bootstrap-DevEnv.ps1`에 중복 없음
