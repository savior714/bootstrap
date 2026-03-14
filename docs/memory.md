# memory.md — Bootstrap DevEnv 작업 로그

---

## [2026-03-10] 초기 디버깅 및 정리

### 발견된 문제

1. **창 즉시 종료 (더블클릭)**: admin self-elevation 후 원본 창이 닫히는 정상 동작이나 혼란 유발 → README에 명시
2. **PS5 파싱 오류**: UTF-8 no BOM 파일을 PS5가 ANSI(CP949)로 읽어 `>>>` 문자열을 리다이렉션 연산자로 오인
   - 증상: `Missing file specification after redirection operator` at line 229
   - 해결: PS1 파일을 **UTF-8 with BOM**으로 재저장

### 초기 변경 사항

| 파일 | 변경 내용 |
| :--- | :--- |
| `Bootstrap-DevEnv.ps1` | PS7 패키지 그룹(#2) 제거, Desc 필드 제거, UTF-8 BOM 적용 |
| `bootstrap.bat` | pwsh 감지 로직 제거 → `powershell.exe` 고정, PS7 echo 제거 |
| `README.md` | 관리자 실행 필수 안내, PS7 행 제거, 용도 열 제거 |
| `docs/CRITICAL_LOGIC.md` | SSOT 신규 작성 |
| `docs/memory.md` | 작업 로그 신규 작성 |

---

## [2026-03-11] 추가 기능 및 정리

### 추가 변경 사항

| 파일 | 변경 내용 |
| :--- | :--- |
| `Bootstrap-DevEnv.ps1` | 그룹 번호 재정렬(1~8 연속), pwsh verCheck 제거, `Add-ToUserPath` 함수 추가, Java/Android PATH 자동 등록 |
| `README.md` | 그룹 번호 테이블 동기화 |
| `docs/CRITICAL_LOGIC.md` | Post-install 자동화 항목 상세 업데이트 |

---

## [2026-03-14] Antigravity 환경 무결성 검증 엔진 (Integrity Engine)

### 인테그리티 변경 사항

| 파일 | 변경 내용 |
| :--- | :--- |
| `scripts/check-env.ps1` | 초기 환경 검증 엔진 구축 (Node, Git, npm, pnpm, yarn 가용성 검증) |
| `scripts/check-env.ps1` | 핵심 설정(.npmrc, .gitconfig) 무결성 검증 로직 추가 (Task 2) |
| `scripts/check-env.ps1` | 파일 시스템 및 인코딩 무결성(UTF-8 no BOM) 검증 로직 추가 (Task 3) |
| `scripts/check-env.ps1` | IDE(VSCode) 설정 무결성 검증 로직 추가 및 settings.json 생성 (Task 4) |
| `scripts/check-env.ps1` | 기술 스택 Dry-Run 검증 로직 추가 (tsc, eslint, prettier) (Task 5) |
| `shared_lint_rules.json` | 신규 생성 규칙 (no-console, semi) |
| `eslint.config.js` | 신규 생성 규칙 (no-console, semi) |
| `scripts/check-env.ps1` | 공유 린트 정책 동기화 검증 로직 추가 (Task 7) |
| `scripts/check-env.ps1` | 통합 보고서(env_report.json) 생성 및 복구 제안 로직 추가 (Task 8) |

### 진행 상황

- [x] Task 1: `scripts/check-env.ps1` 초기 구조 및 Core CLI/Runtime 검증 구현
- [x] Task 2: 핵심 설정 파일(.npmrc, .gitconfig) 무결성 검증
- [x] Task 3: 파일 시스템 및 인코딩 무결성 스캔 로직 추가
- [x] Task 4: IDE(VSCode/Antigravity) 설정 동기화 검증
- [x] Task 5: 기술 스택 헬스체크 (Dry-Run) 및 바이너리 검증
- [x] Task 6: 네트워크 환경 및 레지스트리 도달성 검증
- [x] Task 7: 공유 린트 정책(Shared Policy) 동기화 검증
- [x] Task 8: 통합 보고서(`env_report.json`) 생성 및 자동 복구 제안
- [x] Git Push: 모든 변경 사항을 SSOT 문서에 반영하고 원격 저장소에 푸시
- [x] Fix: `Bootstrap-DevEnv.ps1`을 UTF-8 with BOM으로 재저장하여 PS5 파싱 오류 해결
- [x] Fix: `bootstrap.bat` 끝에 `pause` 추가하여 비정상 종료 시 원인 파악 가능하도록 개선

---

## [2026-03-14] 메뉴 키 입력 버그 수정

### 문제
인터랙티브 선택 메뉴에서 1~8 키 입력 시 `[System.Collections.Specialized.OrderedDictionary]` 관련 에러 발생 후 메뉴 재렌더링.

### 원인
`$groups`는 `[ordered]@{}`(`System.Collections.Specialized.OrderedDictionary`) 타입이며, `.ContainsKey()` 메서드가 존재하지 않음.
`Hashtable`의 `.ContainsKey()`와 혼동 — `OrderedDictionary`는 `.Contains()`만 지원.

### 해결

| 파일 | 변경 내용 |
| :--- | :--- |

---

## [2026-03-14] AI 지침 및 린트 정책 표준화 (Cross-Project Standardization)

### 작업 내용

| `scripts/check-env.ps1` | AI_GUIDELINES.md 존재 여부 검사 및 self-healing 복구 로직 추가 (Task 3) |
| `scripts/fix-encoding.ps1` | PS5 호환성 지원을 위해 --add-bom 옵션 추가 (Task 3) |
| `docs/CRITICAL_LOGIC.md` | 전역 규칙 관리 표준(AI & Technical) 가이드라인 추가 (Task 4) |

### 진행 상황

- [x] Task 1: `templates/AI_GUIDELINES.md` 신규 생성
- [x] Task 2: `shared_lint_rules.json` 고도화
- [x] Task 3: `scripts/check-env.ps1` 지침 동기화 로직 추가
- [x] Task 4: `docs/CRITICAL_LOGIC.md` 전역 규칙 관리 표준 추가

---

## [2026-03-14] 터미널 파싱 에러 방지 프로토콜 (Terminal Interaction Protocol)

### 작업 내용

| `Bootstrap-DevEnv.ps1` | 터미널 초기화 로직 통합 (`init-terminal.ps1` 연동) (Task 3) |
| `docs/CRITICAL_LOGIC.md` | Terminal Interaction Protocol 섹션 추가 (SSOT 반영) (Task 4) |

### 진행 상황

- [x] Task 1: `.antigravityrules` 생성 — 터미널 아키텍처 규칙 정의
- [x] Task 2: `scripts/init-terminal.ps1` 생성 — 세션 초기화 스크립트
- [x] Task 3: `Bootstrap-DevEnv.ps1` 업데이트 — 터미널 설정 통합
- [x] Task 4: `docs/CRITICAL_LOGIC.md` 업데이트 — 터미널 프로토콜 SSOT 반영
- [x] Task 5: 검증 및 `memory.md` 기록


---

## [2026-03-14] Antigravity Zero-Config Automation

### 작업 내용

| 파일 | 변경 내용 |
| :--- | :--- |
| `Bootstrap-DevEnv.ps1` | 전역 환경 변수(`ANTIGRAVITY_BOOTSTRAP_PATH`) 등록 및 PS `$PROFILE` 주입 로직 추가 |
| `scripts/check-env.ps1` | 전역 Git/NPM 설정 무결성 검증 고도화 및 `core.autocrlf=false` 표준화 |
| `docs/CRITICAL_LOGIC.md` | Zero-Config 자동화 섹션(#9) 추가 |

### 진행 상황

- [x] Task 1: `ANTIGRAVITY_BOOTSTRAP_PATH` 환경 변수 사용자 자동 등록 구현
- [x] Task 2: PowerShell Profile(`$PROFILE`)에 `init-terminal.ps1` 영구 주입 로직 추가
- [x] Task 3: 전역 Git(`core.autocrlf=false`, `init.defaultBranch=main`) 및 NPM 설정 강제화
- [x] Task 4: `CRITICAL_LOGIC.md` SSOT 업데이트
- [x] Task 5: `memory.md` 작업 기록 완료


---

## [2026-03-14] 터미널 프로토콜 정밀화 (Terminal Protocol Refinement)

### 작업 내용

| 파일 | 변경 내용 |
| :--- | :--- |
| `scripts/init-terminal.ps1` | UTF-8 인코딩 SSOT 고정, $ProgressPreference 억제 및 텔레메트리 차단 추가 (Task 1) |
| `AI_GUIDELINES.md` | Pre-flight Check, Safe Execution, Terminal Error SOP, Context Caching 지침 추가 (Task 2) |

### 진행 상황

- [x] Task 1: `scripts/init-terminal.ps1` 고도화 및 정밀 설정 반영
- [x] Task 2: `AI_GUIDELINES.md` 행동 지침 (Pre-flight, SOP) 업데이트
- [x] Task 3: `docs/CRITICAL_LOGIC.md` SSOT 프로토콜 동기화
- [x] Task 4: `scripts/check-env.ps1` 인코딩 검증 로직 강화

---

## [2026-03-14] Terminal Protocol 구체적 패턴 명문화 (Codification)

### 작업 내용

| 파일 | 변경 내용 |
| :--- | :--- |
| `templates/AI_GUIDELINES.md` | Section 3 확장: Safe Execution 패턴, Pre-flight 패턴, 에러 기반 탐색 금지 추가 |
| `templates/AI_GUIDELINES.md` | Section 4 신설: Context Caching, 세미콜론 연쇄 금지, `Get-Item` 변경 확인 패턴 |
| `templates/AI_GUIDELINES.md` | Section 6 신설: Windows 경로/인코딩 준수, 파싱 에러 SOP (`Set-Content -Encoding String`) |
| `docs/CRITICAL_LOGIC.md` | Section 8 테이블에 3개 항목 동기화 (에러 기반 탐색 금지, 세미콜론 연쇄 금지, 파일 변경 확인 패턴) |
| `docs/plans/terminal-protocol-codification.md` | Blueprint 신규 생성 (6개 Gap 항목 기반 5-Task 계획) |

### 진행 상황

- [x] Task 1~5: 모든 Gap 항목 명문화 완료
- [x] 검증: `AI_GUIDELINES.md` 76줄 / `CRITICAL_LOGIC.md` 139줄 (300줄 미만)
