from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from scripts.plan_loop.plan_lint.shared import (
    ALLOWED_RETRY,
    ALLOWED_STATUS,
    ATOMIC_UNIT_TAG,
    BLUEPRINT_REQUIRED_DOC_META_FIELDS,
    BLUEPRINT_REQUIRED_FIELDS,
    DEPRECATED_LEVEL_LOW_TAG,
    EXECUTOR_REQUIRED_FIELDS,
    FORBIDDEN_LEVEL_TAG_RE,
    KOREAN_CHAR_RE,
    _extract_doc_meta_fields,
    _is_blueprint_task,
    _is_unfilled_csf_hint,
    _parse_fields,
    _split_task_blocks,
    _task_unit_tag,
    extract_blueprint_title,
    is_blueprint_markdown,
)
from scripts.plan_loop.plan_lint.structural import (
    _lint_active_root_blueprint_governance,
    _lint_dod_checkbox_format,
    _lint_collaboration_summary,
    _lint_task_heading_numeric_phase_task,
    verify_structural_sequence,
)
from scripts.plan_loop.plan_lint.recurrence import lint_active_blueprint_recurrence_guards
from scripts.plan_loop.plan_lint.quality import (
    _lint_conclusion_quality,
    _lint_goal_quality,
    _lint_target_quality,
    _lint_task_goal_block,
    _lint_verify_quality,
)
from scripts.plan_loop.plan_lint.verification import (
    _atomic_unit_contract_issues,
    _atomic_unit_size_warnings,
    _check_korean_first,
    _is_conclusion_placeholder,
    _is_placeholder_value,
    _lint_open_task_conclusion,
    _lint_implementation_review_section,
    _lint_preread_gate,
    _lint_rollup_summary_section,
    _lint_task_conclusion_slot,
    _lint_task_preread_block,
    _lint_template_task_id,
    lint_implementation_review_task_contract,
)


def _lint_blueprint_doc_meta_fields(text: str) -> list[str]:
    issues: list[str] = []
    doc_fields = _extract_doc_meta_fields(text)

    # Linear-Issue: HARD ERROR unless Linear-Policy: internal is set
    linear_policy = doc_fields.get("Linear-Policy", "").strip().lower()
    linear_issue_value = doc_fields.get("Linear-Issue", "").strip()
    if linear_policy == "internal" and linear_issue_value:
        from scripts.linear_sync.lib.plan_metadata import is_linear_placeholder as _is_linear_placeholder

        if not _is_linear_placeholder(linear_issue_value):
            issues.append(
                "Linear-Policy: internal conflicts with a real Linear-Issue (TEM-NN). "
                "Use Linear-Issue: N/A for internal-only tracking, or remove Linear-Policy: internal "
                "for product plans that require Linear board sync and plan-close validation."
            )
    if linear_policy != "internal":
        if not linear_issue_value:
            issues.append(
                "Blueprint doc meta missing required field: Linear-Issue "
                "(use TEM-XXX placeholder; ensure_plan_linear will replace it)"
            )
        else:
            # Check if it's a valid placeholder or real issue
            import re as _re
            LINEAR_ID_RE = _re.compile(r"TEM-\d+", _re.IGNORECASE)
            LINEAR_PLACEHOLDER_IDS = frozenset({"TEM-XXX", "TEM-000", "TEM-999", "XXX", "PENDING", "NONE", "N/A", "NULL"})
            token = linear_issue_value.strip()
            m = _re.search(r"\[(TEM-\d+)\]", token, _re.IGNORECASE)
            if m:
                token = m.group(1).upper()
            elif not LINEAR_ID_RE.fullmatch(token):
                token = _re.sub(r"^[\[\(]|[\]\)]$", "", token).strip().upper()
            if token in LINEAR_PLACEHOLDER_IDS or not LINEAR_ID_RE.fullmatch(token):
                issues.append(
                    f"Blueprint doc meta has invalid Linear-Issue value: '{linear_issue_value}' "
                    "(must be TEM-XXX placeholder or real TEM-NN; set Linear-Policy: internal to skip)"
                )

    for required_meta in BLUEPRINT_REQUIRED_DOC_META_FIELDS:
        if required_meta == "Linear-Issue":
            continue  # Already handled above
        value = doc_fields.get(required_meta, "")
        if _is_placeholder_value(value):
            issues.append(
                f"Blueprint doc meta missing/empty required field: {required_meta}"
            )
    return issues


def lint_plan_text(text: str, file_path: Optional[Path] = None, is_archive_ready: bool = False, *, check_quality: bool = False, check_strict: bool = False) -> tuple[list[str], list[str]]:
    issues: list[str] = []
    warnings: list[str] = []
    is_blueprint_doc = is_blueprint_markdown(text)
    
    # [Hard Guard] Section Sequence Check
    if is_blueprint_doc:
        from scripts.linear_sync.lib.label_policy import (
            validate_blueprint_labels,
            validate_discouraged_blueprint_labels,
        )

        issues.extend(validate_blueprint_labels(text))
        issues.extend(validate_discouraged_blueprint_labels(text, file_path=file_path))
        if file_path is not None:
            from scripts.agent.route_context import find_repo_root
            from scripts.plan_loop.label_sync import lint_domain_label_coverage_warnings

            root = find_repo_root(file_path.parent)
            warnings.extend(
                lint_domain_label_coverage_warnings(
                    text,
                    file_path=file_path,
                    repo_root=root,
                )
            )
        issues.extend(verify_structural_sequence(text))
        issues.extend(_lint_collaboration_summary(text))
        issues.extend(_lint_rollup_summary_section(text))
        issues.extend(_lint_implementation_review_section(text))
        issues.extend(_lint_task_heading_numeric_phase_task(text))
        issues.extend(_lint_preread_gate(text))
        issues.extend(lint_active_blueprint_recurrence_guards(text, file_path))
        issues.extend(lint_implementation_review_task_contract(text))
        governance_issues, governance_warnings = _lint_active_root_blueprint_governance(
            text, file_path, check_strict=check_strict
        )
        issues.extend(governance_issues)
        warnings.extend(governance_warnings)
        dod_issues, dod_warnings = _lint_dod_checkbox_format(text, file_path)
        issues.extend(dod_issues)
        warnings.extend(dod_warnings)
        
        # [] Korean-first title check
        title = extract_blueprint_title(text)
        if title and not KOREAN_CHAR_RE.search(title):
            issues.append(
                f"Blueprint title must contain Korean characters: '{title}'"
            )

    # [] Korean-first body check (모든 .md 파일에 적용)
    issues.extend(_check_korean_first(text))

    if is_archive_ready:
        if not re.search(r"관련 명세|docs/specs/", text, re.IGNORECASE):
            issues.append(
                "[Archive-Ready] Blueprint must contain a reference to related specs "
                "(e.g., '관련 명세' or 'docs/specs/')."
            )

    task_blocks = _split_task_blocks(text)
    if not task_blocks:
        no_tasks_msg = (
            "no task blocks found (expected '#### Task X.Y: ...')"
            if is_blueprint_doc
            else "no task blocks found (expected '#### Task: ...')"
        )
        if is_blueprint_doc:
            issues.append(no_tasks_msg)
            issues.extend(_lint_blueprint_doc_meta_fields(text))
            return (issues, warnings)
        issues.append(no_tasks_msg)
        return (issues, warnings)

    seen_ids: set[str] = set()
    for idx, block in enumerate(task_blocks, start=1):
        fields = _parse_fields(block)
        is_blueprint = _is_blueprint_task(block, fields)
        required = BLUEPRINT_REQUIRED_FIELDS if is_blueprint else EXECUTOR_REQUIRED_FIELDS
        if is_blueprint and not is_blueprint_doc:
            required = tuple(f for f in required if f != "Pre-read")

        missing = [field for field in required if not fields.get(field)]
        if missing:
            issues.append(f"Task#{idx} missing required fields: {', '.join(missing)}")

        if is_blueprint:
            issues.extend(_atomic_unit_contract_issues(idx, fields, check_strict=check_strict))

        if is_blueprint and not missing:
            if FORBIDDEN_LEVEL_TAG_RE.search(block):
                issues.append(
                    f"Task#{idx} forbidden level tag Medium/High — "
                    f"split into smaller tasks with '{ATOMIC_UNIT_TAG}' only"
                )
                continue
            unit_tag = _task_unit_tag(block)
            if not unit_tag:
                issues.append(
                    f"Task#{idx} missing required unit tag '{ATOMIC_UNIT_TAG}' "
                    "(or Epic/Feature for macro plans)"
                )
                continue

            if is_blueprint_doc and file_path:
                file_name_lower = file_path.name.lower()
                is_macro_plan = "epic" in file_name_lower or "feature" in file_name_lower
                if is_macro_plan and unit_tag == ATOMIC_UNIT_TAG:
                    issues.append(
                        f"Task#{idx} has '{ATOMIC_UNIT_TAG}' inside an Epic/Feature plan. "
                        "Epic plans must use '[Unit: Epic]' or '[Unit: Feature]' and be split via /plan."
                    )
                elif not is_macro_plan and unit_tag in ("[Unit: Epic]", "[Unit: Feature]"):
                    issues.append(
                        f"Task#{idx} has '{unit_tag}' inside an Atomic plan. "
                        "Only Epic/Feature plans can have macro units."
                    )
            if unit_tag == DEPRECATED_LEVEL_LOW_TAG:
                issues.append(
                    f"Task#{idx} uses deprecated '{DEPRECATED_LEVEL_LOW_TAG}'; "
                    f"migrate heading to '{ATOMIC_UNIT_TAG}' — lint FAIL"
                )
            if check_strict:
                warnings.extend(_atomic_unit_size_warnings(idx, fields))
            if is_blueprint_doc:
                issues.extend(_lint_task_preread_block(idx, block))
            issues.extend(_lint_task_conclusion_slot(idx, block))

            if check_strict:
                # Task content quality checks (strict tier only)
                task_status = fields.get("Status", "todo")
                issues.extend(_lint_target_quality(idx, fields.get("Target", "")))
                issues.extend(_lint_task_goal_block(idx, block, fields.get("Goal", "")))
                issues.extend(_lint_goal_quality(idx, fields.get("Goal", "")))
                issues.extend(_lint_verify_quality(idx, fields.get("Verify", "")))
                issues.extend(_lint_conclusion_quality(idx, task_status, fields.get("Conclusion", "")))

        status = fields.get("Status", "todo")
        
        if is_archive_ready and status != "done":
            issues.append(f"[Archive-Ready] Task#{idx} is not marked as 'done' (current status: '{status}'). All tasks must be completed before archiving.")

        # Placeholder check for all fields in the task
        for field, value in fields.items():
            if field == "Conclusion" and status in ("todo", "running"):
                issues.extend(_lint_open_task_conclusion(idx, status, value))
                continue
            if field == "Conclusion" and status == "done" and _is_unfilled_csf_hint(value):
                issues.append(
                    f"Task#{idx} field 'Conclusion' still has CSF hint; replace with measured summary before done: {value}"
                )
                continue

            if field == "Conclusion":
                if _is_conclusion_placeholder(value):
                    issues.append(f"Task#{idx} field '{field}' contains placeholder value: {value}")
            else:
                if _is_placeholder_value(value):
                    issues.append(f"Task#{idx} field '{field}' contains placeholder value: {value}")

        task_id = fields.get("Task-ID", "").strip()
        if task_id:
            issues.extend(_lint_template_task_id(idx, task_id))
            if task_id in seen_ids:
                issues.append(f"Task#{idx} duplicate Task-ID: {task_id}")
            else:
                seen_ids.add(task_id)

        status_value = fields.get("Status", "").strip()
        if status_value and status_value not in ALLOWED_STATUS:
            issues.append(
                f"Task#{idx} invalid Status '{status_value}' (allowed: {', '.join(sorted(ALLOWED_STATUS))})"
            )

        retry_policy = fields.get("RetryPolicy", "").strip()
        if retry_policy and retry_policy not in ALLOWED_RETRY:
            issues.append(
                f"Task#{idx} invalid RetryPolicy '{retry_policy}' (allowed: {', '.join(sorted(ALLOWED_RETRY))})"
            )
            
        if is_blueprint:
            plan_name = str(file_path).lower() if file_path else ""
            is_minor = any(word in plan_name for word in ["fix", "lint", "consistency", "minor", "typo"])
            linear_issue = (fields.get("Linear-Issue") or "").strip()
            if not is_minor and not linear_issue:
                issues.append(
                    f"Task#{idx} is missing 'Linear-Issue' mapping. "
                    "Major plans must map to a Linear issue (use TEM-XXX until ensure runs)."
                )

    if is_blueprint_doc:
        issues.extend(_lint_blueprint_doc_meta_fields(text))

    if check_quality and is_blueprint_doc:
        from scripts.plan_loop.plan_lint.blueprint_quality import lint_blueprint_quality_gates

        quality_issues, quality_warnings = lint_blueprint_quality_gates(text)
        issues.extend(quality_issues)
        warnings.extend(quality_warnings)

    return issues, warnings


def lint_plan_file(
    path: Path,
    is_archive_ready: bool = False,
    *,
    check_quality: bool = False,
    check_strict: bool = False,
) -> tuple[list[str], list[str]]:
    return lint_plan_text(
        path.read_text(encoding="utf-8"),
        file_path=path,
        is_archive_ready=is_archive_ready,
        check_quality=check_quality,
        check_strict=check_strict,
    )



