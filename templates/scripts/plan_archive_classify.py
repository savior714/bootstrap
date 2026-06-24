#!/usr/bin/env python3
"""docs/plans/archive/ 하위 폴더 분류 규칙 (archive_plans · organize_archive_plans SSOT)."""

from __future__ import annotations

import re

KEEP_AT_ARCHIVE_ROOT = frozenset({"README.md"})


def classify_archive_subdir(filename: str) -> str:
    """Return archive subdirectory (e.g. 'frontend', 'by-date/202605')."""
    if filename in KEEP_AT_ARCHIVE_ROOT:
        raise ValueError(f"cannot classify archive root file: {filename}")

    n = filename.lower()

    if re.match(r"^m4_", n) or filename.startswith("FIX-UI-MIGRATION"):
        return "root_plans"
    if filename.startswith("PHASE") or filename.startswith("adr-"):
        return "root_plans"

    if re.match(r"^fhir_", n) or filename.startswith("HAPI_"):
        return "fhir"
    if filename.startswith("PLAN_") and ("fhir" in n or "hapi" in n):
        return "fhir"

    if any(x in filename for x in ("EPIC_", "ROADMAP", "STRATEGIC_", "MASTER_PLAN", "MASTER_")):
        return "epic-roadmap"
    if re.match(r"^\d{8}_BLUEPRINT", filename):
        return "epic-roadmap"

    if filename.startswith("PLAN_") and re.search(
        r"(agent|linear|bootstrap|workflow|tem39|tem57|lis|grill|discuss)", n
    ):
        return "agent"
    if "grill_me" in n or "proactive_workflow" in n:
        return "agent"

    if any(
        k in n
        for k in ("knass", "lst_", "hira", "nhis", "nims", "k-nass", "public-data-integration")
    ):
        return "integration"

    if "billing" in n:
        return "billing"

    if n.startswith("ai_") or "ai_log" in n or "ai_worklog" in n:
        return "ai"

    if any(
        k in n
        for k in (
            "consultation",
            "renderer",
            "playwright",
            "widget",
            "layout",
            "header",
            "frontend",
            "jsx_casing",
            "react_component",
            "dashboard",
            "examination",
            "workspacegrid",
        )
    ):
        return "frontend"

    if any(
        k in n
        for k in (
            "docker",
            "_ci",
            "infra",
            "electron",
            "deploy",
            "port_collision",
            "security_patch",
            "typescript_error",
            "lint",
            "biome",
            "type_safety",
            "verify_modernization",
        )
    ):
        return "infra"

    if n.startswith("specs_"):
        return "specs"

    if "migration_guide" in n or filename == "modernize_tech_stack_2026_q2.md":
        return "knowledge"

    if filename.startswith("PLAN_"):
        return "blueprints"

    m = re.match(r"^(\d{8})_", filename)
    if m:
        return f"by-date/{m.group(1)[:6]}"

    if filename == "reports_classification_system.md":
        return "meta"

    if "_report" in n and not filename.startswith("PLAN_"):
        return "reports"

    return "misc"


def archive_relative_path(filename: str) -> str:
    """Return path relative to docs/plans/archive/ (e.g. 'frontend/PLAN_x.md')."""
    subdir = classify_archive_subdir(filename)
    return f"{subdir}/{filename}"
