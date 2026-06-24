"""Contract vs strict tier regression tests for plan-lint."""

from __future__ import annotations

import unittest
from pathlib import Path

from scripts.plan_loop.plan_lint import lint_plan_text


def _goal_conjunction_fixture() -> str:
    """Minimal blueprint with forbidden Goal conjunction (및)."""
    return """<!-- Language: ko -->

# 🗺️ Project Blueprint: tier 계약 테스트

## 문서 메타
- **SSOT Check**: ok
- **Project Status Link**: ok
- **Architectural Goal**: ok
- **Linear-Policy**: internal
- **Linear-Issue**: N/A
- **Priority**: 1
- **Labels**: Improvement

## 📋 업무 요약 (협업용)

### 개요

테스트.

### staff·경영에서 바뀌는 점

- 없음

### 끝났을 때 확인할 것

- 없음

## 🧭 Context Pre-read Gate (실행 전 필수)

<!-- plan-preread:v1 generated=2026-06-01T00:00:00Z paths=0 must_read_installed=0 -->

### Read SSOT

### 재검증 (구현 세션에서 편집 전)

```bash
just route -- --json
```

## 🔍 Diagnosis & Findings

- **현상**: tier 분기 검증

## 🏗️ Architectural Deepening

- **Seam**: linter.py

## 📜 Conceptual Sketch

```text
contract vs strict
```

## 🛡️ Risk & Strategy

- **Risk**: x — **Strategy**: y

## 🔍 Impact Scope

| 영역 | 경로 |
| :--- | :--- |
| linter | scripts/plan_loop/plan_lint/linter.py |

## 🛠️ Step-by-Step Execution Plan

#### Task 1.1: Tier test [Unit: Atomic]
- Task-ID: [TIER-001] | Linear-Issue: N/A | Status: todo | RetryPolicy: none
- **Pre-read**: 이 Task만 Read <!-- plan-task-preread:v1 paths=0 must_read_installed=0 -->
- **Action**: Edit
- **Target**: scripts/plan_loop/plan_lint/linter.py
- **Goal**: Goal 접속사 및 conjunction 검사 tier 분기를 검증한다
- **Diagnostics**: 0
- **Verify**: `just lint`
- **Conclusion**: [판정 — 비개발자용 요약. 검증 결과]
- **Dependency**: None

## 🔁 Conclusion & Summary

- **Roll-up**: ok

## ✅ Definition of Done (DoD)

- `just lint`
"""


class TestPlanLintTierContract(unittest.TestCase):
    def test_contract_mode_ignores_goal_conjunction(self) -> None:
        path = Path("docs/plans/archive/PLAN_tier_contract_test.md")
        issues, _warnings = lint_plan_text(
            _goal_conjunction_fixture(),
            file_path=path,
            check_strict=False,
        )
        conjunction_issues = [
            i for i in issues if "forbidden conjunction" in i or "및" in i
        ]
        self.assertEqual(conjunction_issues, [], issues)

    def test_strict_mode_fails_goal_conjunction(self) -> None:
        path = Path("docs/plans/archive/PLAN_tier_contract_test.md")
        issues, _warnings = lint_plan_text(
            _goal_conjunction_fixture(),
            file_path=path,
            check_strict=True,
        )
        self.assertTrue(
            any("forbidden conjunction" in i for i in issues),
            issues,
        )


if __name__ == "__main__":
    unittest.main()
