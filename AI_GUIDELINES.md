# 🤖 AI Behavioral Guidelines (Antigravity Standard)

이 문서는 모든 프로젝트에서 AI(Antigravity)가 준수해야 할 **최상위 행동 지침**입니다. 이 지침을 위반할 경우 시스템의 안정성이 저해되거나 불필요한 토큰 낭비가 발생할 수 있습니다.

## 1. 안정성 및 신뢰성 (Stability & Reliability)

- **Strict Context Isolation**: 아래 경로는 절대 인덱싱, 읽기, 검색 또는 터미널 출력을 하지 않습니다.
  - `node_modules/**`, `**/target/**`, `.next/**`, `.turbo/**`, `dist/**`, `build/**`, `out/**`, `.pnpm-store/**`
  - `.git/**`, `.vscode/**`, `.idea/**`, `coverage/**`
  - `package-lock.json`, `pnpm-lock.yaml`, `Cargo.lock`, `bun.lockb`, `*.log`, `*.map`
- **Micro-Task Principle**: 1회 응답당 **하나의 Tool Call**만 수행합니다. 읽기/수정/검증을 명확히 분리합니다.
- **Step-Lock Protocol**: 한 응답에서 단 하나의 Task만 실행 후 사용자의 승인을 대기합니다.
- **Refactoring Standard**: 파일이 **300라인**을 초과하면 즉시 기능 분리(Refactoring Plan)를 수립합니다.

## 2. 환경 및 인코딩 (Environment & Encoding)

- **Encoding Standard**:
  - 배치 파일(`.bat`, `.cmd`): **ANSI (CP949)**
  - 그 외 모든 소스 코드: **UTF-8 (no BOM)**
  - *참고*: PowerShell(`.ps1`) 파일이 PS5에서 파싱 오류(`>>>` 등)를 일으킬 경우에만 **UTF-8 with BOM**을 허용합니다.
- **OS Native**: Windows 11 환경을 우선하며, `ls`, `grep` 등 리눅스 명령어가 아닌 **PowerShell 네이티브 문법**을 사용합니다.

## 3. 터미널 및 시스템 (Terminal & Runtime)

- **Quiet Mode**: 모든 CLI 도구 사용 시 `--quiet`, `--silent`, `-q`, `-s` 등 최소 출력 플래그를 강제합니다.
- **Hard Truncation**: 터미널 출력이 방대할 경우 `Select-Object -Last 30` 또는 `Select-Object -First 50` 등으로 엄격하게 제한합니다.
- **Pre-flight Check**: 터미널 작업 전 `scripts/init-terminal.ps1`이 로드되었는지 확인하고, 환경 변수 및 인코딩 설정을 검증합니다.
- **Safe Execution**: 파괴적인 명령(파일 삭제, 저장소 초기화 등) 실행 전에는 반드시 타겟을 재확인하고 `-WhatIf` 플래그를 사용하거나 사용자에게 명시적으로 승인을 요청합니다.
- **Surgical Changes**: 요청받지 않은 리팩토링이나 단순 코드 스타일 수정은 지양하며, 목표 달성에 필요한 **최소한의 코드**만 수정합니다.
- **Zombie Cleanup**: 작업 전 관련 프로세스(`node`, `tsc`, `cargo` 등)가 점유 중인지 확인하고 필요 시 정리합니다.

## 4. 코드 무결성 및 설계 (Code Integrity)

- **Strict Typing**: `any` 또는 `dynamic` 타입을 금지하며, 명시적 타입 선언과 타입 가드를 사용합니다.
- **3-Layer Architecture**: Definition, Repository, Service/Logic 계층 구조를 지향합니다.
- **Early Return**: 조건문의 중첩을 피하고 가독성을 높이기 위해 Early Return 패턴을 사용합니다.
- **No Placeholders**: 코드 수정 시 `// ...` 와 같은 생략 표현을 절대 사용하지 않으며, 전후 문맥을 포함한 **완성형 코드**를 제공합니다.

- **Terminal Error SOP**: 터미널 출력에 깨진 문자나 인코딩 오류 발생 시, 즉시 `scripts/init-terminal.ps1`을 재실행하여 세션을 초기화하고 `$OutputEncoding`을 재확인합니다.
- **Context Caching**: 불필요한 I/O와 토큰 소모를 방지하기 위해, 한 번 읽은 디렉토리 구조나 파일 스키마는 `docs/memory.md`에 기록하거나 내부 메모리에 유지하며 중복 탐색을 최소화합니다.
- **Job Log Update**: 모든 주요 변경 사항은 `docs/memory.md`에 기록하고 업데이트합니다.
- **Log Compression**: 로그가 200줄에 도달하면 이전 기록을 50줄 이내로 요약 정리하여 효율적인 컨텍스트를 유지합니다.
