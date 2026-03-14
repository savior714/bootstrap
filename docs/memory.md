# memory.md — Bootstrap DevEnv 작업 로그

---

## [요약] 2026-03-10 ~ 2026-03-14 누적 작업

| 날짜       | 주요 작업                                                                                                          |
| ---------- | ------------------------------------------------------------------------------------------------------------------ |
| 2026-03-10 | 초기 디버깅: PS5 BOM 파싱 오류 해결, 창 종료 원인 README 명시                                                      |
| 2026-03-11 | 그룹 번호 재정렬(1~8), `Add-ToUserPath` 함수 추가, Java/Android PATH 자동 등록                                     |
| 2026-03-14 | Integrity Engine(`check-env.ps1`) 8단계 구축: Core CLI, 설정 무결성, 인코딩, IDE, 기술스택, 네트워크, 린트, 보고서 |
| 2026-03-14 | 메뉴 버그 수정: `OrderedDictionary` `.ContainsKey()` → `.Contains()`                                               |
| 2026-03-14 | AI 지침 표준화: `templates/AI_GUIDELINES.md`, `shared_lint_rules.json` 고도화                                      |
| 2026-03-14 | Terminal Interaction Protocol 수립 및 CRITICAL_LOGIC.md Section 8 SSOT 반영                                        |
| 2026-03-14 | Zero-Config Automation: `ANTIGRAVITY_BOOTSTRAP_PATH` 환경 변수 등록, PS Profile 주입                               |
| 2026-03-14 | Terminal Protocol 정밀화: `init-terminal.ps1` 고도화, AI_GUIDELINES 패턴 명문화                                    |
| 2026-03-14 | ECO 브랜딩 제거: `Bootstrap-DevEnv.ps1` 5개 하드코딩 흔적 → Antigravity 대체                                       |
| 2026-03-14 | Extended Terminal Protocol: Syntax Check 도입, UTF-8 no BOM 표준화, VSCode 설정 No BOM 보장                        |

**현재 상태**: `CRITICAL_LOGIC.md` 139줄 / `shared_lint_rules.json` 307줄 / `Bootstrap-DevEnv.ps1` ~350줄

---

## [2026-03-14] 하드코딩 금지 및 설정 외부화 (Config Externalization)

### 작업 내용

| 파일                     | 변경 내용                                                                                                    |
| ------------------------ | ------------------------------------------------------------------------------------------------------------ |
| `.gitignore`             | `.env`, `.env.local`, `.env.*.local`, `*.secret`, `*.key` 패턴 추가                                          |
| `.env.example`           | 신규 생성 — 환경 변수 키·설명·기본값 문서화 (Zero-Config 온보딩 기준)                                        |
| `config/packages.json`   | 신규 생성 — 패키지 그룹 메타데이터 외부화. `{WINDOWS_SDK_VER}` 플레이스홀더                                  |
| `config/paths.ps1`       | 신규 생성 — 경로·버전 상수 SSOT. 환경 변수 Override 패턴 (PS5 호환)                                          |
| `Bootstrap-DevEnv.ps1`   | `config/paths.ps1` dot-source 주입, Java 경로·VS SDK 버전 상수화, `$WINGET_ALREADY_INSTALLED_CODE` 상수 추가 |
| `docs/CRITICAL_LOGIC.md` | Section 3 경로 참조를 `config/paths.ps1` 기준으로 업데이트                                                   |

### 진행 상황

- [x] Task 1: AI_GUIDELINES.md 표준화 및 고도화
- [x] Task 2: CLAUDE.md 상속 구조 도입 및 슬림화 (139L -> 43L)
- [x] Task 3: memory.md 업데이트 및 아키텍처 반영

---

## [2026-03-14] Terminal Protocol Extended (Ongoing)

### 작업 내용

| 파일        | 변경 내용                                          |
| ----------- | -------------------------------------------------- |
| `CLAUDE.md` | Section 3 Linux→PowerShell 명령어 매핑 테이블 추가 |

### 진행 상황 (완료)

- [x] Task 1: AI_GUIDELINES.md 표준화 및 고도화 (마스터 가이드라인 승격)
- [x] Task 2: CLAUDE.md 상속 구조 유지 (사용자 요청에 따라 슬림화 없이 현 상태 유지)
- [x] Task 4: AI_GUIDELINES.md 이동성 검증 체크리스트 추가
- [x] Task 5: 신규 프로젝트 온보딩 드라이런(Dry-run) 수행 및 검증 완료

---

## [2026-03-14] AI Guidelines Rationalization & Portability (Ongoing)

### 작업 내용

| 파일               | 변경 내용                                                                         |
| ------------------ | --------------------------------------------------------------------------------- |
| `AI_GUIDELINES.md` | Section 11 드라이런 수행 — 임시 프로젝트 환경에서 온보딩 체크리스트의 실효성 입증 |
| `docs/memory.md`   | 드라이런 결과 기록 및 기술 부채(L300 초과) 해결 계획 수립                         |

### 진행 상황

- [x] Task 1: AI Onboarding Checklist 정상 작동 여부 드라이런 수행
- [x] Task 2: `scripts/check-env.ps1` 무결성 검증(Hash 비교) 로직 추가
- [x] Task 3: `scripts/check-env.ps1` 300라인 초과에 따른 하위 모듈 분리(Refactoring)
- [x] Task 4: `scripts/check-env.ps1`과 `templates/AI_GUIDELINES.md` 간 동기화 정밀 검증

---

## [2026-03-14] Extended Terminal Protocol & Encoding Standard

### 작업 내용

| 파일                       | 변경 내용                                                                                           |
| -------------------------- | --------------------------------------------------------------------------------------------------- |
| `AI_GUIDELINES.md`         | Extended Terminal Protocol (Syntax Check, NoProfile, Recovery SOP) 통합 및 인코딩 UTF-8 no BOM 통일 |
| `scripts/lib/env-core.ps1` | `Update-VSCodeSetting` 함수 수정 — No BOM 보장을 위해 `[System.IO.File]::WriteAllText` 도입         |
| `scripts/check-env.ps1`    | `UTF8NoBom` 검증 대상 확대 (PowerShell 스크립트 전면 포함)                                          |

### 진행 상황

- [x] Task 1: `AI_GUIDELINES.md` 수정 — 확장 터미널 프로토콜 통합
- [x] Task 2: `scripts/lib/env-core.ps1` 및 `check-env.ps1` 수정 (인코딩 표준 준수)
- [x] Task 3: `docs/memory.md` 최신화

---

## [2026-03-14] Finalization & Git Push

### 작업 내용

| 파일                     | 변경 내용                                                                      |
| ------------------------ | ------------------------------------------------------------------------------ |
| `docs/CRITICAL_LOGIC.md` | Section 10 Encoding Standard & File Rules 추가                                |
| `docs/memory.md`         | 세션 최종 요약 및 `/git` 워크플로우 실행 기록 추가                             |
| 전체 프로젝트            | Git 커밋 및 원격 저장소 푸시 (`feat(docs): consolidate architecture standards`) |

### 진행 상황

- [x] Task 1: SSOT 문서(`CRITICAL_LOGIC.md`) 최종 업데이트
- [/] Task 2: `/git` 워크플로우를 통한 Git Commit & Push (진행 중)
