# AGENTS.md — Unified Execution Constitution (Bootstrap Kernel)

에이전트 **헌법 요약**입니다. 우선순위·게이트·레지스트리 진입점만 둡니다. 표·긴 스킬 목록은 레지스트리 파일로 위임합니다.

---

## 0. Priority / Rule Precedence

우선순위는 아래와 같습니다.

1. `PROJECT_RULES.md`
2. 본 문서 (`AGENTS.md`)
3. `agents/core/*.md`
4. `agents/domains/**/*.md` (프로젝트가 추가한 경우)
5. 기타 명세 및 가이드라인

충돌 시 위 순서를 따르며, 불명확하면 질문합니다.

---

## 1. Core Operating Principles
중복 방지: `.cursor/rules/` 미사용. 슬래시·키워드: [WORKFLOW_AND_SKILL_INDEX.md](agents/registry/WORKFLOW_AND_SKILL_INDEX.md).
normative SSOT: [agents/core/principles.md](agents/core/principles.md)

- **Policy**: [PROJECT_RULES.md §3](PROJECT_RULES.md)
- **Think Before Coding · Quick Pick**: [principles.md §1.1](agents/core/principles.md#11-think-before-coding)
- **Simplicity · Surgical · Goal-Driven**: [principles.md §1.2–§1.4](agents/core/principles.md#12-simplicity-first)
- **Bug Fixes**: [/diagnose](agents/workflows/diagnose.md) · [/investigate](agents/workflows/investigate.md)
- **Merge & Review**: [/review](agents/skills/review/SKILL.md)
- **Execution Rules**: [execution.md §2](agents/core/execution.md)
- **Subagent Orchestration (O2 Strengthened)**: [orchestration.md](agents/core/orchestration.md) — 구현·편집·탐색은 Task 위임; **연속 작업 2+ → subagent 필수**; **chunk**(파일 1·함수 1) 순차 · 턴당 spawn 1개; 메인=지휘·합성만
- **Commit Gate Failure**: [error_patterns.md §10](agents/core/error_patterns.md#10-커밋-게이트-실패시--no-verify-금지) — `--no-verify` 우회 절대 금지, 반드시 오류 수정 후 재시도
- **Edit Tool Schema**: [routing.md §1.1](agents/core/routing.md#11-file-edit-tool-schema-편집-도구-ssot) (Cursor) · [runtime_edit_tools.md](agents/core/runtime_edit_tools.md)
- **Workaround Accountability**: [principles.md §1.7](agents/core/principles.md#17-workaround-accountability--close-turn-reflection)
- **Stepwise Execution & Concise Reasoning**: [principles.md §1.5](agents/core/principles.md#15-stepwise-execution--concise-reasoning)
- **Git / PR (HITL)**: [git.md](agents/workflows/git.md) · [PROJECT_RULES.md §3.4](PROJECT_RULES.md) — 사용자 명시 요청만
- **Code Quality Lifecycle** (설계→구현→리뷰→테스트): [code_quality_lifecycle.md](agents/core/code_quality_lifecycle.md)

---

## 2. Execution Gates (pointer)

**O2 선행 (구현·편집·탐색)**: 아래 §2·§3·§4 게이트는 **실행 subagent**가 따른다. 메인은 [orchestration_detail.md](agents/core/orchestration_detail.md) O2 Strengthened — triage·Task spawn·handoff 합성만; 구현·편집·코드베이스 탐색은 **항상 Task 위임**; **연속 작업 2+ → subagent 필수**(메인 연속 직접 수행 금지); **chunk**(파일 1·함수 1) 단위·**턴당 spawn 1개** ([orchestration_detail.md §2 Chunk](agents/core/orchestration_detail.md#chunk--turn-budget)). 질문·설명·[§5 O0](agents/core/orchestration_detail.md#5-직접-실행-예외-o0) 예외만 메인 직접.

**메타 금지 12** normative SSOT: [error_patterns.md#메타-금지-12](agents/core/error_patterns.md#메타-금지-12) (`always_apply`).

### 2.1 Editing / Routing

**실행 subagent MUST** — 규범 SSOT: [routing.md](agents/core/routing.md) §1 · §2 · [orchestration_detail.md §4 Gates](agents/core/orchestration_detail.md#4-handoff-계약-task-prompt-필수). WRONG/CORRECT: [error_patterns §1](agents/core/error_patterns.md#1-파일-편집-실수) lazy-load. 요약: Read 최신본 → oldString 완벽 일치·고유 블록 지정 → old≠new → 원자 편집(함수·컴포넌트 1개) · 기존 파일 Write 금지 — [routing.md §1.5](agents/core/routing.md#15-atomic-edit-granularity-원자-편집-단위). 도구 키: [runtime_edit_tools.md §1](agents/core/runtime_edit_tools.md).

### 2.2 Plan / Blueprint

- **Plan First**: 복합 작업은 `just plan-lint` PASS 전 구현 착수 금지 — [PROJECT_RULES.md §3](PROJECT_RULES.md) · [planning.md](agents/core/planning.md).
- **Task closeout**: Blueprint Task `Status`/`Conclusion`은 **`just plan-task-close` CLI만** — 에디터 직접 수정 **절대 금지** — [plan.md §1.10](agents/workflows/plan.md) · [error_patterns/detail/blueprint.md §5.6](agents/core/error_patterns/detail/blueprint.md#56-task-statusconclusion-에디터-직접-수정).
- **DoD 재귀 금지**: DoD 섹션에 `just plan-close`를 verify 명령어로 포함하지 않음 — `plan_close_gate.py`가 이를 추출해 자기 자신을 호출하는 재귀 타임아웃을 유발함 — [error_patterns/detail/blueprint.md §5.7](agents/core/error_patterns/detail/blueprint.md#57-dod에-just-plan-close-폰리만-폰리마이스통).
- **Archive**: `docs/plans/` 파일 이동 시 **반드시** [`agents/workflows/archive.md`](agents/workflows/archive.md) 먼저 Read → `scripts/archive_plans.py` 실행 — 수동 복사/삭제 **절대 금지** — [archive.md §실행 절차](agents/workflows/archive.md).
- 상세: [planning.md](agents/core/planning.md) · [workflows/plan.md](agents/workflows/plan.md) · [archive.md](agents/workflows/archive.md).

---

## 3. Dynamic Rules & Loading

**세션 always-on (5파일)** — IDE·부트스트랩 포인터(`CLAUDE.md` 등)와 무관; 규칙 본문 SSOT:

1. `PROJECT_RULES.md`
2. `AGENTS.md`
3. `agents/core/principles.md`
4. `agents/core/error_patterns.md`
5. `agents/core/orchestration.md`

**lazy** (편집·route·plan 직전): [LOAD_ORDER.md](agents/registry/LOAD_ORDER.md) Phase 2+ · [CONTEXT_ROUTING.md](agents/registry/CONTEXT_ROUTING.md) · (선택) `ROADMAP.md`.

**실행 subagent** 편집 직전: `just route <paths> --json --write-manifest` → `must_read` Read → `just route-read` → `just route-gate-check`.

---

## 4. Verification

검증 수준·게이트: [verification.md](agents/core/verification.md) — 저장소 수정 있었을 때 세션 종료 검증은 `shell` Task로 `just lint-turn-end` 위임 권장 ([orchestration_detail.md §5](agents/core/orchestration_detail.md#5-메인-에이전트-역할-경계)). 시점별 품질 체크: [code_quality_lifecycle.md](agents/core/code_quality_lifecycle.md).

### 4.1 Partial Edit Tool — 한글 콘텐츠 제한 (Cursor)

**실행 subagent** — 규범 SSOT: [runtime_edit_tools.md](agents/core/runtime_edit_tools.md) §1 · §4. 요약: 부분 수정 도구는 ASCII-only JSON에 최적화(한글 본문 직삽입 시 파싱 실패 가능) · 영문/코드 → 런타임 부분 수정 도구 · 한글·특수문자 대량 → 터미널 우회(§4) · `sed -i ''`(macOS)+한글 금지.

### 4.2 Test — 메시지 전역 고유성

테스트 assertion 문자열은 페이지·출력 내 **단일 요소**만 매칭되도록 고유 식별자를 포함한다. 중복 라벨과 message가 겹치지 않게 하고, 필요 시 `data-testid`를 사용한다.

### 4.3 Plan — closeout 실행 순서 (커널)

`just plan-close`는 프로젝트 DoD에 명시된 검증 레시피를 순서대로 실행한다. **기본 커널**은 Linear 연동 없이 `plan-lint-ci` + `plan-close`만으로 충분하다.

```bash
just plan-lint-ci plan=docs/plans/<file>.md   # 1. Blueprint lint (Linear 생략)
just plan-close plan=docs/plans/<file>.md     # 2. plan close gate
```

프로젝트가 Linear를 쓰면 `Justfile`에 `linear-sync` 레시피를 추가하고 closeout 순서를 확장한다.

### 4.4 Plan — Conclusion 플레이스홀더 금지

`just plan-lint`는 각 Task의 `Conclusion` 필드를 검증한다. Conclusion은 최소 **25자 이상**, 실제 검증 결과(파일명·테스트 수·명령어 결과)를 포함한다. `[완료 시 기입]` 등 플레이스홀더는 금지.

### 4.5 Justfile — DoD 레시피 실존 검증

PLAN DoD의 `just <recipe>`는 실제 justfile에 존재해야 한다. PLAN 작성 시 `just --list`로 레시피 실존을 확인한다.

---

## 5. Reference Index

**Handoff Tier (S/M/L)**: normative SSOT는 프로젝트 루트 [AGENTS.md §5 Handoff Tier](../../AGENTS.md#handoff-tier-sml) 표 · S-tier 최소 블록 · L-tier 전문. bootstrap 커널은 전문 복사 없이 링크만 따른다. Tier별 체크리스트: [orchestration_detail.md §4](agents/core/orchestration_detail.md#4-handoff-계약-task-prompt-필수--agentsmd-5-ssot).

- **Policy / Core**: `PROJECT_RULES.md`, `agents/core/`
- **Registry**: `agents/registry/RULE_INDEX.md`
- **Specs**: `docs/specs/` (프로젝트가 추가한 경우)

에이전트 규칙 SSOT: `PROJECT_RULES.md`, `agents/`, `AGENTS.md`. `CLAUDE.md` · `copilot-instructions.md`는 **부트스트랩 포인터만**(규칙 본문 아님).

중복 방지: `.cursor/rules/` 미사용. **`.cursor/commands/*.md`는 workflow pointer만** (본문 SSOT: `agents/workflows/`). 슬래시·키워드: [WORKFLOW_AND_SKILL_INDEX.md](agents/registry/WORKFLOW_AND_SKILL_INDEX.md).
