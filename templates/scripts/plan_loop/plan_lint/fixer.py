"""Mechanical auto-fix for plan markdown contract issues."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from scripts.plan_loop.plan_lint.shared import (
    ATOMIC_UNIT_TAG,
    BLUEPRINT_REQUIRED_DOC_META_FIELDS,
    CANONICAL_TODO_CONCLUSION_SLOTS,
    DEPRECATED_LEVEL_LOW_TAG,
    REQUIRED_SECTION_HEADINGS,
    REQUIRED_SECTIONS,
    _parse_fields,
    _split_task_blocks,
    _yaml_blueprint_doc_meta_defaults,
)
from scripts.plan_loop.plan_lint.verification import (
    _verify_command_segments,
    _verify_segment_runner,
)


def fix_plan_text(text: str, file_path: Optional[Path] = None) -> tuple[str, list[str]]:
    """Apply mechanical fixes and return (fixed_text, list_of_applied_fixes).

    Fixes applied in order:
      1. Doc meta defaults — fill empty required meta fields with defaults
      2. Missing sections — insert absent REQUIRED_SECTIONS at correct positions
      3. Section order — reorder out-of-order sections to canonical sequence
      4. CSF slot insertion — fill empty todo/running Conclusion with canonical slot
      5. Deprecated tag replacement — [Level: Low] -> [Unit: Atomic]
      6. Short Goal padding — pad Goal < 15 chars with ' — to be specified'
      7. Unrecognized Verify runner — prepend recognized runner if missing (SSOT segment runner)
    """
    fixes: list[str] = []
    result = text

    # 1. Doc meta defaults
    result, fix_meta = _fix_doc_meta_defaults(result, file_path)
    fixes.extend(fix_meta)

    # 2. Missing sections insertion
    result, fix_sections = _fix_missing_sections(result)
    fixes.extend(fix_sections)

    # 3. Section order correction
    result, fix_order = _fix_section_order(result)
    fixes.extend(fix_order)

    # 4. CSF slot insertion for empty todo/running Conclusion
    result, fix_csf = _fix_empty_conclusion_slots(result)
    fixes.extend(fix_csf)

    # 5. Deprecated tag replacement
    result, fix_tags = _fix_deprecated_tags(result)
    fixes.extend(fix_tags)

    # 6. Missing task required fields — insert defaults for absent fields
    result, fix_task_fields = _fix_missing_task_fields(result)
    fixes.extend(fix_task_fields)

    # 7. Short Goal padding — pad Goal < 15 chars
    result, fix_goals = _fix_short_goals(result)
    fixes.extend(fix_goals)

    # 8. Unrecognized Verify runner — prepend recognized runner if missing
    result, fix_verify = _fix_unrecognized_verify(result)
    fixes.extend(fix_verify)

    return result, fixes


def _fix_doc_meta_defaults(text: str, file_path: Optional[Path]) -> tuple[str, list[str]]:
    """Fill empty required blueprint doc meta fields with defaults."""
    fixes: list[str] = []

    if not re.search(r"^# 🗺️ Project Blueprint:", text, re.MULTILINE):
        return text, fixes

    # Find the meta block: from "## 문서 메타" to next ## heading or #### Task
    meta_heading_match = re.search(
        r"(^## 문서 메타\s*\n)",
        text,
        re.MULTILINE,
    )
    if not meta_heading_match:
        return text, fixes

    # Find the end of the meta block
    after_heading = text[meta_heading_match.end():]
    next_section = re.search(r"^(?:## |#### Task)", after_heading, re.MULTILINE)
    if next_section is None:
        # No next section — meta block extends to end of text
        meta_end = len(text)
    else:
        meta_end = meta_heading_match.end() + next_section.start()
    meta_block = text[meta_heading_match.start() : meta_end]

    # Parse existing field lines from the meta block
    existing_fields: dict[str, str] = {}
    for line in meta_block.split("\n"):
        m = re.match(r"^\s*- \*\*([^*]+)\*\*:\s*(.+)$", line)
        if m:
            existing_fields[m.group(1).strip()] = m.group(2).strip()

    # Check if this is a YAML blueprint doc
    from scripts.plan_loop.plan_lint.shared import is_yaml_blueprint_doc

    if is_yaml_blueprint_doc(text):
        defaults = _yaml_blueprint_doc_meta_defaults(text)
    else:
        defaults = {
            "SSOT Check": "N/A",
            "Project Status Link": "N/A",
            "Architectural Goal": "Blueprint",
            "Priority": "2",
            "Labels": "docs",
        }

    # Required fields in canonical order; preserve custom meta bullets from original block.
    new_field_lines: list[str] = []
    for field_name in BLUEPRINT_REQUIRED_DOC_META_FIELDS:
        existing_val = existing_fields.get(field_name, "").strip()
        if existing_val:
            new_field_lines.append(f"- **{field_name}**: {existing_val}")
        elif field_name in defaults:
            new_field_lines.append(f"- **{field_name}**: {defaults[field_name]}")
            fixes.append(f"Meta: filled empty/missing field '{field_name}' with '{defaults[field_name]}'")

    custom_lines: list[str] = []
    for line in meta_block.split("\n"):
        m = re.match(r"^\s*- \*\*([^*]+)\*\*:\s*(.+)$", line)
        if m and m.group(1).strip() not in BLUEPRINT_REQUIRED_DOC_META_FIELDS:
            custom_lines.append(line)

    new_meta_block = "## 문서 메타\n" + "\n".join(new_field_lines)
    if custom_lines:
        new_meta_block += "\n" + "\n".join(custom_lines)
    new_meta_block += "\n"

    # Replace in the full text
    text = text[: meta_heading_match.start()] + new_meta_block + text[meta_end:]

    return text, fixes


def _fix_missing_sections(text: str) -> tuple[str, list[str]]:
    """Insert missing REQUIRED_SECTIONS using canonical headings in SSOT order."""
    fixes: list[str] = []

    for idx, (pattern, name) in enumerate(REQUIRED_SECTIONS):
        if re.search(pattern, text, re.MULTILINE):
            continue

        heading_line = REQUIRED_SECTION_HEADINGS[idx]
        stub = f"\n{heading_line}\n\n[미완성]\n"

        insert_pos = len(text)
        for later_idx in range(idx + 1, len(REQUIRED_SECTIONS)):
            later_match = re.search(
                REQUIRED_SECTIONS[later_idx][0], text, re.MULTILINE
            )
            if later_match:
                insert_pos = later_match.start()
                break
        else:
            for earlier_idx in range(idx - 1, -1, -1):
                earlier_match = re.search(
                    REQUIRED_SECTIONS[earlier_idx][0], text, re.MULTILINE
                )
                if earlier_match:
                    insert_pos = earlier_match.end()
                    break

        text = text[:insert_pos] + stub + text[insert_pos:]
        fixes.append(f"Section: inserted missing '{name}' section")

    return text, fixes


def _fix_section_order(text: str) -> tuple[str, list[str]]:
    """Reorder sections that appear out of canonical sequence."""
    fixes: list[str] = []

    positions: list[tuple[int, str]] = []
    for pattern, name in REQUIRED_SECTIONS:
        match = re.search(pattern, text, re.MULTILINE)
        if match:
            positions.append((match.start(), name))

    # Check if positions are in order
    for i in range(len(positions) - 1):
        if positions[i][0] > positions[i + 1][0]:
            fixes.append(
                f"Section order: '{positions[i+1][1]}' appears before '{positions[i][1]}' "
                f"(may need manual reordering)"
            )
            # Note: full section reordering is complex and risky, so we only warn

    return text, fixes


def _fix_empty_conclusion_slots(text: str) -> tuple[str, list[str]]:
    """Fill empty Conclusion fields on todo/running tasks with canonical CSF slot."""
    fixes: list[str] = []

    task_blocks = _split_task_blocks(text)
    if not task_blocks:
        return text, fixes

    for block in task_blocks:
        fields = _parse_fields(block)
        status = fields.get("Status", "todo")

        if status not in ("todo", "running"):
            continue

        conclusion = fields.get("Conclusion", "").strip()
        if conclusion:
            continue

        # Find the Conclusion field line in this block
        conclusion_match = re.search(
            r"^(- (?:\*\*Conclusion\*\*|Conclusion):)\s*$",
            block,
            re.MULTILINE,
        )
        if conclusion_match:
            # Replace empty Conclusion with canonical slot
            old_line = f"{conclusion_match.group(1)} "
            new_line = f"{conclusion_match.group(1)} {CANONICAL_TODO_CONCLUSION_SLOTS[0]}"
            text = text.replace(old_line, new_line, 1)
            fixes.append(
                f"Conclusion: filled empty CSF slot on {status} task "
                f"with '{CANONICAL_TODO_CONCLUSION_SLOTS[0]}'"
            )

    return text, fixes


def _fix_deprecated_tags(text: str) -> tuple[str, list[str]]:
    """Replace deprecated [Level: Low] with [Unit: Atomic]."""
    fixes: list[str] = []

    if DEPRECATED_LEVEL_LOW_TAG in text:
        count = text.count(DEPRECATED_LEVEL_LOW_TAG)
        text = text.replace(DEPRECATED_LEVEL_LOW_TAG, ATOMIC_UNIT_TAG)
        fixes.append(
            f"Tag: replaced {count} occurrence(s) of deprecated '{DEPRECATED_LEVEL_LOW_TAG}' "
            f"with '{ATOMIC_UNIT_TAG}'"
        )

    return text, fixes


def _fix_linear_issue_placeholder(text: str) -> tuple[str, list[str]]:
    """Replace Linear-Issue TEM-XXX placeholders with sequential issue IDs."""
    fixes: list[str] = []

    # Find all Linear-Issue fields with TEM-XXX
    linear_pattern = re.compile(
        r"(Linear-Issue:\s*)TEM-XXX",
        re.IGNORECASE,
    )

    counter = 1
    def replace_linear(match: re.Match) -> str:
        nonlocal counter
        prefix = match.group(1)
        replacement = f"TEM-{counter:03d}"
        counter += 1
        return f"{prefix}{replacement}"

    new_text, count = linear_pattern.subn(replace_linear, text)
    if count > 0:
        fixes.append(
            f"Linear-Issue: replaced {count} placeholder(s) of 'TEM-XXX' "
            f"with sequential IDs (TEM-001..TEM-{counter - 1:03d})"
        )

    return new_text, fixes


def _fix_missing_task_fields(text: str) -> tuple[str, list[str]]:
    """Insert missing required fields on task blocks with defaults."""
    fixes: list[str] = []

    # Required fields that the lint complains about when missing
    REQUIRED_TASK_FIELDS = (
        ("RetryPolicy", "none"),
        ("Action", "Implement"),
        ("Target", "N/A"),
        ("Diagnostics", "0"),
    )

    task_blocks = _split_task_blocks(text)
    if not task_blocks:
        return text, fixes

    # Process each task block — work on the full text by finding and replacing
    for block in task_blocks:
        # Find insertion position: before the Goal field (bold or plain), or at start of block
        goal_match = re.search(
            r"^(- (?:\*\*Goal\*\*|Goal):)", block, re.MULTILINE
        )
        insert_pos = goal_match.start() if goal_match else 0

        # Find the actual insertion point in the full text
        block_start = text.find(block)
        if block_start < 0:
            continue

        insert_target = block_start + insert_pos

        # Check each field against the actual text (not cached parsed fields)
        for field_name, default_val in REQUIRED_TASK_FIELDS:
            # Check if the field already exists anywhere in this block's region
            block_end = min(block_start + 2000, len(text))
            existing = re.search(
                rf"(?m)^- (?:\*\*{re.escape(field_name)}\*\*|{re.escape(field_name)}):\s*",
                text[block_start:block_end],
            )
            if existing:
                continue

            # Insert the field line
            field_line = f"- **{field_name}**: {default_val}"
            text = text[:insert_target] + f"{field_line}\n" + text[insert_target:]
            fixes.append(
                f"Task field: inserted missing '{field_name}' with default '{default_val}'"
            )

    return text, fixes


# Recognized test/verify runners that the linter accepts
RECOGNIZED_RUNNERS = frozenset([
    "pytest", "just", "pnpm", "uv", "python3", "npm",
    "uv run pytest", "python -m pytest", "python3 -m pytest",
])


def _fix_short_goals(text: str) -> tuple[str, list[str]]:
    """Pad Goal fields shorter than 15 chars with ' — to be specified'."""
    fixes: list[str] = []

    # Match both bold and plain Goal field lines
    goal_re = re.compile(
        r"^(- (?:\*\*Goal\*\*|Goal):\s*)(.+)$", re.MULTILINE
    )

    count = 0

    def pad_goal(match: re.Match) -> str:
        nonlocal count
        prefix = match.group(1)
        value = match.group(2).strip()
        if len(value) >= 15:
            return match.group(0)
        count += 1
        padded = f"{value} — to be specified"
        return f"{prefix}{padded}"

    new_text = goal_re.sub(pad_goal, text)
    if count > 0:
        fixes.append(
            f"Goal: padded {count} short goal(s) (< 15 chars) with ' — to be specified'"
        )

    return new_text, fixes


def _fix_unrecognized_verify(text: str) -> tuple[str, list[str]]:
    """Prepend uv run when no Verify segment matches linter SSOT runner detection."""
    fixes: list[str] = []

    verify_re = re.compile(
        r"^(- (?:\*\*Verify\*\*|Verify):\s*)(.+)$", re.MULTILINE
    )

    count = 0

    def fix_verify(match: re.Match) -> str:
        nonlocal count
        prefix = match.group(1)
        value = match.group(2).strip()
        segments = _verify_command_segments(value)
        if not segments:
            return match.group(0)
        if any(_verify_segment_runner(seg) for seg in segments):
            return match.group(0)
        # Avoid old startswith("just") false positives (e.g. "justify foo").
        if re.match(r"^just\w", value, re.IGNORECASE) and not re.match(
            r"^just(\s|$)", value, re.IGNORECASE
        ):
            return match.group(0)
        count += 1
        return f"{prefix}uv run {value}"

    new_text = verify_re.sub(fix_verify, text)
    if count > 0:
        fixes.append(
            f"Verify: prepended recognized runner to {count} line(s) missing one"
        )

    return new_text, fixes


def apply_fix_to_file(file_path: Path) -> tuple[str, list[str]]:
    """Read file, apply fixes, atomically replace on disk, return (new_content, fixes)."""
    original = file_path.read_text(encoding="utf-8")
    fixed, fixes = fix_plan_text(original, file_path)

    if fixes:
        tmp_path = file_path.parent / f".{file_path.name}.fix.tmp"
        tmp_path.write_text(fixed, encoding="utf-8")
        tmp_path.replace(file_path)

    return fixed, fixes
