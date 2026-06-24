#!/usr/bin/env python3
"""Infer Linear team domain labels from Blueprint paths and body text."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from scripts.linear_sync.lib.label_policy import apply_label_policy_drop_unknown
from scripts.linear_sync.lib.plan_metadata import PATH_LABEL_HINTS

# Linear allowlist labels that describe *where* work happens (not type-only).
DOMAIN_LINEAR_LABELS: frozenset[str] = frozenset(
    {
        "Frontend",
        "Backend",
        "UI/UX",
        "FHIR",
        "E2E",
        "CI",
        "Critical-P0",
    }
)

DOMAIN_LINEAR_LABELS_LOWER = frozenset(name.lower() for name in DOMAIN_LINEAR_LABELS)


def _add_label(bucket: list[str], seen: set[str], label: str) -> None:
    key = label.lower()
    if key not in seen:
        seen.add(key)
        bucket.append(label)


def _path_matches_fragment(posix: str, fragment: str) -> bool:
    """Match PATH_LABEL_HINTS fragments without false positives (e.g. renderer/src → src/)."""
    if fragment == "src/":
        return posix.startswith("src/")
    if fragment.endswith("/"):
        return posix.startswith(fragment) or f"/{fragment}" in f"/{posix}/"
    return fragment in posix


def infer_domain_labels_from_paths(
    paths: Sequence[str],
    text: str = "",
    *,
    plan_path: Path | None = None,
) -> list[str]:
    """Return canonical Linear domain labels inferred from repo paths and plan text."""
    inferred: list[str] = []
    seen: set[str] = set()
    lower_text = (text or "").lower()

    for raw_path in paths:
        posix = str(raw_path).replace("\\", "/").lower()
        if not posix:
            continue
        for fragment, label in PATH_LABEL_HINTS:
            if _path_matches_fragment(posix, fragment):
                _add_label(inferred, seen, label)
        if posix.endswith((".tsx", ".jsx")):
            _add_label(inferred, seen, "Frontend")
        elif posix.endswith(".ts") and "{{FRONTEND_APP_PATH}}" in posix:
            _add_label(inferred, seen, "Frontend")
        elif posix.endswith(".py"):
            if any(token in posix for token in ("src/api", "sidecar", "src/domain", "src/")):
                _add_label(inferred, seen, "Backend")
        if "tests/e2e" in posix or posix.endswith(".spec.ts"):
            _add_label(inferred, seen, "E2E")
        if ".github/workflows" in posix or "docker-compose" in posix:
            _add_label(inferred, seen, "CI")

    if "fhir" in lower_text or "hapi" in lower_text:
        _add_label(inferred, seen, "FHIR")
    if "playwright" in lower_text and "e2e" in lower_text:
        _add_label(inferred, seen, "E2E")

    if plan_path is not None:
        name = plan_path.name.lower()
        if "risk" in name or "security" in name:
            _add_label(inferred, seen, "Critical-P0")
        if "fhir" in name or "hapi" in name:
            _add_label(inferred, seen, "FHIR")
        if "ui" in name or "layout" in name or "frontend" in name:
            _add_label(inferred, seen, "Frontend")

    return apply_label_policy_drop_unknown(inferred, context="infer_domain_labels_from_paths")


def lacks_domain_label(resolved_labels: Sequence[str]) -> bool:
    """True when no domain-facing Linear label is present after normalization."""
    lower = {name.lower() for name in resolved_labels}
    return not bool(lower & DOMAIN_LINEAR_LABELS_LOWER)
