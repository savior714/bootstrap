"""Single source of truth for agents directory path."""
from pathlib import Path

AGENTS_REL = "agents"
SCAFFOLD_AGENTS_REL = "scripts/bootstrap/scaffold/agents"
LEGACY_AGENTS_REL = ".agents"  # compatibility symlink target name


def agents_dir(repo_root: Path) -> Path:
    """Return agents/ dir; prefer agents/, fallback .agents/ (symlink compat)."""
    primary = repo_root / AGENTS_REL
    if primary.is_dir():
        return primary
    legacy = repo_root / LEGACY_AGENTS_REL
    if legacy.is_dir():
        return legacy
    return primary  # expected location even if missing


def agents_rel(path_under_agents: str) -> str:
    """Build repo-relative path like agents/core/foo.md"""
    suffix = path_under_agents.lstrip("/")
    return f"{AGENTS_REL}/{suffix}"


# Common constants
ROUTING_FILE = agents_rel("registry/CONTEXT_ROUTING.md")
PROJECT_SKILL_ROUTING_FILE = agents_rel("registry/PROJECT_SKILL_ROUTING.json")
SESSION_MANIFEST_REL = agents_rel("route/session-manifest.json")
