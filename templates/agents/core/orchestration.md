---
scope:
- '*'
always_apply: true
priority: 1
domain: core
verify_with:
- just prevent-tech-debt
---
<!-- Language: ko -->
# Subagent Orchestration (Main = Conductor)

메인 에이전트는 **지휘·의사결정·합성**만 담당하고, **탐색·구현·검증**은 서브에이전트(Cursor **Task** 도구)에 위임하는 규범 SSOT.

**기본 모드**: **O2 Strengthened** — **구현·편집 요청은 항상** 서브에이전트에 위임한다. **연속 작업 2+**(서로 다른 종류의 작업 단계가 2개 이상 연속 필요)도 **반드시 Task subagent** — 메인 연속 직접 수행 **금지**. 메인은 triage, AskQuestion, Task spawn, 합성만 수행한다. **코드베이스 탐색**(`Grep`/`SemanticSearch`/`Glob`/다파일 `Read`)도 **`explore` Task**에 위임한다. 복합 작업은 **chunk**(파일 1·함수 1) 단위로 순차 Task spawn — [§2 Chunk · Turn budget](#chunk--turn-budget).

**Cross-ref**: [principles.md §1.4](principles.md#14-goal-driven-execution) · [execution.md §3](execution.md) · [LOAD_ORDER.md](../registry/LOAD_ORDER.md) 멀티 에이전트 · [cursor-runtime.md](../skills/skill-creator/references/cursor-runtime.md) Task 매핑.

---

## 0. 적용 순서 (Exception-before-default)

| 순서 | 조건 | 행동 |
| :--- | :--- | :--- |
| 1 | [§5 직접 실행 예외 (O0)](#5-직접-실행-예외-o0) 해당 | 메인이 직접 Read·편집·검증 (좁은 예외만) |
| 2 | [§2 이관 트리거](#2-turn-0-triage--이관-트리거) 하나라도 해당 (**연속 작업 2+** 포함) | **O2 Strengthened** — Turn 0부터 서브에이전트; 메인 연속 직접 수행 금지 |
| 3 | 그 외 — **질문·설명·리뷰만**, 편집·구현 없음 | 메인 직접 Read·답변 |

**우선순위**: 본 절 O2 이관 트리거가 충족되면, 플랫폼의 “좁은 질문은 Task 금지” 힌트보다 **저장소 이관 규범이 우선**한다.

---

## 1. 오케스트레이션 모드

| 모드 | 메인 역할 | 서브 역할 | EMR 기본 |
| :--- | :--- | :--- | :---: |
| **O0 Direct** | 탐색·편집·검증 전부 | 없음 | §5 O0 좁은 예외만 |
| **O1 Explore-first** | triage, AskQuestion, Task 큐, handoff 합성 | `explore` → 범위 보고; 이후 순차 실행 Task | 범위 불명 시 선행 |
| **O2 Sequential delegate** | O1 + **구현·편집 전부 Task** (파일 1개·함수 1개 포함) | `general` / `shell` per step | **기본** |
| **O3 Plan-driven** | Blueprint·plan-lint·Task 순서만 | Blueprint Task마다 subagent + Verify | `/plan` 실행 시 |

O1에서 explore 보고를 받으면, 메인은 **짧은 실행 큐(3~7단계)** 를 제시한 뒤 O2 구현 Task를 순차 spawn한다. 범위가 이미 확정된 단일 편집은 explore 없이 바로 `general` Task로 넘긴다. Blueprint가 있으면 O3을 따른다 — [plan.md](../workflows/plan.md).

---

## 2. Turn 0 Triage · 이관 트리거

메인은 **구현·편집·테스트·코드베이스 탐색 전** 아래만 수행한다. triage에서 허용되는 Read는 **사용자가 `@`로 지정한 파일·IDE에 이미 열린 파일**뿐이다. 그 외 범위·위치 파악은 **`explore` Task spawn** — 메인 `Grep`/`SemanticSearch`/`Glob`/코드 다파일 `Read` **금지**.

1. **요청 유형**: 질문만 / 단일 수정 / 복합·플랜 / 디버그 / 리뷰
2. **범위**: 예상 터치 파일 수·레이어(domain/application/UI) 수
3. **게이트**: Blueprint 필요, `just route` 필요, HITL(`PROJECT_RULES.md` §3) 필요 여부

### 연속 작업 2+ (정의)

실행 계획에 **서로 다른 종류의 작업 단계가 2개 이상 연속** 필요하면 해당한다. 예: 탐색→편집, 편집→검증, Read→route→편집, 파일 A 편집→파일 B 편집, explore→implement, implement→test.

**규칙**: 메인 에이전트가 위 단계를 **연속으로 직접 수행 금지** — 반드시 **Task subagent**에 위임하고 **턴당 spawn 1개·순차 handoff** ([§2 Chunk](#chunk--turn-budget)). 첫 단계만 Task로 넘기고 메인이 다음 단계를 이어 직접 수행하는 것도 **금지**.

### 이관 트리거 (하나라도 해당 → 즉시 서브에이전트 Task)

- **연속 작업 2+** — 위 [정의](#연속-작업-2-정의) 해당 시 **즉시** Task spawn; 메인이 탐색·편집·검증 등을 한 턴·한 세션에서 연속 직접 수행 **금지**
- **파일 편집·구현 요청** — **파일 1개·함수 1개 포함** ([§5 O0](#5-직접-실행-예외-o0) 예외 제외)
- 수정·조사 대상 **파일 2개 이상**, 또는 **레이어 2개 이상** (범위 불명 시 `explore` 먼저)
- `plan` / `blueprint` / `/discover` / PLAN 순차 실행
- 원인 불명 버그·회귀 (`/diagnose` · `/investigate`)
- E2E·다중 테스트 스위트·CI 실패 분석
- 사용자가 “전체 파악 후 진행”·“순차적으로 맡겨” 등 **위임 의도**를 명시

### Turn 0 메인 출력 (O2 Strengthened)

1. 한 줄 목표 재진술
2. 선택 모드 (O2 또는 O3; 범위 불명이면 O1 `explore` 선행)와 이유
3. **즉시** 실행 Task spawn — 범위 불명: `explore` 먼저; 범위 확정: `general` (백그라운드 허용 — Multitask Mode)
4. 서브에이전트 handoff·verify 완료 전 **메인 편집·구현·탐색 착수 금지**

### Chunk · Turn budget

**문제**: 한 턴에 탐색+편집+검증을 몰아하면 컨텍스트 초과·편집 실패·O2 우회가 잦다. **한 번에 다 쓰지 않고 chunk로 쪼갠다.**

| 규칙 | 메인 | 실행 subagent |
| :--- | :--- | :--- |
| **탐색** | `@` 지정·열린 파일 Read만 | `explore` — 코드베이스·범위·리스크·관련 파일 |
| **1 chunk** | 실행 큐를 **문장으로만** 계획 (파일·함수 단위) | 1 Task = **파일 1 + 함수·컴포넌트 1** 변경, 또는 explore 1질문 |
| **1 turn** | explore·구현 Task **최대 1개 spawn** 후 handoff·verify **대기** | chunk 완료 후 §4 Output format 보고 |
| **복합 요청** | 3~7 chunk 큐 제시 → **순차** spawn (의존 chunk 병렬 금지) | 이전 chunk verify PASS 후 다음만 착수 |

**handoff `Mission`에 «파일 N개 수정»·«전체 리팩터» 같은 **다chunk 목표 금지** — chunk마다 별도 Task·별도 verify.

**서브도 동일**: 1 Task 안에서 여러 함수·여러 파일을 한꺼번에 바꾸지 않는다 — [routing.md §1.5](routing.md#15-atomic-edit-granularity-원자-편집-단위).

---

## 3. Subagent 라우팅

| `subagent_type` | 용도 | spawn 시점 |
| :--- | :--- | :--- |
| `explore` | 코드베이스·범위·리스크·관련 파일 목록 | Turn 0·범위 불명·「어디 있나」 — **메인 탐색 금지** |
| `general` | 단일 실행 단계 — route, 편집, 단위 테스트 | O2/O3 각 Task |
| `shell` | `just *`, `pytest`, `plan-task-close`, `lint-turn-end` | 검증·게이트 전용 |
| `ci-investigator` | PR CI 단일 체크 실패 | CI 문의 시 |
| `bugbot` / `security-review` | 명시적 로컬 리뷰 요청 | 사용자 요청 시 |

**병렬**: 독립 탐색·독립 검증만. **구현 Task는 의존성 있으면 순차** — 이전 handoff를 다음 `prompt`에 포함하거나 `resume` 사용.

Cursor Task 필드 SSOT: [runtime_edit_tools.md §1](runtime_edit_tools.md) · eval 예시: [cursor-runtime.md](../skills/skill-creator/references/cursor-runtime.md).

---

## 4. Handoff 계약 (Task `prompt` 필수)

서브에이전트 `prompt`에는 아래 블록을 **반드시** 포함한다. 메인은 완료 후 이 형식의 요약만 파싱한다.

```markdown
## Mission
<한 문장 목표>

## Success criteria
- verify: `<단일 명령 — plan-lint 규칙과 동일하게 1 outcome>`

## Context from parent
- User ask: ...
- Prior conclusions: (이전 Task 요약)

## Bounded scope
- Allowed paths: ...
- Out of scope: ...

## Gates (subagent MUST)
1. `just route <paths> --json --write-manifest`
2. `must_read` 전량 Read
3. `just route-read` → `just route-gate-check`
4. verify 실행 후 결과 보고
5. **원자 편집** — [routing.md §1.5](../../core/routing.md#15-atomic-edit-granularity-원자-편집-단위): 기존 파일 `Write` 금지 · 1회 부분 수정 = 함수·컴포넌트 1개

## Output format (required)
- Changed files: (list)
- Verify: PASS|FAIL + command + 한 줄 요약
- Risks / follow-ups
- Blockers: (있으면 메인 에스컬레이션 — 사용자 질문은 subagent 금지)
```

### 멀티 에이전트 manifest

부모 세션의 `ROUTE_MANIFEST_PATH` · `ROUTE_SESSION_KEY`가 있으면 handoff에 명시한다. 서브는 동일 manifest를 이어 받는다 — [CONTEXT_ROUTING.md §Route 매니페스트](../registry/CONTEXT_ROUTING.md).

---

## 5. 메인 에이전트 역할 경계

### O2 Strengthened 에서 메인 MUST

- Turn 0 triage 및 모드 선언
- `AskQuestion` / `question` — 사용자 의사결정 ([principles.md §1.1](principles.md#111-interactive-refine--quick-pick-에이전트-공통))
- Task spawn · `resume` · handoff 합성
- HITL 승인 요청 (`git push`, 삭제 등)
- 세션 종료 시 검증 위임 (`just lint-turn-end` → `shell` subagent 권장)

### O2 Strengthened 에서 메인 MUST NOT

- **어떤 구현·편집이든** `StrReplace` / `Write` / 직접 구현용 `Shell`(편집·테스트) — **파일 1개·함수 1개 포함**, **런타임별 동등 도구 포함** (`replace_file_content`·`write_to_file` 등, [runtime_edit_tools.md §1](runtime_edit_tools.md)). O0 명시 예외만 제외.
- **코드베이스 탐색** — `Grep` / `SemanticSearch` / `Glob` / 코드 파일 다파일 `Read` (triage: `@`·열린 파일만 예외)
- explore 없이 다파일 `Read`·탐색 도구로 “슬쩍 구현”
- **연속 작업 2+** — 탐색→편집·편집→검증·다파일 편집 등 **서로 다른 종류의 단계를 메인이 연속 직접 수행** ([§2 연속 작업 2+](#연속-작업-2-정의))
- **한 턴에** explore·구현 Task **2개 이상 spawn**, 또는 verify PASS 전 다음 구현 Task spawn
- **한 턴에** 여러 파일·여러 함수를 직접 편집하려는 시도
- handoff `Mission`에 다chunk(다파일·다함수) 목표를 넣고 한 Task에 몰아넣기
- 서브 handoff 없이 완료 선언

### 직접 실행 예외 (O0) — 좁은 carve-out만

- **설명·리뷰·질문 답변만** (편집·구현 없음)
- 사용자가 **“직접 해줘”** / **“메인에서 처리”** 명시
- **PR 생성** 워크플로 (gh·git status 등 — user rule)
- **Blueprint·plan-close** — 메인이 PLAN·`just plan-lint`·`just plan-task-close` 조율만; 구현 Task 본문은 서브에이전트 ([plan.md §1.10](../workflows/plan.md))

---

## 6. 순차 실행 루프 (O1 → O2)

```text
1. Main: triage → explore Task
2. Main: explore 요약 + 짧은 실행 큐 → AskQuestion (필요 시)
3. Main: general Task (step 1) — handoff §4
4. Main: verify PASS 확인 → general Task (step 2) …
5. Main: shell Task — just lint-turn-end (저장소 수정 있었을 때)
6. Main: 사용자-facing 합성 보고 (비개발자 톤 — reporting.md §1.6)
```

Blueprint(O3)는 큐 대신 PLAN Task-ID 순서를 따른다. Task `Status`/`Conclusion`은 **`just plan-task-close`만** — [plan.md §1.10](../workflows/plan.md).

---

## 7. 워크플로 매핑 (pointer)

| 워크플로 | 오케스트레이션 |
| :--- | :--- |
| `/plan` | 메인: Blueprint·plan-lint · 구현은 O3 |
| PLAN 순차 실행 | Task마다 `general`; close는 `shell` |
| `/diagnose` | `explore`+재현 → 수정 `general` |
| `/discover` | seed/emit `shell` · 구현 Blueprint Task당 subagent |
| skill eval | [cursor-runtime.md](../skills/skill-creator/references/cursor-runtime.md) |

상세 워크플로 본문은 각 workflow SSOT에 두고, 본 문서는 **역할 분리·이관 계약**만 규정한다.

---

## 8. 안티패턴

| WRONG | CORRECT |
| :--- | :--- |
| 메인이 탐색→편집·편집→검증 등 **연속 작업 2+**를 직접 수행 | **연속 작업 2+** — 첫 단계 Task spawn → handoff·verify PASS → 다음 Task 순차 |
| 메인이 explore와 구현을 같은 턴에 수행 | explore 완료 → 큐 합의 → Task spawn |
| 메인이 Grep·SemanticSearch로 코드베이스 탐색 | `explore` Task spawn 후 handoff만 파싱 |
| 복합 요청을 한 Task·한 턴에 몰아 처리 | 3~7 chunk 큐 → 턴당 Task 1개 순차 ([§2 Chunk](#chunk--turn-budget)) |
| 서브 prompt에 목표·verify 없음 | §4 handoff 전량 포함 |
| 모든 단순 질문에 Task | 질문·설명만은 O0 — 편집 요청은 O2 |
| 메인이 파일 1개 수정을 “단순”으로 직접 수행 | O2 — `general` Task spawn |
| 서브가 사용자에게 AskQuestion | Blockers만 메인에 보고 |
| handoff 무시하고 transcript 재독 | 구조화 Output format만 신뢰 |
| 기존 파일 `Write`·여러 함수 한 패치 | [routing.md §1.5](routing.md#15-atomic-edit-granularity-원자-편집-단위) — 함수 단위 순차 부분 수정 |

---

## 9. 도입·확장

- **Phase 2 (완료)**: [plan.md](../workflows/plan.md) · [plan/SKILL.md §Execute O3](../skills/plan/SKILL.md) · [execution.md §3](execution.md) · [LOAD_ORDER.md](../registry/LOAD_ORDER.md) · [CONTEXT_ROUTING.md](../registry/CONTEXT_ROUTING.md)
- **Phase 3 (완료)**: [error_patterns/detail/editing.md §1.11](error_patterns/detail/editing.md) WRONG/CORRECT · 기존 «실패 시 Write» 예시 정합
- **O2 강화 (완료·적용 중, 2026-06-17)**: §2 이관 트리거에 «파일 1개·함수 1개 구현» 포함; §0 기본 모드 O2 Strengthened; 메인 직접 편집은 §5 O0 좁은 예외만 (설명·리뷰, 사용자 “직접 해줘”, PR 워크플로, Blueprint 조율)
- **Chunk · Turn budget (2026-06-17)**: 메인 코드베이스 탐색 금지(`explore` 위임); 턴당 Task spawn 1개; 1 Task = 1 chunk(파일 1·함수 1); 다chunk Mission 금지
- **연속 작업 2+ (2026-06-17)**: §2 이관 트리거·§0 적용 순서·§8 안티패턴에 **연속 작업 2+** 명시 — 서로 다른 종류의 작업 단계 2개 이상 연속 시 메인 직접 수행 금지, Task subagent 필수
