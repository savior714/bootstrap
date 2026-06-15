from __future__ import annotations

import argparse
from pathlib import Path

COLOR_RED = "\033[91m"

COLOR_GREEN = "\033[92m"

COLOR_YELLOW = "\033[93m"

COLOR_BLUE = "\033[94m"

COLOR_RESET = "\033[0m"


from scripts.plan_loop.plan_lint.fixer import apply_fix_to_file
from scripts.plan_loop.plan_lint.linter import lint_plan_file
from scripts.plan_loop.plan_lint.shared import ATOMIC_UNIT_TAG, DEPRECATED_LEVEL_LOW_TAG


def _maybe_ensure_linear(plan_file: Path, *, dry_run: bool) -> None:
    """After lint PASS: create Linear issue + patch TEM-XXX placeholders (major plans only).

    MAJOR product blueprints WITHOUT a real Linear-Issue now FAIL lint until created.
    Internal tooling / minor plans skip silently.
    """
    try:
        from scripts.linear_sync.lib.issue_factory import ensure_plan_linear_issue
        from scripts.linear_sync.lib.plan_metadata import (
            needs_linear_issue_creation,
            parse_doc_meta,
            is_linear_placeholder,
        )
    except ImportError as exc:
        print(f"{COLOR_YELLOW}[WARN] Linear ensure skipped (import): {exc}{COLOR_RESET}")
        return

    content = plan_file.read_text(encoding="utf-8")
    if not needs_linear_issue_creation(content, plan_file):
        return

    # Major product blueprint without a real Linear-Issue → FAIL lint
    meta = parse_doc_meta(content, plan_file)
    if meta.linear_issue and not is_linear_placeholder(meta.linear_issue):
        # Already has a real issue — just sync (non-blocking)
        print(f"{COLOR_BLUE}[Linear] Syncing existing issue for {plan_file.name}...{COLOR_RESET}")
        result = ensure_plan_linear_issue(plan_file, dry_run=dry_run)
        if result.message:
            print(f"{COLOR_BLUE}[Linear] {result.message}{COLOR_RESET}")
        return

    # No real Linear-Issue → create it (blocking)
    print(f"{COLOR_BLUE}[Linear] BLOCKING: Creating issue for {plan_file.name}...{COLOR_RESET}")
    result = ensure_plan_linear_issue(plan_file, dry_run=dry_run)
    if result.created and result.identifier:
        print(
            f"{COLOR_GREEN}[Linear] Created {result.identifier}"
            f"{f' — {result.url}' if result.url else ''}{COLOR_RESET}"
        )
    elif result.identifier:
        print(
            f"{COLOR_GREEN}[Linear] Attached {result.identifier}"
            f"{f' — {result.url}' if result.url else ''}{COLOR_RESET}"
        )
    else:
        print(f"{COLOR_RED}[FAIL] Linear issue creation failed: {result.message}{COLOR_RESET}")
        raise SystemExit(1)


def main() -> int:
    parser = argparse.ArgumentParser(description="Lint plan markdown task contracts.")
    parser.add_argument("plan_files", type=Path, nargs="+", help="Path to plan markdown file(s)")
    parser.add_argument(
        "--ensure-linear",
        action="store_true",
        help="After PASS on a file, create/patch Linear issue when TEM-XXX placeholder only",
    )
    parser.add_argument(
        "--skip-linear-ensure",
        action="store_true",
        help="Do not run Linear ensure hook after lint",
    )
    parser.add_argument(
        "--ensure-linear-dry-run",
        action="store_true",
        help="With --ensure-linear, simulate issue creation only",
    )
    parser.add_argument(
        "--archive-ready",
        action="store_true",
        help="Enforce strict checks for archiving (all tasks done, spec links present)",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Apply mechanical auto-fixes before linting and write changes in-place",
    )
    args = parser.parse_args()

    overall_fail = False
    linted_count = 0
    template_link = "file:///.agents/workflows/plan.md"
    auto_ensure = (
        not args.skip_linear_ensure
        and (args.ensure_linear or len(args.plan_files) == 1)
    )
    linear_ensure_failed = False

    for plan_file in args.plan_files:
        if not plan_file.exists():
            print(f"{COLOR_RED}[ERROR] File not found: {plan_file}{COLOR_RESET}")
            overall_fail = True
            continue

        if plan_file.is_dir() or plan_file.suffix != ".md":
            print(f"{COLOR_YELLOW}[SKIP] {plan_file} (not a .md file or is a directory){COLOR_RESET}")
            continue

        linted_count += 1

        # Apply mechanical fixes before linting (opt-in via --fix)
        if args.fix:
            _fixed, fixes = apply_fix_to_file(plan_file)
            if fixes:
                print(f"{COLOR_BLUE}[fix] {plan_file}:")
                for fix in fixes:
                    print(f"  {COLOR_BLUE}- {fix}{COLOR_RESET}")

        issues, warnings = lint_plan_file(plan_file, is_archive_ready=args.archive_ready)

        for warning in warnings:
            print(f"{COLOR_YELLOW}[WARN] {plan_file}: {warning}{COLOR_RESET}")

        if not issues and not warnings:
            print(f"{COLOR_GREEN}[PASS] {plan_file} contract lint passed{COLOR_RESET}")
            if auto_ensure:
                try:
                    _maybe_ensure_linear(plan_file, dry_run=args.ensure_linear_dry_run)
                except SystemExit as exc:
                    overall_fail = True
                    linear_ensure_failed = True
                    if exc.code != 0:
                        continue
        elif not issues and warnings:
            print(f"{COLOR_YELLOW}[WARN] {plan_file} contract lint passed with warnings — fix required before implementation{COLOR_RESET}")
            overall_fail = True
        else:
            print(f"{COLOR_RED}[FAIL] {plan_file} contract lint failed{COLOR_RESET}")
            print(f"{COLOR_YELLOW}Guideline: Follow the structural sequence in {template_link}{COLOR_RESET}")
            for issue in issues:
                print(f" {COLOR_RED}- {issue}{COLOR_RESET}")
            print(
                f"\n{COLOR_BLUE}Tip: Every blueprint task needs '{ATOMIC_UNIT_TAG}' "
                f"(or deprecated '{DEPRECATED_LEVEL_LOW_TAG}') and no placeholders.{COLOR_RESET}\n"
            )
            overall_fail = True

    if linted_count == 0:
        print(f"{COLOR_RED}[ERROR] No .md plan files were linted{COLOR_RESET}")
        return 1

    if linear_ensure_failed:
        return 1
    return 1 if overall_fail else 0
