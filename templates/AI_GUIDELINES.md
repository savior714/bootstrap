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
- **Surgical Changes**: 요청받지 않은 리팩토링이나 단순 코드 스타일 수정은 지양하며, 목표 달성에 필요한 **최소한의 코드**만 수정합니다.
- **Zombie Cleanup**: 작업 전 관련 프로세스(`node`, `tsc`, `cargo` 등)가 점유 중인지 확인하고 필요 시 정리합니다.
- **Safe Execution**: 복잡한 명령이나 파싱 에러가 잦은 도구는 최소 출력 플래그를 강제합니다.
  - ✅ `npm install --no-progress --loglevel=error`
  - ✅ `git clone -q`, `git fetch -q --prune`
  - ❌ `npm install` (플래그 없는 원본 명령 단독 실행 금지)
- **Pre-flight (CLI 존재 확인)**: `gh`, `docker`, `aws`, `python` 등 외부 도구 실행 전 반드시 존재 여부를 확인합니다.
  ```powershell
  if (Get-Command <command> -ErrorAction SilentlyContinue) { ... }
  ```
- **Pre-flight (스크립트 확인)**: `npm run <script>` 실행 전 반드시 `package.json`의 `scripts` 항목을 먼저 확인합니다.
- **에러 기반 탐색 금지**: "명령을 실행한 후 에러가 발생하면 설치가 안 된 것으로 간주"하는 방식은 **절대 금지**합니다. 반드시 `Get-Command` 또는 파일 존재 확인으로 사전 검증합니다.

## 4. 파일 읽기 및 컨텍스트 캐싱 (Context Caching)

- **캐싱 원칙**: 한 번 읽은 파일은 대화 컨텍스트에 캐싱된 것으로 간주합니다. 파일이 수정되지 않았다면 `Get-Content`를 다시 실행하지 않습니다.
- **파일 변경 확인**: 내용이 의심될 경우 전체를 재조회하는 대신 메타데이터로 변경 여부를 먼저 확인합니다.
  ```powershell
  Get-Item <file_path> | Select-Object Name, Length, LastWriteTime
  ```
- **세미콜론 연쇄 금지**: 여러 파일을 동시에 읽을 때 아래 형식을 사용하지 않습니다.
  - ❌ `Get-Content fileA.ps1; Get-Content fileB.ps1`
  - ✅ 각 파일을 별도 Tool Call로 분리하여 읽습니다.
- **터미널 대량 출력 금지**: 파일 내용을 터미널에 그대로 출력하는 행위를 금지합니다. 필요 시 `> "$env:TEMP\out.txt"` 로 저장 후 필요한 라인만 추출합니다.

## 5. 코드 무결성 및 설계 (Code Integrity)

- **Strict Typing**: `any` 또는 `dynamic` 타입을 금지하며, 명시적 타입 선언과 타입 가드를 사용합니다.
- **3-Layer Architecture**: Definition, Repository, Service/Logic 계층 구조를 지향합니다.
- **Early Return**: 조건문의 중첩을 피하고 가독성을 높이기 위해 Early Return 패턴을 사용합니다.
- **No Placeholders**: 코드 수정 시 `// ...` 와 같은 생략 표현을 절대 사용하지 않으며, 전후 문맥을 포함한 **완성형 코드**를 제공합니다.

## 6. Windows 경로 및 인코딩 준수 (Critical)

- **배치 파일 저장**: `.bat`, `.cmd` 파일은 반드시 ANSI(CP949)로 저장합니다. 세션이 UTF-8이더라도 저장 시 인코딩을 명시해야 합니다.
  ```powershell
  Set-Content -Path "file.bat" -Value $content -Encoding String
  ```
- **소스 코드 저장**: `.ps1`, `.ts`, `.js`, `.md` 등은 **UTF-8 (no BOM)**을 사용합니다. (PS5에서 파싱 오류 발생 시 ps1 한정 BOM 허용)
- **경로 표기**: Backslash(`\`) 대신 Slash(`/`)를 사용하거나 PowerShell에서는 `Join-Path`를 사용합니다.
- **파싱 에러 대응 SOP**: 터미널 파싱 에러 감지 시 즉시 아래 순서로 대응합니다.
  1. `Write-Output`으로 버퍼를 비웁니다.
  2. `scripts/init-terminal.ps1`을 재실행하여 세션 인코딩을 초기화합니다.
  3. 에러 메시지가 잘렸다면 `> "$env:TEMP\terminal_log.txt"` 로 저장 후 필요한 라인만 추출합니다.
  4. 가정 없이 원본 텍스트를 기반으로 원인을 진단합니다.

## 7. 작업 기록 (Memory Management)

- 모든 주요 변경 사항은 `docs/memory.md`에 기록하고 업데이트합니다.
- 로그가 200줄에 도달하면 이전 기록을 50줄 이내로 요약 정리하여 효율적인 컨텍스트를 유지합니다.
