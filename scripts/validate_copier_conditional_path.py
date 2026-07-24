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

    # Create answers file template (required for Copier to generate answers)
    # This must exist in the template for answers file to be generated
    answers_template = template_dir / "{{_copier_conf.answers_file}}.jinja"
    answers_template.write_text("# Changes here will be overwritten by Copier\n{{ _copier_answers|to_nice_yaml -}}\n")

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


def parse_answers_file_value(answers_path: Path) -> tuple[str, bool]:
    """
    Parse .copier-answers.yml and extract has_runtime_visual value.

    Requires exact key match and lowercase boolean value.
    Rejects:
    - Prefixed/suffixed keys (e.g., not_has_runtime_visual)
    - Duplicate exact keys
    - Invalid boolean values (only 'true' or 'false' allowed)

    Returns:
        - extracted_value: 'true', 'false', or error indicator
        - parse_ok: True if parsing succeeded with exact key found once
    """
    if not answers_path.exists():
        return "NOT_FOUND", False

    content = answers_path.read_text()
    lines = content.split("\n")

    found_key_count = 0
    extracted_value = "NOT_FOUND"

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if ":" not in stripped:
            continue

        key, separator, value_part = stripped.partition(":")
        if separator != ":":
            continue

        key = key.strip()
        value_part = value_part.strip()

        if key != "has_runtime_visual":
            continue

        found_key_count += 1

        if found_key_count > 1:
            return "DUPLICATE", False

        if value_part == "true":
            extracted_value = "true"
        elif value_part == "false":
            extracted_value = "false"
        else:
            return value_part if value_part else "EMPTY_VALUE", False

    if found_key_count == 0:
        return "NOT_FOUND", False

    return extracted_value, True


def evaluate_profile_result(
    label: str,
    exit_code: int,
    stdout: str,
    stderr: str,
    destination: Path,
    expected_has_file: bool,
    expected_answer: bool,
    expected_answer_str: str,
) -> tuple[bool, list[str], list[str]]:
    """
    Evaluate a single profile's Copier copy result.

    Checks:
    1. Copier command exit code (must be 0)
    2. .copier-answers.yml existence and value correctness
    3. Generated path correctness (runtime-visual.md presence/absence)

    Args:
        label: Profile label ('TRUE' or 'FALSE')
        exit_code: Copier copy command exit code
        stdout: Copier copy stdout
        stderr: Copier copy stderr
        destination: Destination directory path
        expected_has_file: Whether runtime-visual.md should exist
        expected_answer: Expected has_runtime_visual value in answers file

    Returns:
        - profile_pass: bool (True if all checks pass)
        - orphan_paths: list[str] (orphan .jinja paths)
        - issues: list[str] (issue descriptions)
    """
    issues = []
    orphan_paths = []

    # Gate 1: Copier exit code
    if exit_code != 0:
        issue_code = f"{label}_COPY_COMMAND_FAILED"
        issues.append(f"{issue_code}: exit_code={exit_code}")
        # Even if copy failed, still check for orphan paths for diagnostic
        for p in destination.rglob("*.jinja"):
            orphan_paths.append(str(p.relative_to(destination)))
        return False, orphan_paths, issues

    # Gate 2: Answers file existence and value
    answers_path = destination / ".copier-answers.yml"
    extracted_value, parse_ok = parse_answers_file_value(answers_path)

    if not parse_ok or extracted_value == "NOT_FOUND":
        issue_code = f"{label}_ANSWERS_FILE_MISSING"
        issues.append(f"{issue_code}: answers file missing or invalid")
        return False, orphan_paths, issues

    expected_str = "true" if expected_answer else "false"
    if extracted_value != expected_str:
        issue_code = f"{label}_ANSWER_VALUE_MISMATCH"
        issues.append(f"{issue_code}: expected={expected_str}, got={extracted_value}")
        return False, orphan_paths, issues

    # Gate 3: Generated path correctness
    runtime_file = destination / "runtime-visual.md"

    # Check for orphan .jinja files
    for p in destination.rglob("*.jinja"):
        orphan_paths.append(str(p.relative_to(destination)))

    # Check for orphan bare .jinja in root
    bare_jinja = destination / ".jinja"
    if bare_jinja.exists():
        orphan_paths.append(".jinja")

    if expected_has_file:
        if not runtime_file.exists():
            issues.append(f"{label}_RUNTIME_FILE_MISSING: runtime-visual.md should exist but not found")
        else:
            content = runtime_file.read_text()
            if "BOOTSTRAP_RUNTIME_VISUAL_CONDITIONAL_SENTINEL" not in content:
                issues.append(f"{label}_RUNTIME_FILE_MISSING_SENTINEL: sentinel not found")
    else:
        if runtime_file.exists():
            issues.append(f"{label}_RUNTIME_FILE_UNEXPECTED: runtime-visual.md should NOT exist but found")

    # Check orphans
    if orphan_paths:
        issues.append(f"{label}_ORPHAN_JINJA_PATHS: {orphan_paths}")

    profile_pass = len(issues) == 0
    return profile_pass, orphan_paths, issues


def validate_answers_parser_contract() -> bool:
    """
    Self-check: validate parser contract with deterministic test cases.

    Returns True if all cases pass, False otherwise.
    """
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        test_cases = [
            ("VALID_TRUE", "has_runtime_visual: true\n", ("true", True)),
            ("VALID_FALSE", "has_runtime_visual: false\n", ("false", True)),
            ("PREFIXED_KEY", "not_has_runtime_visual: true\n", ("NOT_FOUND", False)),
            ("SUFFIXED_KEY", "has_runtime_visual_extra: true\n", ("NOT_FOUND", False)),
            ("DUPLICATE_SAME", "has_runtime_visual: true\nhas_runtime_visual: true\n", ("DUPLICATE", False)),
            ("DUPLICATE_CONFLICTING", "has_runtime_visual: true\nhas_runtime_visual: false\n", ("DUPLICATE", False)),
            ("INVALID_BOOLEAN", "has_runtime_visual: yes\n", ("yes", False)),
            ("INVALID_BOOLEAN_UPPERCASE", "has_runtime_visual: TRUE\n", ("TRUE", False)),
            ("EMPTY_VALUE", "has_runtime_visual: \n", ("EMPTY_VALUE", False)),
        ]

        for case_name, content, expected in test_cases:
            test_file = root / f"{case_name}.yml"
            test_file.write_text(content, encoding="utf-8")
            result, ok = parse_answers_file_value(test_file)

            expected_val, expected_ok = expected
            if result != expected_val or ok != expected_ok:
                print(f"CONTRACT_PROBE_FAIL: {case_name}")
                print(f"  Expected: {expected_val}, {expected_ok}")
                print(f"  Got: {result}, {ok}")
                return False

        # Special case: commented fake + exact key should pass
        commented_exact = root / "commented_exact.yml"
        commented_exact.write_text(
            "# not_has_runtime_visual: true\nhas_runtime_visual: true\n",
            encoding="utf-8",
        )
        result, ok = parse_answers_file_value(commented_exact)
        if result != "true" or ok != True:
            print(f"CONTRACT_PROBE_FAIL: COMMENTED_FAKE_WITH_VALID_EXACT")
            print(f"  Expected: true, True")
            print(f"  Got: {result}, {ok}")
            return False

        return True


def check_destination(dest_dir: Path, expected_has_file: bool) -> tuple[bool, list[str], str]:
    """Check destination for expected files and orphans (legacy function, kept for reference)."""
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
    # Phase 1: Parser contract self-check
    parser_contract_pass = validate_answers_parser_contract()
    if not parser_contract_pass:
        print("BOOTSTRAP_COPIER_ANSWERS_EXACT_KEY_CONTRACT=FAIL")
        print("Parser contract self-check failed")
        return 1

    print("BOOTSTRAP_COPIER_ANSWERS_EXACT_KEY_CONTRACT=PASS")

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

        # Check results using evaluate_profile_result
        print("\n=== Evaluating profile results ===")

        true_profile_pass, true_orphans, true_issues = evaluate_profile_result(
            label="TRUE",
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            destination=true_dest,
            expected_has_file=True,
            expected_answer=True,
            expected_answer_str="true",
        )

        false_profile_pass, false_orphans, false_issues = evaluate_profile_result(
            label="FALSE",
            exit_code=exit_code2,
            stdout=stdout2,
            stderr=stderr2,
            destination=false_dest,
            expected_has_file=False,
            expected_answer=False,
            expected_answer_str="false",
        )

        # Read answers files for diagnostic using parser SSOT
        true_answers = true_dest / ".copier-answers.yml"
        false_answers = false_dest / ".copier-answers.yml"

        true_answer_value = "NOT_FOUND"
        false_answer_value = "NOT_FOUND"

        if true_answers.exists():
            true_content = true_answers.read_text()
            print(f"\nTrue destination answers:\n{true_content}")
            true_answer_value, _ = parse_answers_file_value(true_answers)
        if false_answers.exists():
            false_content = false_answers.read_text()
            print(f"\nFalse destination answers:\n{false_content}")
            false_answer_value, _ = parse_answers_file_value(false_answers)

        # Final verdict - both profiles must pass
        all_pass = true_profile_pass and false_profile_pass

        # Runtime visual presence diagnostic
        true_runtime_present = "present" if (true_dest / "runtime-visual.md").exists() else "absent"
        false_runtime_present = "present" if (false_dest / "runtime-visual.md").exists() else "absent"

        # Combine all orphan paths
        all_orphans = true_orphans + false_orphans

        print("\n=== Final Results ===")
        print(f"TRUE_COPY_EXIT_CODE={exit_code}")
        print(f"FALSE_COPY_EXIT_CODE={exit_code2}")
        print(f"TRUE_ANSWER_VALUE={true_answer_value}")
        print(f"FALSE_ANSWER_VALUE={false_answer_value}")
        print(f"TRUE_PROFILE_RUNTIME_VISUAL={true_runtime_present}")
        print(f"FALSE_PROFILE_RUNTIME_VISUAL={false_runtime_present}")
        print(f"ORPHAN_TEMPLATE_PATHS={all_orphans if all_orphans else 'none'}")
        print(f"\nTrue profile - runtime-visual.md present: {'PASS' if true_profile_pass else 'FAIL'}")
        print(f"False profile - runtime-visual.md absent: {'PASS' if false_profile_pass else 'FAIL'}")

        if not true_profile_pass:
            print(f"\nTrue profile issues:")
            for issue in true_issues:
                print(f"  - {issue}")
        if not false_profile_pass:
            print(f"\nFalse profile issues:")
            for issue in false_issues:
                print(f"  - {issue}")

        if all_pass:
            print("\nBOOTSTRAP_COPIER_CONDITIONAL_PATH_CONTRACT=PASS")
            return 0
        else:
            print("\nBOOTSTRAP_COPIER_CONDITIONAL_PATH_CONTRACT=FAIL")
            return 1


if __name__ == "__main__":
    sys.exit(main())
