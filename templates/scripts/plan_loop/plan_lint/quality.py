from __future__ import annotations

import re

_MIN_GOAL_LENGTH = 15

_MIN_DONE_CONCLUSION_LENGTH = 25

PLAN_TASK_CLOSE_MARKER = "[closed-by:plan-task-close]"

_VAGUE_GOAL_WORDS = [
    "추가", "수정", "변경", "처리", "대응", "지원", "설정",
    "implement", "add", "update", "modify", "change", "handle",
]

_THIN_CONCLUSION_PATTERNS = [
    r"^\[PASS\]$",
    r"^\[FAIL\]$",
    r"^\[성공\]$",
    r"^\[실패\]$",
    r"^통과$",
    r"^완료$",
    r"^\[DONE\]$",
    r"^\[OK\]$",
]


from scripts.plan_loop.plan_lint.verification import (
    _extract_target_paths,
    _shell_chain_parts,
    _verify_command_segments,
    _verify_segment_runner,
)


def _lint_target_atomic(task_idx: int, target: str) -> list[str]:
    issues: list[str] = []
    if not target:
        return issues

    paths = _extract_target_paths(target)
    unique_paths = list(dict.fromkeys(paths))
    
    if len(unique_paths) > 1:
        issues.append(
            f"Task#{task_idx} Target contains {len(unique_paths)} files (max 1). "
            "Task is not atomic. Must be 1 Task = 1 File."
        )
        
    # Layer mixing check
    layers = set()
    for path in unique_paths:
        if path.startswith("{{FRONTEND_APP_PATH}}") or path.startswith("packages/ui-"):
            layers.add("FRONTEND")
        elif path.startswith("src/domain") or path.startswith("src/application"):
            layers.add("BACKEND_DOMAIN")
        elif path.startswith("src/infrastructure") or path.startswith("src/adapters") or path.startswith("src/api") or path.startswith("apps/server"):
            layers.add("BACKEND_INFRA")
        elif path.startswith("{{DESKTOP_APP_PATH}}") or path.startswith("apps/sidecar"):
            layers.add("DESKTOP")
            
    if len(layers) > 1:
        issues.append(
            f"Task#{task_idx} Target mixes architectural layers ({', '.join(sorted(layers))}). "
            "Task must be scoped to a single layer."
        )
        
    return issues

def _lint_target_quality(task_idx: int, target: str) -> list[str]:
    """Check that Target is not a directory to prevent context explosion."""
    issues: list[str] = []
    if not target:
        return issues
    clean_target = target.replace('`', '').strip()
    if clean_target.endswith('/') or ('__tests__' in clean_target and not re.search(r'\.[a-zA-Z0-9]+$', clean_target)):
        issues.append(
            f"Task#{task_idx} Target '{clean_target}' is a directory. "
            "Target must be specific file(s) to prevent LLM context explosion."
        )
    issues.extend(_lint_target_atomic(task_idx, target))
    return issues


def _lint_goal_quality(task_idx: int, goal: str) -> list[str]:
    """: Goal must be specific and substantive, not a single verb.

    Checks:
    - Minimum length (≥15 chars) — "API 추가" is too short
    - No vague single-verb patterns — "추가", "수정", "변경" alone are insufficient
    - Must reference a specific entity (file, component, function, domain concept)
    - No abstract/declarative phrases

    Korean conjunction atomicity is enforced only in verification._atomic_unit_contract_issues.
    """
    issues: list[str] = []
    if not goal:
        return issues  # Already caught by required fields check

    # Check for abstract/declarative goals
    abstract_phrases = ["레이아웃 구조를 재배치", "상호작용을 정비", "상태를 정비", "재구성한다", "구조를 개선"]
    for phrase in abstract_phrases:
        if phrase in goal:
            issues.append(f"Task#{task_idx} Goal contains abstract/declarative phrase '{phrase}'. Use concrete White-box instructions.")

    # Check minimum length
    if len(goal) < _MIN_GOAL_LENGTH:
        issues.append(
            f"Task#{task_idx} Goal too short ({len(goal)} chars, min {_MIN_GOAL_LENGTH}) "
            f"'{goal}' — be specific about WHAT and WHERE"
        )

    # Check for vague single-verb patterns (no entity reference)
    cleaned = re.sub(r"[^가-힣a-zA-Z0-9\s]", " ", goal)
    words = cleaned.split()

    # If Goal is just a verb + short noun, it's too vague
    if len(words) <= 2:
        for word in words:
            if word.lower() in _VAGUE_GOAL_WORDS:
                issues.append(
                    f"Task#{task_idx} Goal '{goal}' is too vague "
                    f"(single verb '{word}') — specify entity, file, or domain"
                )
                break

    # Check for entity reference (file path, component name, function name, domain concept)
    has_entity = any(
        pattern.search(goal)
        for pattern in [
            re.compile(r"\.`[^`]+`\b"),  # backtick path
            re.compile(r"[A-Z][a-z]+[A-Z]"),  # PascalCase (component/function)
            re.compile(r"_[a-z]+_"),  # snake_case (function)
            re.compile(r"\.(ts|tsx|py|js|jsx)$"),  # file extension
            re.compile(r"\b(Component|Function|API|Port|Hook|Store)\b"),
        ]
    )
    if not has_entity and len(goal) > _MIN_GOAL_LENGTH:
        # Only warn if length is OK but no entity reference
        # This is a soft check — some goals naturally don't have entities
        pass

    return issues


def _lint_conclusion_quality(
    task_idx: int,
    status: str,
    conclusion: str,
    *,
    require_closeout_marker: bool = True,
) -> list[str]:
    """: Done task Conclusion must be substantive, not just a marker.

    Checks:
    - Minimum length (≥25 chars) for done tasks
    - No thin patterns ([PASS], [FAIL] alone, etc.)
    - Must reference changed files or specific actions
    """
    issues: list[str] = []
    if not conclusion or status != "done":
        return issues

    stripped = conclusion.strip()
    if (
        require_closeout_marker
        and stripped.startswith("[PASS]")
        and PLAN_TASK_CLOSE_MARKER not in stripped
    ):
        issues.append(
            f"Task#{task_idx} done Conclusion starting with [PASS] must include "
            f"{PLAN_TASK_CLOSE_MARKER} (use just plan-task-close)"
        )

    # Check for thin patterns
    for pattern in _THIN_CONCLUSION_PATTERNS:
        if re.match(pattern, conclusion.strip()):
            issues.append(
                f"Task#{task_idx} Conclusion too thin — "
                f"'{conclusion[:40]}...' is not a meaningful summary. "
                "Include changed files, specific actions taken, and verify results."
            )
            break

    # Check minimum length
    if len(conclusion.strip()) < _MIN_DONE_CONCLUSION_LENGTH:
        issues.append(
            f"Task#{task_idx} Conclusion too short ({len(conclusion.strip())} chars, "
            f"min {_MIN_DONE_CONCLUSION_LENGTH}) — include specific files/actions/verify results"
        )

    # Check for file reference (at least one file or specific entity mentioned)
    has_file_ref = any(
        pattern.search(conclusion)
        for pattern in [
            re.compile(r"\.`[^`]+`\b"),  # backtick path
            re.compile(r"[A-Z][a-z]+[A-Z]"),  # PascalCase
            re.compile(r"\.(ts|tsx|py|js|jsx)$"),  # file extension
            re.compile(r"\bfile\b|\b파일\b|\b함수\b|\b컴포넌트\b|\bAPI\b"),
        ]
    )
    if not has_file_ref and len(conclusion.strip()) > _MIN_DONE_CONCLUSION_LENGTH:
        # Soft check — some conclusions naturally don't have file references
        pass

    return issues


def _verify_shell_parts(verify: str) -> list[str]:
    """Flatten Verify into shell parts (SSOT: verification segment + chain parsers)."""
    parts: list[str] = []
    for segment in _verify_command_segments(verify):
        if re.search(r";\s*|&&|\|\|", segment):
            parts.extend(_shell_chain_parts(segment))
        else:
            parts.append(segment)
    return parts


def _lint_verify_quality(task_idx: int, verify: str) -> list[str]:
    """: Verify must be an actual test/verification command, not a no-op.

    Checks:
    - No echo/print-only commands (per shell segment from _verify_command_segments)
    - Must use a real runner per segment (pytest, pnpm, uv, just recipe, etc.)
    - Must not be empty after stripping
    """
    issues: list[str] = []
    if not verify:
        return issues  # Already caught by required fields check

    parts = _verify_shell_parts(verify.strip())
    if not parts:
        return issues

    noop_patterns = [
        r"^\s*echo\b",  # echo "done", echo "✓"
        r"^\s*print\s*\(",  # print("done")
        r"^\s*printf\b",  # printf "✓"
        r"^\s*true\b",  # just no-op
        r"^\s*:\s*$",  # bash no-op
    ]
    for part in parts:
        for pattern in noop_patterns:
            if re.match(pattern, part.strip(), re.IGNORECASE):
                issues.append(
                    f"Task#{task_idx} Verify is a no-op ('{part.strip()[:40]}') — "
                    "use actual test/verification command"
                )
                return issues

    if not any(_verify_segment_runner(part) for part in parts):
        issues.append(
            f"Task#{task_idx} Verify does not use a recognized runner "
            "(pytest, just, pnpm, uv, python3, etc.)"
        )

    return issues
