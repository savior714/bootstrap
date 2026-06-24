#!/usr/bin/env python3
"""Sync inferred Linear domain labels into Blueprint doc meta and Task rows."""

from __future__ import annotations

import re
from pathlib import Path

from scripts.linear_sync.lib.label_policy import normalize_label_names
from scripts.linear_sync.lib.plan_metadata import split_label_tokens
from scripts.plan_loop.label_inference import infer_domain_labels_from_paths
from scripts.plan_loop.path_utils import extract_plan_paths, extract_task_paths
from scripts.plan_loop.plan_lint.shared import _split_task_blocks

DOC_LABELS_RE = re.compile(
    r"^(- \*\*Labels\*\*:\s*)(.+)$",
    re.MULTILINE,
)
PACKED_TASK_LINE_RE = re.compile(r"^- Task-ID:\s*(?P<rest>.*)$", re.MULTILINE)


def merge_label_field(existing_raw: str, inferred: list[str]) -> tuple[str, bool]:
    """Merge inferred domain labels into an existing Labels field value."""
    existing_tokens = split_label_tokens(existing_raw)
    existing_resolved, _ = normalize_label_names(existing_tokens)
    inferred_resolved, _ = normalize_label_names(inferred)

    merged: list[str] = []
    seen: set[str] = set()
    changed = False
    for name in existing_resolved + inferred_resolved:
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        merged.append(name)
        if name in inferred_resolved and name not in existing_resolved:
            changed = True

    if not merged:
        return existing_raw.strip(), False
    return ", ".join(merged), changed


def _update_packed_task_labels(line: str, inferred: list[str]) -> tuple[str, bool]:
    parts = line.split("|")
    updated_parts: list[str] = []
    changed = False
    for part in parts:
        stripped = part.strip()
        if stripped.startswith("Labels:"):
            _, value = stripped.split(":", 1)
            new_value, part_changed = merge_label_field(value.strip(), inferred)
            padding = part[: len(part) - len(part.lstrip())]
            updated_parts.append(f"{padding}Labels: {new_value} ")
            changed = changed or part_changed
        else:
            updated_parts.append(part)
    return "|".join(updated_parts), changed


def sync_labels_in_plan_text(
    text: str,
    *,
    repo_root: Path,
    plan_path: Path,
) -> tuple[str, list[str]]:
    """Augment doc meta and Task Labels from Impact Scope / Target paths."""
    plan_paths = extract_plan_paths(text, repo_root)
    return sync_labels_in_plan_text_with_paths(
    text,
    plan_paths=plan_paths,
    repo_root=repo_root,
    plan_path=plan_path,
)


def sync_labels_in_plan_text_with_paths(
    text: str,
    *,
    plan_paths: list[str],
    repo_root: Path,
    plan_path: Path,
) -> tuple[str, list[str]]:
    fixes: list[str] = []
    plan_inferred = infer_domain_labels_from_paths(
        plan_paths,
        text,
        plan_path=plan_path,
    )

    if plan_inferred:
        match = DOC_LABELS_RE.search(text)
        if match:
            prefix, existing = match.group(1), match.group(2).strip()
            merged, changed = merge_label_field(existing, plan_inferred)
            if changed:
                text = DOC_LABELS_RE.sub(f"{prefix}{merged}", text, count=1)
                fixes.append(f"doc meta → {merged}")

    for block in _split_task_blocks(text):
        task_paths = extract_task_paths(block, repo_root)
        if not task_paths:
            continue
        task_inferred = infer_domain_labels_from_paths(
            task_paths,
            block,
            plan_path=plan_path,
        )
        if not task_inferred:
            continue

        task_line_match = PACKED_TASK_LINE_RE.search(block)
        if not task_line_match:
            continue
        original_line = task_line_match.group(0)
        updated_line, changed = _update_packed_task_labels(original_line, task_inferred)
        if changed:
            text = text.replace(original_line, updated_line, 1)
            task_id = re.search(r"\[([A-Z0-9-]+-\d+)\]", original_line)
            label = task_id.group(1) if task_id else "task"
            fixes.append(f"{label} Labels augmented")

    return text, fixes


def lint_domain_label_coverage_warnings(
    text: str,
    *,
    file_path: Path | None,
    repo_root: Path,
) -> list[str]:
    """WARN when Impact Scope implies domain labels missing from doc meta."""
    from scripts.plan_loop.plan_lint.shared import _extract_doc_meta_fields, is_blueprint_markdown

    if file_path is None or not is_blueprint_markdown(text):
        return []

    plan_paths = extract_plan_paths(text, repo_root)
    inferred = infer_domain_labels_from_paths(
        plan_paths,
        text,
        plan_path=file_path,
    )
    if not inferred:
        return []

    doc_fields = _extract_doc_meta_fields(text)
    existing_raw = doc_fields.get("Labels", "").strip()
    merged, changed = merge_label_field(existing_raw, inferred)
    if not changed:
        return []

    try:
        plan_rel = file_path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        plan_rel = str(file_path)

    missing = []
    existing_resolved, _ = normalize_label_names(split_label_tokens(existing_raw))
    existing_lower = {n.lower() for n in existing_resolved}
    inferred_resolved, _ = normalize_label_names(inferred)
    for name in inferred_resolved:
        if name.lower() not in existing_lower:
            missing.append(name)
    if not missing:
        return []

    return [
        "doc meta Labels missing inferred domain label(s): "
        f"{', '.join(missing)} (full suggestion: {merged}) — "
        f"run: just plan-preread {plan_rel} --write"
    ]
