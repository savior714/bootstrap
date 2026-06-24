<!-- Language: ko -->

# Refactor → Plan 핸드오프 · Same-session Blueprint

**SSOT**: 검증 설계(RGR) 3단계 합의 후 **같은 세션**에서 Blueprint 작성·`plan-lint` PASS까지. 해당 턴 직전에 Read.

**공통 계약**: [plan/handoff-contract.md](../../plan/references/handoff-contract.md) — 메뉴 B · 산출물 요약 턴 · 금지 문구.

**관련**: [plan/SKILL.md](../../plan/SKILL.md) Phase W · [discuss/close-handoff.md](../../discuss/references/close-handoff.md) §Same-session plan · [plan.md](../../../workflows/plan.md)

---

## 트리거

아래가 **모두** 충족되면 same-session plan을 **직행**한다 (사용자에게 `/plan` 입력을 시키지 않음).

1. **진단** — 최우선 문제 1문장 확정
2. **심화** — Seam·인터페이스·책임 분리 합의
3. **검증 설계(RGR)** — Red 테스트·Green 기준(명령·케이스) 확정

---

## 3단계 종료 — Close `AskQuestion` (1턴)

RGR 합의 직후 **한 턴**으로 마무리 방향을 묻는다.

| 옵션 | 다음 |
| :--- | :--- |
| **실행 계획(Blueprint)으로 만들기** `(권장)` | §Same-session plan 직행 |
| **이 주제 더 논의하기** | `direction` 유지 — 3단계 중 해당 단계로 복귀 |
| **여기서 마무리** | 노트·채팅만 정리 — PLAN **미작성** |

**금지**: 「`/plan` 하세요」「Blueprint는 다음에」만 텍스트로 던지기 · RGR 미합의 상태에서 Blueprint `(권장)`.

---

## Same-session plan (MUST)

**에이전트 순서** (사용자에게 `/plan`을 시키지 않음):

1. [plan.md](../../../workflows/plan.md) · [plan/SKILL.md](../../plan/SKILL.md) **작성 모드** Read.
2. **3단계 → Blueprint 매핑** (§아래 표)으로 `docs/plans/PLAN_<slug>.md` 초안 작성.
3. `## 🎯 Origin Intent` — 출처: `/refactor` handoff (진단·심화·검증 3단계 합의).
4. `## ⚠️ Edge Case Trace` — RGR·Risk 논의에서 나온 예외. **없으면** [plan/SKILL.md Phase W2](../../plan/SKILL.md) **AskQuestion 1턴** → Trace 행 추가.
5. [TEMPLATE_blueprint.md](../../../../docs/templates/TEMPLATE_blueprint.md) **절 순서** · **`## Agent Execution Pack`**(Impact Scope **직전**) · `실행 순서·선행` · Atomic Task · Closeout Task(`*-999`) 준수.
6. RGR 합의대로 **Red Task를 선행 Phase**에 배치 (TDD Red-first).
6b. Phase W3 **잡무 완료 5문항** — [plan/SKILL.md](../../plan/SKILL.md) · `plan-lint` **직전**
7. `just plan-preread docs/plans/PLAN_<slug>.md --write` → `just plan-lint` **PASS**.
8. (선택) 활성 `DISCUSS_*.md`가 있으면 frontmatter `linked_plan`·`status: handed-off`·§4 `핸드오프: plan — YYYY-MM-DD` 갱신.
9. **산출물 요약 턴** (§아래) — **같은 주제**에 Blueprint 재질문 **금지**.

### 3단계 → Blueprint 절 매핑

| Refactor 단계 | Blueprint 절 | 내용 |
| :--- | :--- | :--- |
| 진단 (Diagnose) | `## 🔍 Diagnosis & Findings` | 현상·근본 원인 |
| 심화 (Deepen) | `## 🏗️ Architectural Deepening` | Seam·Leverage·인터페이스 |
| 검증 설계 (RGR) | Phase 1 Red Task·`Verify`·DoD | 실패 테스트·Green 명령 |
| (합의 스케치) | `## 📜 Conceptual Sketch` | 호출 흐름·책임 (선택) |
| 범위·리스크 | `## 🛡️ Risk & Strategy` · **`## Agent Execution Pack`** · `## 🔍 Impact Scope` | Pack은 Execute 읽기 범위 SSOT |

**plan 작성 SSOT**: [plan/SKILL.md](../../plan/SKILL.md) Phase W0~W5 · [task-decomposition.md](../../plan/references/task-decomposition.md) §Task Goal 작성 SSOT.

---

## 산출물 요약 턴

`plan-lint` PASS **직후 같은 세션** 전용. 본문 18줄 이내. 마지막은 **표준 메뉴 B `AskQuestion`**.

**필수 포함**:

- 리팩 설계: 3단계 한 줄(진단·심화·RGR 확정 요약).
- 설계: 방금 작성한 PLAN 한 줄(Task 개수·`plan-lint` PASS).
- **다음 단계(필수 문장)**: **이 PLAN**에 대해 Blueprint 작성은 **이미 끝났음**을 명시.

**표준 메뉴 B** (discuss와 동일 계약):

| 옵션 | 의미 |
| :--- | :--- |
| **이 PLAN 전체 순차 실행** `(권장)` | Execute 모드 — Dependency 순 · `plan-task-close` · Execution Freeze |
| **새 주제로 discuss/refactor 더 하기** | **새** `DISCUSS_*.md` 또는 새 refactor 사이클 — handed-off PLAN **재편집 금지** |
| **여기서 마무리** | 세션 종료 |

**금지 문구**:

- **이 PLAN**에 대해 `/plan` 다시 · Blueprint 작성 · 「노트 붙여 /plan」
- plan-lint PASS 전 「설계 완료」선언
- **같은 주제** PLAN을 덮어쓰며 두 번째 Blueprint 작성

#### GOOD (산출물 요약 턴) — 복붙용

```text
리팩 설계: Auth 세션 종료 — 진단·심화·RGR(terminateSession Red) 확정.
설계: PLAN_auth_terminate_session — Task 8개, plan-lint PASS.

이 주제의 설계는 끝났습니다. 다음은 이 PLAN 전체를 순서대로 실행하거나, 다른 주제를 새로 논의할 수 있습니다.

AskQuestion: 이 PLAN 전체 순차 실행 (권장) / 새 주제 refactor·discuss / 마무리
```

---

## handed-off PLAN 재진입

`docs/plans/PLAN_*.md`가 이미 존재하고 사용자가 **그 PLAN 실행**을 요청한 경우:

- **refactor 3단계 재시작 금지** — [plan/SKILL.md Execute](../../plan/SKILL.md)로 위임.
- **같은 slug PLAN 재작성 금지** — 범위 재협상은 `blocked` + **새 PLAN**.

---

## DISCUSS 없이 refactor만 한 경우

- `DISCUSS_*.md` 없이도 PLAN 작성·`plan-lint` PASS는 **허용**.
- `Origin Intent` 출처는 `/refactor` handoff로 기록.
- 추후 discuss가 필요하면 **새** DISCUSS를 만들고 `linked_plan`만 연결 (기존 PLAN 본문 수정으로 3단계 재합의 **금지**).

---

## Execute 완료 후 — review (MUST)

메뉴 B **「이 PLAN 전체 순차 실행」** → plan Execute·Closeout 후 **same-session review**. 구현 Task ≥1 `done`이면 **생략 금지**.

**SSOT**: [plan/handoff-from-execute-to-review.md](../../plan/references/handoff-from-execute-to-review.md)
