---
scope: registry
domain: core
---
<!-- Language: ko -->

# Load Order & Precedence (Bootstrap Kernel)

세션 **시작·로딩·종료** 절차 SSOT. 실행 게이트·우선순위는 `AGENTS.md` · `agents/core/*.md`.

---

## Phase 로딩 순서

| Phase | 시점 | 내용 |
| :--- | :--- | :--- |
| **1** | 세션 always-on | `PROJECT_RULES.md` + `AGENTS.md` + core stub 3 — **5파일** ([AGENTS.md §3](../../AGENTS.md#3-dynamic-rules--loading)) |
| **2** | **lazy** — 편집·`just route` 직전 | 본 문서, [CONTEXT_ROUTING.md](CONTEXT_ROUTING.md) |
| **3** | **lazy** — plan·roadmap·discuss | `ROADMAP.md` · `just plan-preread` |
| **4** | `--full` / 편집 직전 | CONTEXT_ROUTING 「Always Load T2」`core/*.md` |
| **5** | 편집 대상 확정 | `just route <paths> --json` → domain · skills |
| **6** | 슬래시·워크플로 | `agents/workflows/<name>.md` ([WORKFLOW_AND_SKILL_INDEX.md](WORKFLOW_AND_SKILL_INDEX.md)) |
| **7** | 종료·명시 트리거 | [reporting.md](../core/reporting.md) §1.0 |

**always-on 5파일**: `PROJECT_RULES.md` → `AGENTS.md` → `core/principles` · `error_patterns` · `orchestration` stub. Phase 2·`ROADMAP.md`는 lazy.

**첫 응답**: 위 세션 시작 SSOT. 코드·문서 편집 착수 전 Phase 2 Read.

**멀티 에이전트**: `ROUTE_MANIFEST_PATH` · `ROUTE_SESSION_KEY`. **필수 파일 부재**: 사용자 보고 — 거버넌스 placeholder 생성 금지.

**부모→서브 handoff**: Task `prompt`에 `ROUTE_MANIFEST_PATH`·`ROUTE_SESSION_KEY`를 명시해 동일 route manifest를 이어 받는다 — [orchestration.md §4](../core/orchestration.md#4-handoff-계약-task-prompt-필수) · [CONTEXT_ROUTING.md](CONTEXT_ROUTING.md) 「Route 매니페스트」.

**O2 Strengthened 세션**: 메인은 Phase 5 route gate를 **직접** 돌리지 않고 실행 subagent에 위임한다(메인은 triage·Task spawn·합성만). **연속 작업 2+ → subagent 필수** — 탐색→편집·편집→검증 등 서로 다른 종류의 작업 단계가 2개 이상 연속이면 메인 연속 직접 수행 금지 ([orchestration.md §2](../core/orchestration.md#연속-작업-2-정의)).

### 편집 직전 (Phase 5)

**`just route <paths> --json --write-manifest` → `must_read` 전량 Read → `just route-read` → `just route-gate-check`** — [execution.md](../core/execution.md) §2.8.

### 종료 (저장소 수정 후)

[reporting.md](../core/reporting.md) §1.0: `just lint-turn-end`.

### 규칙 정합성

레지스트리 상충·깨진 참조 → `docs/agent-context/memory/changelog/` 또는 Blueprint.

**충돌 해결**: [AGENTS.md §0](../../AGENTS.md). Phase는 로딩 순서이며 우선순위를 재정의하지 않음.

---

**Last Updated**: 2026-06-12 · Bootstrap kernel subset
