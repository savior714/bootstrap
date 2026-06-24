"""Tests for plan-lint implementation review task (-098) guards."""

from __future__ import annotations

import unittest
from pathlib import Path

from scripts.plan_loop.plan_lint import lint_plan_text
from scripts.plan_loop.plan_lint.recurrence import lint_active_blueprint_recurrence_guards
from scripts.plan_loop.plan_lint.verification import lint_implementation_review_task_contract


def _review_preread() -> str:
    return """- **Pre-read**: 이 Task만 — `write`/`patch` 전 **전부** Read
  1. `[project_skill]` `agents/skills/review/SKILL.md`
  2. `[spec]` `agents/skills/plan/references/handoff-from-execute-to-review.md`
  3. `[spec]` `docs/plans/PLAN_review_test.md`
  4. `[rule]` `agents/core/error_patterns/detail/editing.md`"""


def _body(*, with_review: bool = False, code_target: str = "{{FRONTEND_APP_PATH}}/src/Foo.tsx") -> str:
    review_phase = ""
    review_task = ""
    if with_review:
        review_phase = f"""
### Phase 8 — Implementation review

#### Task 8.8: Implementation Review 작성 [Unit: Atomic]
- Task-ID: [REV-098] | Status: todo | RetryPolicy: none
{_review_preread()}
- **Action**: Edit
- **Target**: docs/plans/PLAN_review_test.md
- **Goal**: review/SKILL workflow로 Findings를 작성하고 Implementation Review 절을 채운다.
- **Diagnostics**: 0
- **Verify**: `just plan-review-gate plan=docs/plans/PLAN_review_test.md`
- **Conclusion**: [판정 — 비개발자용 요약. 검증 결과]
- **Dependency**: REV-001
"""
    impl_task = ""
    if code_target:
        impl_task = f"""
#### Task 1.1: Fix module [Unit: Atomic]
- Task-ID: [REV-001] | Status: todo | RetryPolicy: none
- **Pre-read**: none
- **Action**: Edit
- **Target**: `{code_target}`
- **Goal**: fix the module export
- **Diagnostics**: 0
- **Verify**: `just plan-lint docs/plans/PLAN_review_test.md`
- **Conclusion**: [판정 — 비개발자용 요약. 검증 결과]
- **Dependency**: None
"""
    return f"""<!-- Language: ko -->

# 🗺️ Project Blueprint: Review Task 테스트

## 문서 메타
- **SSOT Check**: ok
- **Project Status Link**: ok
- **Architectural Goal**: ok
- **Linear-Issue**: TEM-999

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

Pack.

## 🔍 Impact Scope

| f | r |
| :--- | :--- |
| a | b |

## Agent Completion Contract

| 허용 | 금지 |
| :--- | :--- |
| plan-task-close | 직접 수정 |

## 🛠️ Step-by-Step Execution Plan

{impl_task}
{review_phase}
#### Task 9.9: Closeout [Unit: Atomic]
- Task-ID: [REV-099] | Status: todo | RetryPolicy: none
- **Pre-read**: none
- **Action**: Edit
- **Target**: docs/plans/PLAN_review_test.md
- **Goal**: Roll-up 작성
- **Diagnostics**: 0
- **Verify**: `just plan-close plan=docs/plans/PLAN_review_test.md`
- **Conclusion**: [판정 — 비개발자용 요약. 검증 결과]
- **Dependency**: REV-098

## 🔍 Implementation Review

- **High**: none
- **Medium**: none
- **Low**: placeholder for lint only — twenty-five chars minimum here

## 🔁 Conclusion & Summary

- **Roll-up**: pending

## ✅ Definition of Done (DoD)

- `just plan-lint docs/plans/PLAN_review_test.md`
"""


class TestPlanLintReviewTask(unittest.TestCase):
    def test_code_target_without_review_task_fails(self):
        body = _body(with_review=False)
        path = Path("docs/plans/PLAN_review_test.md")
        issues = lint_active_blueprint_recurrence_guards(body, path)
        self.assertTrue(
            any("missing review task" in i.lower() or "Task-ID [*-098]" in i for i in issues),
            issues,
        )

    def test_code_target_with_review_task_passes_recurrence(self):
        body = _body(with_review=True)
        path = Path("docs/plans/PLAN_review_test.md")
        issues = lint_active_blueprint_recurrence_guards(body, path)
        review_issues = [
            i
            for i in issues
            if "review task" in i.lower() or "implementation review" in i.lower()
        ]
        self.assertEqual(review_issues, [], issues)

    def test_docs_only_plan_without_review_passes(self):
        body = _body(with_review=False, code_target="docs/plans/PLAN_docs_only.md")
        path = Path("docs/plans/PLAN_review_test.md")
        issues = lint_active_blueprint_recurrence_guards(body, path)
        review_issues = [
            i
            for i in issues
            if "review task" in i.lower() or "Task-ID [*-098]" in i
        ]
        self.assertEqual(review_issues, [], issues)

    def test_review_task_without_review_skill_preread_fails(self):
        body = _body(with_review=True).replace(
            "`agents/skills/review/SKILL.md`",
            "`agents/skills/open-design-frontend/SKILL.md`",
        )
        issues = lint_implementation_review_task_contract(body)
        self.assertTrue(
            any("review/SKILL.md" in i for i in issues),
            issues,
        )


if __name__ == "__main__":
    unittest.main()
