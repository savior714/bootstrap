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


@lru_cache(maxsize=4)
def load_justfile_recipe_names(justfile_path: str) -> frozenset[str]:
    path = Path(justfile_path)
    if not path.is_file():
        return frozenset()
    names: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        name = _recipe_name_from_header_line(line)
        if name:
            names.add(name)
    return frozenset(names)
