"""Tests for design/narrative natural-language zone lint (backtick/path bans)."""

from __future__ import annotations

from scripts.plan_loop.plan_lint import lint_plan_text
from scripts.plan_loop.plan_lint.quality import _lint_goal_format, _lint_task_goal_block
from scripts.plan_loop.plan_lint.structural import _lint_design_natural_language_zones
from scripts.plan_loop.tests.test_blueprint_governance import _minimal_blueprint_body


def _body_with_origin_intent(origin_block: str) -> str:
    base = _minimal_blueprint_body(with_contract=False, with_scope=False)
    insert_at = base.index("## 🔍 Diagnosis & Findings")
    origin = f"## 🎯 Origin Intent\n\n{origin_block}\n\n"
    return base[:insert_at] + origin + base[insert_at:]


def test_origin_intent_backtick_fails() -> None:
    content = _body_with_origin_intent("- **원래 목적**: `just plan-lint` 통과\n")
    issues = _lint_design_natural_language_zones(content)
    assert any("Origin Intent" in issue and "backtick" in issue for issue in issues)


def test_diagnosis_backtick_fails() -> None:
    content = _minimal_blueprint_body(with_contract=False, with_scope=False).replace(
        "- **현상**: x",
        "- **현상**: `{{FRONTEND_APP_PATH}}` 오류",
    )
    issues = _lint_design_natural_language_zones(content)
    assert any("Diagnosis" in issue for issue in issues)


def test_edge_case_trace_plain_table_passes() -> None:
    content = _body_with_origin_intent(
        "## ⚠️ Edge Case Trace\n\n"
        "| 엣지 | 출처 | Task-ID | 비고 |\n"
        "| :--- | :--- | :--- | :--- |\n"
        "| 빈 목록 | Origin | TST-002 | |\n"
    )
    # Edge section is separate — build properly
    base = _minimal_blueprint_body(with_contract=False, with_scope=False)
    insert_at = base.index("## 🔍 Diagnosis & Findings")
    block = (
        "## 🎯 Origin Intent\n\n- 목적: 테스트\n\n"
        "## ⚠️ Edge Case Trace\n\n"
        "| 엣지 | 출처 | Task-ID | 비고 |\n"
        "| :--- | :--- | :--- | :--- |\n"
        "| 빈 목록 | Origin | TST-002 | |\n\n"
    )
    content = base[:insert_at] + block + base[insert_at:]
    issues = _lint_design_natural_language_zones(content)
    assert not any("Edge Case Trace" in issue for issue in issues)


def test_goal_multiline_fails() -> None:
    goal = "선행 Task Conclusion을 근거로\n`## 🔁 Conclusion & Summary` Roll-up 작성"
    issues = _lint_goal_format(1, goal)
    assert any("single line" in issue for issue in issues)


def test_goal_single_line_closeout_passes() -> None:
    goal = (
        "선행 Task Conclusion을 근거로 Conclusion and Summary Roll-up 1문단을 "
        "실측으로 작성한다."
    )
    assert _lint_goal_format(9, goal) == []


def test_goal_multiline_fails_lint_integration() -> None:
    content = _minimal_blueprint_body(with_contract=True, with_scope=True)
    content = content.replace(
        "- **Goal**: fix",
        "- **Goal**: 선행 Task Conclusion을 근거로\n`## 🔁 Conclusion & Summary` Roll-up 작성",
    )
    issues, _warnings = lint_plan_text(content)
    assert any("Goal must be a single line" in issue for issue in issues)
