#!/usr/bin/env bash
# Install ../bootstrap/templates into a target project root (bootstrap SSOT).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE_ROOT="${SCRIPT_DIR}/templates"
TARGET_ROOT="${1:-.}"

# Seeded only when absent — do not overwrite project-owned SSOT files.
SEED_ONLY_PATHS=(
  "docs/design.md"
  "docs/agent-context/memory/MEMORY.md"
  "docs/agent-context/memory/changelog/README.md"
  "docs/agent-context/memory/PROJECT_REFACTORING_BACKLOG.md"
)

if [[ ! -d "${TEMPLATE_ROOT}" ]]; then
  echo "[FAIL] templates not found at ${TEMPLATE_ROOT}" >&2
  echo "Run from EMR repo sibling: just bootstrap-sync apply=1" >&2
  exit 1
fi

TARGET_ROOT="$(cd "${TARGET_ROOT}" && pwd)"
echo "Installing bootstrap kernel into ${TARGET_ROOT}"

if [[ -f "${TARGET_ROOT}/AGENTS.md" || -f "${TARGET_ROOT}/verify.sh" ]]; then
  echo "[WARN] Target already has AGENTS.md or verify.sh — files will be overwritten."
  echo "Press Ctrl+C to abort, or wait 5 seconds..."
  sleep 5
fi

rsync_excludes=(--exclude '.gitkeep')
for rel in "${SEED_ONLY_PATHS[@]}"; do
  rsync_excludes+=(--exclude "$rel")
done

rsync -a "${rsync_excludes[@]}" "${TEMPLATE_ROOT}/" "${TARGET_ROOT}/"

seed_if_missing() {
  local rel="$1"
  local dest="${TARGET_ROOT}/${rel}"
  local src="${TEMPLATE_ROOT}/${rel}"
  if [[ -f "$dest" ]]; then
    echo "[SKIP] ${rel} already exists"
    return
  fi
  if [[ ! -f "$src" ]]; then
    echo "[WARN] seed template missing: ${rel}" >&2
    return
  fi
  mkdir -p "$(dirname "$dest")"
  cp "$src" "$dest"
  echo "[SEED] Created ${rel}"
}

echo ""
echo "Project SSOT (seed if missing)..."
for rel in "${SEED_ONLY_PATHS[@]}"; do
  seed_if_missing "$rel"
done

# Legacy handoff path — recommend migration to agent-context/memory
if [[ -d "${TARGET_ROOT}/docs/memory" && ! -f "${TARGET_ROOT}/docs/agent-context/memory/MEMORY.md" ]]; then
  echo "[WARN] docs/memory/ found without docs/agent-context/memory/MEMORY.md"
  echo "       Migrate handoff notes into MEMORY.md, then remove docs/memory/."
fi

if [[ -f "${TARGET_ROOT}/pyproject.toml" ]] && command -v uv >/dev/null 2>&1; then
  echo ""
  echo "[SETUP] uv sync (dev dependencies)..."
  (cd "${TARGET_ROOT}" && uv sync)
fi

echo ""
echo "Next steps:"
echo "  1. Merge templates/Justfile.snippet into your Justfile (verify / ci / lint-turn-end)"
echo "  2. Replace {{PLACEHOLDER}} in AGENTS.md / PROJECT_RULES.md / MEMORY.md / docs/design.md"
echo "  3. Retire docs/memory/ if present — use docs/agent-context/memory/MEMORY.md"
echo "  4. Run: just verify   (or: uv run pytest tests && ./verify.sh)"
echo ""
echo "[NOTE] Use pytest via 'uv run pytest' — plain 'pip install pytest' is not required."

echo "[PASS] bootstrap install complete"
