#!/usr/bin/env python3
"""Plan implementation review gate (Blueprint Task -098 Verify).

Checks:
1) Plan has code implementation tasks (Target under apps/, src/, scripts/, packages/, tests/
   — excludes docs/plans/ and -098/-099 tasks)
2) If code tasks exist: must have Task-ID [*-098] with Verify containing plan-review-gate
3) Must have ## Implementation Review section
4) When -098 exists: Implementation Review body must not be a placeholder

Usage:
  python3 scripts/verify/plan_review_gate.py --plan docs/plans/PLAN_xxx.md
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.plan_loop.plan_lint.verification import (
    IMPLEMENTATION_REVIEW_SECTION_RE,
    _has_code_implementation_tasks,
    _has_implementation_review_task,
    extract_implementation_review_body,
    is_implementation_review_placeholder,
    lint_implementation_review_task_contract,
)


def check_plan_review_gate(plan_text: str) -> list[str]:
    """Return blocking issues; empty list means PASS."""
    if not _has_code_implementation_tasks(plan_text):
        return []

    issues: list[str] = []
    issues.extend(lint_implementation_review_task_contract(plan_text))
    if not _has_implementation_review_task(plan_text):
        issues.append(
            "missing implementation review task with Task-ID [*-098] and "
            "Verify containing plan-review-gate"
        )
    if not IMPLEMENTATION_REVIEW_SECTION_RE.search(plan_text):
        issues.append("missing section: ## 🔍 Implementation Review")
    elif _has_implementation_review_task(plan_text):
        body = extract_implementation_review_body(plan_text) or ""
        if is_implementation_review_placeholder(body):
            preview = body.splitlines()[0][:80] if body else "(empty)"
            issues.append(
                "Implementation Review section is still a placeholder — "
                f"current: {preview!r}. "
                "Write a measured findings summary (High/Medium/Low) before Verify."
            )
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Gate implementation review for plan documents.")
    parser.add_argument("--plan", required=True, type=Path, help="Path to target plan markdown")
    args = parser.parse_args()

    repo_root = Path.cwd()
    plan_arg = str(args.plan)
    if plan_arg.startswith("plan="):
        plan_arg = plan_arg.split("=", 1)[1]
    plan_path_raw = Path(plan_arg)
    plan_path = plan_path_raw if plan_path_raw.is_absolute() else (repo_root / plan_path_raw)
    if not plan_path.exists():
        print(f"[FAIL] plan file not found: {plan_path}")
        return 1

    plan_text = plan_path.read_text(encoding="utf-8")
    issues = check_plan_review_gate(plan_text)

    if issues:
        print("[FAIL] plan review gate failed")
        for issue in issues:
            print(f" - {issue}")
        print(
            "hint: (1) 마지막 구현 Task 다음에 Task -098(Implementation review) 추가, "
            "(2) Pre-read에 `agents/skills/review/SKILL.md` 포함 후 review/SKILL workflow 실행, "
            "(3) Findings 작성 후 `## 🔍 Implementation Review` 절 채우기, "
            "(4) Verify에 `just plan-review-gate plan=docs/plans/<file>.md` 지정."
        )
        return 1

    print("[PASS] plan review gate passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
