from __future__ import annotations

import re

from scripts.plan_loop.plan_lint.shared import (
    BAD_PATTERNS,
    CANONICAL_TODO_CONCLUSION_SLOTS,
    CJK_CHAR_RE,
    CONCLUSION_ALLOWED_MARKERS,
    KOREAN_CHAR_RE,
    LANG_KO_RE,
    TASK_ID_PATTERN,
    TASK_PREREAD_MARKER,
    _is_unfilled_csf_hint,
    _is_valid_open_conclusion,
    _looks_like_premature_measured_conclusion,
    CONCLUSION_FIELD_LINE_RE,
    EXTRA_TASK_CONCLUSION_HEADING_RE,
)

UPPERCASE_BRACKET_PLACEHOLDER_RE = re.compile(r"^\[[A-Z][A-Z0-9_\s-]*\]$")
BRACKET_ONLY_VALUE_RE = re.compile(r"^\[[^\]]+\]$")


def _is_bracket_slot_placeholder(normalized: str) -> bool:
    """Bracket-only template values ([TBD], [목표 이름], …) excluding Task-ID patterns."""
    if not BRACKET_ONLY_VALUE_RE.fullmatch(normalized):
        return False
    if TASK_ID_PATTERN.match(normalized):
        return False
    if UPPERCASE_BRACKET_PLACEHOLDER_RE.fullmatch(normalized):
        return True
    if normalized in CANONICAL_TODO_CONCLUSION_SLOTS or _is_unfilled_csf_hint(normalized):
        return True
    inner = normalized[1:-1]
    # AGENTS.md §4.4: Conclusion은 최소 25자 이상. 25자 이상이면 실제 Conclusion로 인정.
    if len(inner) >= 25:
        return False
    return bool(KOREAN_CHAR_RE.search(inner))


def _check_korean_first(text: str) -> list[str]:
    """: <!-- Language: ko --> 마커가 있으면 본문 한자(Unified Ideographs) 검사."""
    if not LANG_KO_RE.search(text):
        return []
    matches = CJK_CHAR_RE.findall(text)
    if not matches:
        return []
    unique = sorted(set(matches))
    return [f"한자 혼용 감지 ({', '.join(unique)}) — `<!-- Language: ko -->` 파일은 한국어 사용"]


def _is_placeholder_value(value: str) -> bool:
    normalized = value.strip()
    if not normalized:
        return True

    if normalized in ("...", "…"):
        return True

    # Exclude Task ID patterns like [PLAN-001], [LINT-001] from placeholder check
    if TASK_ID_PATTERN.match(normalized):
        return False

    for pattern in BAD_PATTERNS:
        if re.search(pattern, normalized):
            return True

    return _is_bracket_slot_placeholder(normalized)


def _is_conclusion_placeholder(value: str) -> bool:
    """Conclusion 전용 placeholder 체크 — 결과 마커([PASS], [FAIL]] 등)는 허용."""
    normalized = value.strip()
    if not normalized:
        return True

    # 허용된 결과 마커로 시작하면 통과 (예: "[PASS] tests/api/... 생성." )
    for marker in CONCLUSION_ALLOWED_MARKERS:
        if normalized.startswith(marker):
            return False

    # 기존 BAD_PATTERns 중 Conclusion에 민감한 것만 적용
    for pattern in BAD_PATTERNS:
        if re.search(pattern, normalized):
            return True

    return _is_bracket_slot_placeholder(normalized)


def _lint_open_task_conclusion(task_idx: int, status: str, value: str) -> list[str]:
    """todo/running must keep CSF slot; measured Conclusion only after Verify + done."""
    issues: list[str] = []
    if status not in ("todo", "running"):
        return issues
    if _looks_like_premature_measured_conclusion(value):
        issues.append(
            f"Task#{task_idx} Status={status!r} but Conclusion reads like post-Verify "
            "measured text; use CSF slot "
            "'[판정 — 비개발자용 요약. 검증 결과]' until Verify PASS, then Status: done"
        )
        return issues
    if not _is_valid_open_conclusion(value):
        issues.append(
            f"Task#{task_idx} Status={status!r}: Conclusion must be a CSF slot hint "
            "(e.g. '[판정 — 비개발자용 요약. 검증 결과]'), not narrative or predicted results"
        )
    return issues


def _lint_task_conclusion_slot(task_idx: int, block: str) -> list[str]:
    """FAIL if a blueprint task has duplicate Conclusion fields or extra headings."""
    issues: list[str] = []
    conclusion_lines = len(CONCLUSION_FIELD_LINE_RE.findall(block))
    if conclusion_lines > 1:
        issues.append(
            f"Task#{task_idx} has {conclusion_lines} Conclusion field lines — "
            "keep exactly one '- **Conclusion**:' and replace it in-place "
            "(do not append a second Conclusion at the task bottom)"
        )
    extra_headings = EXTRA_TASK_CONCLUSION_HEADING_RE.findall(block)
    if extra_headings:
        issues.append(
            f"Task#{task_idx} contains Conclusion heading inside the task block "
            f"({extra_headings[0]!r}) — use only a single '- **Conclusion**:' line"
        )
    return issues


def _lint_task_preread_block(task_idx: int, block: str) -> list[str]:
    """Task-level Pre-read must be machine-generated and list routable paths."""
    issues: list[str] = []
    if TASK_PREREAD_MARKER not in block:
        issues.append(
            f"Task#{task_idx} missing Task-level Pre-read — "
            "run: just plan-preread docs/plans/<file>.md --write"
        )
        return issues
    if not re.search(
        r"`(?:\.agents|docs|apps|src|scripts|PROJECT_RULES\.md)|`PROJECT_RULES\.md`",
        block,
    ):
        issues.append(
            f"Task#{task_idx} Pre-read has no installed paths — "
            "set concrete Target, then: just plan-preread docs/plans/<file>.md --write"
        )
    return issues


def _lint_preread_gate(content: str) -> list[str]:
    """Context Pre-read Gate must be machine-generated (plan_preread_manifest.py)."""
    issues: list[str] = []
    if "## 🧭 Context Pre-read Gate" not in content:
        return issues
    if "<!-- plan-preread:v1" not in content:
        issues.append(
            "Context Pre-read Gate missing plan-preread:v1 marker — "
            "run: just plan-preread docs/plans/<this-file>.md --write"
        )
        return issues
    block_match = re.search(
        r"## 🧭 Context Pre-read Gate.*?(?=^## |\Z)",
        content,
        re.MULTILINE | re.DOTALL,
    )
    if not block_match:
        return issues
    block = block_match.group(0)
    if "### Read SSOT" not in block:
        issues.append(
            "Context Pre-read Gate missing '### Read SSOT' subsection — "
            "run: just plan-preread docs/plans/<file>.md --write"
        )
    marker = re.search(r"<!-- plan-preread:v1[^>]*paths=(\d+)", block)
    if marker and int(marker.group(1)) > 0 and "plan-task-preread:v1" not in content:
        issues.append(
            "Plan has routable paths but no Task-level Pre-read markers — "
            "run: just plan-preread docs/plans/<file>.md --write"
        )
    return issues


def _shell_chain_parts(text: str) -> list[str]:
    """Split one shell fragment; ignore `;` `&&` `||` inside quotes only.

    Shell redirection operators (>, <, >>, 2>&1, etc.) are NOT chain separators
    and should not cause splitting. Only ; && || are chain operators.
    """
    stripped = text
    bucket: list[str] = []

    def _mask(m: re.Match[str]) -> str:
        bucket.append(m.group(0))
        return f"\x00QSEG{len(bucket) - 1}\x00"

    # Mask quotes first (existing behavior)
    stripped = re.sub(r"'[^']*'", _mask, stripped)
    stripped = re.sub(r'"[^"]*"', _mask, stripped)

    # Split only on actual chain operators: ; && ||
    # Shell redirection (>, <, >>, 2>&1, etc.) must NOT cause splitting
    return [s.strip() for s in re.split(r";\s*|&&|\|\|", stripped) if s.strip()]


_PATH_ONLY_BACKTICK_RE = re.compile(r"^[\w./-]+\.\w{1,10}$")

_RUNNER_TOKEN_PATTERNS: tuple[str, ...] = (
    r"uv run",
    r"npm run",
    r"bun run",
    r"pnpm(?:\s+exec)?",
    r"just",
    r"pytest",
    r"python3?",
    r"cd",
    r"rg",
    r"grep",
    r"test",
    r"wc",
    r"curl",
    r"bash",
)


_UV_RUN_SUBPROCESS_RE = re.compile(r"^(?:pytest|python3?)\b", re.IGNORECASE)


def _count_runner_tokens(segment: str) -> int:
    """Count distinct runner invocations in one shell segment (uv run pytest = one)."""
    text = segment
    count = 0
    while text:
        best_match: re.Match[str] | None = None
        for pattern in _RUNNER_TOKEN_PATTERNS:
            match = re.search(rf"\b{pattern}\b", text, re.IGNORECASE)
            if match and (best_match is None or match.start() < best_match.start()):
                best_match = match
        if best_match is None:
            break
        count += 1
        remainder = text[best_match.end() :].lstrip()
        if best_match.group(0).lower() == "uv run":
            subprocess = _UV_RUN_SUBPROCESS_RE.match(remainder)
            if subprocess:
                remainder = remainder[subprocess.end() :].lstrip()
        text = remainder
    return count


def _is_shell_backtick(inner: str) -> bool:
    """True when backtick content is a shell invocation (not inline path/field names)."""
    text = inner.strip()
    if not text:
        return False
    if _PATH_ONLY_BACKTICK_RE.match(text) and not re.search(r"[;&]|\|\||&&", text):
        return False
    if _verify_segment_runner(text):
        return True
    if re.match(r"^(cd|rg |grep |test |wc |curl |bash )", text, re.IGNORECASE):
        return True
    if re.search(r"[;&]|\|\||&&", text):
        return True
    return False


def _verify_command_segments(verify: str) -> list[str]:
    """Split Verify into atomic shell segments (shell-like backticks only)."""
    segments: list[str] = []
    for match in re.finditer(r"`([^`]*)`", verify):
        inner = match.group(1)
        if _is_shell_backtick(inner):
            segments.extend(_shell_chain_parts(inner))
    if segments:
        return segments
    stripped = verify.strip()
    if not stripped:
        return []
    return _shell_chain_parts(stripped)


def _verify_segment_runner(segment: str) -> bool:
    """One invocation per segment (uv run pytest counts as one)."""
    if re.search(r"\buv run\b", segment, re.IGNORECASE):
        return True
    if re.match(
        r"^(cd|rg|grep|test|wc|curl|bash)\b",
        segment.strip(),
        re.IGNORECASE,
    ):
        return True
    return bool(
        re.search(
            r"\b(just|pytest|pnpm(?:\s+exec)?|npm run|bun run|python3?)\b",
            segment,
            re.IGNORECASE,
        )
    )


def _extract_target_paths(target: str) -> list[str]:
    """Extract discrete repo paths from Target (backtick-first; splits space/comma/middot)."""

    def _split_chunk(chunk: str) -> list[str]:
        return [p.strip() for p in re.split(r"[,·]|\s+", chunk) if p.strip()]

    backticks = re.findall(r"`([^`]+)`", target)
    if backticks:
        paths: list[str] = []
        for inner in backticks:
            paths.extend(_split_chunk(inner))
        return paths
    return [p.strip() for p in re.split(r"[,·]", target) if p.strip()]


def _atomic_unit_contract_issues(task_idx: int, fields: dict[str, str]) -> list[str]:
    """Hard FAIL: violates single-Verify atomic ticket (.agents/workflows/plan.md §1.10)."""
    issues: list[str] = []
    verify = (fields.get("Verify") or "").strip()
    if not verify:
        return issues

    segments = _verify_command_segments(verify)
    if len(segments) >= 2:
        issues.append(
            f"Task#{task_idx} Verify must be one shell command (found {len(segments)} segments "
            "from ;, &&, ||) — split into separate [Unit: Atomic] tasks"
        )
    elif len(segments) == 1:
        runner_hits = _count_runner_tokens(segments[0])
        if runner_hits >= 2:
            issues.append(
                f"Task#{task_idx} Verify must be one runner invocation — "
                "split tasks or use one composite just recipe"
            )

    goal = (fields.get("Goal") or "").strip()
    issues.extend(_validate_goal_atomicity_conjunctions(goal))

    issues.extend(_single_proof_verify_issues(task_idx, verify))

    return issues


def _single_proof_verify_issues(task_idx: int, verify: str) -> list[str]:
    """FAIL: pytest without narrow selector cannot prove one outcome (plan.md §1.9 Single Proof)."""
    issues: list[str] = []
    segments = _verify_command_segments(verify)
    if len(segments) != 1:
        return issues
    segment = segments[0]
    if not re.search(r"\bpytest\b", segment, re.IGNORECASE):
        return issues
    if re.search(r"-k\s+\S", segment) or "::" in segment:
        return issues
    if re.search(
        r"\bpytest\b.*?(?:tests/|[\w./-]+\.py)(?:\s|$)",
        segment,
        re.IGNORECASE,
    ):
        issues.append(
            f"Task#{task_idx} Verify must prove one automated outcome "
            "(use pytest -k <one> or path::test_name) — split tasks"
        )
    return issues


def _validate_goal_atomicity_conjunctions(goal_text: str) -> list[str]:
    """: Goal 원자성 검사 — 한국어 접속사 (및, 그리고, 또한, 동시에) 감지.

    Returns list of error messages if forbidden conjunctions found.
    """
    issues: list[str] = []
    if not goal_text:
        return issues

    # Forbidden Korean conjunctions that indicate non-atomic goals
    forbidden_conjunctions = ["및", "그리고", "또한", "또한번", "동시에"]

    for conj in forbidden_conjunctions:
        # Word boundary or whitespace-isolated conjunction detection
        if re.search(rf"\s+{conj}\s+", goal_text):
            issues.append(
                f"Goal must be atomic. Found forbidden conjunction: '{conj}'"
            )

    return issues


def _atomic_unit_size_warnings(task_idx: int, fields: dict[str, str]) -> list[str]:
    """WARN-only heuristics: atomic tag present but task may still be oversized."""
    warnings: list[str] = []
    verify = (fields.get("Verify") or "").strip()
    target = (fields.get("Target") or "").strip()
    goal = (fields.get("Goal") or "").strip()
    action = (fields.get("Action") or "").strip()

    if verify:
        segments = _verify_command_segments(verify)
        if len(segments) == 1:
            runner_hits = _count_runner_tokens(segments[0])
            if runner_hits >= 2:
                warnings.append(
                    f"Task#{task_idx} Verify names {runner_hits} runners "
                    "(just/pytest/pnpm/uv/…) — split tasks or one composite verify"
                )

    if target:
        if re.search(
            r"\.\.\.|…|\b(multiple|several|various)\b|"
            r"\bTBD\b|\btbd\b|전체|모든\s|일괄",
            target,
            re.IGNORECASE,
        ):
            warnings.append(
                f"Task#{task_idx} Target looks vague — list concrete file path(s)"
            )

        paths = _extract_target_paths(target)
        if len(paths) > 3:
            warnings.append(
                f"Task#{task_idx} Target lists {len(paths)} paths — "
                "consider MUC grouping with one Verify or split tasks"
            )

        broad_dir_suffixes = (
            "/src/app",
            "/src/components",
            "/src/features",
            "/src/store",
            "{{FRONTEND_APP_PATH}}/src",
        )
        for path in paths:
            normalized = path.rstrip("/")
            if "." not in normalized.split("/")[-1]:
                if any(normalized.endswith(suffix) for suffix in broad_dir_suffixes):
                    warnings.append(
                        f"Task#{task_idx} Target is broad directory `{path}` — "
                        "prefer a single file or named file batch"
                    )
                    break

    scope = f"{action} {goal}"
    if re.search(
        r"구현\s*전체|전면\s*|entire|full\s+implementation|리팩터\s*전체|"
        r"whole\s+module|end-to-end\s+implementation",
        scope,
        re.IGNORECASE,
    ):
        warnings.append(
            f"Task#{task_idx} Goal/Action suggests whole-feature scope — "
            "split into atomic tasks"
        )

    return warnings


ROLLUP_SUMMARY_SECTION_RE = re.compile(
    r"^##\s*🔁\s*Conclusion\s*&\s*Summary\s*$",
    re.MULTILINE,
)

ROLLUP_PLACEHOLDER_LINE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"^\(Roll-up:", re.IGNORECASE),
    re.compile(r"완료\s*후\s*기입"),
    re.compile(r"완료\s*후\s*갱신"),
    re.compile(r"\(Task\s+완료\s*후"),
    re.compile(r"closeout\s*후\s*기입", re.IGNORECASE),
    re.compile(r"^\[Roll-up\s*—", re.IGNORECASE),
    re.compile(r"^\-\s*\*\*Roll-up\*\*:\s*…\s*$"),
    re.compile(r"^\-\s*\*\*Roll-up\*\*:\s*\.\.\.\s*$"),
    re.compile(r"^\[완료\s*시\s*기입\]"),
)

_MIN_ROLLUP_SUMMARY_LENGTH = 25


def extract_rollup_summary_body(text: str) -> str | None:
    """Return non-heading body under ## Conclusion & Summary, or None if missing."""
    match = ROLLUP_SUMMARY_SECTION_RE.search(text)
    if not match:
        return None
    start = match.end()
    next_section = re.search(r"\n## ", text[start:])
    end = start + next_section.start() if next_section else len(text)
    return text[start:end].strip()


def is_rollup_summary_placeholder(body: str) -> bool:
    """True when Roll-up section is empty or still a template hint."""
    normalized = body.strip()
    if not normalized:
        return True
    if len(normalized) < _MIN_ROLLUP_SUMMARY_LENGTH:
        return True
    for line in normalized.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        for pattern in ROLLUP_PLACEHOLDER_LINE_PATTERNS:
            if pattern.search(stripped):
                return True
        for bad in BAD_PATTERNS:
            if re.search(bad, stripped):
                return True
        if stripped in CANONICAL_TODO_CONCLUSION_SLOTS:
            return True
    return False


def _closeout_task_is_done(text: str) -> bool:
    """True when a Blueprint closeout task (Roll-up Goal + plan-close Verify) is done."""
    from scripts.plan_loop.plan_lint.shared import _parse_fields, _split_task_blocks

    for block in _split_task_blocks(text):
        fields = _parse_fields(block)
        goal = (fields.get("Goal") or "").lower()
        verify = (fields.get("Verify") or "").lower()
        status = (fields.get("Status") or "").lower()
        if "roll-up" in goal and "plan-close" in verify and status == "done":
            return True
    return False


def _lint_rollup_summary_section(text: str) -> list[str]:
    """FAIL when closeout Task is done but document Roll-up is still a placeholder."""
    if not ROLLUP_SUMMARY_SECTION_RE.search(text):
        return []
    body = extract_rollup_summary_body(text) or ""
    if not _closeout_task_is_done(text):
        return []
    if is_rollup_summary_placeholder(body):
        return [
            "Conclusion & Summary Roll-up is still a placeholder — "
            "write a measured 1-paragraph summary under "
            "'## 🔁 Conclusion & Summary' before closing the closeout Task "
            "(see .agents/workflows/plan.md closeout gate)"
        ]
    return []


def check_rollup_summary_for_close(text: str) -> list[str]:
    """plan-close gate: Roll-up section must be filled before plan completion."""
    body = extract_rollup_summary_body(text)
    if body is None:
        return ["missing section: ## 🔁 Conclusion & Summary"]
    if is_rollup_summary_placeholder(body):
        preview = body.splitlines()[0][:80] if body else "(empty)"
        return [
            "Conclusion & Summary Roll-up is still a placeholder — "
            f"current: {preview!r}. "
            "Write a measured 1-paragraph summary before running plan-close."
        ]
    return []


ROLLUP_SUMMARY_SECTION_RE = re.compile(
    r"^##\s*🔁\s*Conclusion\s*&\s*Summary\s*$",
    re.MULTILINE,
)

ROLLUP_PLACEHOLDER_LINE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"^\(Roll-up:", re.IGNORECASE),
    re.compile(r"완료\s*후\s*기입"),
    re.compile(r"완료\s*후\s*갱신"),
    re.compile(r"\(Task\s+완료\s*후"),
    re.compile(r"closeout\s*후\s*기입", re.IGNORECASE),
    re.compile(r"^\[Roll-up\s*—", re.IGNORECASE),
    re.compile(r"^\-\s*\*\*Roll-up\*\*:\s*…\s*$"),
    re.compile(r"^\-\s*\*\*Roll-up\*\*:\s*\.\.\.\s*$"),
    re.compile(r"^\[완료\s*시\s*기입\]"),
)

_MIN_ROLLUP_SUMMARY_LENGTH = 25


def extract_rollup_summary_body(text: str) -> str | None:
    """Return non-heading body under ## Conclusion & Summary, or None if missing."""
    match = ROLLUP_SUMMARY_SECTION_RE.search(text)
    if not match:
        return None
    start = match.end()
    next_section = re.search(r"\n## ", text[start:])
    end = start + next_section.start() if next_section else len(text)
    return text[start:end].strip()


def is_rollup_summary_placeholder(body: str) -> bool:
    """True when Roll-up section is empty or still a template hint."""
    normalized = body.strip()
    if not normalized:
        return True
    if len(normalized) < _MIN_ROLLUP_SUMMARY_LENGTH:
        return True
    for line in normalized.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        for pattern in ROLLUP_PLACEHOLDER_LINE_PATTERNS:
            if pattern.search(stripped):
                return True
        for bad in BAD_PATTERNS:
            if re.search(bad, stripped):
                return True
        if stripped in CANONICAL_TODO_CONCLUSION_SLOTS:
            return True
    return False


def _closeout_task_is_done(text: str) -> bool:
    """True when a Blueprint closeout task (Roll-up Goal + plan-close Verify) is done."""
    from scripts.plan_loop.plan_lint.shared import _parse_fields, _split_task_blocks

    for block in _split_task_blocks(text):
        fields = _parse_fields(block)
        goal = (fields.get("Goal") or "").lower()
        verify = (fields.get("Verify") or "").lower()
        status = (fields.get("Status") or "").lower()
        if "roll-up" in goal and "plan-close" in verify and status == "done":
            return True
    return False


def _lint_rollup_summary_section(text: str) -> list[str]:
    """FAIL when closeout Task is done but document Roll-up is still a placeholder."""
    if not ROLLUP_SUMMARY_SECTION_RE.search(text):
        return []
    body = extract_rollup_summary_body(text) or ""
    if not _closeout_task_is_done(text):
        return []
    if is_rollup_summary_placeholder(body):
        return [
            "Conclusion & Summary Roll-up is still a placeholder — "
            "write a measured 1-paragraph summary under "
            "'## 🔁 Conclusion & Summary' before closing the closeout Task "
            "(see .agents/workflows/plan.md closeout gate)"
        ]
    return []


def check_rollup_summary_for_close(text: str) -> list[str]:
    """plan-close gate: Roll-up section must be filled before plan completion."""
    body = extract_rollup_summary_body(text)
    if body is None:
        return ["missing section: ## 🔁 Conclusion & Summary"]
    if is_rollup_summary_placeholder(body):
        preview = body.splitlines()[0][:80] if body else "(empty)"
        return [
            "Conclusion & Summary Roll-up is still a placeholder — "
            f"current: {preview!r}. "
            "Write a measured 1-paragraph summary before running plan-close."
        ]
    return []
