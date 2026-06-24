import tempfile
import unittest
from pathlib import Path
import subprocess

from scripts.plan_loop.plan_task_close import close_task_in_markdown


class TestPlanTaskClose(unittest.TestCase):
    def _write_temp_plan(self, content: str) -> Path:
        tmp = tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8")
        tmp.write(content)
        tmp.close()
        return Path(tmp.name)

    def test_updates_only_target_task_block(self):
        plan = self._write_temp_plan(
            """# Test Blueprint

#### Task 1.1: First task [Unit: Atomic]
- Task-ID: TASK-001 | Status: todo | Priority: 1
- **Goal**: first
- **Conclusion**: [placeholder]
- **Dependency**: None

#### Task 1.2: Second task [Unit: Atomic]
- Task-ID: TASK-002 | Status: todo | Priority: 1
- **Goal**: second
- **Conclusion**: [placeholder]
- **Dependency**: TASK-001
"""
        )
        try:
            close_task_in_markdown(plan, "TASK-001", "[PASS] first task 완료. 검증 통과 확인.")
            updated = plan.read_text(encoding="utf-8")
        finally:
            plan.unlink(missing_ok=True)

        self.assertIn("- Task-ID: TASK-001 | Status: done | Priority: 1", updated)
        self.assertIn("- **Conclusion**: [PASS] first task 완료. 검증 통과 확인.", updated)
        self.assertIn("[closed-by:plan-task-close]", updated)
        self.assertIn("- Task-ID: TASK-002 | Status: todo | Priority: 1", updated)
        self.assertIn("#### Task 1.2: Second task [Unit: Atomic]", updated)
        self.assertIn("- **Conclusion**: [placeholder]", updated)

    def test_adds_blank_line_before_next_task_heading(self):
        plan = self._write_temp_plan(
            """# Test Blueprint

#### Task 1.1: First task [Unit: Atomic]
- Task-ID: TASK-001 | Status: todo | Priority: 1
- **Goal**: first
- **Conclusion**: [placeholder]
- **Dependency**: None
#### Task 1.2: Second task [Unit: Atomic]
- Task-ID: TASK-002 | Status: todo | Priority: 1
- **Goal**: second
- **Conclusion**: [placeholder]
- **Dependency**: TASK-001
"""
        )
        try:
            close_task_in_markdown(plan, "TASK-001", "[PASS] first task 완료. 검증 통과 확인.")
            updated = plan.read_text(encoding="utf-8")
        finally:
            plan.unlink(missing_ok=True)

        self.assertIn(
            "- **Dependency**: None\n\n#### Task 1.2: Second task [Unit: Atomic]",
            updated,
        )

    def test_duplicate_task_id_raises_system_exit(self):
        plan = self._write_temp_plan(
            """# Test Blueprint

#### Task 1.1: First task [Unit: Atomic]
- Task-ID: TASK-001 | Status: todo | Priority: 1
- **Goal**: first
- **Conclusion**: [placeholder]

#### Task 1.2: Duplicate task [Unit: Atomic]
- Task-ID: TASK-001 | Status: todo | Priority: 1
- **Goal**: dup
- **Conclusion**: [placeholder]
"""
        )
        try:
            with self.assertRaises(SystemExit):
                close_task_in_markdown(plan, "TASK-001", "[PASS] done")
        finally:
            plan.unlink(missing_ok=True)

    def test_cli_verify_failure_keeps_document_unchanged(self):
        plan = self._write_temp_plan(
            """# Test Blueprint

#### Task 1.1: First task [Unit: Atomic]
- Task-ID: TASK-001 | Status: todo | Priority: 1
- **Goal**: first
- **Conclusion**: [placeholder]
"""
        )
        script_path = Path(__file__).resolve().parents[1] / "plan_task_close.py"
        try:
            before = plan.read_text(encoding="utf-8")
            result = subprocess.run(
                [
                    "python3",
                    str(script_path),
                    "--plan",
                    str(plan),
                    "--task",
                    "TASK-001",
                    "--conclusion",
                    "[PASS] task done verification completed.",
                    "--verify-cmd",
                    "python3 -c \"raise SystemExit(1)\"",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            after = plan.read_text(encoding="utf-8")
        finally:
            plan.unlink(missing_ok=True)

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(before, after)

    def test_cli_verify_success_updates_document(self):
        plan = self._write_temp_plan(
            """# Test Blueprint

#### Task 1.1: First task [Unit: Atomic]
- Task-ID: TASK-001 | Status: todo | Priority: 1
- **Goal**: first
- **Conclusion**: [placeholder]
"""
        )
        script_path = Path(__file__).resolve().parents[1] / "plan_task_close.py"
        try:
            result = subprocess.run(
                [
                    "python3",
                    str(script_path),
                    "--plan",
                    str(plan),
                    "--task",
                    "TASK-001",
                    "--conclusion",
                    "[PASS] task done verification completed.",
                    "--verify-cmd",
                    "python3 -c \"raise SystemExit(0)\"",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            after = plan.read_text(encoding="utf-8")
        finally:
            plan.unlink(missing_ok=True)

        self.assertEqual(result.returncode, 0)
        self.assertIn("Status: done", after)
        self.assertIn("- **Conclusion**: [PASS] task done verification completed.", after)
        self.assertIn("[closed-by:plan-task-close]", after)


class TestConclusionValidation(unittest.TestCase):
    """close 시 부적합 Conclusion 거부 검증 (TEM-237 / CCV-001)."""

    def _write_temp_plan(self, content: str) -> Path:
        tmp = tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8")
        tmp.write(content)
        tmp.close()
        return Path(tmp.name)

    _PLAN_TEMPLATE = """\
# Test Blueprint

#### Task 1.1: First task [Unit: Atomic]
- Task-ID: TASK-001 | Status: todo | Priority: 1
- **Goal**: first
- **Conclusion**: [placeholder]
- **Dependency**: None
"""

    def test_thin_pattern_conclusion_rejected(self):
        """[PASS] 단독 Conclusion은 close 시 SystemExit으로 거부되어야 한다."""
        plan = self._write_temp_plan(self._PLAN_TEMPLATE)
        try:
            with self.assertRaises(SystemExit):
                close_task_in_markdown(plan, "TASK-001", "[PASS]")
            # 마크다운이 수정되지 않았는지 확인
            content = plan.read_text(encoding="utf-8")
            self.assertNotIn("Status: done", content)
        finally:
            plan.unlink(missing_ok=True)

    def test_short_conclusion_rejected(self):
        """25자 미만 짧은 Conclusion은 close 시 SystemExit으로 거부되어야 한다."""
        plan = self._write_temp_plan(self._PLAN_TEMPLATE)
        try:
            with self.assertRaises(SystemExit):
                close_task_in_markdown(plan, "TASK-001", "짧은 결론입니다")
            content = plan.read_text(encoding="utf-8")
            self.assertNotIn("Status: done", content)
        finally:
            plan.unlink(missing_ok=True)

    def test_placeholder_conclusion_rejected(self):
        """[TBD] placeholder Conclusion은 close 시 SystemExit으로 거부되어야 한다."""
        plan = self._write_temp_plan(self._PLAN_TEMPLATE)
        try:
            with self.assertRaises(SystemExit):
                close_task_in_markdown(plan, "TASK-001", "[TBD]")
            content = plan.read_text(encoding="utf-8")
            self.assertNotIn("Status: done", content)
        finally:
            plan.unlink(missing_ok=True)

    def test_valid_conclusion_accepted(self):
        """충분히 길고 구체적인 Conclusion은 정상 close되어야 한다."""
        plan = self._write_temp_plan(self._PLAN_TEMPLATE)
        try:
            close_task_in_markdown(
                plan, "TASK-001",
                "[PASS] Conclusion 품질 검증 게이트를 plan_task_close에 삽입했다. Verify pytest exit 0."
            )
            content = plan.read_text(encoding="utf-8")
            self.assertIn("Status: done", content)
        finally:
            plan.unlink(missing_ok=True)


class TestPlanTaskCloseHardening(unittest.TestCase):
    """plan-task-close 안전 강화 회귀 (PLAN_plan_task_close_hardening)."""

    def _write_temp_plan(self, content: str) -> Path:
        tmp = tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8")
        tmp.write(content)
        tmp.close()
        return Path(tmp.name)

    _VALID_CONCLUSION = (
        "[PASS] duplicate Task-ID close 거부 검증. Blueprint 미변경 확인. pytest exit 0."
    )

    def test_duplicate_task_id_close_rejected(self):
        plan = self._write_temp_plan(
            """# Test Blueprint

#### Task 1.1: First task [Unit: Atomic]
- Task-ID: TASK-001 | Status: todo | Priority: 1
- **Goal**: first
- **Conclusion**: [placeholder]

#### Task 1.2: Duplicate task [Unit: Atomic]
- Task-ID: TASK-001 | Status: todo | Priority: 1
- **Goal**: dup
- **Conclusion**: [placeholder]
"""
        )
        try:
            before = plan.read_text(encoding="utf-8")
            with self.assertRaises(SystemExit):
                close_task_in_markdown(plan, "TASK-001", self._VALID_CONCLUSION)
            after = plan.read_text(encoding="utf-8")
            self.assertEqual(before, after)
            self.assertNotIn("Status: done", after)
        finally:
            plan.unlink(missing_ok=True)

    def test_missing_conclusion_field_close_rejected(self):
        plan = self._write_temp_plan(
            """# Test Blueprint

#### Task 1.1: No conclusion field [Unit: Atomic]
- Task-ID: TASK-001 | Status: todo | Priority: 1
- **Goal**: first
- **Dependency**: None
"""
        )
        try:
            before = plan.read_text(encoding="utf-8")
            with self.assertRaises(SystemExit):
                close_task_in_markdown(
                    plan,
                    "TASK-001",
                    "[PASS] Conclusion 필드 없음 close 거부. Blueprint 미변경. pytest exit 0.",
                )
            after = plan.read_text(encoding="utf-8")
            self.assertEqual(before, after)
            self.assertNotIn("Status: done", after)
        finally:
            plan.unlink(missing_ok=True)

    def test_newline_conclusion_rejected(self):
        plan = self._write_temp_plan(
            """# Test Blueprint

#### Task 1.1: First task [Unit: Atomic]
- Task-ID: TASK-001 | Status: todo | Priority: 1
- **Goal**: first
- **Conclusion**: [placeholder]
"""
        )
        try:
            before = plan.read_text(encoding="utf-8")
            with self.assertRaises(SystemExit):
                close_task_in_markdown(
                    plan,
                    "TASK-001",
                    "[PASS] first line\nsecond line breaks blueprint structure.",
                )
            after = plan.read_text(encoding="utf-8")
            self.assertEqual(before, after)
            self.assertNotIn("Status: done", after)
        finally:
            plan.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
