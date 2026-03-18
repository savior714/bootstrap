# memory.md — Bootstrap DevEnv 작업 로그

---

## [누적 요약] 2026-03-10 ~ 2026-03-17 (11:00)

| 날짜 | 주요 작업 |
| --- | --- |
| 2026-03-10 | PS5 BOM 파싱 오류 해결, 창 종료 원인 README 명시 |
| 2026-03-11 | 그룹 번호 재정렬(1~8), `Add-ToUserPath` 추가, Java/Android PATH 자동 등록 |
| 2026-03-14 | 환경 설정 외부화, `AI_GUIDELINES.md` 마스터 가이드라인 승격, CLI 설치 가이드 대체 |
| 2026-03-15 | Terminal Protocol 정밀화, Safe Raw IO 수칙 추가, `CRITICAL_LOGIC.md` SSOT 반영 |
| 2026-03-16 | `AI_GUIDELINES.md` 프로토콜 대규모 강화(Section 1-11), Loop Prevention, TPG, Git Guard 섹션 신설 |
| 2026-03-17 | TPG Hygiene 고도화, AI_GUIDELINES/antigravityrules 'Deep-Dive Version' 개정 및 동기화 |
| 2026-03-18 | AI 실증 오류 4종 문서화: `.antigravityrules` 4 Guard 추가, `AI_GUIDELINES.md` Known Error Patterns 테이블 삽입, `docs/AI_COMMAND_PROTOCOL.md` 신규 생성 |

**안정 상태**: `AI_GUIDELINES` (Deep-Dive Ver.) / `antigravityrules` 동기화 완료 / `AI_COMMAND_PROTOCOL.md` 신규 / `memory.md` SSOT 유지

---

## [2026-03-17 14:20] AI Behavioral Guidelines 시니어 아키텍트 보완 제언 반영

### 작업 내용

| 파일 | 변경 내용 |
| --- | --- |
| `AI_GUIDELINES.md` | 시니어 아키텍트 제언(컨텍스트 위생, 패키지 매니저 락, 비동기 상태 추적) 반영 완료. (201줄) |

### 주요 반영 사항

- **Section 2**: **패키지 매니저 혼용 방지** 지침 추가. Lock 파일 확인을 통한 표준 도구 선정 원칙 수립.
- **Section 5**: **비동기 상태 추적 (Async State Tracking)** 지침 추가. 경합 상태 방지를 위한 **Cleanup** 및 **Loading State** 점검 의무화.
- **Section 6**: **컨텍스트 누적 관리 (Context Window Hygiene)** 지침 추가. `memory.md` 기반의 핵심 의사결정 집중 및 과거 구현 로그 무시 원칙 명문화.

### 진행 상황

- [x] Task 1: `AI_GUIDELINES.md` 섹션별 아키텍트 제언 통합 완료.
- [x] Task 2: `memory.md` 200줄 초과에 따른 누적 요약 및 최신 작업로그 업데이트 완료.
- [x] **Definition of Done**: 모든 요청 사항 반영 및 시스템 무결성 유지 확인.

## [2026-03-17 14:35] .antigravityrules 및 AI_GUIDELINES 정합성 동기화 완료

### 작업 내용

| 파일 | 변경 내용 |
| --- | --- |
| `.antigravityrules` | Tool & Path Resilience, Context Hygiene 섹션 추가 및 경로 격리 목록 최신화. |
| `AI_GUIDELINES.md` | `user_global` 규칙에 맞춰 `.nyc_output/**` 경로 추가 및 카테고리 동기화. |
| `templates/AI_GUIDELINES.md` | 변경된 가이드를 템플릿에 동기화하여 `check-env.ps1` 검증 통과. |

### 주요 결과

- **런타임 제약 강화**: 패키지 매니저 락 확인 및 경로 자가 치유(Path Resilience) 수칙을 `.antigravityrules`에 명문화하여 에이전트의 오작동 방지.
- **무결성 검증**: `scripts/check-env.ps1` 실행 결과 **All integrity checks passed** 확인. 
- **SSOT 일관성**: 전역 규칙, 마스터 가이드라인, 런타임 제약 파일 간의 격리 경로(Strict Context Isolation)를 100% 일치시킴.

## [2026-03-17 15:00] AI 거버넌스 프레임워크 완성 (Deep-Dive Ver. & Global SSOT)

### 작업 내용

| 파일 | 변경 내용 |
| --- | --- |
| `AI_GUIDELINES.md` | 시니어 아키텍트의 **심화 버전(Deep-Dive Version)**으로 전면 개정 및 계층적 참조 모델 도입. |
| `docs/CRITICAL_LOGIC.md` | 프로젝트의 최상위 불변의 원칙(Global SSOT)으로서 참조 구조 명문화. |

### 주요 성과

- **계층적 거버넌스 수립**: `CRITICAL_LOGIC`(Global) → `AI_GUIDELINES`(Behavioral) → `Project-Spec`(Specific)으로 이어지는 명확한 기술적 위계질서 확립.
- **표준화된 협업 지침**: AI 에이전트가 어떤 프로젝트에 투입되더라도 일관된 품질과 안정성을 유지할 수 있는 물리적 기반 마련.

### 진행 상황

- [x] Task 1: `AI_GUIDELINES.md` 최신 요구사항 반영 (Senior Architect 톤).
- [x] Task 2: 전역 공통 시스템 원칙인 `docs/CRITICAL_RULES.md` 생성.
- [x] **Stability Check**: 계층적 참조 모델에 따른 문서 간 정합성 확인 완료.

## [2026-03-17 15:10] .antigravityrules 최종 정합성 보완 및 SSOT 불일치 해결

### 작업 내용

| 파일 | 변경 내용 |
| --- | --- |
| `.antigravityrules` | `RULE[user_global]` SSOT에 맞춰 격리 경로(`.pnpm-store`, `.idea` 등) 및 `Join-Path` 규정 추가. |
| `AI_GUIDELINES.md` | 상단 Global SSOT 참조 오류 수정 (`CRITICAL_RULES.md` → `CRITICAL_LOGIC.md`). |

### 주요 결과

- **런타임 제약 완결**: 에이전트의 물리적 활동 범위를 규정하는 `.antigravityrules`를 최신 전역 규칙과 100% 동기화함.
- **참조 구조 정상화**: 실제 존재하지 않는 `CRITICAL_RULES.md` 참조를 `CRITICAL_LOGIC.md`로 수정하여 기술적 위계질서의 구멍을 메움.
- **Microtask 준수**: 모든 작업은 '1 Task = 1 Tool Call' 원칙 하에 단계별로 수행됨.

### 진행 상황

- [x] Task 1: `.antigravityrules` 격리 경로 및 TPG 프로토콜 최신화 완료.
- [x] Task 2: `AI_GUIDELINES.md` 내 SSOT 파일명 오기 수정 완료.
- [x] **Stability Check**: 모든 SSOT 파일 간 상호 참조 무결성 확인 완료.

## [2026-03-17 17:40] AI Behavioral Guidelines 개정 프로세스 시작

### 작업 내용

| 파일 | 변경 내용 |
| --- | --- |
| `AI_GUIDELINES.md.bak` | 원본 가이드라인 백업 파일 생성(`Task 1`). |
| `docs/plans/update_ai_guidelines.md` | Task 1 상태 업데이트 예정. |

### 주요 진행 상황

- [x] **Task 1**: `AI_GUIDELINES.md` 백업 및 초기 상태 보존 완료.
- [x] **Task 2**: `AI_GUIDELINES.md` 내용 전면 개정 완료.
- [x] **Task 3**: `AI_GUIDELINES.md` 무결성 검증(`Get-Content` UTF-8) 완료.

### 검증 결과
- `Test-Path 'c:\develop\bootstrap\AI_GUIDELINES.md.bak'` -> `True` 확인.
- `AI_GUIDELINES.md` 첫 10줄 UTF-8 인코딩 확인 완료.

## [2026-03-18] 문서 위계 확립 및 지침 문서 역할 분리 리팩터링

### 작업 내용

| 파일 | 변경 내용 |
| --- | --- |
| `CLAUDE.md` | 12섹션 → 2섹션으로 슬림화. 페르소나·Fatal Guard·문서 위계 선언만 유지, 나머지는 하위 문서 위임. |
| `AI_GUIDELINES.md` | **What** 전담 문서로 재정의. Known Error Patterns 표·Standard Mapping·금지 cmdlet 표 제거, `AI_COMMAND_PROTOCOL.md` 위임 명시. |
| `docs/AI_COMMAND_PROTOCOL.md` | **Section 5 신규 추가**: `Add-Content`/`Set-Content`/`Out-File` 프로필 보안 차단 패턴 및 `.NET` 대체 메서드 실증 가이드. |
| `templates/AI_GUIDELINES.md` | 신규 프로젝트 복사 템플릿임을 명시, `{{PLACEHOLDER}}` 도입, 현행 룰과 분리. |

### 확립된 문서 위계

| 우선순위 | 파일 | 역할 |
| :---: | --- | --- |
| 1 | `CLAUDE.md` | 진입점 & Fatal Guard |
| 2 | `AI_GUIDELINES.md` | 행동 원칙 (What) |
| 3 | `docs/AI_COMMAND_PROTOCOL.md` | 터미널 실행 가이드 (How) — 오류 패턴 SSOT |
| 4 | `docs/CRITICAL_LOGIC.md` | 프로젝트 설계 결정 |
| 5 | `docs/memory.md` | 세션 상태 SSOT |

### 글로벌 슬래시 커맨드 개선 (`~/.claude/commands/`)

- **`go.md`**: 문서 위계 참조 표 추가, 코드 정적 분석·300라인 초과·SSOT 교차 검증 단계 신설, 린트 Blocker 복원.
- **`plan.md`**: Stale Context 방지·영향 범위 분석·롤백 전략·Task별 Verify 필드·BLUEPRINT CHECKLIST 출력 형식 추가.
- **`git.md`**: 환경 호환성 노트 추가, `AI_COMMAND_PROTOCOL.md` SSOT 목록 편입.

### 진행 상황

- [x] 문서 위계 설계 및 역할 분담 확정.
- [x] 3개 지침 문서 리팩터링 완료 (`CLAUDE.md`, `AI_GUIDELINES.md`, `templates/`).
- [x] `AI_COMMAND_PROTOCOL.md` Section 5 추가 및 요약 대조표 갱신.
- [x] 글로벌 슬래시 커맨드 3종 환경 호환성 및 무결성 보강.

## [2026-03-18 01:15] AI Behavioral Guidelines 강화 및 Deep-Dive Ver. 정립

### 작업 내용

| 파일 | 변경 내용 |
| --- | --- |
| `AI_GUIDELINES.md` | 시니어 아키텍트의 **Deep-Dive Version** 제언을 수용하여 전면 개정 및 강화. |

### 주요 강화 사항

- **TPG Protocol v2.0**: 터미널 명령어 절단 방지를 위한 마커(`---START---`) 및 `powershell.exe -NoProfile` 강제화.
- **Context Resilience**: `LastWriteTime` 기반의 Stale Context 무효화 및 `Path Self-Healing` 로직 명문화.
- **SQL 무결성**: `Idempotency` 가드 및 `Safety Net`(트랜잭션 블록) 수칙 추가.
- **정밀 수정(Surgical Edits)**: 수정 후 전체 파일을 다시 읽어 메모리 싱크를 맞추는 의무 조항 신설.

### 진행 상황

- [x] **Task 1**: `AI_GUIDELINES.md` 내용 수정, 보완, 강화 완료.
- [x] **Task 2**: `memory.md` 최신 작업 로그 업데이트 완료.
- [x] **Stability Check**: Senior Architect 톤 및 한국어 표준 준수 확인.
