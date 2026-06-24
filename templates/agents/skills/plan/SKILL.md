---
name: plan
description: >
  Blueprint(PLAN_*.md) 작성·plan-lint·Task 실행·plan-task-close·plan-close까지 에이전트가 CLI를 직접
  돌리며 SSOT를 유지한다. Origin Intent·Edge Case Trace·AskQuestion(작성 전 1턴)으로 엣지를 Task에
  매핑하고, plan-lint PASS 후 실행 시 Blueprint 구조 동결(Execution Freeze)을 지킨다. Use for /plan,
  blueprint, PLAN_*.md, plan-lint, plan-task-close, «이 플랜 다 실행», Task 분해·설계. 방향만 합의는
  discuss, 아키텍처 assessment는 assess, 무코드 리팩 설계는 refactor, discover emit 후 구현 실행은
  plan Execute. 채팅-only 장문 계획 금지.
license: MIT
metadata:
  version: "1.0.4"
disable-model-invocation: true
---

<!-- Language: ko -->

# Plan

**Blueprint**(`docs/plans/PLAN_*.md`) **작성·검증·Task 실행·종료** — 에이전트가 **CLI를 직접** 돌린다.

**하지 않는 것**: 무코드 방향 토론(discuss), feature 정밀 assessment(/assess), 버그 수정 루프(diagnose), 채팅-only 장문 계획.

> **이웃**: 방향·범위 → [discuss](../discuss/SKILL.md) · assessment → [assessment-driven-planning](../assessment-driven-planning/SKILL.md) · 리팩 **설계** → [refactor](../refactor/SKILL.md) · discover emit → **plan Execute** · Task 중 코드 drift → [sync](../sync/SKILL.md)

워크플로 부록(anti-pattern 미러): [plan.md](../../workflows/plan.md)

---

# Response Language (MUST)

채팅·Blueprint **협업용 절**은 **한국어**. Task `Target`·`Verify`·경로·CLI는 영문 가능. **영문-only 단락 금지.**

정책: [markdown.md](../../domains/documentation/markdown.md) Korean First Policy

---

# Skill Boundary (MUST)

| 사용자 요청 | 이 스킬 | 대안 |
| :--- | :--- | :--- |
| `PLAN_*.md` 작성·Task 분해·plan-lint | ✅ plan **작성** | — |
| `@PLAN_*.md` 전체·Task 연속 **실행** | ✅ plan **Execute** | — |
| Task Verify 후 closeout | ✅ plan Execute (4단계) | — |
| «어디를 개선할까»·막연한 방향 | — | [discuss](../discuss/SKILL.md) |
| Shallow→Deep·assessment 스펙 | — | `/assess` |
| 리팩 **무코드** 3단 설계 | — | [refactor](../refactor/SKILL.md) |
| discover가 emit한 Implement Blueprint **실행** | ✅ plan Execute | discover는 emit만 |
| 버그 재현·고정 | — | [diagnose](../diagnose/SKILL.md) |
| 세션 마무리·다음 에이전트 이관 | — | `/go` |

**오분기 시**: 작성 vs Execute 중 하나를 **끝까지**. boundary 한 줄만 쓰고 종료 **금지**.

### 모드 판별 (매 턴 MUST)

```text
PLAN 파일·Task 실행·plan-lint/plan-task-close/plan-close?
  ├─ 신규 Blueprint·Task 추가·Edge Trace·plan-lint PASS 목표 → 작성 모드
  ├─ 기존 PLAN + «실행»·«Task N»·연속 진행 → Execute 모드 (동결)
  └─ discuss만·코드 패치만·assessment만 → handoff
```

### plan ↔ 이웃 스킬 (양방향)

| 출발 | 조건 | 다음 |
| :--- | :--- | :--- |
| discuss | same-session plan·DISCUSS §3 [확정] | plan **작성** — [discuss/close-handoff.md](../discuss/references/close-handoff.md) |
| refactor | 3단계(진단·심화·RGR) 합의·Close «Blueprint» | plan **작성** — [refactor/handoff-to-plan.md](../refactor/references/handoff-to-plan.md) |
| review | close «Blueprint»·High/Medium 후속 | plan **작성** — [review/handoff-to-plan.md](../review/references/handoff-to-plan.md) |
| assess | Decision-Lock §4.1~4.4 확정 | plan **작성** — [assessment-driven-planning/handoff-to-plan.md](../assessment-driven-planning/references/handoff-to-plan.md) |
| discover | `discover-emit` exit 0 | plan **Execute** 안내 — [discover/handoff-to-plan.md](../discover/references/handoff-to-plan.md) |
| deep-research | GAP·구현 합의 | plan **작성** — [deep-research/handoff-to-plan.md](../deep-research/references/handoff-to-plan.md) |
| playwright | 탐색·Blueprint·lint PASS | 메뉴 B — [handoff-contract.md](references/handoff-contract.md) |
| audit | (선택) 개선 Blueprint | plan **작성** — [handoff-contract.md](references/handoff-contract.md) |
| plan Execute | Closeout 완료 · 구현 Task ≥1 `done` | **review** — [handoff-from-execute-to-review.md](references/handoff-from-execute-to-review.md) |
| plan 작성 | 범위·아키텍처 **미확정** | discuss — Blueprint **저장 전** |
| plan Execute | 설계 갭·범위 재협상 필요 | `blocked` + **새 PLAN** — 실행 중 AskQuestion **금지** |

**공통 계약**: [handoff-contract.md](references/handoff-contract.md)

---

# Iron Law

1. **Artifact-first** — `/plan` 요청 시 **반드시** `docs/plans/PLAN_*.md`. 채팅-only 장문 계획 **금지** ([planning.md](../../core/planning.md) §0).
2. **plan-lint PASS 전 구현 금지** — 구조 검증 exit 0 없이 코드·Task 실행 착수 **금지**.
3. **plan-task-close만** — Task `Status`/`Conclusion` **에디터 직접 수정 금지**.
4. **Execution Freeze** — lint PASS + 전체 실행 요청 후 Blueprint 구조 변경·실행 중 AskQuestion 분기 **금지** ([references/execution-gates.md](references/execution-gates.md)).
5. **Edge before happy path** — Origin Intent + Edge Case Trace + (필요 시) AskQuestion **1턴** 후 Task화. Trace `해당 없음`만으로 happy path만 쓰기 **금지**.
6. **Verify → close → lint** — Task 「완료」 채팅은 **plan-lint PASS 후**만.
7. **Atomic decomposition** — local LLM은 Task를 **잘게** 쪼갠 Blueprint만 실행한다. 1 Task = 1 File · White-box Goal · runner Verify — [task-decomposition.md](references/task-decomposition.md). **plan-lint PASS ≠ 템플릿 품질 OK**.
8. **Pre-read every Task** — Execute·Write 모두 Task `Pre-read` **전부 Read** 후 편집. 무관 스킬 Pre-read **금지**.
9. **분해 논리 필수** — Task 목록만 나열 **금지**. `## 실행 순서·선행` + Phase intro + Task `Diagnostics`(분해 이유). Target은 **Impact Scope**에서만 — eval meta·workspace fixture **금지**(Origin Intent 예외 제외).

---

# Agent-executable (MUST)

「로컬에서 돌려보세요」로 넘기지 않는다. 아래를 **직접** 실행하고 stdout·exit code를 Conclusion에 반영한다.

| 유형 | 명령 |
| :--- | :--- |
| Pre-read | `just plan-preread docs/plans/<file>.md --write` |
| 구조 검증 | `just plan-lint docs/plans/<file>.md` |
| Task 종료 | `just plan-task-close plan=... task=<ID> conclusion="..."` |
| Linear (제품) | `python3 scripts/linear_sync/ensure_plan_linear.py <path>` |
| Closeout | `just docs-ssot-headers` → `just linear-sync` → `just plan-close plan=...` |
| Task Verify | Blueprint에 적힌 **셸 명령 1개** (에이전트가 실행) |

### 보고 필수: **실행한 검증**

작성·Execute 턴 마무리 시 최소 1행:

| 명령 | 결과 |
| :--- | :--- |
| `just plan-lint …` | exit 0 / FAIL 요약 |
| `just plan-task-close …` | task ID + conclusion 반영 |
| Task Verify | exit 0 / blocked 사유 |

**금지**: plan-lint 미실행·plan-task-close 없이 `Status: done` 선언 · Conclusion 플레이스홀더로 done

상세 계약: [references/blueprint-contract.md](references/blueprint-contract.md)  
핸드오프(스킬→Blueprint): [references/handoff-contract.md](references/handoff-contract.md)  
실행·동결·closeout: [references/execution-gates.md](references/execution-gates.md)

---

# 작성 모드 (Write)

**트리거**: 신규 `/plan`, Blueprint 초안, Task 추가, `plan-lint` PASS 목표.

## Phase W0 — Intent & handoff

1. 출처 분류: discuss handoff / refactor handoff / **review handoff** / **assess handoff** / **discover-emit** / **deep-research handoff** / **playwright** / **audit** / research / 직접 요청.
2. **[TEMPLATE_blueprint.md](../../../docs/templates/TEMPLATE_blueprint.md) Read** — 「복사용 뼈대」**절 순서**가 Blueprint 골격 SSOT.
3. [task-decomposition.md](references/task-decomposition.md) Read — Atomic·Pre-read 규칙.
4. `just route` — 편집 대상 경로·must_read.

## Phase W0.5 — Template skeleton (MUST)

lint 게이트 **전** 아래를 **뼈대 순서대로** 채운다. 섹션 생략·순서 뒤바꿈 **금지**.

`문서 메타` → `📎 관련 명세` → `📋 업무 요약` → `🎯 Origin Intent` → `⚠️ Edge Case Trace` → `🧭 Context Pre-read Gate` → **`실행 순서·선행`(Task 분해 표)`** → `Diagnosis` → … → `Impact Scope`(Task 전에 파일 목록) → `Agent Completion Contract` → `Execution Plan` → …

**품질 게이트**: plan-lint PASS만으로 작성 완료 **선언 금지** — Phase W3 Atomic 체크리스트 통과 후 W4.

## Phase W1 — Origin Intent & Edge Case Trace

Blueprint 본문에 **저장·plan-lint 전** 필수:

| 순서 | 액션 |
| :---: | :--- |
| 1 | `## 🎯 Origin Intent` 1~3줄 |
| 2 | `## ⚠️ Edge Case Trace` 표 — 행마다 Task-ID 또는 `범위 밖` |
| 3 | 갭 감사 — 미매핑 행 없을 때까지 Task 보완 또는 「이번에 안 하는 것」 |
| 4 | (권장) Phase 0 gap audit Task 1개 |

## Phase W2 — Edge Case Design Gate (AskQuestion)

**Decision Gate 시점** — Task **실행 중** AskQuestion **금지**.

| 조건 | 행동 |
| :--- | :--- |
| DISCUSS §3 엣지 **[확정] 1건+** | Trace에 반영 — AskQuestion **생략 가능** |
| discuss handoff인데 §3 엣지 없음 | **AskQuestion 1턴** — [plain-language-questions.md](../discuss/references/plain-language-questions.md) §엣지 |
| **refactor handoff** — RGR·Risk에서 엣지 1건+ 합의됨 | Trace에 반영 — AskQuestion **생략 가능** |
| **refactor handoff** — 엣지 미기록 | **AskQuestion 1턴** — 동일 §엣지 |
| **review handoff** — Findings에 엣지·회귀 시나리오 있음 | Trace에 반영 |
| **review handoff** — 엣지 없음 | **AskQuestion 1턴** |
| **assess handoff** — §4.4 부작용·완화 | Trace·Risk에 반영 — 생략 가능 |
| **assess handoff** — §4.4 빈약 | **AskQuestion 1턴** |
| **deep-research handoff** — `pending_review`·법적 격리 항목 | Trace **범위 밖** 또는 전용 Task |
| **playwright** / **audit** | 탐색·리포트 Findings → Trace — 없으면 **AskQuestion 1턴** |
| **discover-emit** | 큐 `verify_hint`·split 명세 → Trace — AskQuestion **생략** |
| 직접 `/plan` | 동일 **AskQuestion 1턴** |

**AskQuestion 규칙** (1턴 = 질문 1개, 3~4옵션, `(권장)` 1개):

- staff가 겪을 **예외 2~3개**를 구체 문장으로 제시.
- 옵션 예: 「{상황A} 포함」 / 「{상황B} 포함」 / 「둘 다」 / 「happy path만 — 예외 범위 밖」.
- 답 → Trace 행 + Task 보완 또는 「이번에 안 하는 것」.

## Phase W3 — Task 분해 & 협업 요약

1. **`## 🔍 Impact Scope` 먼저** — 수정 파일·역할 표 (Task Target 후보 SSOT).
2. **[task-decomposition.md](references/task-decomposition.md) Iron rules**로 Task 후보 분해.
3. **`## 실행 순서·선행` 표** — Task-ID · **왜** · 선행 · 한 줄 산출 · 병렬 여부 ([task-decomposition.md](references/task-decomposition.md) §실행 순서·선행).
4. **Execution Plan** — Phase마다 **분해 논리 2~3문장** intro → Task 블록.
5. 각 Task `- **Diagnostics**:` — 분해 논리 1줄 (**`0` 금지**).

- `## 📋 업무 요약 (협업용)` — [TEMPLATE_blueprint_collaboration_summary.md](../../../docs/templates/TEMPLATE_blueprint_collaboration_summary.md)
- 1 Task = 1 File · White-box Goal · runner Verify · Phase 내 연속 번호
- Pre-read: `editing.md` + `just route <Target>` must_read

**Task Goal 작성 SSOT**: [task-decomposition.md](references/task-decomposition.md) §Task Goal 작성 SSOT — 작성 전 BAD/GOOD 3종(추상 Goal·엔티티 없음·TDD Red 누락)을 반드시 확인한다.

**자가 점검 (MUST)** — 하나라도 NO면 재분해:

| 질문 | YES |
| :--- | :--- |
| Goal에 동사가 1개뿐인가? | |
| Target이 단일 파일·**Impact Scope에 있음**? | |
| Verify가 pytest/just/python3/pnpm인가? | |
| Pre-read가 Target·도메인과 연관되는가? | |
| BKF-001 수준 white-box Goal? | |
| **`실행 순서·선행` 표 있음**? | |
| **Diagnostics에 분해 이유** (≠0)? | |
| **eval/workspace meta Target 없음**? | |
| **code Target 있으면 Task -098 + review/SKILL Pre-read**? | |

**Implementation Review Task (code Blueprint MUST)**: 마지막 구현 Task 다음 **Task-ID `[SLUG-098]`** — Pre-read **1번** `[project_skill]` `agents/skills/review/SKILL.md` · Goal에 **review/SKILL** · Verify `just plan-review-gate` · closeout(-099) **Dependency = -098**. SSOT: [TEMPLATE_blueprint.md](../../../docs/templates/TEMPLATE_blueprint.md) §Implementation Review Task.

### 잡무 완료 체크리스트

Phase W4 `plan-lint` **직전** — Execute 진입 전 작성자가 아래 **11문항**을 **모두** 통과해야 한다.

**품질 (기존 5)**

- **Goal white-box**: 각 Task Goal이 파일·함수·동작 수준 white-box 명세인가?
- **Pre-read 완비**: 각 Task `Pre-read`가 Target·도메인과 연관되며 `plan-preread`로 주입되었는가?
- **Verify runner 1개**: 각 Task `Verify`가 `just`/`pytest`/`python3`/`pnpm` runner **명령 1개**인가?
- **선행 Task 닫힘**: `Dependency`가 있는 Task의 선행 Task-ID가 Blueprint에 존재하는가? (실행 전 `done`은 Execute 책임)
- **Edge Trace 매핑**: `## ⚠️ Edge Case Trace` 인범위 행이 Task-ID에 매핑되었거나 「이번에 안 하는 것」에 기록되었는가?

**Lint-first (첫 `plan-lint` FAIL 방지 — 7)**

| # | 확인 |
| :---: | :--- |
| 1 | 업무 요약·Origin Intent·Edge Trace·Diagnosis·Risk — **백틱·경로·CLI 없음** |
| 2 | Execution Plan blockquote에 **`Conclusion`**·**`plan-lint`** 둘 다 있음 |
| 3 | Task-ID가 `[SLUG-NNN]` 실값( `[XXX-001]`·`[TBD]`·한글 `[…]` **금지** ) |
| 4 | 메타·Task `Labels`에 **`plan`/`docs` 없음** — allowlist; active root **`docs` FAIL** |
| 5 | 각 `Target`이 **단일 파일 경로** (디렉터리·`/` 끝 **금지**) |
| 6 | `just plan-preread … --write` 완료 (`docs/plans/` Target fallback 포함) |
| 7 | Task **Goal 한 줄** — markdown 헤딩·줄바꿈 **금지** (closeout 9.9) |
| 8 | code Target ≥1이면 **Task -098** — Pre-read 1번 `agents/skills/review/SKILL.md` · Verify `just plan-review-gate` · closeout(-099) Dependency = -098 |

SSOT: [TEMPLATE_blueprint.md](../../../docs/templates/TEMPLATE_blueprint.md) 「Lint-first 작성 체크리스트」

## Phase W4 — CLI & lint

```text
Target·Task-ID·Labels 확정 → ensure_plan_linear (제품) → plan-preread --write → plan-lint → exit 0
```

FAIL 시 수정 후 재실행. PASS 전 구현·Execute **금지**.

## Phase W5 — Write 마무리

실행한 검증 표 + Next Steps (AskQuestion **금지** — 채팅 텍스트):

```markdown
## 다음 단계

- **A. (권장) Blueprint 그대로 두기** — lint PASS 확인만. 실행은 다음 턴 `@PLAN_…` + «실행».
- **B. Task 1.1부터 Execute** — «Task 1.1 실행해줘» 또는 «이 플랜 다 실행».
- **C. discuss로 범위 재조정** — Trace·범위가 아직 불안할 때.
```

---

# Execute 모드

**트리거**: `@PLAN_*.md` · «이 플랜 다 실행» · «Task X.Y» · discover emit 후 구현.

## Phase E0 — Freeze 확인

1. `just plan-lint` **PASS** 확인 (stdout `[WARN]` 없음).
2. **Execution Freeze** 선언 — 이후 Blueprint 구조 변경 **금지** ([execution-gates.md](references/execution-gates.md)).
3. (Phase 0 Task 있으면) **첫 1 Task만** — 완료 후 동결.

**Execution Pack Read (MUST)**: Execute·경량 subagent는 Blueprint에서 **`## Agent Execution Pack` 절·`Agent Completion Contract`·현재 Task 블록·해당 Task `Pre-read`** 만 Read한다. `Origin Intent`·`Diagnosis`·`Architectural Deepening`·`Conceptual Sketch`·`Risk & Strategy` 등 설계 절은 **읽지 않는다** — [TEMPLATE_blueprint.md](../../../docs/templates/TEMPLATE_blueprint.md) Pack 구성 SSOT.

## Phase E1 — Task 루프 (Dependency 순, 1개씩)

**Orchestration O3** ([orchestration.md](../../core/orchestration.md)): Execute 모드에서 **메인은 지휘만** 한다. 아래 표의 행 1~7은 **`general` 또는 `shell` Task**가 수행하고, 메인은 Task spawn·handoff 합성·다음 Task 진행만 담당한다.

| E1 행 | subagent | 비고 |
| :---: | :--- | :--- |
| 1~4 | `general` | Pre-read·route·편집 — handoff에 Blueprint Task 블록 전문 포함 · 편집은 [routing.md §1.5](../../core/routing.md#15-atomic-edit-granularity-원자-편집-단위) |
| 5~7 | `shell` | Verify · `plan-task-close` · `plan-lint` |

**Execute 보고·실행 시 Blueprint Task 블록을 그대로 인용**한다 — 추상 「동결」 요약만으로 Task 대체 **금지**.

각 Task:

| 순서 | 액션 |
| :---: | :--- |
| 0 | Blueprint에서 **Task-ID·Pre-read·Goal·Target·Verify·Dependency** 인용(Execute Report Template) |
| 1 | Task `Pre-read` **전부 Read** — 읽은 경로를 보고에 표로 기록 |
| 2 | `just route <Target>` → route-gate-check (편집 직전) |
| 3 | Target 경로 **실존** 확인 |
| 4 | Goal 범위 **1 File** 편집 |
| 5 | Task `Verify` **1개** 실행 → exit 0 |
| 6 | `just plan-task-close` |
| 7 | `just plan-lint` PASS |

Verify 실패 반복 → `blocked` + Conclusion — Blueprint 패치 **금지**.

### Execute Report Template (MUST)

다음 Task 보고 시 **최소** 아래 블록:

```markdown
## 다음 Task: {Task-ID} — {제목}

| 필드 | Blueprint 값 |
| :--- | :--- |
| Pre-read | (번호 목록 — 착수 전 Read) |
| Target | `path/to/file` |
| Goal | (Blueprint 그대로) |
| Verify | `...` |
| Dependency | ... |

### Pre-read 실행

| # | 경로 | Read 완료 |
| :---: | :--- | :---: |
| 1 | ... | ✅ |

### 실행한 검증

| 명령 | 결과 |
| :--- | :--- |
| ... | exit 0 |
```

## Phase E2 — Review Task (-098) then Closeout (-099)

선행 **구현** Task 전부 `done` → review/SKILL Findings → `## 🔍 Implementation Review` → `plan-review-gate` → Review Task `plan-task-close` → `plan-lint`.

이어서 Roll-up → `plan-close` → closeout Task `plan-task-close` → `plan-lint`.

**다음 권장**: Phase E3 **세션 review SKILL** — [handoff-from-execute-to-review.md](references/handoff-from-execute-to-review.md).

## Phase E3 — Execute 마무리

| 순서 | 액션 |
| :---: | :--- |
| 1 | Review Task -098 **실행한 검증** 표 (plan-review-gate · plan-lint) |
| 2 | Closeout **실행한 검증** 표 (plan-close · plan-lint) |
| 3 | **세션 구현 점검 (권장)** — [review/SKILL.md](../review/SKILL.md) · [handoff-from-execute-to-review.md](references/handoff-from-execute-to-review.md) |
| 4 | review close 이후 저장소 수정 시 — [reporting.md §1.0](../../core/reporting.md) `just sync-turn-end` |

**금지**: Review Task -098 생략 · Closeout 직후 세션 review 없이 「완료」만 보고 (구현 변경 시).

**(선택)** review close에서 마무리 선택 시 `/go` 한 줄 — review **이후**만.

---

# Anti-patterns

| 증상 | 올바른 행동 |
| :--- | :--- |
| 채팅에만 50줄 계획 | `docs/plans/PLAN_*.md` 작성 |
| lint 전 코드 수정 | plan-lint PASS |
| **업무 요약·설계 절 백틱** | 평문만 — 기술 절로 이동 |
| **Task Goal 줄바꿈** | 한 줄 — `` `## 🔁 …` `` 헤딩 금지 |
| **Agent scope에 Conclusion 누락** | blockquote에 `Conclusion`·`plan-lint` 명시 |
| **Task-ID `[XXX-001]`·`[TBD]`** | PLAN slug에서 `[SLUG-001]` 실값 부여 |
| **`Labels: plan`** | `Improvement` 또는 `tooling`(alias) |
| **`Labels: docs`** | `Improvement` (active root Blueprint FAIL) |
| **Target 디렉터리** | Impact Scope에서 파일 1개 지정 |
| **Pre-read 마커 없음** | `plan-preread --write` — `docs/plans/` Target fallback 자동 주입 |
| Conclusion에 `\| 표` | 텍스트 1줄 |
| 에디터로 Status 수정 | `plan-task-close` |
| 실행 중 Task 추가·AskQuestion | `blocked` + 새 PLAN |
| Trace `해당 없음`만 | Edge AskQuestion 1턴 |
| `just plan-close` without linear-sync | docs-ssot-headers → linear-sync → plan-close |
| discover emit 후 discuss 재논의 | plan Execute |
| lint PASS인데 Task 2~3개뿐 | [task-decomposition.md](references/task-decomposition.md) 재분해 |
| Pre-read에 무관 스kill | route Target must_read |
| Execute 보고에 Pre-read 없음 | Execute Report Template |
| `test -f`/`grep` 단독 Verify | pytest/just runner |
| Task 1.1→2.9 번호 점프 | Phase 내 연속 번호 |
| Task 목록만·분해 논리 없음 | `실행 순서·선행` + Diagnostics |
| Scope 밖 Target (eval prompt 등) | Impact Scope → Task |
| Diagnostics: `0` | 분해 이유 1줄 |

Reference: [ANTI_PATTERN_FORMAT.md](../../../docs/agent-context/ANTI_PATTERN_FORMAT.md) · [error_patterns/detail/blueprint.md](../../core/error_patterns/detail/blueprint.md)

---

# Registry sync (version bump)

`metadata.version` 또는 Iron Law·Skill Boundary 변경 시 아래 **3파일을 함께** 갱신한다 — SKILL만 bump하고 registry를 두면 discovery drift가 난다.

- [SKILL_CATALOG.json](../../registry/SKILL_CATALOG.json) — `project_skills` plan 항목 `summary` (v1.0.2 경계: disable-model-invocation · Agent-executable · 실행 순서·선행 · Diagnostics · Impact Scope · discuss handoff)
- [WORKFLOW_AND_SKILL_INDEX.md](../../registry/WORKFLOW_AND_SKILL_INDEX.md) — **Plan 경계** 문단 (ellipsis 금지 · Iron Law #9 분해 논리 전문)
- [WORKFLOW_AND_SKILL_INDEX.md](../../registry/WORKFLOW_AND_SKILL_INDEX.md) — 슬래시 표 `/plan` Usage 행 (작성·Execute·실행 순서·선행·closeout)

---

# Final Rule

**모드부터 분류한다.** 작성 → Impact Scope → **실행 순서·선행** → Atomic Task → lint. Execute → Task 블록·Pre-read. **Task만 나열한 Blueprint는 불완전.**
