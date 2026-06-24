import unittest
from pathlib import Path

from scripts.plan_loop.plan_lint import lint_plan_text
from scripts.plan_loop.tests.test_blueprint_governance import _minimal_blueprint_body


def _placeholder_fixture(*, task_id: str, goal: str, diagnosis: str = "- **현상**: x") -> str:
    """Contract-valid blueprint focused on placeholder detection."""
    return f"""<!-- Language: ko -->

# 🗺️ Project Blueprint: placeholder 테스트

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

<!-- plan-preread:v1 generated=2026-01-01T00:00:00Z paths=0 must_read_installed=0 -->

### Read SSOT

### 재검증 (구현 세션에서 편집 전)

```bash
just route -- --json
```

## 🔍 Diagnosis & Findings

{diagnosis}

## 🏗️ Architectural Deepening

- **Seam**: x

## 📜 Conceptual Sketch

sketch

## 🛡️ Risk & Strategy

- **Risk**: x — **Strategy**: y

## 🔍 Impact Scope

| f | r |
| :--- | :--- |
| a | b |

## 🛠️ Step-by-Step Execution Plan

#### Task 1.1: Fix [Unit: Atomic]
- Task-ID: {task_id} | Linear-Issue: N/A | Status: todo | RetryPolicy: none
- **Pre-read**: 이 Task만 Read <!-- plan-task-preread:v1 paths=0 must_read_installed=0 -->
- **Action**: Edit
- **Target**: file.py
- **Goal**: {goal}
- **Diagnostics**: 0
- **Verify**: `just lint`
- **Conclusion**: [판정 — 비개발자용 요약. 검증 결과]
- **Dependency**: None

## 🔁 Conclusion & Summary

- **Roll-up**: ok

## ✅ Definition of Done (DoD)

- `just lint`
"""


_ARCHIVE_PATH = Path("docs/plans/archive/PLAN_placeholder_test.md")


class TestPlaceholderDetectionWithTaskIDs(unittest.TestCase):
    """Test that Task ID patterns like [PLAN-001] are NOT flagged as placeholders."""

    def test_plan_reference_not_flagged_as_placeholder(self):
        """[PLAN-001] should pass — it's a valid Task ID reference."""
        content = _placeholder_fixture(
            task_id="[LINT-001]",
            goal="placeholder detection 오탐을 수정한다",
        )
        issues, _warnings = lint_plan_text(content, file_path=_ARCHIVE_PATH)
        # Should NOT have placeholder errors for [PLAN-001] or [LINT-001]
        self.assertFalse(
            any("placeholder" in issue.lower() for issue in issues),
            f"Task ID [LINT-001] should not be flagged as placeholder. Issues: {issues}"
        )

    def test_plan_link_in_goal_not_flagged(self):
        """[PLAN-001] in Goal should pass — it's a reference, not a placeholder."""
        content = _placeholder_fixture(
            task_id="[LINT-002]",
            goal="[PLAN-001]에 기술된 이슈를 참고하여 placeholder 오탐을 수정한다",
            diagnosis="- **현상**: [PLAN-001] 참조 맥락",
        )
        issues, _warnings = lint_plan_text(content, file_path=_ARCHIVE_PATH)
        # Should NOT have placeholder errors
        self.assertFalse(
            any("placeholder" in issue.lower() for issue in issues),
            f"[PLAN-001] reference should not be flagged. Issues: {issues}"
        )

    def test_various_task_id_formats_not_flagged(self):
        """Test various Task ID formats are not flagged."""
        test_cases = [
            "[PLAN-001]",
            "[LINT-001]",
            "[TEM-001]",
            "[OBP-001]",
            "[RDP-001]",
            "[ABC-123]",
            "[XYZ-9999]",
        ]

        for task_id in test_cases:
            content = _placeholder_fixture(
                task_id=task_id,
                goal="다양한 Task-ID 형식이 placeholder로 오탐되지 않는지 검증한다",
            )
            issues, _warnings = lint_plan_text(content, file_path=_ARCHIVE_PATH)
            self.assertFalse(
                any("placeholder" in issue.lower() for issue in issues),
                f"Task ID {task_id} should not be flagged as placeholder. Issues: {issues}"
            )

    def test_actual_placeholder_still_detected(self):
        """[TBD] should still be flagged as placeholder."""
        content = """<!-- Language: ko -->
# 🗺️ Project Blueprint: 테스트 계획서
## 문서 메타
- **SSOT Check**: [TBD]
- **Project Status Link**: ok
- **Architectural Goal**: ok
- **Priority**: 3
- **Labels**: Test
- **Linear-Issue**: TEM-XXX

## 📋 업무 요약 (협업용)
### 개요
테스트

### staff·경영에서 바뀌는 점
테스트

### 끝났을 때 확인할 것
테스트

## 🧭 Context Pre-read Gate (실행 전 필수)
<!-- plan-preread:v1 generated=2026-01-01T00:00:00Z paths=0 must_read_installed=0 -->

### Read SSOT

### 재검증 (구현 세션에서 편집 전)
```bash
just route -- --json
```

## 🔍 Diagnosis & Findings
...

## 🏗️ Architectural Deepening
...

## 📜 Conceptual Sketch
...

## 🛡️ Risk & Strategy
- **Risk**: x | **Strategy**: y

## 🔍 Impact Scope
||| f | 1 | r | n |

## 🛠️ Step-by-Step Execution Plan
#### Task 1.1: Test [Unit: Atomic]
- Task-ID: [LINT-003] | Status: todo | RetryPolicy: none
- **Pre-read**: 이 Task 만 — `write`/`patch` 전 **전부** Read <!-- plan-task-preread:v1 paths=0 must_read_installed=0 -->
- Action: Edit
- Target: file.py
- Goal: test
- Diagnostics: none
- Verify: just lint
- Conclusion: done
- Dependency: None

## 🔁 Conclusion & Summary
- Roll-up: ok
- Continuity: ok

## ✅ Definition of Done (DoD)
1. Done.
"""
        issues, _warnings = lint_plan_text(content)
        # [TBD] is in doc meta, not task field - check for missing/empty error
        self.assertTrue(
            any("placeholder" in issue.lower() or "missing/empty" in issue.lower() for issue in issues),
            f"[TBD] should still be flagged as placeholder. Issues: {issues}"
        )

    def test_template_task_id_xxx_fails_lint(self):
        """[XXX-001] is regex-valid but must FAIL as template placeholder."""
        content = _minimal_blueprint_body(with_contract=True, with_scope=True).replace(
            "[TST-001]", "[XXX-001]"
        )
        issues, _warnings = lint_plan_text(content)
        self.assertTrue(
            any("template placeholder" in issue and "XXX" in issue for issue in issues),
            f"Expected template Task-ID FAIL. Issues: {issues}",
        )


class TestRollupSummaryPlaceholder(unittest.TestCase):
    """Roll-up section placeholder detection (closeout Task done + plan-close gate)."""

    _BLUEPRINT_PREFIX = """
# 🗺️ Project Blueprint: Roll-up 테스트
## 문서 메타
- SSOT Check: ok
- Project Status Link: ok
- Architectural Goal: ok

## 🔍 Diagnosis & Findings
Symptoms...

## 🏗️ Architectural Deepening
Deepening...

## 📜 Conceptual Sketch
Sketch...

## 🛡️ Risk & Strategy
- **Risk**: x | **Strategy**: y

## 🔍 Impact Scope
| f | r |

## 🛠️ Step-by-Step Execution Plan
#### Task 1.1: 구현 [Unit: Atomic]
- Task-ID: [RUP-001] | Status: done | RetryPolicy: none
- **Pre-read**: paths <!-- plan-task-preread:v1 paths=1 must_read_installed=1 -->
  1. `[rule]` `agents/core/execution.md`
- Action: Edit
- Target: file.py
- Goal: 구현 완료
- Diagnostics: 0
- Verify: just lint
- Conclusion: [PASS] done [closed-by:plan-task-close]
- Dependency: None

### Phase 2 — Blueprint closeout
#### Task 2.1: Roll-up [Unit: Atomic]
- Task-ID: [RUP-099] | Status: {closeout_status} | RetryPolicy: none
- **Pre-read**: paths <!-- plan-task-preread:v1 paths=1 must_read_installed=1 -->
  1. `[rule]` `agents/workflows/plan.md`
- Action: Document
- Target: docs/plans/PLAN_rollup_test.md
- Goal: Roll-up 1문단 작성 후 plan-close로 검증한다.
- Diagnostics: 0
- Verify: `just plan-close plan=docs/plans/PLAN_rollup_test.md`
- Conclusion: {closeout_conclusion}
- Dependency: RUP-001

## 🔁 Conclusion & Summary

{rollup_body}

## ✅ Definition of Done (DoD)
- `just lint`
"""

    def test_closeout_done_with_placeholder_rollup_fails_lint(self):
        content = self._BLUEPRINT_PREFIX.format(
            closeout_status="done",
            closeout_conclusion="[PASS] roll-up done [closed-by:plan-task-close]",
            rollup_body="(Roll-up: Task 2.1 closeout 후 기입.)",
        )
        issues, _warnings = lint_plan_text(content)
        self.assertTrue(
            any("Roll-up is still a placeholder" in issue for issue in issues),
            f"Expected rollup placeholder lint FAIL. Issues: {issues}",
        )

    def test_closeout_todo_with_placeholder_rollup_passes_lint(self):
        content = self._BLUEPRINT_PREFIX.format(
            closeout_status="todo",
            closeout_conclusion="[판정 — 비개발자용 요약. 검증 결과]",
            rollup_body="(Roll-up: Task 2.1 closeout 후 기입.)",
        )
        issues, _warnings = lint_plan_text(content)
        self.assertFalse(
            any("Roll-up is still a placeholder" in issue for issue in issues),
            f"Mid-plan placeholder should not FAIL lint. Issues: {issues}",
        )

    def test_filled_rollup_passes_lint_when_closeout_done(self):
        content = self._BLUEPRINT_PREFIX.format(
            closeout_status="done",
            closeout_conclusion="[PASS] roll-up done [closed-by:plan-task-close]",
            rollup_body=(
                "Child 플랜 완료: baseline 16건을 0으로 줄였고 "
                "test-coupling-gate·ddd-gate가 PASS입니다."
            ),
        )
        issues, _warnings = lint_plan_text(content)
        self.assertFalse(
            any("Roll-up is still a placeholder" in issue for issue in issues),
            f"Filled rollup should PASS. Issues: {issues}",
        )


if __name__ == "__main__":
    unittest.main()
