<!-- Language: ko -->

# Blueprint 핸드오프 공통 계약 (Same-session plan)

**SSOT**: discuss · refactor · review · assess · discover emit · deep-research · playwright · audit 등 **모든 Blueprint 산출 경로**가 공유하는 same-session 계약. 스킬별 트리거·입력 매핑은 각 `references/handoff-to-plan.md` 또는 워크플로 부록.

**관련**: [plan/SKILL.md](../SKILL.md) Phase W~W5 · [discuss/close-handoff.md](../../discuss/references/close-handoff.md) §Same-session plan · [execution-gates.md](execution-gates.md)

---

## 핵심 원칙 (MUST)

1. **사용자에게 `/plan` 입력을 시키지 않는다** — 에이전트가 같은 세션에서 Blueprint 작성·lint 또는 Execute 안내까지 이어간다.
2. **plan-lint PASS 전 「설계 완료」선언 금지**.
3. **같은 주제 PLAN 재작성 금지** — handed-off·lint PASS PLAN 재진입은 **Execute**만.
4. **금지 문구**: 「`/plan` 하세요」「노트 붙여 /plan」「Blueprint는 다음에」만 텍스트로 던지기.

---

## 표준 파이프라인 (작성 경로)

Blueprint를 **에이전트가 작성**하는 경로(discuss · refactor · review · assess · deep-research · playwright · audit):

| 순서 | 액션 |
| :---: | :--- |
| 1 | [plan.md](../../../workflows/plan.md) · [plan/SKILL.md](../SKILL.md) **작성 모드** Read |
| 2 | [TEMPLATE_blueprint.md](../../../../docs/templates/TEMPLATE_blueprint.md) 절 순서 · `Origin Intent` · `Edge Case Trace` · **`## Agent Execution Pack`**(Impact Scope **직전**) · `실행 순서·선행` |
| 2b | [plan/SKILL.md](../SKILL.md) Phase W3 **잡무 완료 5문항** 통과 — `plan-lint` **직전** |
| 3 | `just plan-preread docs/plans/PLAN_<slug>.md --write` |
| 4 | `just plan-lint docs/plans/PLAN_<slug>.md` **PASS** |
| 5 | (선택) `DISCUSS_*.md` `linked_plan` · `handed-off` |
| 6 | **산출물 요약 턴** + 표준 메뉴 B `AskQuestion` |
| 7 | (메뉴 B **「이 PLAN 전체 순차 실행」** 선택 시) plan **Execute** — [execution-gates.md](execution-gates.md) |
| 8 | Execute Closeout 후 **review** — 세션 구현 점검 **MUST** — [handoff-from-execute-to-review.md](handoff-from-execute-to-review.md) |

**기계 발급 경로**(discover `discover-emit`): 2~4는 emit이 수행 — 에이전트는 **6번(메뉴 B)** 만 직행. **7~8**은 Execute 선택 시 동일.

---

## 표준 메뉴 B (plan-lint PASS 직후)

| 옵션 | 의미 |
| :--- | :--- |
| **이 PLAN 전체 순차 실행** `(권장)` | plan **Execute** — Dependency 순 · closeout · **이어서 review**(구현 점검 MUST) — [handoff-from-execute-to-review.md](handoff-from-execute-to-review.md) |
| **새 주제로 discuss/refactor/… 더 하기** | **새** 논의·설계 사이클 — handed-off PLAN **재편집 금지** |
| **여기서 마무리** | 세션 종료 |

**금지**: 메뉴 B에 **「Task 1.1만」** 옵션 · **같은 PLAN**에 Blueprint 재작성 안내.

---

## 산출물 요약 턴 (필수 형식)

`plan-lint` PASS 직후 · 본문 **18줄 이내** · 마지막은 **메뉴 B AskQuestion**.

**필수 포함**:

- 입력(논의·리뷰·assess·리서치 등) 한 줄
- PLAN 한 줄(Task 개수·`plan-lint` PASS)
- **「이 주제의 설계는 끝났습니다」** — Blueprint 작성 **이미 완료** 명시

#### GOOD — 복붙용 골격

```text
{입력 요약 한 줄}
설계: PLAN_<slug> — Task N개, plan-lint PASS.

이 주제의 설계는 끝났습니다. 다음은 이 PLAN 전체를 순서대로 실행하거나, 다른 주제를 새로 논의할 수 있습니다.

AskQuestion: 이 PLAN 전체 순차 실행 (권장) / 새 주제 {discuss|refactor|…} / 마무리
```

---

## handed-off PLAN 재진입

`docs/plans/PLAN_*.md` 존재 + `plan-lint` PASS + 사용자가 **그 PLAN 실행** 요청:

- 원 설계 스킬 **재시작 금지** → [plan/SKILL.md Execute](../SKILL.md)
- 범위 재협상 → `blocked` + **새 PLAN** (동일 slug 덮어쓰기 금지)

---

## 스킬별 핸드오프 SSOT 인덱스

| 출처 | 핸드오프 SSOT | Blueprint 입력 |
| :--- | :--- | :--- |
| discuss | [discuss/close-handoff.md](../../discuss/references/close-handoff.md) | DISCUSS §3·§2·엣지 |
| refactor | [refactor/handoff-to-plan.md](../../refactor/references/handoff-to-plan.md) | 진단·심화·RGR 3단계 |
| review | [review/handoff-to-plan.md](../../review/references/handoff-to-plan.md) | High/Medium Findings |
| assess | [assessment-driven-planning/handoff-to-plan.md](../../assessment-driven-planning/references/handoff-to-plan.md) | SPEC §4 Decision-Lock |
| discover emit | [discover/handoff-to-plan.md](../../discover/references/handoff-to-plan.md) | `discover-emit` 산출물 |
| deep-research | [deep-research/handoff-to-plan.md](../../deep-research/references/handoff-to-plan.md) | research_results·GAP |
| playwright | [playwright.md](../../../workflows/playwright.md) §5 핸드오프 | 브라우저 탐색 Findings |
| audit | [audit.md](../../../workflows/audit.md) §핸드오프 | 최저 카테고리·개선 항목 |
| **Execute 완료** | [handoff-from-execute-to-review.md](handoff-from-execute-to-review.md) | 세션 구현 diff · review MUST |

**plan 작성 시 출처 분류**: [plan/SKILL.md](../SKILL.md) Phase W0.
