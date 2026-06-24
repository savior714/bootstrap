import unittest

from scripts.plan_loop.plan_lint import TASK_ID_PATTERN
from scripts.plan_loop.plan_lint.shared import (
    extract_task_id_leading_prefix,
    is_template_task_id,
)


class TestTaskIDPatternRegex(unittest.TestCase):
    """Test TASK_ID_PATTERN regex directly."""

    def test_valid_task_id_patterns(self):
        """Valid Task ID patterns should match."""
        valid_ids = [
            "[PLAN-001]",
            "[LINT-001]",
            "[TEM-001]",
            "[OBP-001]",
            "[ABC-123]",
            "[XYZ-9999]",
            "[AB-123]",  # Minimum: 2 letters, 3 digits
            "[LINT-SHR-001]",  # Multi-segment blueprint task IDs
        ]

        for task_id in valid_ids:
            self.assertTrue(
                TASK_ID_PATTERN.match(task_id),
                f"{task_id} should match TASK_ID_PATTERN"
            )

    def test_invalid_task_id_patterns(self):
        """Invalid patterns should NOT match."""
        invalid_ids = [
            "[TBD]",           # No dash
            "[TODO]",          # No dash
            "[PLAN-12]",       # Only 2 digits
            "[P-123]",         # Only 1 letter
            "[PLAN-ABC]",      # No digits
            "[plan-001]",      # Lowercase
            "[PLAN001]",       # No dash
            "[Plan-001]",      # Mixed case
        ]

        for task_id in invalid_ids:
            self.assertFalse(
                TASK_ID_PATTERN.match(task_id),
                f"{task_id} should NOT match TASK_ID_PATTERN"
            )

    def test_placeholder_patterns_not_matched(self):
        """Actual placeholders should NOT match TASK_ID_PATTERN."""
        placeholders = [
            "[TBD]",
            "[TODO]",
            "[VALUE]",
            "[판정 — 비개발자용 요약]",
            "[목표 이름]",
            "[절대 경로]",
        ]

        for placeholder in placeholders:
            self.assertFalse(
                TASK_ID_PATTERN.match(placeholder),
                f"{placeholder} should NOT match TASK_ID_PATTERN"
            )


class TestTemplateTaskIDDetection(unittest.TestCase):
    """Template skeleton prefixes (XXX, SLUG) must fail plan-lint even when regex-valid."""

    def test_template_prefixes_flagged(self):
        for task_id in ("[XXX-001]", "[SLUG-001]", "[XXX-099]"):
            self.assertTrue(is_template_task_id(task_id), task_id)

    def test_real_prefixes_not_flagged(self):
        for task_id in ("[PLAN-001]", "[USRT-001]", "[LINT-SHR-001]", "[TEM-356-001]"):
            self.assertFalse(is_template_task_id(task_id), task_id)

    def test_extract_leading_prefix(self):
        self.assertEqual(extract_task_id_leading_prefix("[LINT-SHR-005]"), "LINT")
        self.assertEqual(extract_task_id_leading_prefix("[XXX-001]"), "XXX")
        self.assertIsNone(extract_task_id_leading_prefix("[TBD]"))


if __name__ == "__main__":
    unittest.main()
