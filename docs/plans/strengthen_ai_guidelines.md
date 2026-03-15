# 🗺️ Project Blueprint: AI_GUIDELINES.md 강화

> 생성 일시: 2026-03-16 | 상태: 설계 승인 대기

## 🎯 Architectural Goal

- `AI_GUIDELINES.md`에 **Terminal Protocol (Architect Version)**의 핵심 내용을 흡수하여 에이전트의 기술적 체크리스트를 강화합니다.
- 현재 문서에 부재하거나 불충분한 8가지 영역을 식별하여 각각 원자적 Edit으로 통합합니다.
- **SSOT**: `docs/CRITICAL_LOGIC.md`와 충돌하지 않으며, `CLAUDE.md`의 Section 2·3·5·8을 보완합니다.

---

## 🔍 Gap Analysis — 현재 대비 누락 항목

| 항목 | Terminal Protocol 원본 | 현재 AI_GUIDELINES.md | 보강 필요도 |
|------|------------------------|----------------------|------------|
| 세션 초기화 완전성 | `InputEncoding`, `PSDefaultParameterValues`, `Clear-Host` | InputEncoding·PSDefaultParameterValues 누락 | **높음** |
| Catch 블록 위생 | `catch {}` vs `catch (e) {}` — TS6133 방지 | 미존재 | **높음** |
| Import 보존 원칙 | Zero-Tolerance (삭제 금지, 파일 전체 사용처 확인) | `Surgical Edits`로 부분 언급만 | **높음** |
| Cmdlet 파라미터 사전 검증 | `Get-Command + ContainsKey('Param')` 패턴 | `Get-Command` 존재 확인만 | **중간** |
| 설정 파일 존재 확인 | `tsconfig.json`, `package.json scripts` 사전 Test-Path | 미존재 | **중간** |
| node_modules 상태 체크 | `Module Not Found` 방지 로직 | 미존재 | **중간** |
| 컨텍스트 캐싱 원칙 | 파일 메타데이터 비교, 재읽기 금지 | 미존재 | **높음** |
| 로그 파일 우회 복구 | `> build_log.txt 2>&1` + `Get-Content -Tail 30` | 미존재 | **중간** |
| Linux→PowerShell 명령어 매핑 | `head/grep/rm -rf` 대체 표 | 미존재 (텍스트 언급만) | **높음** |
| 전역 스코프 삭제 전 검증 | `Select-String -Recursive` 증명 의무 | 미존재 | **중간** |

---

## 🛠️ Step-by-Step Execution Plan

> ⚠️ **각 Task는 단 하나의 도구 호출(Edit 1개)로 완료되어야 한다.**
> 현재 AI_GUIDELINES.md는 82줄 — 300줄 미만이므로 Refactoring Task 불필요.

### 📦 Task List

- [ ] **Task 1: Section 2 — 세션 초기화 블록 강화**
  - **Tool**: `Edit`
  - **Target**: `AI_GUIDELINES.md` — `## 2. 터미널 및 런타임 제어` 내 세션 초기화 코드블록
  - **Goal**: `[Console]::InputEncoding`, `$PSDefaultParameterValues['Out-File:Encoding']`, `Clear-Host` 3개 항목 추가
  - **Pseudocode**:
    ```powershell
    # 기존 2줄 블록을 4줄로 확장
    $OutputEncoding = [System.Text.Encoding]::UTF8
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    [Console]::InputEncoding = [System.Text.Encoding]::UTF8        # 추가
    $PSDefaultParameterValues['Out-File:Encoding'] = 'utf8'        # 추가
    $env:TERM = 'dumb'; $env:NO_COLOR = '1'
    $ProgressPreference = 'SilentlyContinue'
    Clear-Host  # 버퍼 잔상 제거 — 추가
    ```
  - **Dependency**: None

- [ ] **Task 2: Section 2 — Cmdlet 파라미터 사전 검증 패턴 추가**
  - **Tool**: `Edit`
  - **Target**: `AI_GUIDELINES.md` — `기술적 가용성 확인` 항목 하단에 신규 규칙 삽입
  - **Goal**: `Get-Command`로 도구 존재 여부 확인에서 더 나아가, **파라미터 키** 존재까지 검증하는 패턴 추가
  - **Pseudocode**:
    ```
    - **Cmdlet 파라미터 Pre-Validation**: 버전 의존적 파라미터 사용 전
      $cmd = Get-Command <Cmdlet> -ErrorAction SilentlyContinue
      if ($cmd -and $cmd.Parameters.ContainsKey('<ParamName>')) { ... }
      else { # fallback }
    ```
  - **Dependency**: None

- [ ] **Task 3: Section 2 — 설정 파일·의존성 사전 확인 규칙 추가**
  - **Tool**: `Edit`
  - **Target**: `AI_GUIDELINES.md` — `기술적 가용성 확인` 항목 하단
  - **Goal**: `tsc` 실행 전 `tsconfig.json` 확인, `npm run` 전 스크립트 존재 확인, `node_modules` 상태 체크 규칙 추가
  - **Pseudocode**:
    ```
    - **설정 파일 기반 의사결정**: 도구 실행 전 반드시 Test-Path로 선검증
      - tsc → tsconfig.json 존재 확인
      - npm run <script> → package.json 내 해당 스크립트 정의 확인
      - 빌드 명령 전 node_modules 유효성 확인, 미비 시 npm install 제안 우선
    ```
  - **Dependency**: None

- [ ] **Task 4: Section 2 — 컨텍스트 캐싱 및 파일 메타데이터 비교 규칙 추가**
  - **Tool**: `Edit`
  - **Target**: `AI_GUIDELINES.md` — `명령어 체이닝 금지` 항목 인근에 신규 항목 추가
  - **Goal**: 동일 파일 재읽기 금지 원칙 + 메타데이터 경량 대조 패턴 추가
  - **Pseudocode**:
    ```
    - **컨텍스트 캐싱 원칙**: 대화 기록에 이미 포함된 파일은 재읽지 않는다.
      변경 의심 시 전체 읽기 전 메타데이터만 대조:
      Get-Item <path> | Select-Object Name, Length, LastWriteTime,
        @{N='Hash'; E={(Get-FileHash $_.FullName).Hash.Substring(0,8)}}
    ```
  - **Dependency**: None

- [ ] **Task 5: Section 5 — Catch 블록 위생 + Import 보존 원칙 추가**
  - **Tool**: `Edit`
  - **Target**: `AI_GUIDELINES.md` — `## 5. 클린 코드 및 기능 구현 수칙` 내 `Surgical Edits` 항목 보강
  - **Goal**: TS6133 방지를 위한 catch 패턴 명시 + Import Zero-Tolerance 정책 명시
  - **Pseudocode**:
    ```
    - **Catch Block Hygiene (TS6133 방지)**: 에러 객체 미사용 시
      Bad:  catch (e) { ... }   ← TS6133 유발
      Good: catch { ... }       ← 현대적, 선호
      Alt:  catch (_e) { ... }  ← 선언 필요 시
    - **Import 보존 Zero-Tolerance**: 현재 함수에 미사용처럼 보여도
      같은 파일 내 다른 함수에서 사용 중일 가능성 99%. 자의적 삭제 금지.
      삭제 전 반드시 Select-String -Recursive로 전체 프로젝트 검색 후 증명.
    ```
  - **Dependency**: None

- [ ] **Task 6: Section 8 — 복구 SOP 및 로그 파일 우회 전략 강화**
  - **Tool**: `Edit`
  - **Target**: `AI_GUIDELINES.md` — `## 8. 기술적 체크리스트 및 복구` 에러 복구 흐름 항목
  - **Goal**: `TERMINAL_RECOVERY_MARKER` 사용법, `-NoProfile` 격리, 로그 파일 우회 전략 구체화
  - **Pseudocode**:
    ```
    - 버퍼 오염 시: Write-Output "=== TERMINAL_RECOVERY_MARKER ===" 로 스트림 절단
    - \e]633; 시퀀스 감지 시: 이후 모든 명령에 powershell.exe -NoProfile 접두어 필수
    - 출력이 과도하거나 인코딩 계속 깨질 때:
      npm run build > build_log.txt 2>&1
      Get-Content build_log.txt -Tail 30
    ```
  - **Dependency**: None

- [ ] **Task 7: Section 2 (또는 별도 박스) — Linux→PowerShell 명령어 매핑 표 추가**
  - **Tool**: `Edit`
  - **Target**: `AI_GUIDELINES.md` — Section 2 하단 또는 Section 8 하단
  - **Goal**: `head`, `grep`, `rm -rf`, `cat`, `ls` 등 리눅스 습관 명령어를 PowerShell 표준으로 매핑하는 테이블 추가
  - **Pseudocode**:
    ```markdown
    | Linux 습관 | PowerShell 표준 |
    |------------|----------------|
    | head -n N  | Select-Object -First N |
    | grep       | Select-String |
    | rm -rf     | Remove-Item -Recurse -Force |
    | cat        | Get-Content |
    | ls         | Get-ChildItem |
    ```
  - **Dependency**: None

- [ ] **Task 8: 무결성 확인 — 문서 최종 검토**
  - **Tool**: `Read`
  - **Target**: `AI_GUIDELINES.md` (전체)
  - **Goal**: 7개 Edit 반영 후 전체 흐름, 중복 항목, 300줄 초과 여부 확인
  - **Dependency**: Task 1 ~ Task 7

---

## ⚠️ 기술적 제약 및 규칙

- **Encoding**: AI_GUIDELINES.md는 `UTF-8 no BOM` 유지.
- **추가만**: 기존 항목 삭제·이동 없이 보강(Augmentation) 원칙 적용.
- **중복 금지**: Terminal Protocol의 내용 중 이미 존재하는 항목(예: AST Parser, 명령어 체이닝 금지)은 중복 추가하지 않고 기존 항목을 강화하는 방식으로 통합.

## ✅ Definition of Done

1. [ ] 8개 Task 완료 후 AI_GUIDELINES.md가 300줄 이내 유지.
2. [ ] Terminal Protocol의 모든 핵심 체크리스트가 AI_GUIDELINES.md에 흡수됨.
3. [ ] `memory.md` 변경 사항 반영 완료.
