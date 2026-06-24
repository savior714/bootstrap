<!-- Language: ko -->

# Review → Plan 핸드오프

**SSOT**: close 턴 Blueprint 선택 시 same-session plan. 공통 계약: [plan/handoff-contract.md](../../plan/references/handoff-contract.md).

**관련**: [review/SKILL.md](../SKILL.md) §Close turn · [plan/SKILL.md](../../plan/SKILL.md) Phase W

---

## 트리거

- close `AskQuestion`에서 **「권장 수정을 실행 계획(Blueprint)으로 정리하기」** `(권장)` 선택
- 사용자가 리뷰 직후 **「Blueprint로」「plan으로」** 명시
- **Fast-path**: 사용자가 이미 plan 연속을 선택 → handoff AskQuestion **생략** → §Same-session plan 직행

**생략 조건**: 실질 이슈 없음 close · 단일 1~2줄 fix만 선택(「지금 바로 소규모만 고치기」).

---

## Same-session plan (MUST)

1. [plan/SKILL.md](../../plan/SKILL.md) 작성 모드 · [handoff-contract.md](../../plan/references/handoff-contract.md) Read.
2. `docs/plans/PLAN_<slug>.md` 작성:
   - `Origin Intent` 출처: `/review` — `{base}...HEAD` 또는 지정 diff 범위
   - `Edge Case Trace` — 리뷰 Medium/High의 엣지·회귀 시나리오 → Task-ID 또는 범위 밖
   - `Diagnosis` — 리뷰 Findings 요약(High 우선)
   - **`## Agent Execution Pack`** — [TEMPLATE_blueprint.md](../../../../docs/templates/TEMPLATE_blueprint.md) · Impact Scope **직전** (Execute Pack-only Read SSOT)
   - Task Goal — **White-box** · High/Medium 1건당 Atomic Task(가능 시)
   - Red 우선 — 회귀 방지 테스트가 리뷰 권고에 있으면 선행 Phase
   - Phase W3 **잡무 완료 5문항** — [plan/SKILL.md](../../plan/SKILL.md) · `plan-lint` 직전
3. `just plan-preread` → `just plan-lint` PASS.
4. **산출물 요약 턴** + 표준 메뉴 B — [handoff-contract.md](../../plan/references/handoff-contract.md) §메뉴 B.

**금지**: `/plan`만 안내 · 리뷰 본문 없이 handoff · lint 전 완료 선언.

#### GOOD (산출물 요약 턴) — 복붙용

```text
리뷰: auth logout diff — High 2건·Medium 1건 Findings.
설계: PLAN_auth_logout_review — Task 4개, plan-lint PASS.

이 주제의 설계는 끝났습니다. 다음은 이 PLAN 전체를 순서대로 실행하거나, 다른 주제를 새로 논의할 수 있습니다.

AskQuestion: 이 PLAN 전체 순차 실행 (권장) / 새 주제 review·discuss / 마무리
```

---

## handed-off PLAN 재진입

동일 diff·동일 PLAN 실행 요청 → review **금지** — plan **Execute**.

---

## Execute 완료 후 — review (MUST)

review → plan 작성 → 메뉴 B Execute → Closeout 후 **다시 review**로 세션 구현 점검. 구현 Task ≥1 `done`이면 **생략 금지**.

**SSOT**: [plan/handoff-from-execute-to-review.md](../../plan/references/handoff-from-execute-to-review.md)
