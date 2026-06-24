"""Parse Justfile recipe names for plan-lint DoD validation."""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_JUSTFILE = REPO_ROOT / "Justfile"


def extract_just_recipe_name(command: str) -> str | None:
    """First recipe name from a shell command like `just plan-lint docs/plans/PLAN_xxx.md`."""
    stripped = command.strip()
    if not stripped.startswith("just "):
        return None
    rest = stripped.removeprefix("just ").strip()
    if not rest:
        return None
    return rest.split()[0]


def _recipe_name_from_header_line(line: str) -> str | None:
    """Return recipe name when line is a Justfile recipe header."""
    if not line or line[0].isspace() or line.startswith("\t"):
        return None
    if ":=" in line or line.strip().startswith("["):
        return None
    head = line.split("#", 1)[0].rstrip()
    if not head.endswith(":"):
        return None
    token = head[:-1].strip().split()[0]
    if re.fullmatch(r"[a-zA-Z][a-zA-Z0-9_-]*", token):
        return token
    return None


_IMPORT_RE = re.compile(r'^\s*import\s+"([^"]+)"\s*(?:#.*)?$')


def _resolve_justfile_chain(
    justfile_path: Path,
    *,
    visited: frozenset[Path] | None = None,
) -> list[Path]:
    """Root justfile plus transitively imported modules (cycle-safe, root first)."""
    resolved = justfile_path.resolve()
    if not resolved.is_file():
        return []
    seen = visited or frozenset()
    if resolved in seen:
        return []
    next_seen = seen | {resolved}
    chain = [resolved]
    for line in resolved.read_text(encoding="utf-8").splitlines():
        match = _IMPORT_RE.match(line)
        if not match:
            continue
        imported = (resolved.parent / match.group(1)).resolve()
        chain.extend(_resolve_justfile_chain(imported, visited=next_seen))
    return chain


def _parse_recipe_bodies_from_file(path: Path) -> dict[str, str]:
    bodies: dict[str, list[str]] = {}
    current: str | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        name = _recipe_name_from_header_line(line)
        if name:
            current = name
            bodies[current] = []
            continue
        if current is not None:
            bodies[current].append(line)
    return {name: "\n".join(lines) for name, lines in bodies.items()}


def clear_justfile_recipe_caches() -> None:
    """Clear LRU caches — call from tests after Justfile edits."""
    load_justfile_recipe_names.cache_clear()
    load_justfile_recipe_bodies.cache_clear()


@lru_cache(maxsize=4)
def load_justfile_recipe_names(justfile_path: str) -> frozenset[str]:
    path = Path(justfile_path)
    names: set[str] = set()
    for jf in _resolve_justfile_chain(path):
        for line in jf.read_text(encoding="utf-8").splitlines():
            name = _recipe_name_from_header_line(line)
            if name:
                names.add(name)
    return frozenset(names)


_JUST_INVOKE_RE = re.compile(r"\bjust\s+([a-zA-Z][a-zA-Z0-9_-]*)")


@lru_cache(maxsize=4)
def load_justfile_recipe_bodies(justfile_path: str) -> dict[str, str]:
    """Map Justfile recipe name → recipe body (indented lines only)."""
    path = Path(justfile_path)
    bodies: dict[str, str] = {}
    for jf in _resolve_justfile_chain(path):
        bodies.update(_parse_recipe_bodies_from_file(jf))
    return bodies


def expand_just_recipe_names(
    roots: set[str],
    *,
    justfile_path: str = str(DEFAULT_JUSTFILE),
) -> frozenset[str]:
    """Expand aggregate recipes via `just sub-recipe` references in Justfile bodies."""
    bodies = load_justfile_recipe_bodies(justfile_path)
    expanded = set(roots)
    pending = list(roots)
    while pending:
        name = pending.pop()
        body = bodies.get(name, "")
        for match in _JUST_INVOKE_RE.finditer(body):
            sub = match.group(1)
            if sub not in expanded:
                expanded.add(sub)
                pending.append(sub)
    return frozenset(expanded)
