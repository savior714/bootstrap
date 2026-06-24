<!-- Language: ko -->

# Execution Gates (lazy Read)

**SSOT**: [plan.md](../../../workflows/plan.md) (슬림 부록) · [planning.md](../../../core/planning.md) §0

`/plan` **실행 모드**·Task closeout·Closeout Task 전에 Read한다.

---

## CLI 순서 (Agent-executable)

| 단계 | 명령 | 시점 |
| :--- | :--- | :--- |
| Pre-read | `just plan-preread docs/plans/<file>.md --write` | plan-lint **전** |
| 구조 검증 | `just plan-lint docs/plans/<file>.md` | 구현 **전** — exit 0 필수 |
| Task 종료 | `just plan-task-close plan=... task=<ID> conclusion="..."` | Verify exit 0 **후** |
| Task 종료 후 | `just plan-lint docs/plans/<file>.md` | 매 Task |
| 구현 리뷰 | `just plan-review-gate plan=docs/plans/<file>.md` | Review Task (-098) |
| 플랜 마감 | `just docs-ssot-headers` → `just linear-sync` → `just plan-close plan=...` | Closeout Task (-099) |
| 세션 종료 | `just lint-turn-end` | (권장) |

**금지**: `plan-task-close` 없이 Task 완료 선언 · Status/Conclusion **에디터 직접 수정**

---

## Lint-first (작성 → 첫 plan-lint)

Blueprint **초안 저장 후** 아래 순서를 **한 번에** 수행한다 — 항목 누락 시 plan-lint가 흔히 잡는 6종 FAIL.

```text
1. 업무 요약·Origin Intent — 백틱·경로 제거 (평문만)
2. Agent scope blockquote — Conclusion + plan-lint 문자열 확인
3. Task-ID·Labels·Target — placeholder·plan 라벨·디렉터리 제거
4. just plan-preread docs/plans/<file>.md --write
5. just plan-lint docs/plans/<file>.md
```

| # | 확인 |
| :---: | :--- |
| 1 | 협업 요약에 `` ` ``·`src/`·CLI 없음 |
| 2 | `> **에이전트 스코프**`에 Conclusion·plan-lint |
| 3 | Task-ID = `[SLUG-NNN]` (XXX/TBD 금지) |
| 4 | Labels ≠ `plan` — Improvement/tooling/Feature |
| 5 | Target = 단일 파일 |
| 6 | plan-task-preread:v1 마커 (plan-preread --write) |

SSOT: [TEMPLATE_blueprint.md](../../../../docs/templates/TEMPLATE_blueprint.md) · [plan/SKILL.md §Phase W3](../SKILL.md)

---

## Blueprint 실행 동결 (Execution Freeze)

**동결 시작**: `plan-lint` PASS **후** 사용자가 전체·연속 실행 요청 (또는 Task 1.1 착수)

| 동결 중 허용 | 동결 중 금지 |
| :--- | :--- |
| `just plan-task-close` | Task 추가·삭제·재번호 |
| Closeout Roll-up 1문단 | Goal/Target/Dependency/Verify 수정 |
| | Edge Case Trace·Origin Intent 구조 변경 |
| | 실행 중 AskQuestion으로 범위 재협상 |

**막히면**: Task `Status: blocked` + Conclusion에 사유 → 사용자 보고 → **새 `PLAN_*.md`** 또는 `just plan-reset-gate`

**Phase 0**: Trace·보완은 **작성 단계**에서 끝내는 것이 표준. 남아 있으면 전체 실행 **첫 1 Task만** — 완료 직후 동결.

---

## Task Closeout 4단계

| 순서 | 액션 |
| :---: | :--- |
| 1 | Task `Verify` 셸 명령 1개 → exit 0 |
| 2 | `just plan-task-close` |
| 3 | 스크립트가 Status→`done` + Conclusion 갱신 |
| 4 | `just plan-lint` PASS — 채팅 「완료」는 **4 이후만** |

---

## Review Task (closeout 직전, -098)

| 순서 | 액션 |
| :---: | :--- |
| 1 | 선행 **구현** Task 전부 `done` + Conclusion 실측 |
| 2 | [review/SKILL.md](../../review/SKILL.md) — diff-first Findings |
| 3 | `## 🔍 Implementation Review` 절 작성 (High/Medium/Low) |
| 4 | `just plan-review-gate plan=...` → exit 0 |
| 5 | `just plan-task-close` → `just plan-lint` |

**금지**: 구현 Task만 `done`으로 두고 Implementation Review placeholder 방치

---

## Closeout Task (마지막, -099)

| 순서 | 액션 |
| :---: | :--- |
| 1 | 선행 구현 Task 전부 `done` + Conclusion 실측 |
| 2 | `## 🔁 Conclusion & Summary` Roll-up 1문단 |
| 3 | `just plan-close plan=...` → exit 0 |
| 4 | `just plan-task-close` → `just plan-lint` |

**금지**: 구현 Task만 `done`으로 두고 Roll-up placeholder 방치

---

## 전체 실행 순서 (Execute 모드)

```text
plan-lint PASS 확인
  ↓
(Phase 0 있으면 1회만)
  ↓
Dependency 순 Task 1개씩:
  Pre-read → 편집 → Verify → plan-task-close → plan-lint
  ↓
Review Task (-098) → plan-review-gate → plan-task-close → plan-lint
  ↓
Closeout Task (-099) → plan-close → plan-task-close → plan-lint
  ↓
(선택) 세션 review SKILL — [handoff-from-execute-to-review.md](handoff-from-execute-to-review.md)
  ↓
(저장소 수정 시) just sync-turn-end
```

중간 Blueprint 재작성·Task 분해 **하지 않음**.

---

## Execute 완료 → Review (Blueprint Task -098 + 세션 점검)

**SSOT**: [handoff-from-execute-to-review.md](handoff-from-execute-to-review.md)

| 조건 | 행동 |
| :--- | :--- |
| 구현 Task ≥1 + 코드 Target | Blueprint **Task -098** (Implementation review) **MUST** — closeout **전** |
| Review Task -098 완료 후 | Closeout Task -099 → plan-close |
| 세션 종료 시 (Execute 완료) | review SKILL로 diff-first 점검 (Task -098과 **별개**·보완) |
| Blueprint 작성만 · Execute 없음 | review Task·세션 review **생략** |

**금지**: plan Execute 「완료」 선언 후 review 없이 세션 종료.
