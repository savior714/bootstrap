"""Tests for blueprint quality gates (--check-quality)."""

from __future__ import annotations

import unittest

from scripts.plan_loop.plan_lint.blueprint_quality import (
    lint_blueprint_quality_gates,
    lint_execution_order_dependency_sync,
    lint_verify_test_pairing,
    parse_execution_order_table,
    parse_task_dependency_map,
)


def _minimal_blueprint(
    *,
    execution_rows: str,
    task_blocks: str,
    dod_lines: str = "- `just lint`",
) -> str:
    return f"""<!-- Language: ko -->

# 🗺️ Project Blueprint: 품질 게이트 테스트

## 문서 메타
- **SSOT Check**: ok
- **Project Status Link**: ok
- **Architectural Goal**: ok
- **Priority**: 2
- **Labels**: Improvement
- **Linear-Issue**: TEM-XXX
- **Linear-Policy**: internal

## 📎 관련 명세

| 문서 | 범위 |
| :--- | :--- |
| `docs/specs/ui/SPEC_ui_test.md` | test |

## 📋 업무 요약 (협업용)

### 개요

테스트.

### staff·경영에서 바뀌는 점

- 없음

### 끝났을 때 확인할 것

- 없음

## 🎯 Origin Intent

- **출처**: test
- **원래 목적**: test
- **완료 관찰**: test

## ⚠️ Edge Case Trace

| 엣지 케이스 | 출처 | Task-ID / 범위 밖 | 비고 |
| :--- | :--- | :--- | :--- |
| 없음 | test | 범위 밖 | — |

## 🔍 Diagnosis & Findings

- **현상**: x

## 🏗️ Architectural Deepening

- **Seam**: x

## 📜 Conceptual Sketch

```
sketch
```

## 🛡️ Risk & Strategy

- **Risk**: x — **Strategy**: y

## Agent Execution Pack

> Execute pack.

## 🔍 Impact Scope

| f | r |
| :--- | :--- |
| a | b |

## 실행 순서·선행

| 순서 | Task-ID | 왜 | 선행 | 산출 | 병렬 |
| :---: | :--- | :--- | :--- | :--- | :---: |
{execution_rows}

## Agent Completion Contract

| 허용 | 금지 |
| :--- | :--- |
| close | edit |

## 🛠️ Step-by-Step Execution Plan

> **에이전트 스코프**: Verify PASS → Conclusion → plan-task-close → plan-lint

{task_blocks}

## 🔁 Conclusion & Summary

- **Roll-up**: pending

## ✅ Definition of Done (DoD)

{dod_lines}
"""


class TestExecutionOrderParsing(unittest.TestCase):
    def test_parse_table_and_task_deps(self):
        text = _minimal_blueprint(
            execution_rows="| 1 | QLT-001 | why | None | out | — |",
            task_blocks="""
#### Task 1.1: One [Unit: Atomic]
- Task-ID: [QLT-001] | Status: todo | RetryPolicy: none
- **Pre-read**: x
- **Action**: Edit | **Target**: `a.py`
- **Goal**: change export in a.py
- **Diagnostics**: edge trace maps here
- **Verify**: `just lint`
- **Conclusion**: [판정 — 비개발자용 요약. 검증 결과]
- **Dependency**: None
""",
        )
        table = parse_execution_order_table(text)
        self.assertEqual(table["QLT-001"]["predecessors"], set())
        self.assertEqual(parse_task_dependency_map(text)["QLT-001"], set())


class TestQualityGateDepsSync(unittest.TestCase):
    def test_mismatch_fails(self):
        text = _minimal_blueprint(
            execution_rows="| 1 | QLT-001 | why | None | out | — |\n| 2 | QLT-002 | why | QLT-001 | out | — |",
            task_blocks="""
#### Task 1.1: First [Unit: Atomic]
- Task-ID: [QLT-001] | Status: todo | RetryPolicy: none
- **Pre-read**: x
- **Action**: Edit | **Target**: `a.py`
- **Goal**: change export in a.py
- **Diagnostics**: first task
- **Verify**: `just lint`
- **Conclusion**: [판정 — 비개발자용 요약. 검증 결과]
- **Dependency**: None

#### Task 1.2: Second [Unit: Atomic]
- Task-ID: [QLT-002] | Status: todo | RetryPolicy: none
- **Pre-read**: x
- **Action**: Edit | **Target**: `b.py`
- **Goal**: change export in b.py
- **Diagnostics**: depends on wrong id
- **Verify**: `just lint`
- **Conclusion**: [판정 — 비개발자용 요약. 검증 결과]
- **Dependency**: QLT-001
""",
        )
        # Table says QLT-002 depends QLT-001 — matches. Now break order.
        text_bad = text.replace(
            "| 2 | QLT-002 | why | QLT-001 | out | — |",
            "| 2 | QLT-002 | why | None | out | — |",
        )
        issues = lint_execution_order_dependency_sync(text_bad)
        self.assertTrue(any("QLT-002" in issue and "≠ Dependency" in issue for issue in issues))

    def test_order_inversion_fails(self):
        text = _minimal_blueprint(
            execution_rows="| 1 | QLT-002 | why | QLT-001 | out | — |\n| 2 | QLT-001 | why | None | out | — |",
            task_blocks="""
#### Task 1.1: First [Unit: Atomic]
- Task-ID: [QLT-001] | Status: todo | RetryPolicy: none
- **Pre-read**: x
- **Action**: Edit | **Target**: `a.py`
- **Goal**: change export in a.py
- **Diagnostics**: first
- **Verify**: `just lint`
- **Conclusion**: [판정 — 비개발자용 요약. 검증 결과]
- **Dependency**: None

#### Task 1.2: Second [Unit: Atomic]
- Task-ID: [QLT-002] | Status: todo | RetryPolicy: none
- **Pre-read**: x
- **Action**: Edit | **Target**: `b.py`
- **Goal**: change export in b.py
- **Diagnostics**: second
- **Verify**: `just lint`
- **Conclusion**: [판정 — 비개발자용 요약. 검증 결과]
- **Dependency**: QLT-001
""",
        )
        issues = lint_execution_order_dependency_sync(text)
        self.assertTrue(any("order 1 must be after" in issue for issue in issues))


class TestVerifyTestPairing(unittest.TestCase):
    def test_ser_recipe_matches_test_target(self):
        text = _minimal_blueprint(
            execution_rows="| 1 | QLT-001 | why | None | out | — |",
            task_blocks="""
#### Task 1.1: RED [Unit: Atomic]
- Task-ID: [QLT-001] | Status: todo | RetryPolicy: none
- **Pre-read**: x
- **Action**: Edit | **Target**: `{{FRONTEND_APP_PATH}}/tests/unit/app/dashboard/useDashboardServerSession.transient-cap.test.ts`
- **Goal**: write transient cap red test in useDashboardServerSession.transient-cap.test.ts
- **Diagnostics**: red first
- **Verify**: `just renderer-vitest-ser-transient-cap`
- **Conclusion**: [판정 — 비개발자용 요약. 검증 결과]
- **Dependency**: None
""",
        )
        issues = lint_verify_test_pairing(text)
        self.assertEqual(issues, [])


class TestLintBlueprintQualityIntegration(unittest.TestCase):
    def test_warn_on_dod_gap(self):
        text = _minimal_blueprint(
            execution_rows="| 1 | QLT-001 | why | None | out | — |",
            task_blocks="""
#### Task 1.1: RED [Unit: Atomic]
- Task-ID: [QLT-001] | Status: todo | RetryPolicy: none
- **Pre-read**: x
- **Action**: Edit | **Target**: `{{FRONTEND_APP_PATH}}/tests/unit/app/dashboard/useDashboardServerSession.transient-cap.test.ts`
- **Goal**: write transient cap red test in useDashboardServerSession.transient-cap.test.ts
- **Diagnostics**: red first
- **Verify**: `just renderer-vitest-ser-transient-cap`
- **Conclusion**: [판정 — 비개발자용 요약. 검증 결과]
- **Dependency**: None
""",
            dod_lines="- `just lint`",
        )
        issues, warnings = lint_blueprint_quality_gates(text)
        self.assertEqual(issues, [])
        self.assertTrue(any("Quality #10" in w for w in warnings))
