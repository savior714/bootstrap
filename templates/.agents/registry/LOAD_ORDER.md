---
scope: registry
domain: core
---
<!-- Language: ko -->

# Load Order & Precedence (Bootstrap Kernel)

세션 **시작·로딩·종료** 절차 SSOT. 실행 게이트·우선순위는 `AGENTS.md` · `.agents/core/*.md`.

---

## Phase 로딩 순서

| Phase | 시점 | 내용 |
| :--- | :--- | :--- |
| **1** | 세션 시작 | `PROJECT_RULES.md`, `AGENTS.md` |
| **2** | **lazy** — 편집·`just route` 직전 | 본 문서, [CONTEXT_ROUTING.md](CONTEXT_ROUTING.md) |
| **3** | 세션 시작 | `docs/agent-context/memory/MEMORY.md` 인덱스(≤200줄). `ROADMAP.md`는 plan·roadmap·discuss 시 lazy |
| **4** | `--full` / 편집 직전 | CONTEXT_ROUTING 「Always Load T2」`core/*.md` |
| **5** | 편집 대상 확정 | `just route <paths> --json` → domain · skills |
| **6** | 슬래시·워크플로 | `.agents/workflows/<name>.md` ([WORKFLOW_AND_SKILL_INDEX.md](WORKFLOW_AND_SKILL_INDEX.md)) |
| **7** | 종료·명시 트리거 | [reporting.md](../core/reporting.md) §1.0 · [memory_hygiene.md](../core/memory_hygiene.md) |

**세션 시작 SSOT**: `PROJECT_RULES.md` + `MEMORY.md` 인덱스.

**첫 응답**: 위 세션 시작 SSOT. 코드·문서 편집 착수 전 Phase 2 Read.

**멀티 에이전트**: `ROUTE_MANIFEST_PATH` · `ROUTE_SESSION_KEY`. **필수 파일 부재**: 사용자 보고 — 거버넌스 placeholder 생성 금지.

### 편집 직전 (Phase 5)

**`just route <paths> --json --write-manifest` → `must_read` 전량 Read → `just route-read` → `just route-gate-check`** — [execution.md](../core/execution.md) §2.8.

### 종료 (저장소 수정 후)

[reporting.md](../core/reporting.md) §1.0: `just lint-turn-end` → [memory_hygiene.md](../core/memory_hygiene.md).

### 규칙 정합성

레지스트리 상충·깨진 참조 → `docs/agent-context/memory/changelog/` 또는 Blueprint.

**충돌 해결**: [AGENTS.md §0](../../AGENTS.md). Phase는 로딩 순서이며 우선순위를 재정의하지 않음.

---

**Last Updated**: 2026-06-12 · Bootstrap kernel subset
