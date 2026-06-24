"""Blueprint quality gates (#8 Verify–test, #9 deps sync, #10 DoD coverage) — plan-lint --check-quality."""

from __future__ import annotations

import re
from pathlib import Path

from scripts.plan_loop.plan_lint.justfile_recipes import (
    DEFAULT_JUSTFILE,
    expand_just_recipe_names,
    extract_just_recipe_name,
    load_justfile_recipe_bodies,
)
from scripts.plan_loop.plan_lint.recurrence import extract_dod_backtick_commands
from scripts.plan_loop.plan_lint.shared import (
    _parse_fields,
    _split_task_blocks,
    is_blueprint_markdown,
)

EXECUTION_ORDER_HEADING_RE = re.compile(r"^##\s*실행\s*순서·선행\s*$", re.MULTILINE)
EXECUTION_TABLE_ROW_RE = re.compile(r"^\|\s*(\d+)\s*\|\s*([A-Z]{2,}-\d{3})\s*\|")
TASK_ID_BRACKET_RE = re.compile(r"\[([A-Z]{2,}-\d{3})\]")
TEST_TARGET_RE = re.compile(r"tests/.+\.test\.(?:tsx?|ts)$")
VITEST_PATH_RE = re.compile(r"vitest\s+run\s+(\S+)")
PLAN_VERIFY_PREFIXES = ("plan-",)

_EMPTY_CELLS = frozenset({"", "—", "-", "none", "None", "✗", "✓"})


def _normalize_dep_cell(value: str) -> set[str]:
    stripped = value.strip()
    if stripped in _EMPTY_CELLS:
        return set()
    return {part.strip() for part in re.split(r",\s*", stripped) if part.strip()}


def _bare_task_id_from_field(task_id_value: str) -> str | None:
    match = TASK_ID_BRACKET_RE.search(task_id_value.strip())
    return match.group(1) if match else None


def _execution_order_section(text: str) -> str:
    match = EXECUTION_ORDER_HEADING_RE.search(text)
    if not match:
        return ""
    rest = text[match.end() :]
    next_heading = re.search(r"^##\s+\S", rest, re.MULTILINE)
    return rest[: next_heading.start()] if next_heading else rest


def parse_execution_order_table(text: str) -> dict[str, dict[str, object]]:
    """Parse `## 실행 순서·선행` table into task-id → order, predecessors, parallel."""
    section = _execution_order_section(text)
    rows: dict[str, dict[str, object]] = {}
    for line in section.splitlines():
        if not EXECUTION_TABLE_ROW_RE.match(line):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 6:
            continue
        order_s, task_id, _why, predecessor, _output, parallel = cells[:6]
        try:
            order = int(order_s)
        except ValueError:
            continue
        preds = _normalize_dep_cell(predecessor)
        parallel_deps = _normalize_dep_cell(parallel)
        rows[task_id] = {
            "order": order,
            "predecessors": preds,
            "parallel": parallel_deps,
        }
    return rows


def parse_task_dependency_map(text: str) -> dict[str, set[str]]:
    """Task-ID → Dependency set from Execution Plan task blocks."""
    deps: dict[str, set[str]] = {}
    for block in _split_task_blocks(text):
        fields = _parse_fields(block)
        task_id = _bare_task_id_from_field(fields.get("Task-ID", ""))
        if not task_id:
            continue
        deps[task_id] = _normalize_dep_cell(fields.get("Dependency", ""))
    return deps


def lint_execution_order_dependency_sync(text: str) -> list[str]:
    """#9: `실행 순서·선행` 표 ↔ Task `Dependency` must match; order must respect DAG."""
    table = parse_execution_order_table(text)
    task_deps = parse_task_dependency_map(text)
    if not table:
        return ["Quality #9: missing or empty `## 실행 순서·선행` table"]

    issues: list[str] = []
    table_ids = set(table)
    task_ids = set(task_deps)

    missing_in_table = sorted(task_ids - table_ids)
    missing_in_tasks = sorted(table_ids - task_ids)
    if missing_in_table:
        issues.append(
            "Quality #9: Task blocks without execution-order row: "
            + ", ".join(missing_in_table[:8])
            + (" …" if len(missing_in_table) > 8 else "")
        )
    if missing_in_tasks:
        issues.append(
            "Quality #9: execution-order rows without Task block: "
            + ", ".join(missing_in_tasks[:8])
            + (" …" if len(missing_in_tasks) > 8 else "")
        )

    for task_id in sorted(table_ids & task_ids):
        row = table[task_id]
        table_pred = row["predecessors"]
        parallel = row["parallel"]
        block_pred = task_deps[task_id]
        allowed_table = table_pred if not parallel else table_pred | parallel
        if block_pred != table_pred and block_pred != allowed_table:
            issues.append(
                f"Quality #9: [{task_id}] execution-order 선행="
                f"{sorted(table_pred)!r} parallel={sorted(parallel)!r} "
                f"≠ Dependency={sorted(block_pred)!r}"
            )
        if not table_pred.issubset(block_pred):
            issues.append(
                f"Quality #9: [{task_id}] Dependency must include execution-order 선행 "
                f"{sorted(table_pred)!r}"
            )
        order = int(row["order"])
        for pred in block_pred:
            pred_row = table.get(pred)
            if pred_row is None:
                continue
            pred_order = int(pred_row["order"])
            if order <= pred_order:
                issues.append(
                    f"Quality #9: [{task_id}] order {order} must be after "
                    f"dependency [{pred}] order {pred_order}"
                )
    return issues


def _normalize_target_path(target: str) -> str:
    path = target.strip().strip("`")
    if path.startswith("{{FRONTEND_APP_PATH}}/"):
        return path.removeprefix("{{FRONTEND_APP_PATH}}/")
    return path


def _vitest_paths_in_recipe_body(body: str) -> list[str]:
    return [match.group(1) for match in VITEST_PATH_RE.finditer(body)]


def lint_verify_test_pairing(
    text: str,
    *,
    justfile_path: str = str(DEFAULT_JUSTFILE),
) -> list[str]:
    """#8: test-file Target tasks must Verify via just recipe that runs that test only."""
    bodies = load_justfile_recipe_bodies(justfile_path)
    issues: list[str] = []

    for idx, block in enumerate(_split_task_blocks(text), start=1):
        fields = _parse_fields(block)
        target = fields.get("Target", "").strip().strip("`")
        if not TEST_TARGET_RE.search(target.replace("\\", "/")):
            continue
        verify = fields.get("Verify", "").strip().strip("`")
        norm_target = _normalize_target_path(target)
        basename = Path(norm_target).name

        recipe = extract_just_recipe_name(verify)
        if not recipe:
            issues.append(
                f"Quality #8: Task#{idx} test Target `{basename}` Verify must use "
                f"`just <recipe>` (got `{verify}`)"
            )
            continue
        body = bodies.get(recipe, "")
        if not body:
            issues.append(
                f"Quality #8: Task#{idx} Verify recipe `just {recipe}` not found in Justfile"
            )
            continue
        vitest_paths = _vitest_paths_in_recipe_body(body)
        if not vitest_paths:
            issues.append(
                f"Quality #8: Task#{idx} recipe `just {recipe}` has no `vitest run <path>`"
            )
            continue
        if len(vitest_paths) > 1:
            issues.append(
                f"Quality #8: Task#{idx} recipe `just {recipe}` runs multiple test paths "
                f"(expected single-file proof for `{basename}`)"
            )
            continue
        run_path = vitest_paths[0]
        if not (run_path.endswith(basename) or run_path.endswith(norm_target)):
            issues.append(
                f"Quality #8: Task#{idx} Target `{basename}` but `just {recipe}` runs `{run_path}`"
            )
    return issues


def lint_dod_verify_coverage(
    text: str,
    *,
    justfile_path: str = str(DEFAULT_JUSTFILE),
) -> list[str]:
    """#10 WARN: Task Verify `just` recipes (non-plan) should appear in DoD (direct or aggregate)."""
    task_recipes: set[str] = set()
    for block in _split_task_blocks(text):
        fields = _parse_fields(block)
        verify = fields.get("Verify", "").strip().strip("`")
        recipe = extract_just_recipe_name(verify)
        if not recipe:
            continue
        if any(recipe.startswith(prefix) for prefix in PLAN_VERIFY_PREFIXES):
            continue
        if recipe.startswith("renderer-e2e-"):
            task_recipes.add(recipe)
            continue
        if recipe.startswith("renderer-vitest-"):
            task_recipes.add(recipe)

    if not task_recipes:
        return []

    dod_commands = extract_dod_backtick_commands(text)
    dod_roots = {name for cmd in dod_commands if (name := extract_just_recipe_name(cmd))}
    dod_expanded = expand_just_recipe_names(dod_roots, justfile_path=justfile_path)

    missing = sorted(task_recipes - dod_expanded)
    if not missing:
        return []
    shown = missing[:6]
    suffix = " …" if len(missing) > 6 else ""
    return [
        "Quality #10: Task Verify recipes not covered by DoD (direct or aggregate): "
        + ", ".join(f"`just {name}`" for name in shown)
        + suffix
    ]


def lint_blueprint_quality_gates(
    text: str,
    *,
    justfile_path: str = str(DEFAULT_JUSTFILE),
    check_deps: bool = True,
    check_verify_test: bool = True,
    check_dod: bool = True,
) -> tuple[list[str], list[str]]:
    """Run SER blueprint quality gates. Returns (hard_issues, warnings)."""
    if not is_blueprint_markdown(text):
        return [], []

    issues: list[str] = []
    warnings: list[str] = []

    if check_deps:
        issues.extend(lint_execution_order_dependency_sync(text))
    if check_verify_test:
        issues.extend(lint_verify_test_pairing(text, justfile_path=justfile_path))
    if check_dod:
        warnings.extend(lint_dod_verify_coverage(text, justfile_path=justfile_path))

    return issues, warnings
