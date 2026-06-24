<!-- Language: ko -->

# Blueprint Contract (lazy Read)

**SSOT**: [planning.md](../../../core/planning.md) §2 · [plan_lint.py](../../../../scripts/plan_loop/plan_lint.py)

`/plan` **작성 모드**에서 Blueprint 저장·`just plan-lint` 전에 Read한다.

---

## 필수 3항 (plan_lint HARD)

| # | 항목 | 위치 |
| :---: | :--- | :--- |
| 1 | `## Agent Completion Contract` | Execution Plan **직전** |
| 2 | `> **에이전트 스코프**:` blockquote | Execution Plan **첫 Task 직전** |
| 3 | 각 Task `- **Conclusion**:` | todo/running: CSF 슬롯 · done: 실측 1줄 (≥25자) |

---

## 문서 메타·구조

| 항목 | 규칙 |
| :--- | :--- |
| 제목 | `# 🗺️ Project Blueprint: …` |
| 메타 | `SSOT Check`, `Project Status Link`, `Architectural Goal`, `Linear-Issue` |
| 협업 요약 | `## 📋 업무 요약 (협업용)` — 경로·CLI·백틱 **금지** |
| Origin Intent | `## 🎯 Origin Intent` — 1~3줄, 경로·CLI 금지 |
| Edge Case Trace | `## ⚠️ Edge Case Trace` — 표 최소 1행, Task-ID 또는 `범위 밖` |
| Task 헤딩 | `#### Task X.Y: 제목 [Unit: Atomic]` (X·Y **숫자만**) |
| Task 필드 | `Task-ID`, `Pre-read`, `Action`, `Target`, `Goal`, `Diagnostics`, `Verify`, `Conclusion`, `Dependency` |
| Verify | 셸 명령 **1개** (`;` `&&` `||` 금지) |
| Closeout | 마지막 Task 1개 — Roll-up + `just plan-close` |
| DoD | 백틱 명령 목록 — `just plan-close` **자체 포함 금지** (재귀) |

템플릿: [TEMPLATE_blueprint.md](../../../../docs/templates/TEMPLATE_blueprint.md)  
협업 요약: [TEMPLATE_blueprint_collaboration_summary.md](../../../../docs/templates/TEMPLATE_blueprint_collaboration_summary.md)

---

## Lint-first authoring (첫 `plan-lint` FAIL 방지)

`plan-preread --write` → `plan-lint` **직전** — [TEMPLATE_blueprint.md](../../../../docs/templates/TEMPLATE_blueprint.md) 「Lint-first 작성 체크리스트」와 동일.

| FAIL 유형 | 작성 시 MUST |
| :--- | :--- |
| 업무 요약 백틱·경로 | 협업 절·Origin Intent·Edge Trace·Diagnosis·Risk = **평문 한국어** |
| Agent scope | blockquote에 **`Conclusion`** + **`plan-lint`** |
| Task-ID placeholder | `[SLUG-NNN]` 실값 — `[XXX-001]`·`[TBD]` 금지 |
| Labels `plan` / `docs` | **`Improvement`** / alias `tooling` — active root **`docs` FAIL** |
| Target 디렉터리 | **파일 1개** — Impact Scope SSOT |
| Pre-read 마커 | **`just plan-preread … --write`** — `docs/plans/` Target fallback |
| Goal 줄바꿈 | **한 줄** — `` `## …` `` 헤딩·continuation line **금지** |

---

## Conclusion 게이트

| Status | Conclusion |
| :--- | :--- |
| `todo` / `running` | CSF 슬롯만 (`[판정 — …]` 등) |
| `done` | 실측 1줄 + Verify exit 0 근거 (플레이스홀더 **금지**) |
| `blocked` | 막힌 이유 1줄 |

**금지**: Conclusion에 마크다운 표(`|`) · 에디터로 Status/Conclusion 직접 수정

---

## Linear

| 유형 | 절차 |
| :--- | :--- |
| 제품 기능 | `python3 scripts/linear_sync/ensure_plan_linear.py <path>` — 하드코딩 ID **금지** |
| 내부 tooling | `Linear-Policy: internal` + `Linear-Issue: N/A` |

---

## Strategic rules (요약)

- **OHT**: 복수 가설 → **별도** `PLAN_*.md` — 한 파일에 옵션 분기 Task 체인 금지
- **Zero-Choice**: 실행 중 AskQuestion 분기 금지 — Decision Gate는 **작성 전**만
- **No Optional Tasks**: `(선택)` / `(Optional)` Task 제목 **금지**
- **Target SSOT**: Task 실행 전 `Target` 경로 실존 확인 — phantom path → `blocked`
- **Epic split**: `PLAN_epic_` 또는 거시 Task → 하위 Blueprint로 분해

---

## Edge Case Trace 체크리스트

해당 시 표에 행 추가: 빈 입력·null·경계값 · API 실패·타임아웃 · 동시성 · UI 빈/오류/로딩 · 권한·세션 · 오프라인 · 시드 없음 — [code_quality_lifecycle.md](../../../core/code_quality_lifecycle.md) §2 I-4.
