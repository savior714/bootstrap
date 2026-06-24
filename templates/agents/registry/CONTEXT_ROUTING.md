---
scope: registry
domain: core
---
<!-- Language: ko -->

# Context Routing Strategy (Bootstrap Kernel)

작업 경로에 따른 규칙 로딩 테이블. **커널에 포함된 도메인·스킬만** 참조합니다.

## 컨텍스트 Tier

| Tier | 시점 | 내용 |
| :--- | :--- | :--- |
| **T0** | always-applied (5파일) | `PROJECT_RULES.md` + `AGENTS.md` + core stub 3 — [AGENTS.md §3](../../AGENTS.md#3-dynamic-rules--loading) |
| **T1** | *(통합 → T0)* | — |
| **T1†** | lazy | `LOAD_ORDER`, 본 문서, (선택) `docs/plans/ROADMAP.md` |
| **T2** | `just route` / 편집 직전 | Always Load + domain rules |
| **T3** | lazy | `error_patterns/detail/*.md` 등 on-demand |

**금지**: `patterns.yaml` always_apply · 존재하지 않는 도메인 파일을 Path 표에 넣지 않음.

---

## 상시 적용 (Always Load — Tier T2, `just route --full`)

- `core/execution.md`, `core/verification.md`, `core/planning.md`, `core/reporting.md`
- `core/runtime_edit_tools.md`, `core/code_quality_lifecycle.md`
- `core/resilience.md`
- `core/error_patterns.md` 헤더

---

## 경로별 동적 매핑 (커널 포함분)

| 파일 경로 패턴 (Glob) | 적용 규칙 | 용도 |
| :--- | :--- | :--- |
| `tests/e2e/**/*`, `**/*.spec.ts` | [testing/playwright.md](../domains/testing/playwright.md) | Playwright E2E |

**프로젝트별 확장**: `{{FRONTEND_APP_PATH}}/**/*.{ts,tsx}` 등은 프로젝트가 `agents/domains/` 규칙을 추가한 뒤 본 표에 행을 넣으세요. EMR 예시(full glob·`PROJECT_SKILL_ROUTING.json`)는 EMR `agents/registry/CONTEXT_ROUTING.md`를 참고합니다.

---

## 키워드 · 슬래시

**카탈로그 SSOT**: [WORKFLOW_AND_SKILL_INDEX.md](WORKFLOW_AND_SKILL_INDEX.md).

`PROJECT_SKILL_ROUTING.json` · `SKILL_CATALOG.json`은 bootstrap 커널에 **미포함** — 수동 Read 라우팅(색인 표)을 우선 사용합니다.

---

**우선순위**: [AGENTS.md §0](../../AGENTS.md) — `PROJECT_RULES` > `AGENTS` > 경로 매핑 > core.

**세션 lazy**: [LOAD_ORDER.md](LOAD_ORDER.md) Phase 2 — 본 문서 Glob·Tier는 **편집·route 직전** Read.

**Last Updated**: 2026-06-12 · Bootstrap kernel subset
