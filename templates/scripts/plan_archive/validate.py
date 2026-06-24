"""Plan reference validation and repair commands."""

from __future__ import annotations

import os
import subprocess
import sys

from scripts.plan_archive.collect import collect_missing_plan_refs, resolve_plan_reference
from scripts.plan_archive.constants import REPO_ROOT
from scripts.plan_archive.rewrite import (
    build_repair_path_map,
    patch_broken_plan_references,
)

def cmd_check() -> int:
    """docs/plans 또는 archive/legacy 에 없는 대상을 가리키는 참조 나열."""
    missing = collect_missing_plan_refs()

    if not missing:
        print("OK: docs/plans 참조는 모두 기존 파일(plans 루트·archive·docs/archive/plans)과 대응됩니다.")
        return 0

    print("누락된 플랜 파일을 가리키는 참조:\n")
    for base in sorted(missing.keys()):
        hint = resolve_plan_reference(base)
        hint_s = f"  → 제안: {hint}" if hint else ""
        print(f"  {base}{hint_s}")
        for ref in sorted(set(missing[base])):
            print(f"    - {ref}")
    return 1


def cmd_repair(dry_run: bool) -> int:
    """끊긴 docs/plans/*.md 참조를 resolve_plan_reference SSOT로 일괄 치환."""
    missing = collect_missing_plan_refs()
    if not missing:
        print("OK: 수리할 끊긴 plans 참조 없음.")
        return 0

    path_map = build_repair_path_map(missing)
    unresolved = sorted(set(missing) - set(path_map))
    if unresolved:
        print("경고: SSOT 경로를 찾지 못한 basename (수동 처리 필요):", file=sys.stderr)
        for base in unresolved:
            print(f"  - {base}", file=sys.stderr)

    if not path_map:
        return 1 if unresolved else 0

    print(f"치환 맵 {len(path_map)}건 — {'dry-run' if dry_run else '적용'}")
    for base, rel in sorted(path_map.items()):
        display = rel if not rel.startswith("__legacy__:") else rel.removeprefix("__legacy__:")
        print(f"  docs/plans/{base} -> {display}")

    changed = patch_broken_plan_references(path_map, dry_run=dry_run)
    print(f"{'[dry-run] ' if dry_run else ''}수정된 파일 수: {changed}")

    if dry_run:
        return 0
    remaining = collect_missing_plan_refs()
    if remaining:
        print(f"\n남은 누락 참조: {len(remaining)} basename — `archive_plans.py check` 실행", file=sys.stderr)
        return 1
    print("OK: repair 후 끊긴 plans 참조 없음.")
    return 0 if not unresolved else 1


def cmd_guard_deleted() -> int:
    """git이 추적 중인 docs/plans/archive 파일이 워킹트리에서 삭제됐는지 감지."""
    import subprocess

    proc = subprocess.run(
        ["git", "ls-files", "--deleted", "docs/plans/archive"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    deleted = [line.strip() for line in proc.stdout.splitlines() if line.strip().endswith(".md")]
    if not deleted:
        print("OK: 추적 중인 archive 플랜 파일의 워킹트리 삭제 없음.")
        return 0
    print("FAIL: 워킹트리에서 삭제된 추적 archive 플랜 (복구: git restore docs/plans/archive/):\n")
    for path in deleted[:30]:
        print(f"  - {path}")
    if len(deleted) > 30:
        print(f"  ... 외 {len(deleted) - 30}건")
    return 1

_UNIFIED_SYNC_PYTHONPATH = "src:."


def _unified_sync_subprocess_env() -> dict[str, str]:
    """Justfile `export PYTHONPATH := "src:."` 와 동일 — sync.py의 `scripts.*` import용."""
    env = os.environ.copy()
    env["PYTHONPATH"] = _UNIFIED_SYNC_PYTHONPATH
    return env


def run_unified_sync_check(*, dry_run: bool, skip: bool) -> int:
    """플랜 이동 전 code-lock·spec 정합 검사 (`just sync --check`와 동일)."""
    if dry_run:
        print("\n[Unified-Sync] dry-run — 검사 생략")
        return 0
    if skip:
        print("\n[Unified-Sync] 건너뜀 (--skip-unified-sync)")
        return 0

    sync_script = REPO_ROOT / "scripts" / "agent" / "sync.py"
    if not sync_script.is_file():
        print(f"  ❌ Unified sync 스크립트 없음: {sync_script}", file=sys.stderr)
        return 1

    cmd = [sys.executable, str(sync_script), "--check"]
    if os.environ.get("CI", "").lower() == "true":
        cmd.append("--strict")

    print(
        "\n[Unified-Sync] 플랜 이동 전 code-lock·spec 정합 검사 "
        "(scripts/agent/sync.py --check)..."
    )
    result = subprocess.run(
        cmd,
        cwd=str(REPO_ROOT),
        env=_unified_sync_subprocess_env(),
        check=False,
    )
    if result.returncode != 0:
        print(
            f"  ❌ Unified sync 실패(exit {result.returncode}) — "
            "`just sync --nudge`로 후보 스펙을 확인한 뒤 명세를 갱신하고 "
            "`just sync --check`를 다시 실행하세요. "
            "오프라인·긴급 이동만 `--skip-unified-sync`를 사용하세요.",
            file=sys.stderr,
        )
        return result.returncode
    print("  ✅ Unified sync PASS")
    return 0
