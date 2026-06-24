<!-- Language: ko -->

# Write Checklist — 잡무 완료 14문항 (lazy Read)

**SSOT**: [plan/SKILL.md](../SKILL.md) Phase W3~W4 · [TEMPLATE_blueprint.md](../../../../docs/templates/TEMPLATE_blueprint.md)

`just plan-lint-quality` **직전** — Execute 진입 전 작성자가 아래 **14문항**을 **모두** 통과해야 한다.

---

## W3 자가 점검 (Task 분해 직후)

하나라도 NO면 재분해:

| 질문 | YES |
| :--- | :--- |
| Goal에 동사가 1개뿐인가? | |
| Target이 단일 파일·**Impact Scope에 있음**? | |
| Verify가 pytest/just/python3/pnpm인가? | |
| **RED Verify recipe가 Target test 파일만 실행하는가?** (#8) | |
| **실행 순서·선행 표.선행 = Task Dependency?** (#9) | |
| Pre-read에 **Target 소스 `[spec]`** 포함 (cap drop 시)? | |
| Pre-read가 Target·도메인과 연관되는가? | |
| BKF-001 수준 white-box Goal? | |
| **`실행 순서·선행` 표 있음**? | |
| **Diagnostics에 분해 이유** (≠0)? | |
| **DoD·업무 요약·aggregate recipe 3-way 일치?** (#10) | |
| **eval/workspace meta Target 없음**? | |
| **code Target 있으면 Task -098 + review/SKILL Pre-read**? | |

**Implementation Review Task (code Blueprint MUST)**: 마지막 구현 Task 다음 **Task-ID `[SLUG-098]`** — Pre-read **1번** `[project_skill]` `agents/skills/review/SKILL.md` · Goal에 **review/SKILL** · Verify `just plan-review-gate` · closeout(-099) **Dependency = -098**. SSOT: [TEMPLATE_blueprint.md](../../../../docs/templates/TEMPLATE_blueprint.md) §Implementation Review Task.

---

## 14문항 — 품질 (실측·경로 — 8)

- **Goal white-box**: 각 Task Goal이 파일·함수·동작 수준 white-box 명세인가?
- **Pre-read 완비**: 각 Task `Pre-read`가 Target·도메인과 연관되며 `plan-preread`로 주입되었는가? Target `[spec]` 포함?
- **Verify runner 1개**: 각 Task `Verify`가 `just`/`pytest`/`python3`/`pnpm` runner **명령 1개**인가?
- **Verify–test 1:1 (#8)**: RED/Green Task Verify가 **해당 Target test 파일만** 실행하는 recipe인가? (기존 gate recipe 재사용 **금지**)
- **표 ↔ Dependency (#9)**: `## 실행 순서·선행` 표 **선행** = Task `Dependency` — policy→test→impl·RED→Green 역전 없음?
- **선행 Task 닫힘**: `Dependency`가 있는 Task의 선행 Task-ID가 Blueprint에 존재하는가? (실행 전 `done`은 Execute 책임)
- **Edge Trace 매핑**: `## ⚠️ Edge Case Trace` 인범위 행이 Task-ID에 매핑되었거나 「이번에 안 하는 것」에 기록되었는가? Diagnosis 행 수와 정합?
- **DoD 3-way (#10)**: 「끝났을 때 확인」·P0 Edge·Impact Scope 변경이 DoD 백틱 명령(또는 aggregate recipe)에 포함되는가?

---

## 14문항 — Lint-first (형식 10 + review 11)

| # | 확인 |
| :---: | :--- |
| 1 | 업무 요약·Origin Intent·Edge Trace·Diagnosis·Risk — **백틱·경로·CLI 없음** |
| 2 | Execution Plan blockquote에 **`Conclusion`**·**`plan-lint`** 둘 다 있음 |
| 3 | Task-ID가 `[SLUG-NNN]` 실값( `[XXX-001]`·`[TBD]`·한글 `[…]` **금지** ) |
| 4 | 메타·Task `Labels`에 **`plan`/`docs` 없음** — allowlist; active root **`docs` FAIL** |
| 5 | 각 `Target`이 **단일 파일 경로** (디렉터리·`/` 끝 **금지**) |
| 6 | `just plan-preread … --write` 완료 (`docs/plans/` Target fallback 포함) |
| 7 | Task **Goal 한 줄** — markdown 헤딩·줄바꿈 **금지** (closeout 9.9) |
| 8 | RED Task Verify = **신규 test 전용** `just` recipe (Justfile stub 선행) |
| 9 | **실행 순서·선행** 표 ↔ Task `Dependency` **동기화** |
| 10 | DoD·업무 요약 acceptance·aggregate recipe **3-way** |
| 11 | code Target ≥1이면 **Task -098** — Pre-read 1번 `agents/skills/review/SKILL.md` · Verify `just plan-review-gate` · closeout(-099) Dependency = -098 |

---

## 자동 검증 (MUST)

`just plan-lint-quality docs/plans/PLAN_<slug>.md` — contract lint + quality gates (#8 FAIL, #9 FAIL, #10 WARN). `just plan-lint … --check-quality` 동일.

SSOT: [TEMPLATE_blueprint.md](../../../../docs/templates/TEMPLATE_blueprint.md) 「Lint-first 작성 체크리스트」· [task-decomposition.md](task-decomposition.md) §Verify–test 1:1 · §실행 순서·선행
