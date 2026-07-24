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


def create_production_temp_repo(working_tree_root: Path, tmp_dir: Path) -> Path:
    """
    Create a temporary git repository from current working tree for production validation.

    Does NOT use git archive. Copies working tree files directly to allow
    validation before commit.

    Returns the path to the temp repo directory.
    """
    temp_repo = tmp_dir / "production-template"
    temp_repo.mkdir()

    # Copy copier.yml and template/ from working tree
    import shutil
    copier_yml_src = working_tree_root / "copier.yml"
    template_src = working_tree_root / "template"

    if copier_yml_src.exists():
        shutil.copy2(copier_yml_src, temp_repo / "copier.yml")

    if template_src.exists():
        shutil.copytree(template_src, temp_repo / "template")

    # Initialize git repo
    run_cmd(["git", "init"], cwd=temp_repo)
    run_cmd(["git", "config", "user.name", "Validator"], cwd=temp_repo)
    run_cmd(["git", "config", "user.email", "validator@localhost"], cwd=temp_repo)
    run_cmd(["git", "add", "."], cwd=temp_repo)
    run_cmd(["git", "commit", "-m", "Production template for validation"], cwd=temp_repo)
    run_cmd(["git", "tag", "v0.0.1"], cwd=temp_repo)

    return temp_repo


def validate_production_template(
    temp_repo: Path,
    dest_true: Path,
    dest_false: Path,
) -> tuple[bool, list[str]]:
    """
    Validate production template with true and false profiles.

    Returns (passed, diagnostic_messages).
    """
    issues = []

    # True profile copy
    true_data_file = dest_true.parent / "true_data.yml"
    true_data_file.write_text(
        "project_name: Runtime Visual True Probe\n"
        "project_slug: runtime-visual-true-probe\n"
        "canonical_branch: main\n"
        "main_only: true\n"
        "package_tool: other\n"
        "lint_command: \"\"\n"
        "typecheck_command: \"\"\n"
        "targeted_test_command: \"\"\n"
        "release_check_command: \"\"\n"
        "has_runtime_visual: true\n"
        "has_database: false\n"
        "has_content_provenance: false\n"
        "regulated_domain: false\n"
    )

    cmd_true = [
        "uv", "run", "copier", "copy",
        "--defaults",
        "--vcs-ref", "v0.0.1",
        "--data-file", str(true_data_file),
        str(temp_repo),
        str(dest_true),
    ]
    exit_code_true, stdout_true, stderr_true = run_cmd(cmd_true)
    true_data_file.unlink(missing_ok=True)

    # False profile copy
    false_data_file = dest_false.parent / "false_data.yml"
    false_data_file.write_text(
        "project_name: Runtime Visual False Probe\n"
        "project_slug: runtime-visual-false-probe\n"
        "canonical_branch: main\n"
        "main_only: true\n"
        "package_tool: other\n"
        "lint_command: \"\"\n"
        "typecheck_command: \"\"\n"
        "targeted_test_command: \"\"\n"
        "release_check_command: \"\"\n"
        "has_runtime_visual: false\n"
        "has_database: false\n"
        "has_content_provenance: false\n"
        "regulated_domain: false\n"
    )

    cmd_false = [
        "uv", "run", "copier", "copy",
        "--defaults",
        "--vcs-ref", "v0.0.1",
        "--data-file", str(false_data_file),
        str(temp_repo),
        str(dest_false),
    ]
    exit_code_false, stdout_false, stderr_false = run_cmd(cmd_false)
    false_data_file.unlink(missing_ok=True)

    # Check true profile
    true_workflow = dest_true / "agents/modules/runtime-visual/WORKFLOW.md"
    true_profile = dest_true / "agents/project/runtime-visual/PROFILE.md"

    if exit_code_true != 0:
        issues.append(f"PRODUCTION_TRUE_COPY_EXIT_CODE={exit_code_true}")
    else:
        issues.append("PRODUCTION_TRUE_COPY_EXIT_CODE=0")

    if not true_workflow.exists():
        issues.append("PRODUCTION_TRUE_WORKFLOW=missing")
    else:
        issues.append("PRODUCTION_TRUE_WORKFLOW=present")
        content = true_workflow.read_text()
        if "RUNTIME_VISUAL_CORE_VERSION=1" not in content:
            issues.append("PRODUCTION_TRUE_WORKFLOW_MISSING_SENTINEL")
        if "Runtime Visual Module Disabled" in content:
            issues.append("PRODUCTION_TRUE_WORKFLOW_CONTAINS_DISABLED_PLACEHOLDER")
        # Check for unresolved Jinja markers
        if "{%" in content or "{{" in content:
            issues.append("PRODUCTION_TRUE_WORKFLOW_HAS_UNRESOLVED_JINJA")

    if not true_profile.exists():
        issues.append("PRODUCTION_TRUE_PROFILE=missing")
    else:
        issues.append("PRODUCTION_TRUE_PROFILE=present")
        content = true_profile.read_text()
        if "PROFILE_STATUS: INCOMPLETE" not in content:
            issues.append("PRODUCTION_TRUE_PROFILE_MISSING_STATUS")
        if "Runtime Visual Module Disabled" in content:
            issues.append("PRODUCTION_TRUE_PROFILE_CONTAINS_DISABLED_PLACEHOLDER")
        if "{%" in content or "{{" in content:
            issues.append("PRODUCTION_TRUE_PROFILE_HAS_UNRESOLVED_JINJA")

    # Check false profile
    false_modules_dir = dest_false / "agents/modules/runtime-visual"
    false_project_dir = dest_false / "agents/project/runtime-visual"

    if exit_code_false != 0:
        issues.append(f"PRODUCTION_FALSE_COPY_EXIT_CODE={exit_code_false}")
    else:
        issues.append("PRODUCTION_FALSE_COPY_EXIT_CODE=0")

    if false_modules_dir.exists():
        issues.append("PRODUCTION_FALSE_MODULES_PATH_EXISTS")

    if false_project_dir.exists():
        issues.append("PRODUCTION_FALSE_PROJECT_PATH_EXISTS")

    # Check for any runtime-visual named paths in false destination
    runtime_visual_paths = []
    for p in dest_false.rglob("*"):
        if "runtime-visual" in p.name:
            runtime_visual_paths.append(str(p.relative_to(dest_false)))

    if runtime_visual_paths:
        issues.append(f"PRODUCTION_FALSE_RUNTIME_VISUAL_PATHS={runtime_visual_paths}")
    else:
        issues.append("PRODUCTION_FALSE_RUNTIME_VISUAL_PATHS=none")

    # Check for orphan .jinja files in both destinations
    orphan_jinja = []
    for dest in [dest_true, dest_false]:
        for p in dest.rglob("*.jinja"):
            rel = str(p.relative_to(dest))
            if rel not in orphan_jinja:
                orphan_jinja.append(rel)

    if orphan_jinja:
        issues.append(f"PRODUCTION_ORPHAN_JINJA_PATHS={orphan_jinja}")
    else:
        issues.append("PRODUCTION_ORPHAN_JINJA_PATHS=none")

    # Check for .gitkeep in false destination
    gitkeep_paths = []
    for p in dest_false.rglob(".gitkeep"):
        rel = str(p.relative_to(dest_false))
        gitkeep_paths.append(rel)

    if gitkeep_paths:
        issues.append(f"PRODUCTION_FALSE_GITKEEP_PATHS={gitkeep_paths}")

    passed = (
        exit_code_true == 0 and
        exit_code_false == 0 and
        true_workflow.exists() and
        true_profile.exists() and
        not false_modules_dir.exists() and
        not false_project_dir.exists() and
        "Runtime Visual Module Disabled" not in true_workflow.read_text() and
        "Runtime Visual Module Disabled" not in true_profile.read_text() and
        not orphan_jinja
    )

    return passed, issues


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

        # Create fixture for synthetic conditional path test
        fixture_dir = tmpdir_path / "fixture"
        fixture_dir.mkdir()
        create_fixture(fixture_dir)
        init_fixture_git(fixture_dir)

        # Create destinations for synthetic test
        true_dest_synthetic = tmpdir_path / "true-dest"
        false_dest_synthetic = tmpdir_path / "false-dest"

        # Run copier for synthetic test
        print("\n=== Running synthetic conditional path test ===")
        exit_code_syn, stdout_syn, stderr_syn = run_copier_copy(
            fixture_dir,
            {"has_runtime_visual": True},
            true_dest_synthetic,
        )
        exit_code_syn2, stdout_syn2, stderr_syn2 = run_copier_copy(
            fixture_dir,
            {"has_runtime_visual": False},
            false_dest_synthetic,
        )

        # Check synthetic results
        print("\n=== Evaluating synthetic profile results ===")

        true_profile_pass, true_orphans, true_issues = evaluate_profile_result(
            label="TRUE",
            exit_code=exit_code_syn,
            stdout=stdout_syn,
            stderr=stderr_syn,
            destination=true_dest_synthetic,
            expected_has_file=True,
            expected_answer=True,
            expected_answer_str="true",
        )

        false_profile_pass, false_orphans, false_issues = evaluate_profile_result(
            label="FALSE",
            exit_code=exit_code_syn2,
            stdout=stdout_syn2,
            stderr=stderr_syn2,
            destination=false_dest_synthetic,
            expected_has_file=False,
            expected_answer=False,
            expected_answer_str="false",
        )

        synthetic_all_pass = true_profile_pass and false_profile_pass

        if synthetic_all_pass:
            print("\nBOOTSTRAP_COPIER_CONDITIONAL_PATH_CONTRACT=PASS")
        else:
            print("\nBOOTSTRAP_COPIER_CONDITIONAL_PATH_CONTRACT=FAIL")
            if not true_profile_pass:
                for issue in true_issues:
                    print(f"  TRUE: {issue}")
            if not false_profile_pass:
                for issue in false_issues:
                    print(f"  FALSE: {issue}")

        # Phase 2: Production template validation
        print("\n=== Running production template validation ===")

        # Create temp repo from working tree
        import shutil
        working_tree = Path("/Users/seungjulee/Desktop/Dev/bootstrap")
        temp_repo = create_production_temp_repo(working_tree, tmpdir_path)

        # Create destinations for production test
        dest_true_prod = tmpdir_path / "true-prod"
        dest_false_prod = tmpdir_path / "false-prod"

        prod_passed, prod_issues = validate_production_template(
            temp_repo,
            dest_true_prod,
            dest_false_prod,
        )

        print("\n=== Production Validation Results ===")
        for issue in prod_issues:
            print(f"  {issue}")

        if prod_passed:
            print("\nBOOTSTRAP_RUNTIME_VISUAL_PRODUCTION_CONDITIONAL_PATH_CONTRACT=PASS")
        else:
            print("\nBOOTSTRAP_RUNTIME_VISUAL_PRODUCTION_CONDITIONAL_PATH_CONTRACT=FAIL")

        # Final overall result
        print("\n=== Overall Validation Summary ===")
        if synthetic_all_pass and prod_passed:
            print("\nAll contracts passed.")
            return 0
        else:
            print("\nSome contracts failed.")
            return 1


if __name__ == "__main__":
    sys.exit(main())
