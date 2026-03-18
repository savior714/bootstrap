# Dev Environment Bootstrap

Windows 11 개발환경 일괄 설치 스크립트. **winget** 기반으로 동작하며, 설치할 도구를 인터랙티브하게 선택할 수 있습니다.

## 대상 프로젝트 스택

`eco_pediatrics`, `cheonggu`, `law`, `golf_scoring`, `stock_vercel`, `blog`, `fmkorea`, `mail`, `myllm` 등 전체 개발 프로젝트를 커버합니다.

## 사용법

### 포맷된 새 PC에서 처음 설치

```bash
# 1. 이 레포를 클론
git clone https://github.com/savior714/bootstrap.git
cd bootstrap

# 2. bootstrap.bat 우클릭 → "관리자 권한으로 실행"
bootstrap.bat
```

> ⚠️ **반드시 관리자 권한으로 실행해야 합니다.**
>
> 더블클릭으로 실행하면 창이 바로 꺼지는 현상이 발생합니다.
> 이는 오류가 아니라, 스크립트가 내부적으로 관리자 권한 재실행을 시도하면서
> 원본 창이 닫히고 UAC 프롬프트가 뜨는 정상 동작입니다.
> **UAC 창에서 "예"를 누르면 새 창에서 계속 실행됩니다.**
>
> 창이 뜨지 않거나 즉시 종료된다면 아래 방법으로 직접 실행하세요:
>
> ```powershell
> # 관리자 권한 PowerShell에서 실행
> powershell -ExecutionPolicy Bypass -File Bootstrap-DevEnv.ps1
> ```

## 설치 가능한 도구

실행 시 아래 목록에서 숫자 키로 토글 → `Enter`로 설치 시작합니다.
`A` = 전체 선택, `N` = 전체 해제

| #   | 항목                                                        | 기본 선택 |
| --- | ----------------------------------------------------------- | :-------: |
| 1   | **Core** — Git, Python 3.14, Node.js LTS, Rust (rustup), uv |    ✅     |
| 2   | **VS Build Tools 2022** (MSVC + Windows SDK)                |    ✅     |
| 3   | **Windows Terminal**                                        |    ✅     |
| 4   | Go                                                          |    ⬜     |
| 5   | Java (Temurin JDK 17 LTS)                                   |    ⬜     |
| 6   | Android Studio                                              |    ⬜     |
| 7   | Docker Desktop                                              |    ⬜     |
| --- | ----------------------------------------------------------- | :-------: |

## 설치 후 추가 설정

별도로 직접 설치해야 하는 도구:

- **Antigravity IDE**
- **VS Code** / **Cursor AI**
- **Supabase CLI**: `npm install -g supabase` 명령어로 직접 설치하십시오. (winget 미지원)

> Android Studio(6번) 선택 시 `ANDROID_HOME` 및 PATH(`platform-tools`, `emulator`)가 **자동으로 설정**됩니다.
> 단, SDK 실제 파일은 Android Studio 최초 실행 후 다운로드됩니다.

## 설치 완료 후

```bash
# 새 터미널을 열어 PATH 적용 후
# 프로젝트 레포 클론 → 해당 프로젝트의 eco.bat 실행
eco.bat   # [2] Environment Setup
```

## 환경 무결성 검증 (Integrity Check)

설치가 완료되었거나 기존 환경의 정합성을 확인하려면 아래 명령어를 실행하세요:

```powershell
# 환경 무결성 검사 및 보고서 생성
powershell -ExecutionPolicy Bypass -File scripts/check-env.ps1
```

이 스크립트는 Node.js, Git, Lint 설정, 파일 인코딩 등을 검사하고 `env_report.json`을 생성합니다.

## Zero-Config 자동화 (Aritgravity 최적화)

`bootstrap.bat` 실행 시 아래 설정이 전역적으로 자동 적용됩니다:

- **터미널 세션 고정**: `$PROFILE`에 `init-terminal.ps1`이 주입되어 모든 PowerShell 세션의 인코딩이 UTF-8로 고정됩니다.
- **전역 지침 연결**: `ANTIGRAVITY_BOOTSTRAP_PATH` 환경 변수가 등록되어, 에이전트가 다른 프로젝트에서도 이 레포의 `AI_GUIDELINES.md`를 참조할 수 있습니다.
- **Git/NPM 표준화**: `core.autocrlf = false`, `init.defaultBranch = main` 등의 전역 설정이 강제 적용됩니다.

## 요구사항

- Windows 11 (winget 내장)
- 인터넷 연결
- 관리자 권한 (스크립트 실행 시 자동 요청)

## 파일 구조

```
bootstrap/
├── bootstrap.bat               # 더블클릭 런처 (powershell.exe 실행)
├── Bootstrap-DevEnv.ps1        # 설치 로직 본체
├── CLAUDE.md                   # AI 에이전트 진입점 & Fatal Guard
├── AI_GUIDELINES.md            # AI 행동 원칙 SSOT
├── .antigravityrules           # Antigravity 에이전트 런타임 제약
├── .cursorrules                # Cursor AI 전용 규칙
├── scripts/
│   ├── check-env.ps1           # 환경 무결성 검증 엔진
│   ├── init-terminal.ps1       # 터미널 세션 초기화 프로토콜
│   ├── type-check-slice.ps1    # TypeScript Error-Only Context 추출기
│   └── types-extractor.ts      # ts-morph 기반 타입 정의 추출기
├── shared_lint_rules.json      # 전역 공유 린트 정책
├── eslint.config.js            # 프로젝트 표준 린트 설정
├── .vscode/
│   ├── tasks.json              # TypeScript 타입 체크 태스크
│   └── settings.json           # Language Service + 컨텍스트 오염 방지
├── README.md
└── docs/
    ├── CRITICAL_LOGIC.md       # 설계 결정 SSOT
    ├── memory.md               # 작업 로그 (세션 상태 SSOT)
    ├── AI_COMMAND_PROTOCOL.md  # 터미널 실행 가이드 & 오류 패턴
    ├── TS_TYPE_VALIDATION.md   # TypeScript 타입 검증 전략 (3-IDE)
    ├── TS_ADVANCED_PATTERNS.md # DDD 타입 분리 / Symbol Ref / Flatten
    └── VIBE_CODING_PROTOCOL.md # Validate-and-Prune / L1/L2/L3
```
