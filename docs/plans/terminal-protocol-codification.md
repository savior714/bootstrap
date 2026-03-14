# 🗺️ Project Blueprint: Terminal Protocol Codification

> 생성 일시: 2026-03-14 | 상태: 설계 승인 대기

## 🎯 Architectural Goal

- **기존 Terminal Protocol의 구체적 패턴 명문화**: `CRITICAL_LOGIC.md` Section 8 및 `AI_GUIDELINES.md`에는 원칙만 존재하며, 실제 에이전트가 따라야 할 **구체적 명령 패턴**이 누락되어 있음. 이를 행동 지침 수준으로 정밀화한다.
- **Gap 해소 대상 (6개 항목)**:
  1. `npm install --no-progress --loglevel=error` 등 도구별 Safe Execution 플래그
  2. `Get-Command <cmd> -ErrorAction SilentlyContinue` Pre-flight 패턴
  3. **에러 기반 탐색 금지** 원칙 (명령 날려보고 에러 확인하는 방식)
  4. `Get-Item | Select-Object Name, Length, LastWriteTime` 파일 변경 확인 패턴
  5. **세미콜론 연쇄 금지** (`Get-Content ...; Get-Content ...`)
  6. `.bat` 파일 저장 시 `Set-Content -Encoding String` 명시
- **SSOT 정렬**: `CRITICAL_LOGIC.md` Section 8(Terminal Interaction Protocol) 및 `templates/AI_GUIDELINES.md`와 완전히 일치해야 함.

---

## 🛠️ Step-by-Step Execution Plan

> 아래 목록은 **독립적인 기능 단위**로 설계되었습니다. 우선순위에 따라 원하는 항목을 선택하여 진행을 요청하세요.

### 📦 Task List

> ⚠️ **각 Task는 단 하나의 도구 호출(Read / Edit / Write / Bash 중 1개)로 완료되어야 한다.**

---

- [ ] **Task 1: AI_GUIDELINES.md — Section 3 Safe Execution 패턴 추가**
  - **Tool**: `Edit`
  - **Target**: `c:/develop/bootstrap/templates/AI_GUIDELINES.md`
  - **Goal**: `## 3. 터미널 및 시스템` 섹션에 Safe Execution 및 Pre-flight 구체 패턴 추가
  - **Pseudocode**:
    ```markdown
    - **Safe Execution**: `npm install --no-progress --loglevel=error` / `git clone -q` 등 도구별 최소 출력 플래그 강제.
    - **Pre-flight (CLI 존재 확인)**: 외부 도구 실행 전 반드시 `if (Get-Command <cmd> -ErrorAction SilentlyContinue)` 로 존재 여부 확인.
    - **Pre-flight (스크립트 확인)**: `npm run <script>` 실행 전 `package.json`의 `scripts` 항목을 먼저 확인.
    - **에러 기반 탐색 금지**: "명령 실행 후 에러로 존재 여부 판단" 방식 절대 금지. 반드시 사전 확인.
    ```
  - **Dependency**: None

---

- [ ] **Task 2: AI_GUIDELINES.md — Section 3 Context Caching 패턴 추가**
  - **Tool**: `Edit`
  - **Target**: `c:/develop/bootstrap/templates/AI_GUIDELINES.md`
  - **Goal**: `## 3. 터미널 및 시스템` 섹션에 Context Caching 및 세미콜론 연쇄 금지 추가
  - **Pseudocode**:
    ```markdown
    - **Context Caching**: 읽은 파일은 대화 컨텍스트에 캐싱된 것으로 간주. 파일이 수정되지 않았다면 재조회 금지.
    - **파일 변경 확인**: 재조회 전 `Get-Item <path> | Select-Object Name, Length, LastWriteTime` 으로 변경 여부만 확인.
    - **세미콜론 연쇄 금지**: `Get-Content ...; Get-Content ...` 형식의 다중 파일 동시 읽기 금지.
    ```
  - **Dependency**: Task 1

---

- [ ] **Task 3: AI_GUIDELINES.md — Section 6 추가 (Windows 경로 및 인코딩)**
  - **Tool**: `Edit`
  - **Target**: `c:/develop/bootstrap/templates/AI_GUIDELINES.md`
  - **Goal**: `.bat` 저장 시 `Set-Content -Encoding String` 패턴 및 Slash 사용 원칙을 별도 섹션으로 명문화
  - **Pseudocode**:
    ```markdown
    ## 6. Windows 경로 및 인코딩 준수 (Critical)
    - **배치 파일 저장**: `Set-Content -Path "file.bat" -Value $content -Encoding String`
    - **경로 표기**: Backslash(\) 대신 Slash(/)를 사용하거나 `Join-Path`를 사용.
    - **파싱 에러 SOP**: 에러 감지 시 → `Write-Output`으로 버퍼 비우기 → `init-terminal.ps1` 재실행 → 필요 시 `> terminal_log.txt` 저장 후 추출.
    ```
  - **Dependency**: Task 2

---

- [ ] **Task 4: CRITICAL_LOGIC.md — Section 8 구체 패턴 동기화**
  - **Tool**: `Edit`
  - **Target**: `c:/develop/bootstrap/docs/CRITICAL_LOGIC.md`
  - **Goal**: Section 8의 테이블에 `세미콜론 연쇄 금지`, `에러 기반 탐색 금지`, `Get-Item 변경 확인 패턴` 항목 추가
  - **Pseudocode**:
    ```markdown
    | **에러 기반 탐색 금지** | 명령 실행 후 에러로 존재 여부 판단하는 방식 절대 금지. Get-Command로 사전 확인 필수 |
    | **세미콜론 연쇄 금지** | `Get-Content; Get-Content` 형식의 다중 동시 읽기 금지 |
    | **파일 변경 확인** | `Get-Item <path> | Select-Object Name, Length, LastWriteTime` 패턴 사용 |
    ```
  - **Dependency**: Task 3

---

- [ ] **Task 5: 검증 — AI_GUIDELINES.md 라인 수 확인**
  - **Tool**: `Bash`
  - **Command**: `(Get-Content "c:/develop/bootstrap/templates/AI_GUIDELINES.md").Count`
  - **Goal**: 수정 후 파일이 300라인 미만임을 확인 (글로벌 룰 0 준수)
  - **Dependency**: Task 4

---

## ⚠️ 기술적 제약 및 규칙 (SSOT)

| 항목 | 규칙 |
|------|------|
| **인코딩** | `AI_GUIDELINES.md`, `CRITICAL_LOGIC.md` 모두 **UTF-8 no BOM** |
| **PS1 인코딩** | `init-terminal.ps1`은 PS5 호환을 위해 **UTF-8 with BOM** 유지 |
| **bat 인코딩** | `.bat` 파일 저장은 반드시 `Set-Content -Encoding String` (ANSI/CP949 출력) |
| **수정 범위** | 기존 완성된 `init-terminal.ps1`은 수정 금지. `AI_GUIDELINES.md`, `CRITICAL_LOGIC.md`만 대상 |
| **리팩토링** | 기능 구현에 필수적이지 않은 리팩토링 금지 |

## ✅ Definition of Done

1. [ ] `AI_GUIDELINES.md`에 6개 Gap 항목이 모두 구체적 패턴 수준으로 명문화됨.
2. [ ] `CRITICAL_LOGIC.md` Section 8이 신규 항목과 동기화됨.
3. [ ] 두 파일 모두 300라인 미만 유지.
4. [ ] `memory.md`에 변경 사항 반영 완료.
