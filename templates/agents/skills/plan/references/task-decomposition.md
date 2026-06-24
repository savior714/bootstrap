<!-- Language: ko -->

# Atomic Task Decomposition (lazy Read)

**SSOT**: [TEMPLATE_blueprint.md](../../../../docs/templates/TEMPLATE_blueprint.md) MUST NOT · [planning.md](../../../core/planning.md) §0 Granularity

작성 모드 **Phase W3**·Task 추가 전 **반드시** Read.

---

## 왜 잘게 쪼개는가

로컬·소형 LLM은 **한 Task에 파일·개념이 여러 개**면 실수율이 급증한다. Blueprint는 **에이전트 1턴 ≈ Task 1개**가 되도록 쪼갠다. plan-lint PASS만으로 품질 충분 **아님** — 아래 휴리스틱을 **사람 눈**으로도 통과해야 한다.

---

## Iron rules (MUST)

| # | 규칙 | FAIL 예 |
| :---: | :--- | :--- |
| 1 | **1 Task = 1 File** — `Target`에 파일 **1개**만 | `Target: a.ts, b.ts` |
| 2 | **1 Goal = 1 동작** — `및`/`그리고`/`또한`/`동시에` **금지** | 「README 작성 및 GRADING 작성」 |
| 3 | **White-box Goal** — 파일·함수·문자열·UI 상태까지 구체 | 「레이아웃 재배치」 |
| 4 | **순차 번호** — `Task N.M` Phase 내 연속 (1.1→1.2→1.3). **2.9·4.1 점프 금지** (Closeout만 마지막 Phase) | Task 1.1 → 1.2 → **2.9** |
| 5 | **Verify = runner 1개** — `just`/`pytest`/`uv run pytest`/`pnpm`/`python3` | `test -f`·`grep`·`echo` 단독 |
| 6 | **신규 로직 → Red Task 선행** — 실패 테스트 Task → 구현 Task ([tdd.md](../../../domains/testing/tdd.md)) | 구현만 있고 테스트 Task 없음 |
| 7 | **Seam 분리** — 큰 `page.tsx` 연속 수정 금지 → Hook/View **신규 파일 Task** 선행 | page.tsx 3연속 Edit |
| 8 | **Target = 파일** — 디렉터리 Target **금지** | `Target: src/features/foo/` |

---

## 분해 절차 (Write)

```text
기능/수정 범위 확정
  ↓
Impact Scope 표에 파일 나열
  ↓
파일마다: (선택) Red 테스트 Task → Edit/Create Task → (선택) 통합 Verify Task
  ↓
한 Goal에 동사 2개 보이면 Task 2개로 분할
  ↓
Edge Trace 행마다 Task-ID 매핑 — 없으면 Atomic Task 추가
  ↓
Closeout Task 1개 (마지막 Phase)
```

**목표 밀도**: 제품 기능 Blueprint는 구현 Task **보통 5~15개+**. 2~3개 거대 Task는 **재분해** 대상.

---

## Pre-read (Task마다)

| 규칙 | 내용 |
| :--- | :--- |
| **항상** | `[error_pattern_detail]` `agents/core/error_patterns/detail/editing.md` |
| **Target 기준** | `just route <Target> --json` → must_read를 Task Pre-read에 **태그+경로**로 나열 |
| **도메인** | 테스트 Task → `tdd.md` · `error_patterns/detail/testing.md` · FE → route 도메인 spec |
| **금지** | Target과 **무관**한 스킬(예: composition-patterns)을 Pre-read에 넣기 |

Draft 후 **반드시** `just plan-preread docs/plans/<file>.md --write` — Task별 `plan-task-preread:v1` 마커 없으면 lint FAIL. **수동 `[rule]` 나열만 두고 CLI 생략 금지.**

| 작성 단계 | 행동 |
| :--- | :--- |
| Target·Task-ID 확정 전 | Pre-read placeholder 주석만 (`paths=0`) |
| Target 확정 후 | `just plan-preread … --write` → 마커·must_read 경로 주입 |
| plan-lint 전 | 전 Task에 `plan-task-preread:v1` 존재 확인 |

---

## 실행 순서·선행 (MUST — Execution Plan **직전**)

Task 목록만 나열하고 **왜·어떤 순서**인지 없으면 품질 FAIL (iteration-2 피드백).

Blueprint에 `## 실행 순서·선행` 절을 두고 **Task-ID마다** 아래 표를 채운다:

| 순서 | Task-ID | 왜 이 Task인가 (분해 논리) | 선행 | 한 줄 산출 | 병렬 |
| :---: | :--- | :--- | :--- | :--- | :---: |
| 1 | BKF-001 | check FAIL만으로는 apply 경로를 모름 → 힌트 1줄 | None | sync.py 힌트 | — |
| 2 | BKF-002 | 힌트만으로는 CI가 drift 통과 → agent-lint 게이트 | BKF-001 | Justfile 1줄 | ✗ |

**규칙**:
- **Impact Scope** 표의 각 파일(행)이 **최소 1 Task**와 연결되어야 함 — Scope에 없는 Target **금지**
- Phase 헤더(`### Phase N — …`) 아래 **2~3문장**으로 Phase 묶음 이유·진행 방향 기술
- 각 Task `- **Diagnostics**:` 에 **분해 논리 1줄** (숫자 `0` placeholder **금지**) — 예: `Edge Trace「apply 누락」→ BKF-002가 lint에서 catch`

---

## Work-shaped Task (실제 작업 형태)

| OK Target | FAIL Target (meta·역할 불명) |
| :--- | :--- |
| `scripts/bootstrap/sync.py` | `artifacts/.../prompt.md` (eval run 메모) |
| `agents/skills/plan/SKILL.md` | `agents/registry/SKILL_CATALOG.json` metadata 잡동사 |
| `tests/unit/.../test_foo.py` | `evals.json` assertion 한 줄 추가만 |

**eval·skill-creator 인프라**를 Task로 쪼개달라는 Origin Intent가 **없으면** — Blueprint는 **기능·규칙·버그·문서** 작업만 Task화. skill-creator workspace 경로는 **산출물 저장**이지 Task Target 아님.

---

## 좋은 Task 예 (BKF-001 패턴)

```markdown
#### Task 1.1: check 실패 메시지에 apply 힌트를 보강한다 [Unit: Atomic]
- Task-ID: BKF-001 | ...
- **Pre-read**: 이 Task만 — `write`/`patch` 전 **전부** Read
  1. `[error_pattern_detail]` `agents/core/error_patterns/detail/editing.md`
- **Target**: scripts/bootstrap/sync.py
- **Goal**: `--check` FAIL 시 stdout에 `just bootstrap-sync apply=1` 안내 문구가 포함되도록 sync.py check 분기 메시지를 보강한다.
- **Verify**: `uv run pytest tests/unit/scripts/test_bootstrap_sync.py::test_sanitize_text_replaces_placeholders -q`
```

---

## Task Goal 작성 SSOT

**normative**: TEMPLATE MUST NOT · Iron rules #2·#3·#6 — 본 절이 BAD/GOOD·공식·예외의 **단일 참조점**이다.

### 작성 공식 (1문장)

> `[Target 파일]의 [함수·컴포넌트·절]에서 [관측 가능한 변경]을 [구체 조건·결과]로 만든다.`

### BAD/GOOD — 우선 3종

에이전트가 가장 자주 틀리는 패턴. 하나라도 해당하면 Goal을 다시 쓴다.

#### ① 추상·선언적 Goal

| | 예시 |
| :--- | :--- |
| **BAD** | `레이아웃을 재배치한다` · `상태를 정비한다` · `UX를 개선한다` |
| **GOOD** | `DiagnosisPanel.tsx`의 Grid 행 순서를 diagnosis → prescription으로 바꾸고 `PrescriptionPanel` 연동 prop을 `diagnosisOrder` 기준으로 맞춘다. |

#### ② 엔티티·파일 없음

| | 예시 |
| :--- | :--- |
| **BAD** | `드래프트 저장 로직을 수정한다` (어떤 파일·함수인지 불명) |
| **GOOD** | `useReceptionFormDraft.ts`의 `persistDraft`가 `encounterId`가 null일 때 localStorage 키를 `reception-draft-anonymous`로 쓰도록 분기를 추가한다. |

#### ③ TDD Red 누락

| | 예시 |
| :--- | :--- |
| **BAD** | 신규 로직 Task만 있고 선행 Red 테스트 Task 없음 — `mapCopayCategoryToMedicalAidType.ts`에 매핑 함수를 구현한다. |
| **GOOD** | Task 1.1(Red): `mapCopayCategoryToMedicalAidType.test.ts`에 copay 카테고리별 `MedicalAidType` 매핑 실패 테스트를 추가한다. → Task 1.2: `mapCopayCategoryToMedicalAidType.ts`에 매핑 테이블을 구현한다. |

### 자가검사 체크리스트

Goal 초안 후 **하나라도 NO**면 재작성:

- [ ] 접속사(`및`/`그리고`/`또한`/`동시에`) 없음 — 동사 1개
- [ ] Target 파일명 또는 함수·컴포넌트·절명이 Goal에 등장
- [ ] 관측 가능한 결과(문자열·UI 상태·API 응답·테스트 assertion)가 1개 이상
- [ ] 신규 로직이면 Red 테스트 Task가 **선행** Execution Plan에 있음
- [ ] 아래 예외 표에 해당하지 않으면 White-box 수준 충족

### White-box 예외 (완화 허용 패턴)

Closeout·문서-only Task는 파일·함수까지 박지 않아도 된다. **대신 문서 절명·파일명 패턴**을 Goal에 명시한다.

| 유형 | Goal 패턴 예 | 비고 |
| :--- | :--- | :--- |
| **Closeout Roll-up** | `선행 Task Conclusion을 근거로 Conclusion and Summary Roll-up 1문단을 실측으로 작성한다.` | 구조 변경 없음 · Target = Blueprint 파일 |
| **문서-only** | `task-decomposition.md`의 「좋은 Task 예」 직후에 `Task Goal 작성 SSOT` 절을 추가해 BAD/GOOD 3종·작성 공식·체크리스트·예외 목록을 넣는다. | 절명·추가 내용을 Goal에 나열 |
| **메타·레지스트리** | `SKILL_CATALOG.json`에 plan 스킬 항목의 `references` 배열에 `task-decomposition.md` 경로를 추가한다. | eval·workspace meta는 Work-shaped 표 참고 |

> **주의**: lint PASS만으로 Goal 품질이 보장되지 않는다 — 본 절 준수는 **작성자 책임**.

---

## Template 품질 게이트 (lint PASS ≠ 완료)

작성 완료 전 체크:

- [ ] [TEMPLATE_blueprint.md](../../../../docs/templates/TEMPLATE_blueprint.md) 「복사용 뼈대」**절 순서**와 동일 (메타 → 관련 명세 → 업무 요약 → Origin → Trace → … → Execution Plan)
- [ ] Task 필드 **전부** 존재 (Task-ID, Pre-read, Action, Target, Goal, Diagnostics, Verify, Conclusion, Dependency)
- [ ] Pre-read가 **Target·도메인**과 연관
- [ ] Verify가 runner 기반
- [ ] 구현 Task ≥ 범위에 맞는 개수 (pilot 2개짜리는 **의심**)
- [ ] `## 실행 순서·선행` 표 — Task-ID마다 **왜·선행·한 줄 산출**
- [ ] **code Target 있으면 Task -098** — Pre-read 1번 `agents/skills/review/SKILL.md` · Verify `just plan-review-gate` · closeout(-099) Dependency = -098
- [ ] Impact Scope 행 ↔ Task Target **1:1 대응** (Scope 밖 Target 없음)
- [ ] Task `Diagnostics` ≠ `0` — 분해 논리 1줄 이상
- [ ] Phase intro에 **왜 이 Phase인지** 2~3문장
