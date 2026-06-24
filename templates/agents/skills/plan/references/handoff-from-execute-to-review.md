<!-- Language: ko -->

# Plan Execute → Review (Blueprint Task -098 + 세션 구현 점검)

**SSOT**: discuss · refactor · review · assess · discover emit · deep-research · playwright · audit 등 **모든 Blueprint 경로**에서 **Execute로 구현까지 끝낸 뒤** review. 공통 Blueprint 작성·메뉴 B: [handoff-contract.md](handoff-contract.md).

**관련**: [plan/SKILL.md](../SKILL.md) Phase E2/E3 · [execution-gates.md](execution-gates.md) · [review/SKILL.md](../../review/SKILL.md)

---

## 역할 분리 (MUST)

| 단계 | 담당 | 산출 |
| :--- | :--- | :--- |
| Blueprint 작성·lint | plan **작성** (+ 각 스킬 handoff) | `PLAN_*.md` · 메뉴 B |
| Implement Task 실행 | plan **Execute** | 코드·설정 패치 · `plan-task-close` |
| **Blueprint 구현 리뷰** | **Review Task -098** | `## 🔍 Implementation Review` · `plan-review-gate` PASS |
| Closeout | plan **Execute** Phase E2 | Roll-up · `plan-close` · closeout Task `plan-task-close` |
| **세션 구현 점검** | **review SKILL** (선택·보완) | diff-first Findings · 실행한 검증 · close AskQuestion |

plan Execute는 closeout **전에** Task -098을 **건너뛰지 않는다**. 세션 review SKILL은 Blueprint Task -098과 **별개**이나 Execute 완료 후 권장된다.

---

## 트리거 (MUST)

아래 **모두** 해당 (코드 구현 Blueprint):

1. plan **Execute** — 선행 구현 Task 전부 `done`
2. **Review Task -098** — `just plan-review-gate` exit 0 · `plan-task-close` · `plan-lint` PASS
3. **Closeout Task -099** — `just plan-close` exit 0 · closeout Task `plan-task-close` · `plan-lint` PASS
4. 본 세션에서 **구현 Task** 1개 이상 `Status: done` + 저장소 코드 변경

**출처 무관** — handoff 스킬이 discuss·assess·discover 등 무엇이든, Execute 경로는 동일.

---

## 생략 (SKIP)

| 조건 | 이유 |
| :--- | :--- |
| 메뉴 B에서 **「여기서 마무리」**만 선택 — Execute 없음 | 구현 없음 |
| Blueprint 작성·lint만 하고 Execute 착수 **전** 세션 종료 | 구현 없음 |
| 구현 Task 0개 (docs-only) + 코드 Target 없음 | Review Task -098 생략 가능 |
| 사용자가 **「리뷰 생략」** 명시 | HITL 예외 |

---

## 절차 (MUST) — Review Task -098

| 순서 | 액션 |
| :---: | :--- |
| 1 | [review/SKILL.md](../../review/SKILL.md) **Read** — Iron Law · diff-first |
| 2 | **Gather** — `git diff` (Blueprint Task Target 범위) |
| 3 | **Run verification** — review §Agent-executable (Task Verify와 중복 가능) |
| 4 | **Findings** — High / Medium / Low |
| 5 | `## 🔍 Implementation Review` 절 작성 |
| 6 | `just plan-review-gate plan=docs/plans/<file>.md` → exit 0 |
| 7 | `just plan-task-close` → `just plan-lint` |

**금지**:

- 구현 Task `done` 후 Review Task -098 **생략**하고 Closeout(-099) 착수
- Implementation Review placeholder로 `plan-review-gate` 통과 시도

---

## Post-execute review close (세션 review SKILL — 요약)

Closeout(-099) 완료 **후** 세션 review SKILL을 이어갈 수 있다. Execute 직후이므로 close `(권장)` **1번에 「Blueprint 만들기」를 두지 않는다**.

| 상황 | `(권장)` 후속 |
| :--- | :--- |
| 실질 이슈 없음 | **여기서 마무리** |
| 국소적 High/Medium | **지금 바로 소규모만 고치기** |
| 범위·트레이드오프 불명확 | **리뷰·수정 범위 더 discuss하기** |
| 다파일·동작 변경 필요 | **새 slug Blueprint** (same-session plan **작성** — Findings 근거) |

전문: [review/SKILL.md §Post-execute close](../../review/SKILL.md)

---

## 세션 종료 순서 (Execute + review)

```text
plan Execute Task 루프 (구현 Task)
  ↓
Review Task -098 (review/SKILL → Implementation Review → plan-review-gate → plan-task-close → plan-lint)
  ↓
Closeout -099 (docs-ssot-headers → linear-sync → plan-close → plan-task-close → plan-lint)
  ↓
(선택) 세션 review SKILL (본 문서 §Post-execute)
  ↓
(저장소 수정 시) just sync-turn-end — [reporting.md §1.0](../../../core/reporting.md)
```

---

## 스킬별 handoff에서의 위치

각 `handoff-to-plan.md` · discuss `close-handoff.md` 파이프라인:

```text
… → plan-lint PASS → 메뉴 B
  → (선택) Execute → Review Task -098 → Closeout -099 → (선택) 세션 review → 세션 종료
```

메뉴 B **「이 PLAN 전체 순차 실행」** 선택 시 — Execute 후 **Task -098(구현 리뷰)** 이 closeout **전에** 이어진다고 **한 줄** 안내 가능.
