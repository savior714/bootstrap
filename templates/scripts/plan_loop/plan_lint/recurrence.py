"""Recurrence guards — blueprint patterns that fail at closeout/archive if unchecked at authoring."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from scripts.plan_loop.plan_lint.justfile_recipes import (
    DEFAULT_JUSTFILE,
    extract_just_recipe_name,
    load_justfile_recipe_names,
)
from scripts.plan_loop.plan_lint.structural import _is_active_root_blueprint_path

DOD_SECTION_START_RE = re.compile(
    r"^##\s*✅\s*Definition of Done\s*\(\s*DoD\s*\)",
    re.MULTILINE,
)

RELATED_SPECS_HEADING_RE = re.compile(
    r"^##\s*📎\s*관련\s*명세\s*$",
    re.MULTILINE,
)

PLAN_CLOSE_COMMAND_RE = re.compile(r"\bplan-close\b", re.IGNORECASE)


def is_plan_close_command(command: str) -> bool:
    """True when a backtick command invokes the plan-close gate (DoD recursion hazard)."""
    return bool(PLAN_CLOSE_COMMAND_RE.search(command.strip()))


def extract_dod_backtick_commands(text: str) -> list[str]:
    """Backtick shell commands listed under ## Definition of Done (DoD)."""
    lines = text.splitlines()
    in_dod = False
    commands: list[str] = []
    list_item_re = re.compile(r"^\s*(?:[-*]\s+|\d+\.\s+)")
    verify_prefixes = (
        "just ",
        "pytest ",
        "pnpm ",
        "npm ",
        "yarn ",
        "python3 ",
        "uv run ",
        "playwright ",
    )

    for line in lines:
        if DOD_SECTION_START_RE.match(line):
            in_dod = True
            continue
        if in_dod and re.match(r"^##\s", line):
            break
        if not in_dod or not list_item_re.match(line):
            continue
        for cmd in re.findall(r"`([^`]+)`", line):
            cmd = cmd.strip()
            if cmd.startswith(verify_prefixes):
                commands.append(cmd)
    return commands


def lint_active_blueprint_recurrence_guards(
    text: str, file_path: Optional[Path] = None
) -> list[str]:
    """HARD checks for active root blueprints — archive/closeout friction prevention."""
    if not _is_active_root_blueprint_path(file_path):
        return []

    issues: list[str] = []

    for cmd in extract_dod_backtick_commands(text):
        if is_plan_close_command(cmd):
            issues.append(
                "DoD must not include `just plan-close` — it causes plan_close_gate "
                "recursion/timeouts. List concrete verify commands only; run plan-close "
                "via the Closeout Task Verify (see docs/templates/TEMPLATE_blueprint.md "
                "§Definition of Done)."
            )
            break

    has_specs_heading = bool(RELATED_SPECS_HEADING_RE.search(text))
    has_specs_path = bool(re.search(r"docs/specs/", text))
    if not has_specs_heading and not has_specs_path:
        issues.append(
            "Active blueprint missing related specs — add `## 📎 관련 명세` with at "
            "least one `docs/specs/...` path (archive-ready and closeout SSOT)."
        )
    elif has_specs_heading and not has_specs_path:
        issues.append(
            "`## 📎 관련 명세` present but no `docs/specs/` path — add a spec table row "
            "with repo-root `docs/specs/...` path."
        )

    known_recipes = load_justfile_recipe_names(str(DEFAULT_JUSTFILE))
    if known_recipes:
        for cmd in extract_dod_backtick_commands(text):
            if is_plan_close_command(cmd):
                continue
            recipe = extract_just_recipe_name(cmd)
            if recipe and recipe not in known_recipes:
                issues.append(
                    f"DoD references unknown Justfile recipe `just {recipe}` — "
                    f"run `just --list` and fix the command or add the recipe to Justfile."
                )

    return issues
