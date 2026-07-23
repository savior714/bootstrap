#!/usr/bin/env python3
"""Validate Copier conditional template paths with _subdirectory.

Tests that Copier 9.17.0 supports:
1. _subdirectory: template
2. Jinja conditional in template filename

This is a minimal regression validator for the conditional path contract.
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

TARGET_COPIER_VERSION = "9.17.0"


def run_cmd(cmd: list[str], cwd: Path | None = None) -> tuple[int, str, str]:
    """Run command and return (exit_code, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)


def create_fixture(fixture_dir: Path) -> None:
    """Create minimal fixture structure."""
    # Create copier.yml
    copier_yml = fixture_dir / "copier.yml"
    copier_yml.write_text(
        """_min_copier_version: "9.1.0"
_subdirectory: template
_answers_file: .copier-answers.yml

has_runtime_visual:
  type: bool
  default: false
"""
    )

    # Create template directory and conditional file
    template_dir = fixture_dir / "template"
    template_dir.mkdir(exist_ok=True)

    # Create conditional template file
    # Filename: {% if has_runtime_visual %}runtime-visual.md{% endif %}.jinja
    conditional_filename = "{% if has_runtime_visual %}runtime-visual.md{% endif %}.jinja"
    template_file = template_dir / conditional_filename
    template_file.write_text("BOOTSTRAP_RUNTIME_VISUAL_CONDITIONAL_SENTINEL\n")


def init_fixture_git(fixture_dir: Path) -> None:
    """Initialize fixture as Git repo, commit, and tag."""
    # git init
    exit_code, _, _ = run_cmd(["git", "init"], cwd=fixture_dir)
    if exit_code != 0:
        raise RuntimeError("Failed to init fixture git")

    # git add .
    exit_code, _, _ = run_cmd(["git", "add", "."], cwd=fixture_dir)
    if exit_code != 0:
        raise RuntimeError("Failed to add fixture files")

    # git commit
    exit_code, _, _ = run_cmd(
        ["git", "commit", "-m", "Initial fixture for conditional path test"],
        cwd=fixture_dir,
    )
    if exit_code != 0:
        raise RuntimeError("Failed to commit fixture")

    # git tag v0.0.1
    exit_code, _, _ = run_cmd(["git", "tag", "v0.0.1"], cwd=fixture_dir)
    if exit_code != 0:
        raise RuntimeError("Failed to tag fixture")


def run_copier_copy(
    fixture_path: Path,
    data: dict[str, bool],
    dest_dir: Path,
) -> tuple[int, str, str]:
    """Run copier copy with given data."""
    # Create temp data file
    data_file = dest_dir.parent / f"data_{dest_dir.name}.yml"
    data_file.write_text(f"has_runtime_visual: {str(data['has_runtime_visual']).lower()}\n")

    cmd = [
        "uv", "run", "copier", "copy",
        "--defaults",
        "--vcs-ref", "v0.0.1",
        "--data-file", str(data_file),
        str(fixture_path),
        str(dest_dir),
    ]

    exit_code, stdout, stderr = run_cmd(cmd)

    # Cleanup temp data file
    data_file.unlink(missing_ok=True)

    return exit_code, stdout, stderr


def check_destination(dest_dir: Path, expected_has_file: bool) -> tuple[bool, list[str], str]:
    """Check destination for expected files and orphans."""
    issues = []
    runtime_file = dest_dir / "runtime-visual.md"
    orphan_jinja = []

    # Check for orphan .jinja files
    for p in dest_dir.rglob("*.jinja"):
        orphan_jinja.append(str(p.relative_to(dest_dir)))

    # Check for orphan bare .jinja in root
    bare_jinja = dest_dir / ".jinja"
    if bare_jinja.exists():
        orphan_jinja.append(".jinja")

    # Check runtime-visual.md
    if expected_has_file:
        if not runtime_file.exists():
            issues.append("runtime-visual.md should exist but not found")
        else:
            content = runtime_file.read_text()
            if "BOOTSTRAP_RUNTIME_VISUAL_CONDITIONAL_SENTINEL" not in content:
                issues.append("runtime-visual.md missing sentinel")
    else:
        if runtime_file.exists():
            issues.append("runtime-visual.md should NOT exist but found")

    # Check orphans
    if orphan_jinja:
        issues.append(f"Orphan .jinja paths found: {orphan_jinja}")

    is_pass = len(issues) == 0
    return is_pass, orphan_jinja, "\n".join(issues)


def main() -> int:
    """Run the validator."""
    # Check Copier version
    exit_code, stdout, stderr = run_cmd(["uv", "run", "copier", "--version"])
    if exit_code != 0:
        print(f"Failed to get Copier version: {stderr}")
        return 1

    version_line = stdout.strip()
    if TARGET_COPIER_VERSION not in version_line:
        print(f"RESULT: BLOCKED_COPIER_VERSION_MISMATCH")
        print(f"Expected: {TARGET_COPIER_VERSION}, Got: {version_line}")
        return 1

    print(f"Copier version: {version_line}")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create fixture
        fixture_dir = tmpdir_path / "fixture"
        fixture_dir.mkdir()
        create_fixture(fixture_dir)
        init_fixture_git(fixture_dir)

        # Create destinations
        true_dest = tmpdir_path / "true-dest"
        false_dest = tmpdir_path / "false-dest"

        # Run copier for true profile
        print("\n=== Running copier for true profile ===")
        exit_code, stdout, stderr = run_copier_copy(
            fixture_dir,
            {"has_runtime_visual": True},
            true_dest,
        )
        print(f"Exit code: {exit_code}")
        if stdout:
            print(f"STDOUT: {stdout[:500]}")
        if stderr:
            print(f"STDERR: {stderr[:500]}")

        # Run copier for false profile
        print("\n=== Running copier for false profile ===")
        exit_code2, stdout2, stderr2 = run_copier_copy(
            fixture_dir,
            {"has_runtime_visual": False},
            false_dest,
        )
        print(f"Exit code: {exit_code2}")
        if stdout2:
            print(f"STDOUT: {stdout2[:500]}")
        if stderr2:
            print(f"STDERR: {stderr2[:500]}")

        # Check results
        print("\n=== Checking results ===")

        true_pass, true_orphans, true_issues = check_destination(true_dest, expected_has_file=True)
        false_pass, false_orphans, false_issues = check_destination(false_dest, expected_has_file=False)

        # Read answers files for diagnostic
        true_answers = true_dest / ".copier-answers.yml"
        false_answers = false_dest / ".copier-answers.yml"

        if true_answers.exists():
            print(f"\nTrue destination answers:\n{true_answers.read_text()}")
        if false_answers.exists():
            print(f"\nFalse destination answers:\n{false_answers.read_text()}")

        # Final verdict
        all_pass = true_pass and false_pass

        print("\n=== Final Results ===")
        print(f"True profile - runtime-visual.md present: {'PASS' if true_pass else 'FAIL'}")
        print(f"False profile - runtime-visual.md absent: {'PASS' if false_pass else 'FAIL'}")
        print(f"Orphan .jinja paths (true): {true_orphans if true_orphans else 'none'}")
        print(f"Orphan .jinja paths (false): {false_orphans if false_orphans else 'none'}")

        if not true_pass:
            print(f"\nTrue profile issues:\n{true_issues}")
        if not false_pass:
            print(f"\nFalse profile issues:\n{false_issues}")

        if all_pass:
            print("\nBOOTSTRAP_COPIER_CONDITIONAL_PATH_CONTRACT=PASS")
            return 0
        else:
            print("\nBOOTSTRAP_COPIER_CONDITIONAL_PATH_CONTRACT=FAIL")
            return 1


if __name__ == "__main__":
    sys.exit(main())
