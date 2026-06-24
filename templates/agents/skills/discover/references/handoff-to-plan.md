<!-- Language: ko -->

# Discover emit → Plan Execute 핸드오프

**SSOT**: `discover-emit`이 Blueprint를 **기계 발급**한 뒤 same-session **Execute 안내**. 공통 계약: [plan/handoff-contract.md](../../plan/references/handoff-contract.md).

**관련**: [discover/SKILL.md](../SKILL.md) §3 · [discover.md](../../../workflows/discover.md)

---

## 역할 분리 (MUST)

| 단계 | 담당 | 산출 |
| :--- | :--- | :--- |
| discover Run·validate·emit | discover 스킬 + CLI | `PLAN_discover_implement_*_<timestamp>.md` |
| Implement Task 실행 | plan **Execute** | 코드 패치 · `plan-task-close` |

discover는 **emit만** — Implement Task 코드 수정 **금지**.

---

## 트리거

`just discover-emit` exit 0 · stdout·`artifacts/discover/latest_*_implement_plan.txt`에 경로 확정.

---

## emit 직후 (MUST)

**에이전트 순서** (사용자에게 `@` + `/plan` **시키지 않음**):

1. emit 경로 Read — `plan-lint`는 emit이 이미 수행(exit 0 전제).
2. Blueprint Task 개수·큐 lane 한 줄 요약.
3. **산출물 요약 턴** — [handoff-contract.md](../../plan/references/handoff-contract.md) §GOOD 골격.
4. 표준 **메뉴 B** `AskQuestion` — **「이 PLAN 전체 순차 실행」`(권장)`**.

**금지**:

```text
위 파일을 @ 멘션하고 /plan 을 사용하여…
```

**올바른 안내**: 「설계(emit)는 끝났습니다. 이 PLAN 전체를 순서대로 실행할 수 있습니다.»

---

## handed-off 재진입

이미 emit된 `PLAN_discover_implement_*.md` + 사용자 «실행» → discover **금지** — plan **Execute**.

새 Run·새 emit → **새 타임스탬프 PLAN** (기존 덮어쓰기 없음).

---

## Execute 완료 후 — review (MUST)

메뉴 B Execute → **Review Task(-098)** → Closeout(-099) 후 **same-session review**. 구현 Task ≥1 `done`이면 **생략 금지**.

- **Blueprint Task -098**: Pre-read `agents/skills/review/SKILL.md` · `## 🔍 Implementation Review` · `just plan-review-gate`
- **세션 review**: Task -098과 별개·보완 — diff-first Findings

**SSOT**: [plan/handoff-from-execute-to-review.md](../../plan/references/handoff-from-execute-to-review.md)
