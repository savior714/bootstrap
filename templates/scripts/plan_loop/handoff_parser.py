"""Parse agent hand-off markdown into Blueprint scaffold inputs."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_BOUNDED_SCOPE_HEADING_RE = re.compile(
    r"(?:###\s+)?Bounded\s+scope|편집\s*허용\s*경로",
    re.IGNORECASE,
)
_FENCED_CODE_RE = re.compile(r"```[^\n]*\n(.*?)```", re.DOTALL)
_DOD_HEADING_RE = re.compile(
    r"(?:###\s+)?(?:Verify\s*\(DoD\)|Definition of Done|DoD)",
    re.IGNORECASE,
)
_SPEC_PATH_RE = re.compile(r"`(docs/specs/[^`]+\.md)`")
_BACKTICK_CMD_RE = re.compile(
    r"^[-*]\s+`((?:just |uv run |pnpm |pytest )[^`]+)`",
    re.MULTILINE,
)
_RECOMMENDED_ORDER_RE = re.compile(
    r"(?:###\s+)?권장\s*작업\s*순서|Recommended\s+(?:work\s+)?order",
    re.IGNORECASE,
)
_NUMBERED_ITEM_RE = re.compile(r"^\s*\d+\.\s+\*\*(.+?)\*\*|^\s*\d+\.\s+(.+)$", re.MULTILINE)
_OUT_OF_SCOPE_RE = re.compile(
    r"(?:###\s+)?(?:Out of scope|이번에\s*안\s*하는\s*것|범위\s*밖)",
    re.IGNORECASE,
)
_ASK_QUESTION_RE = re.compile(r"AskQuestion|제품\s*정책", re.IGNORECASE)


@dataclass
class HandoffParseResult:
    title: str
    bounded_paths: list[str] = field(default_factory=list)
    spec_paths: list[str] = field(default_factory=list)
    dod_commands: list[str] = field(default_factory=list)
    recommended_phases: list[str] = field(default_factory=list)
    out_of_scope_lines: list[str] = field(default_factory=list)
    needs_policy_task: bool = False
    origin_summary: str = ""


def _section_after(text: str, heading_re: re.Pattern[str]) -> str:
    match = heading_re.search(text)
    if not match:
        return ""
    rest = text[match.end() :]
    next_heading = re.search(r"\n#{1,3}\s+\S", rest)
    return rest[: next_heading.start()] if next_heading else rest


def _first_fenced_block(section: str) -> str:
    match = _FENCED_CODE_RE.search(section)
    return match.group(1) if match else ""


def _normalize_path_line(line: str) -> str | None:
    stripped = line.strip().strip("`")
    if not stripped or stripped.startswith("#"):
        return None
    if " " in stripped and not stripped.startswith("docs/"):
        return None
    if stripped.endswith("/"):
        return None
    if stripped.endswith("**") or stripped.endswith("*"):
        stripped = stripped.rstrip("*")
    return stripped


def extract_bounded_scope_paths(text: str) -> list[str]:
    section = _section_after(text, _BOUNDED_SCOPE_HEADING_RE)
    if not section:
        return []
    body = _first_fenced_block(section) or section
    paths: list[str] = []
    for line in body.splitlines():
        normalized = _normalize_path_line(line)
        if normalized and normalized not in paths:
            paths.append(normalized)
    return paths


def extract_dod_commands(text: str) -> list[str]:
    section = _section_after(text, _DOD_HEADING_RE)
    if not section:
        return []
    commands: list[str] = []
    for match in _BACKTICK_CMD_RE.finditer(section):
        cmd = match.group(1).strip()
        if cmd and cmd not in commands:
            commands.append(cmd)
    fenced = _first_fenced_block(section)
    if fenced:
        for line in fenced.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("`") and line.endswith("`"):
                cmd = line.strip("`").strip()
            else:
                cmd = line
            if cmd and cmd not in commands:
                commands.append(cmd)
    return commands


def extract_spec_paths(text: str) -> list[str]:
    found = _SPEC_PATH_RE.findall(text)
    unique: list[str] = []
    for path in found:
        if path not in unique:
            unique.append(path)
    return unique


def extract_recommended_phases(text: str) -> list[str]:
    section = _section_after(text, _RECOMMENDED_ORDER_RE)
    if not section:
        return []
    phases: list[str] = []
    for match in _NUMBERED_ITEM_RE.finditer(section):
        label = (match.group(1) or match.group(2) or "").strip()
        label = re.sub(r"\s*—.*$", "", label)
        label = re.sub(r"\s*\(.*\)$", "", label).strip()
        if label and label not in phases:
            phases.append(label)
    return phases


def extract_out_of_scope(text: str) -> list[str]:
    section = _section_after(text, _OUT_OF_SCOPE_RE)
    if not section:
        return []
    lines: list[str] = []
    for line in section.splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            lines.append(stripped[2:].strip())
    return lines


def derive_task_prefix(slug: str, *, override: str | None = None) -> str:
    if override:
        token = re.sub(r"[^A-Za-z]", "", override.upper())
        return token[:4] if len(token) >= 2 else token.ljust(2, "X")
    parts = [p for p in re.split(r"[_-]+", slug) if p]
    letters = "".join(p[0].upper() for p in parts[:4] if p)
    return letters[:4] if len(letters) >= 2 else "PLN"


def _infer_title(text: str, slug: str) -> str:
    for pattern in (
        r"Hand-off\s*Prompt:\s*(.+)",
        r"^#\s+(.+)",
        r"##\s+Hand-off\s*Prompt:\s*(.+)",
    ):
        match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return slug.replace("_", " ")


def _origin_summary(text: str) -> str:
    section = _section_after(text, re.compile(r"배경|Background|사용자\s*의도", re.IGNORECASE))
    if not section:
        return ""
    for line in section.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            return stripped[:200]
    return ""


def parse_handoff_markdown(text: str, *, slug: str, title: str | None = None) -> HandoffParseResult:
    bounded = extract_bounded_scope_paths(text)
    specs = extract_spec_paths(text)
    if not specs:
        specs = [p for p in bounded if p.startswith("docs/specs/")]

    return HandoffParseResult(
        title=title or _infer_title(text, slug),
        bounded_paths=bounded,
        spec_paths=specs,
        dod_commands=extract_dod_commands(text),
        recommended_phases=extract_recommended_phases(text),
        out_of_scope_lines=extract_out_of_scope(text),
        needs_policy_task=bool(_ASK_QUESTION_RE.search(text)),
        origin_summary=_origin_summary(text),
    )


def pick_target_for_phase(phase_label: str, paths: list[str]) -> str | None:
    """Heuristic: map a recommended-order phase label to one bounded path."""
    label = phase_label.lower()
    rules: list[tuple[str, str]] = [
        (r"스펙|spec", r"docs/specs/"),
        (r"테스트|test|tdd", r"tests/"),
        (r"boot|bootstrap|schema", r"run_schema_boot"),
        (r"sql|필터|router", r"order_set_router|router_helpers"),
        (r"관리|admin", r"admin/components"),
        (r"진료|consultation|mock", r"consultation/"),
        (r"shared|타입|ssot", r"packages/shared"),
    ]
    for pattern, path_hint in rules:
        if re.search(pattern, label, re.IGNORECASE):
            for path in paths:
                if path_hint in path.replace("\\", "/"):
                    return path
    return None


def default_verify_for_target(target: str, plan_path: str) -> str:
    normalized = target.replace("\\", "/")
    if normalized.startswith("docs/specs/"):
        return "just docs-ssot-headers"
    if normalized.startswith("docs/plans/"):
        return f"just plan-lint {plan_path}"
    if normalized.startswith("tests/") and normalized.endswith(".py"):
        return f"uv run pytest {normalized}::test_placeholder_red -q"
    if normalized.startswith("{{FRONTEND_APP_PATH}}/"):
        return "just renderer-typecheck"
    if normalized.startswith("src/"):
        return "just lint-be"
    return f"just plan-lint {plan_path}"
