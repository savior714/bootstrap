"""Plan archive move operations (archive, unarchive, sweep)."""

from __future__ import annotations

import shutil
import subprocess
import sys

from scripts.plan_archive.collect import (
    find_archived_plan,
    normalize_name,
    plan_has_only_linear_placeholders,
)
from scripts.plan_archive.constants import ARCHIVE, PLANS, REPO_ROOT
from scripts.plan_archive.rewrite import patch_repo_references
from scripts.plan_archive.validate import run_unified_sync_check
from scripts.plan_archive_classify import KEEP_AT_ARCHIVE_ROOT, archive_relative_path


def _run_optional_post_archive_hooks(base: str, rel: str) -> None:
    """EMR lifecycle hooks — bootstrap 커널에서는 모듈 부재 시 건너뜀."""
    try:
        from scripts.plan_lifecycle.roadmap_product_patch import apply_on_archive

        apply_on_archive(ARCHIVE, rel)
    except ImportError:
        pass
    try:
        from scripts.archive_discussions import archive_for_plan

        archive_for_plan(base)
    except ImportError:
        pass
    try:
        from scripts.sync_roadmap_changelog import append_from_archived_plan

        append_from_archived_plan(rel)
    except ImportError:
        pass


def cmd_sweep(dry_run: bool) -> int:
    """archive 루트에 남은 플랜 *.md 를 분류 폴더로 이동 + 참조 갱신."""
    moves: dict[str, str] = {}
    for path in sorted(ARCHIVE.glob("*.md")):
        name = path.name
        if name in KEEP_AT_ARCHIVE_ROOT:
            continue
        moves[name] = archive_relative_path(name)

    if not moves:
        print("OK: archive 루트에 재분류할 플랜 없음 (README만 유지).")
        return 0

    print(f"archive 루트 재분류: {len(moves)}건")
    for base, rel in sorted(moves.items()):
        src = ARCHIVE / base
        dst = ARCHIVE / rel
        if dst.is_file():
            print(f"Skip (이미 존재): {rel}", file=sys.stderr)
            continue
        if dry_run:
            print(f"[dry-run] mv archive/{base} -> archive/{rel}")
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
            print(f"이동: archive/{base} -> archive/{rel}")

    changed = patch_repo_references(moves, to_archive=True, dry_run=dry_run)
    if dry_run:
        print(f"[dry-run] 참조 갱신 예상 파일 수: {changed}")
    else:
        print(f"참조 갱신된 파일 수: {changed}")
    return 0


def cmd_archive(
    names: list[str],
    dry_run: bool,
    skip_unified_sync: bool,
    skip_linear_sync: bool = False,
) -> int:
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    path_map: dict[str, str] = {}
    unified_sync_done = False

    for raw in names:
        base = normalize_name(raw)
        rel = archive_relative_path(base)
        src = PLANS / base
        dst = ARCHIVE / rel

        existing = find_archived_plan(base)
        if existing is not None:
            print(
                f"Skip (이미 archive 존재): {existing.relative_to(REPO_ROOT)}",
                file=sys.stderr,
            )
            continue
        if not src.is_file():
            print(f"오류: plans 루트에 없음: {src}", file=sys.stderr)
            return 1

        path_map[base] = rel

        if dry_run:
            print(f"[dry-run] mv {src.relative_to(REPO_ROOT)} -> {dst.relative_to(REPO_ROOT)} ({rel.split('/')[0]}/)")
        else:
            # [Archive-Ready] Pre-flight Check
            lint_script = REPO_ROOT / "scripts" / "plan_loop" / "plan_lint.py"
            if lint_script.exists():
                print(f"\n[Pre-flight] '{base}' 아카이브 적합성 검증 중...")
                lint_result = subprocess.run(
                    [sys.executable, str(lint_script), "--archive-ready", str(src)],
                    capture_output=True,
                    text=True,
                    cwd=str(REPO_ROOT),
                    check=False,
                )
                if lint_result.returncode != 0:
                    print(
                        f"  ❌ 아카이브 사전 검증 실패 (exit {lint_result.returncode}) — "
                        f"플랜 파일이 아카이브 준비되지 않았습니다:\n{lint_result.stdout}\n{lint_result.stderr}",
                        file=sys.stderr,
                    )
                    return 1

            if skip_linear_sync:
                print(f"\n[Linear-Sync] 건너뜀 (--skip-linear-sync): {base}")
            elif plan_has_only_linear_placeholders(src):
                print(f"\n[Linear-Sync] Linear 이슈 없음(placeholder·Minor) — 동기화 생략(실패 아님): {base}")
            else:
                print(f"\n[Linear-Sync] '{base}' 아카이브 전 최종 동기화 실행 중...")
                try:
                    sync_script = REPO_ROOT / "scripts" / "linear_sync" / "sync_engine.py"
                    if sync_script.exists():
                        cmd = [
                            sys.executable,
                            "-m",
                            "scripts.linear_sync.sync_engine",
                            "--plan",
                            str(src),
                            "--strict",
                        ]
                        result = subprocess.run(
                            cmd,
                            capture_output=True,
                            text=True,
                            cwd=str(REPO_ROOT),
                            check=False,
                        )
                        if result.stdout:
                            print(result.stdout)
                        if result.stderr:
                            print(result.stderr, file=sys.stderr)
                        if result.returncode != 0:
                            print(
                                f"  ❌ Linear 동기화 실패(exit {result.returncode}) — "
                                "플랜 파일을 이동하지 않습니다. 키·네트워크·워크플로 매핑을 확인하세요. "
                                f"수동 보정: `just linear-sync-archive plan=docs/plans/archive/{rel}`",
                                file=sys.stderr,
                            )
                            return 1
                    else:
                        print(
                            f"  ⚠️ Linear sync 스크립트 없음 — 건너뜀: {sync_script}",
                        )
                except Exception as e:
                    print(f"  ❌ Linear 동기화 중 오류: {e}", file=sys.stderr)
                    return 1

            if not unified_sync_done:
                sync_code = run_unified_sync_check(
                    dry_run=False,
                    skip=skip_unified_sync,
                )
                if sync_code != 0:
                    return sync_code
                unified_sync_done = True

            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
            print(f"이동: {src.relative_to(REPO_ROOT)} -> {dst.relative_to(REPO_ROOT)}")
            # git staging: 새 파일 추가 + 삭제된 파일 표시
            subprocess.run(
                ["git", "add", str(dst), str(src)],
                cwd=str(REPO_ROOT),
                capture_output=True,
                check=False,
            )
            _run_optional_post_archive_hooks(base, rel)

    if not path_map:
        print("아카이브할 신규 파일 없음.", file=sys.stderr)
        return 0

    changed = patch_repo_references(path_map, to_archive=True, dry_run=dry_run)
    if dry_run:
        print(f"[dry-run] 수정될 파일 수: {changed}")
    else:
        print(f"참조 갱신된 파일 수: {changed}")
        # 참조 파일 변경을 git staging에 반영
        if changed > 0:
            subprocess.run(
                ["git", "add", "."],
                cwd=str(REPO_ROOT),
                capture_output=True,
                check=False,
            )
        sweep_code = cmd_sweep(dry_run=False)
        if sweep_code != 0:
            return sweep_code

        # 아카이브 후 다른 활성 플랜들의 Linear 상태 자동 Pull 동기화 실행
        print("\n[Linear-Sync] 아카이브 후 다른 활성 플랜들의 Linear 상태 자동 Pull 동기화 실행...")
        active_plans = list(PLANS.glob("PLAN_*.md"))
        sync_script = REPO_ROOT / "scripts" / "linear_sync" / "sync_engine.py"
        if sync_script.exists():
            for plan_file in active_plans:
                if plan_file.name == "README.md":
                    continue
                print(f"  📂 Pulling {plan_file.name}...")
                cmd = [sys.executable, "-m", "scripts.linear_sync.sync_engine", "--pull", "--plan", str(plan_file)]
                subprocess.run(cmd, cwd=str(REPO_ROOT), check=False)
        else:
            print("  ⚠️ sync_engine.py 스크립트가 없어 pull 동기화를 건너뜁니다.")
    return 0


def cmd_unarchive(names: list[str], dry_run: bool) -> int:
    path_map: dict[str, str] = {}

    for raw in names:
        base = normalize_name(raw)
        src = find_archived_plan(base)
        if src is None:
            print(f"오류: archive 에 없음: {base}", file=sys.stderr)
            return 1
        rel = src.relative_to(ARCHIVE).as_posix()
        path_map[base] = rel
        dst = PLANS / base
        if dst.is_file():
            print(f"오류: 대상이 이미 plans 루트에 존재: {dst}", file=sys.stderr)
            return 1
        if dry_run:
            print(f"[dry-run] mv {src.relative_to(REPO_ROOT)} -> {dst.relative_to(REPO_ROOT)}")
        else:
            shutil.move(str(src), str(dst))
            print(f"복귀: {src.relative_to(REPO_ROOT)} -> {dst.relative_to(REPO_ROOT)}")
            # git staging: 새 파일 추가 + archive에서 삭제된 파일 표시
            subprocess.run(
                ["git", "add", str(dst), str(src)],
                cwd=str(REPO_ROOT),
                capture_output=True,
                check=False,
            )

    changed = patch_repo_references(path_map, to_archive=False, dry_run=dry_run)
    if dry_run:
        print(f"[dry-run] 수정될 파일 수: {changed}")
    else:
        print(f"참조 갱신된 파일 수: {changed}")
        if changed > 0:
            subprocess.run(
                ["git", "add", "."],
                cwd=str(REPO_ROOT),
                capture_output=True,
                check=False,
            )
    return 0
