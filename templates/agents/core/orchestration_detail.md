---
scope:
- '*'
always_apply: false
priority: 1
domain: core
verify_with:
- just prevent-tech-debt
---
<!-- Language: ko -->
# Subagent Orchestration — 상세 (lazy-load)

**always-on 헤더**: [orchestration.md](orchestration.md). Task spawn·handoff 직전 Read.

---

## 1. 기본 원칙

**실행은 subagent에 위임한다.** 메인은 triage·의사결정·Task spawn·handoff 합성만 담당한다.

| 담당 | 메인 | subagent (Task) |
| :--- | :--- | :--- |
| 탐색 | — | `explore` |
| 편집·구현 | — | `general` |
| 검증·게이트 | — | `shell` |
| 사용자 의사결정 | `AskQuestion` | — |
| Task spawn·합성 | ✓ | — |

**턴당 Task 1개** — verify PASS 후 다음 Task. **1 Task = 작은 단위**(파일 1·함수 1 권장) — [routing.md §1.5](routing.md#15-atomic-edit-granularity-원자-편집-단위).

---

## 2. 메인 vs subagent

### 메인이 하는 일

- 요청 triage (한 줄 목표 재진술)
- `AskQuestion` / HITL 승인
- **즉시** 적절한 Task spawn
- handoff 요약 파싱 → 다음 Task 또는 사용자 보고

### 메인이 하지 않는 일

- 코드베이스 탐색 (`Grep` / `SemanticSearch` / `Glob` / 다파일 `Read`)
- 파일 편집 (`StrReplace` / `Write` 및 런타임 동등 도구)
- `just route` · `route-gate-check` · 테스트·lint 직접 실행

### 예외 (메인 직접 허용)

- **질문·설명·리뷰만** (편집 없음)
- 사용자가 **«직접 해줘»** / **«메인에서 처리»** 명시
- **PR 생성** 워크플로 (gh·git — user rule)
- Blueprint·plan-close **조율만** (구현 본문은 subagent) — [plan.md](../workflows/plan.md)

---

## 3. Subagent 라우팅

| `subagent_type` | 용도 |
| :--- | :--- |
| `explore` | 코드베이스·범위·관련 파일 |
| `general` | route · 편집 · 단위 테스트 |
| `shell` | `just *`, `pytest`, `lint-turn-end` |
| `ci-investigator` | PR CI 단일 체크 실패 |
| `bugbot` / `security-review` | 사용자 명시적 리뷰 요청 |

범위 불명 → `explore` 먼저. 범위 확정 → `general`. Blueprint 실행 → Task마다 subagent — [plan.md](../workflows/plan.md).

Cursor Task 필드: [runtime_edit_tools.md §1](runtime_edit_tools.md).

---

## 4. Handoff 계약 (Task `prompt` 필수) — AGENTS.md §5 SSOT

**normative SSOT**: Handoff Tier 판정·S-tier 최소 블록·L-tier 전문 markdown은 [AGENTS.md §5 Handoff Tier](../../AGENTS.md#handoff-tier-sml)만 따른다. 메인은 완료 후 Output format 요약만 파싱한다.

### Tier별 메인 prompt 체크리스트

| prompt 섹션 | S | M | L |
| :--- | :---: | :---: | :---: |
| Mission | ✓ | ✓ | ✓ |
| Success criteria (verify 1개) | ✓ | ✓ | ✓ |
| Bounded scope (Allowed paths) | ✓ | ✓ | ✓ |
| Context from parent | — | ✓ | ✓ |
| Gates (route·원자 편집) | S: [routing.md §2 S-tier](routing.md#s-tier-축약-절차) | M: 4단계 | L: 4단계 전부 |
| Output format | — | ✓ | ✓ |
| §5b Task-type 행 | — | 해당 시 | 해당 시 |
| Blueprint 형식·plan-preread·plan-lint (AGENTS §5 표) | — | — | ✓ |

**handoff 전문 markdown 블록은 본 절에 두지 않는다** — L-tier 전문은 AGENTS §5 Handoff contract (L-tier)만 SSOT.

`ROUTE_MANIFEST_PATH` · `ROUTE_SESSION_KEY` — [CONTEXT_ROUTING.md](../registry/CONTEXT_ROUTING.md).

---

## 5. 실행 루프

```text
1. Main: triage → Task spawn (explore 또는 general)
2. Sub: 실행 + verify 보고
3. Main: PASS 확인 → 다음 Task 또는 사용자 합성 보고
4. 저장소 수정 있었으면 shell Task — just lint-turn-end
```

---

## 6. 안티패턴 (요약)

| WRONG | CORRECT |
| :--- | :--- |
| 메인이 탐색·편집·검증 직접 수행 | Task spawn → handoff 대기 |
| 한 턴에 여러 Task·다파일 편집 | 턴당 1 Task · 작은 chunk 순차 |
| handoff 없이 완료 선언 | §4 Output format 보고 후 합성 |
