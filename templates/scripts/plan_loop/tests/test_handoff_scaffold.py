"""Tests for hand-off parser and blueprint scaffold."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

from scripts.plan_loop.handoff_parser import (
    derive_task_prefix,
    extract_bounded_scope_paths,
    extract_dod_commands,
    extract_recommended_phases,
    parse_handoff_markdown,
    pick_target_for_phase,
)
from scripts.plan_loop.plan_lint.linter import lint_plan_text
from scripts.plan_loop.scaffold_blueprint_from_handoff import render_blueprint_markdown

_FIXTURE = Path(__file__).parent / "fixtures" / "handoff_sample.md"
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


class TestHandoffParser(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = _FIXTURE.read_text(encoding="utf-8")

    def test_bounded_scope_paths(self) -> None:
        paths = extract_bounded_scope_paths(self.text)
        self.assertIn("docs/specs/business/SPEC_biz_sample.md", paths)
        self.assertIn("tests/api/v1/test_sample_scope.py", paths)
        self.assertTrue(all(not p.endswith("/") for p in paths))

    def test_recommended_phases(self) -> None:
        phases = extract_recommended_phases(self.text)
        self.assertGreaterEqual(len(phases), 3)
        self.assertTrue(any("스펙" in p for p in phases))

    def test_dod_commands(self) -> None:
        cmds = extract_dod_commands(self.text)
        self.assertTrue(any("pytest" in c for c in cmds))
        self.assertTrue(any("lint-turn-end" in c for c in cmds))

    def test_derive_prefix_override(self) -> None:
        self.assertEqual(derive_task_prefix("order_set_scope", override="ORDS"), "ORDS")

    def test_pick_target_for_phase(self) -> None:
        paths = extract_bounded_scope_paths(self.text)
        self.assertEqual(
            pick_target_for_phase("스펙 갱신", paths),
            "docs/specs/business/SPEC_biz_sample.md",
        )


class TestScaffoldBlueprint(unittest.TestCase):
    def test_render_contains_required_sections(self) -> None:
        parsed = parse_handoff_markdown(_FIXTURE.read_text(encoding="utf-8"), slug="sample_hardening")
        body = render_blueprint_markdown(slug="sample_hardening", parsed=parsed, prefix="SAMP")
        self.assertIn("## Agent Execution Pack", body)
        self.assertIn("[SAMP-098]", body)
        self.assertIn("[SAMP-099]", body)
        self.assertIn("docs/specs/business/SPEC_biz_sample.md", body)

    def test_scaffold_contract_lint_passes_after_preread(self) -> None:
        parsed = parse_handoff_markdown(_FIXTURE.read_text(encoding="utf-8"), slug="sample_hardening")
        body = render_blueprint_markdown(slug="sample_hardening", parsed=parsed, prefix="SAMP")
        plan_path = _REPO_ROOT / "docs/plans/PLAN_sample_hardening_scaffold_test.md"
        plan_path.write_text(body, encoding="utf-8")
        try:
            preread = subprocess.run(
                [
                    sys.executable,
                    "scripts/plan_loop/plan_preread_manifest.py",
                    str(plan_path.relative_to(_REPO_ROOT)),
                    "--write",
                ],
                capture_output=True,
                text=True,
                cwd=_REPO_ROOT,
            )
            self.assertEqual(preread.returncode, 0, msg=preread.stderr + preread.stdout)
            refreshed = plan_path.read_text(encoding="utf-8")
            issues, _warnings = lint_plan_text(
                refreshed,
                file_path=plan_path,
            )
            self.assertEqual(issues, [], msg="\n".join(issues))
        finally:
            plan_path.unlink(missing_ok=True)


class TestJustfileRecipeExpansion(unittest.TestCase):
    def test_expand_follows_nested_just_calls(self) -> None:
        from scripts.plan_loop.plan_lint.justfile_recipes import expand_just_recipe_names

        expanded = expand_just_recipe_names({"lint-fe"})
        self.assertIn("lint-fe", expanded)
        self.assertTrue(len(expanded) >= 1)


class TestPlanLintQualityCli(unittest.TestCase):
    def test_help_lists_check_quality(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "scripts.plan_loop.plan_lint", "--help"],
            capture_output=True,
            text=True,
            cwd=_REPO_ROOT,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("--check-quality", result.stdout)

    def test_check_quality_runs_on_minimal_blueprint(self) -> None:
        from scripts.plan_loop.tests.test_plan_lint_blueprint_quality import _minimal_blueprint

        text = _minimal_blueprint(
            execution_rows="| 1 | QLT-001 | why | None | out | — |",
            task_blocks="""
#### Task 1.1: One [Unit: Atomic]
- Task-ID: [QLT-001] | Status: todo | RetryPolicy: none
- **Pre-read**: x
- **Action**: Edit | **Target**: `a.py`
- **Goal**: change export in a.py
- **Diagnostics**: edge
- **Verify**: `just lint`
- **Conclusion**: [판정 — 비개발자용 요약. 검증 결과]
- **Dependency**: None
""",
        )
        issues, warnings = lint_plan_text(text, check_quality=True)
        self.assertIsInstance(issues, list)
        self.assertIsInstance(warnings, list)


if __name__ == "__main__":
    unittest.main()
