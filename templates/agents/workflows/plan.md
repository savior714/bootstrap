---
situation: 신규 기능 설계
# trigger: /plan  ← catalog metadata only; Read this file before executing (error_patterns/detail/workflow.md#161)
level: Mandatory
description: Blueprint 작성·실행·Task 종료 — 프로토콜 SSOT는 plan/SKILL.md
version: 1.5.0
last_updated: 2026-06-13
scope: workflow
domain: workflow
---
<!-- Language: ko -->

# `/plan` Workflow

**프로토콜 SSOT**: [agents/skills/plan/SKILL.md](../skills/plan/SKILL.md) — 실행 전 Read.

Blueprint(`docs/plans/PLAN_*.md`) **작성·plan-lint·Task 실행·plan-close**. 계약 normative SSOT: [planning.md](../core/planning.md) §2.

---

## {{PROJECT_NAME}} 부록 (SKILL 미러)

When / When NOT · Phase W/E · Edge AskQuestion · Execution Freeze 전문은 **SKILL**을 본다. 아래는 **어긋나기 쉬운 규칙만** 미러.

### Anti-pattern at write (요약)

- **증상**: 채팅-only 계획, lint 전 구현, 에디터로 Status/Conclusion 수정, 실행 중 Blueprint 패치.
- **원인**: Artifact-first·plan-task-close·Execution Freeze 미준수.
- ❌ WRONG: plan-lint 없이 Task 1.1 코드 수정 · Conclusion placeholder로 `done` · 실행 중 AskQuestion으로 범위 재협상.
- ✅ CORRECT: `plan-preread --write` → `plan-lint` PASS → Execute 시 동결 → Verify → `plan-task-close` → `plan-lint`.
- 공통 포맷: [`docs/agent-context/ANTI_PATTERN_FORMAT.md`](../../docs/agent-context/ANTI_PATTERN_FORMAT.md)

### Lint-first at write (첫 plan-lint FAIL 6종)

템플릿·스킬 SSOT: [TEMPLATE_blueprint.md](../../docs/templates/TEMPLATE_blueprint.md) 「Lint-first 작성 체크리스트」· [plan/SKILL.md §Phase W3](../skills/plan/SKILL.md).

| # | ❌ 흔한 초안 | ✅ 작성 시 |
| :---: | :--- | :--- |
| 1 | 업무 요약에 `` `just plan-lint` `` | 평문: 「구조 검사 통과」 |
| 2 | Agent scope에 Verify만 | **Conclusion**·**plan-lint** 명시 |
| 3 | `Task-ID: [XXX-001]` | `[USRT-001]` 등 slug 기반 실값 |
| 4 | `Labels: plan` / unknown | `Improvement` 또는 `tooling` |
| 5 | `Target: {{FRONTEND_APP_PATH}}/src/.../` | `Target: apps/.../File.tsx` |
| 6 | Pre-read 수동 2줄만 | `just plan-preread … --write` 후 마커 |

### 철칙 (우선)

1. **Artifact-first** — `docs/plans/PLAN_*.md` 없이 설계 완료 인정 **금지**.
2. **plan-lint PASS 전 구현 금지**.
3. **plan-task-close만** — Task Status/Conclusion 에디터 직접 수정 **금지**.
4. **Execution Freeze** — lint PASS + 전체 실행 요청 후 Blueprint 구조 변경 **금지** — [SKILL §Execute](../skills/plan/SKILL.md) · [references/execution-gates.md](../skills/plan/references/execution-gates.md).
5. **Edge before happy path** — Origin Intent + Edge Case Trace + (필요 시) AskQuestion **1턴**.
6. **Atomic Task** — 1 Task = 1 File · Impact Scope 연동 · **실행 순서·선행** 표 — [task-decomposition.md](../skills/plan/references/task-decomposition.md).
7. **Pre-read every Task** — Execute 시 Task Pre-read 전부 Read · 무관 스킬 Pre-read 금지.
8. **Closeout 순서** — Review Task(-098) 완료 후 `docs-ssot-headers` → `linear-sync` → `plan-close` ([planning.md](../core/planning.md) §2.4).
9. **Orchestration O3** — PLAN **Execute** 시 메인=지휘만 · Task 구현·Verify·`plan-task-close`는 **subagent(Task)** 위임 — [orchestration_detail.md §2](../core/orchestration_detail.md#2-turn-0-triage--이관-트리거) · [orchestration_detail.md §6](../core/orchestration_detail.md#6-순차-실행-루프-o1--o2) · [plan/SKILL.md §Execute O3](../skills/plan/SKILL.md).
10. **Execute → Review Task -098** — 코드 구현 Task가 있으면 closeout **전** Implementation review Task **MUST** — [handoff-from-execute-to-review.md](../skills/plan/references/handoff-from-execute-to-review.md).

| 단계 | 명령 |
| :--- | :--- |
| 신규 Blueprint | [`TEMPLATE_blueprint.md`](../../docs/templates/TEMPLATE_blueprint.md) → `docs/plans/PLAN_<slug>.md` |
| Linear (제품) | `python3 scripts/linear_sync/ensure_plan_linear.py docs/plans/PLAN_<slug>.md` |
| Pre-read | `just plan-preread docs/plans/<file>.md --write` |
| 구조 검증 | `just plan-lint docs/plans/<file>.md` |
| 품질 게이트 (#8–#10) | `just plan-lint-quality docs/plans/<file>.md` (또는 `plan-lint … --check-quality`) |
| hand-off → Blueprint 골격 | `just plan-scaffold-handoff slug=<slug> handoff=<path.md> --write [--prefix ORDS]` |
| Task 종료 | `just plan-task-close plan=... task=<ID> conclusion="..."` |
| 구현 리뷰 | `just plan-review-gate plan=docs/plans/<file>.md` (Review Task -098 Verify) |
| 플랜 마감 | `just plan-close plan=docs/plans/<file>.md` (Closeout Task -099 Verify) |
| 역방향 리셋 (예외) | `just plan-reset-gate plan=... task=... sha=<git-sha> approval="..."` → `--apply` |
| 세션 종료 | `just lint-turn-end` |

### lazy (필요 시 Read)

| 주제 | SSOT |
| :--- | :--- |
| 핸드오프(스킬→Blueprint) | [plan/references/handoff-contract.md](../skills/plan/references/handoff-contract.md) |
| Atomic Task·Pre-read | [plan/references/task-decomposition.md](../skills/plan/references/task-decomposition.md) |
| 실행 동결·closeout 4단계 | [plan/references/execution-gates.md](../skills/plan/references/execution-gates.md) |
| Execute → review (Task -098 + 세션 점검) | [plan/references/handoff-from-execute-to-review.md](../skills/plan/references/handoff-from-execute-to-review.md) |
| Subagent O3 (Execute 위임) | [orchestration.md](../core/orchestration.md) |
| Edge AskQuestion 뱅크 | [discuss/references/plain-language-questions.md](../skills/discuss/references/plain-language-questions.md) |
| DISCUSS same-session | [discuss/SKILL.md](../skills/discuss/SKILL.md) |
| Review gate 스크립트 | [`plan_review_gate.py`](../../scripts/verify/plan_review_gate.py) |
| Close gate 스크립트 | [`plan_close_gate.py`](../../scripts/verify/plan_close_gate.py) |
| Archive | [archive.md](archive.md) |
