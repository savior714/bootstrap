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


def run_cmd(cmd: list[str], cwd: Path | None = None, timeout: int = 300) -> tuple[int, str, str]:
    """Run command and return (exit_code, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired as e:
        return 1, "", f"Command timed out after {timeout}s: {e}"
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
        "uvx", "copier", "copy",
        "--defaults",
        "--vcs-ref", "v0.0.1",
        "--data-file", str(data_file),
        str(fixture_path),
        str(dest_dir),
    ]

    exit_code, stdout, stderr = run_cmd(cmd, timeout=120)

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


def evaluate_production_output_contract(
    exit_code_true: int,
    exit_code_false: int,
    dest_true: Path,
    dest_false: Path,
) -> tuple[bool, list[str], list[str]]:
    """
    Evaluate production output contract with explicit boolean checks.

    Returns (passed, diagnostics, failures).

    Explicit boolean checks:
    - true_copy_ok
    - false_copy_ok
    - true_workflow_exists
    - true_workflow_sentinel_ok
    - true_workflow_disabled_absent
    - true_workflow_jinja_resolved
    - true_profile_exists
    - true_profile_status_ok
    - true_profile_disabled_absent
    - true_profile_jinja_resolved
    - false_modules_dir_absent
    - false_project_dir_absent
    - false_runtime_visual_paths_absent
    - false_gitkeep_paths_absent
    - orphan_jinja_absent
    """
    diagnostics = []
    failures = []

    # True copy check
    true_copy_ok = exit_code_true == 0
    if not true_copy_ok:
        failures.append("PRODUCTION_TRUE_COPY_FAILED")
        diagnostics.append(f"True copy exit code: {exit_code_true}")

    # False copy check
    false_copy_ok = exit_code_false == 0
    if not false_copy_ok:
        failures.append("PRODUCTION_FALSE_COPY_FAILED")
        diagnostics.append(f"False copy exit code: {exit_code_false}")

    # True workflow checks
    true_workflow = dest_true / "agents/modules/runtime-visual/WORKFLOW.md"
    true_workflow_exists = true_workflow.exists()

    # Initialize booleans to False, set to True only when checks pass
    true_workflow_sentinel_ok = False
    true_workflow_disabled_absent = False
    true_workflow_jinja_resolved = False

    if not true_workflow_exists:
        failures.append("PRODUCTION_TRUE_WORKFLOW_MISSING")
        diagnostics.append("WORKFLOW.md does not exist")
    else:
        content = true_workflow.read_text()

        true_workflow_sentinel_ok = "RUNTIME_VISUAL_CORE_VERSION=1" in content
        if not true_workflow_sentinel_ok:
            failures.append("PRODUCTION_TRUE_WORKFLOW_SENTINEL_MISSING")
            diagnostics.append("RUNTIME_VISUAL_CORE_VERSION=1 not found")

        true_workflow_disabled_absent = "Runtime Visual Module Disabled" not in content
        if not true_workflow_disabled_absent:
            failures.append("PRODUCTION_TRUE_WORKFLOW_CONTAINS_DISABLED_PLACEHOLDER")
            diagnostics.append("Disabled placeholder found")

        true_workflow_jinja_resolved = "{%" not in content and "{{" not in content
        if not true_workflow_jinja_resolved:
            failures.append("PRODUCTION_TRUE_WORKFLOW_UNRESOLVED_JINJA")
            diagnostics.append("Unresolved Jinja markers found")

    # True profile checks
    true_profile = dest_true / "agents/project/runtime-visual/PROFILE.md"
    true_profile_exists = true_profile.exists()

    # Initialize booleans to False, set to True only when checks pass
    true_profile_status_ok = False
    true_profile_disabled_absent = False
    true_profile_jinja_resolved = False

    if not true_profile_exists:
        failures.append("PRODUCTION_TRUE_PROFILE_MISSING")
        diagnostics.append("PROFILE.md does not exist")
    else:
        content = true_profile.read_text()

        true_profile_status_ok = "PROFILE_STATUS: INCOMPLETE" in content
        if not true_profile_status_ok:
            failures.append("PRODUCTION_TRUE_PROFILE_STATUS_MISSING")
            diagnostics.append("PROFILE_STATUS: INCOMPLETE not found")

        true_profile_disabled_absent = "Runtime Visual Module Disabled" not in content
        if not true_profile_disabled_absent:
            failures.append("PRODUCTION_TRUE_PROFILE_CONTAINS_DISABLED_PLACEHOLDER")
            diagnostics.append("Disabled placeholder found")

        true_profile_jinja_resolved = "{%" not in content and "{{" not in content
        if not true_profile_jinja_resolved:
            failures.append("PRODUCTION_TRUE_PROFILE_UNRESOLVED_JINJA")
            diagnostics.append("Unresolved Jinja markers found")

    # False destination checks
    false_modules_dir = dest_false / "agents/modules/runtime-visual"
    false_project_dir = dest_false / "agents/project/runtime-visual"

    false_modules_dir_absent = not false_modules_dir.exists()
    if not false_modules_dir_absent:
        failures.append("PRODUCTION_FALSE_MODULES_PATH_EXISTS")
        diagnostics.append("modules/runtime-visual path exists in false dest")

    false_project_dir_absent = not false_project_dir.exists()
    if not false_project_dir_absent:
        failures.append("PRODUCTION_FALSE_PROJECT_PATH_EXISTS")
        diagnostics.append("project/runtime-visual path exists in false dest")

    # Check for any runtime-visual named paths in false destination
    runtime_visual_paths = []
    for p in dest_false.rglob("*"):
        if "runtime-visual" in p.name:
            runtime_visual_paths.append(str(p.relative_to(dest_false)))

    false_runtime_visual_paths_absent = len(runtime_visual_paths) == 0
    if not false_runtime_visual_paths_absent:
        failures.append("PRODUCTION_FALSE_RUNTIME_VISUAL_PATH_EXISTS")
        diagnostics.append(f"Stray runtime-visual paths: {runtime_visual_paths}")

    # Check for .gitkeep in false destination
    gitkeep_paths = []
    for p in dest_false.rglob(".gitkeep"):
        rel = str(p.relative_to(dest_false))
        gitkeep_paths.append(rel)

    false_gitkeep_paths_absent = len(gitkeep_paths) == 0
    if not false_gitkeep_paths_absent:
        failures.append("PRODUCTION_FALSE_GITKEEP_EXISTS")
        diagnostics.append(f".gitkeep paths: {gitkeep_paths}")

    # Check for orphan .jinja files in both destinations
    orphan_jinja = []
    for dest in [dest_true, dest_false]:
        for p in dest.rglob("*.jinja"):
            rel = str(p.relative_to(dest))
            if rel not in orphan_jinja:
                orphan_jinja.append(rel)

    orphan_jinja_absent = len(orphan_jinja) == 0
    if not orphan_jinja_absent:
        failures.append("PRODUCTION_ORPHAN_JINJA_EXISTS")
        diagnostics.append(f"Orphan .jinja paths: {orphan_jinja}")

    # Final passed: all booleans must be True
    passed = all(
        [
            true_copy_ok,
            false_copy_ok,
            true_workflow_exists,
            true_workflow_sentinel_ok,
            true_workflow_disabled_absent,
            true_workflow_jinja_resolved,
            true_profile_exists,
            true_profile_status_ok,
            true_profile_disabled_absent,
            true_profile_jinja_resolved,
            false_modules_dir_absent,
            false_project_dir_absent,
            false_runtime_visual_paths_absent,
            false_gitkeep_paths_absent,
            orphan_jinja_absent,
        ]
    )

    return passed, diagnostics, failures


def validate_production_validator_gate_contract() -> tuple[bool, str]:
    """
    Durable fail-closed probe: self-check with deterministic test cases.

    Tests that the validator correctly fails on invalid outputs.

    Returns (passed, marker).
    """
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir_path = Path(tmp)

        test_cases = [
            # Case 1: Valid baseline → PASS
            (
                "VALID_BASELINE",
                True,
                {
                    "true_workflow_content": "RUNTIME_VISUAL_CORE_VERSION=1\n",
                    "true_profile_content": "PROFILE_STATUS: INCOMPLETE\n",
                    "false_stray_paths": False,
                    "false_gitkeep": False,
                    "orphan_jinja": False,
                },
                True,
            ),
            # Case 2: Missing workflow sentinel → FAIL
            (
                "MISSING_WORKFLOW_SENTINEL",
                True,
                {
                    "true_workflow_content": "Some content\n",
                    "true_profile_content": "PROFILE_STATUS: INCOMPLETE\n",
                    "false_stray_paths": False,
                    "false_gitkeep": False,
                    "orphan_jinja": False,
                },
                False,
            ),
            # Case 3: Missing profile status → FAIL
            (
                "MISSING_PROFILE_STATUS",
                True,
                {
                    "true_workflow_content": "RUNTIME_VISUAL_CORE_VERSION=1\n",
                    "true_profile_content": "Some content\n",
                    "false_stray_paths": False,
                    "false_gitkeep": False,
                    "orphan_jinja": False,
                },
                False,
            ),
            # Case 4: Unresolved workflow Jinja → FAIL
            (
                "UNRESOLVED_WORKFLOW_JINJA",
                True,
                {
                    "true_workflow_content": "RUNTIME_VISUAL_CORE_VERSION=1\n{{ broken }}\n",
                    "true_profile_content": "PROFILE_STATUS: INCOMPLETE\n",
                    "false_stray_paths": False,
                    "false_gitkeep": False,
                    "orphan_jinja": False,
                },
                False,
            ),
            # Case 5: Unresolved profile Jinja → FAIL
            (
                "UNRESOLVED_PROFILE_JINJA",
                True,
                {
                    "true_workflow_content": "RUNTIME_VISUAL_CORE_VERSION=1\n",
                    "true_profile_content": "PROFILE_STATUS: INCOMPLETE\n{% broken %}\n",
                    "false_stray_paths": False,
                    "false_gitkeep": False,
                    "orphan_jinja": False,
                },
                False,
            ),
            # Case 6: False stray runtime path → FAIL
            (
                "FALSE_STRAY_RUNTIME_VISUAL_PATH",
                True,
                {
                    "true_workflow_content": "RUNTIME_VISUAL_CORE_VERSION=1\n",
                    "true_profile_content": "PROFILE_STATUS: INCOMPLETE\n",
                    "false_stray_paths": True,
                    "false_gitkeep": False,
                    "orphan_jinja": False,
                },
                False,
            ),
            # Case 7: False .gitkeep → FAIL
            (
                "FALSE_GITKEEP",
                True,
                {
                    "true_workflow_content": "RUNTIME_VISUAL_CORE_VERSION=1\n",
                    "true_profile_content": "PROFILE_STATUS: INCOMPLETE\n",
                    "false_stray_paths": False,
                    "false_gitkeep": True,
                    "orphan_jinja": False,
                },
                False,
            ),
        ]

        for case_name, true_copy_ok, config, expected_pass in test_cases:
            dest_true = tmpdir_path / f"true_{case_name}"
            dest_false = tmpdir_path / f"false_{case_name}"
            dest_true.mkdir()
            dest_false.mkdir()

            # Create true destination structure
            if config["true_workflow_content"]:
                workflow_dir = dest_true / "agents/modules/runtime-visual"
                workflow_dir.mkdir(parents=True)
                workflow = workflow_dir / "WORKFLOW.md"
                workflow.write_text(config["true_workflow_content"])

            if config["true_profile_content"]:
                profile_dir = dest_true / "agents/project/runtime-visual"
                profile_dir.mkdir(parents=True)
                profile = profile_dir / "PROFILE.md"
                profile.write_text(config["true_profile_content"])

            # Create false destination stray paths
            if config["false_stray_paths"]:
                stray_dir = dest_false / "agents/other/stray-runtime-visual"
                stray_dir.mkdir(parents=True)

            # Create false destination .gitkeep
            if config["false_gitkeep"]:
                stray_dir = dest_false / "agents/other/stray-runtime-visual"
                stray_dir.mkdir(parents=True)
                gitkeep = stray_dir / ".gitkeep"
                gitkeep.write_text("")

            # Evaluate
            passed, diagnostics, failures = evaluate_production_output_contract(
                exit_code_true=0 if true_copy_ok else 1,
                exit_code_false=0,
                dest_true=dest_true,
                dest_false=dest_false,
            )

            if passed != expected_pass:
                return False, f"{case_name}: expected {expected_pass}, got {passed}"

            # For FAIL cases, verify failure code is present
            if not expected_pass and len(failures) == 0:
                return False, f"{case_name}: expected failures but got none"

        return True, "BOOTSTRAP_RUNTIME_VISUAL_PRODUCTION_VALIDATOR_GATE_CONTRACT=PASS"


def validate_production_template(
    temp_repo: Path,
    dest_true: Path,
    dest_false: Path,
) -> tuple[bool, list[str]]:
    """
    Validate production template with true and false profiles.

    Returns (passed, diagnostic_messages).
    """
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
        "uvx", "copier", "copy",
        "--defaults",
        "--vcs-ref", "v0.0.1",
        "--data-file", str(true_data_file),
        str(temp_repo),
        str(dest_true),
    ]
    exit_code_true, stdout_true, stderr_true = run_cmd(cmd_true, timeout=120)
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
        "uvx", "copier", "copy",
        "--defaults",
        "--vcs-ref", "v0.0.1",
        "--data-file", str(false_data_file),
        str(temp_repo),
        str(dest_false),
    ]
    exit_code_false, stdout_false, stderr_false = run_cmd(cmd_false, timeout=120)
    false_data_file.unlink(missing_ok=True)

    # Use the new evaluation function
    passed, diagnostics, failures = evaluate_production_output_contract(
        exit_code_true=exit_code_true,
        exit_code_false=exit_code_false,
        dest_true=dest_true,
        dest_false=dest_false,
    )

    # Combine diagnostics and failures for backward compatibility
    issues = diagnostics + failures

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
    exit_code, stdout, stderr = run_cmd(["uvx", "copier", "--version"], timeout=30)
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

        # Phase 2: Validator gate contract self-check
        print("\n=== Running validator gate contract self-check ===")
        gate_passed, gate_marker = validate_production_validator_gate_contract()

        if not gate_passed:
            print(f"\nBOOTSTRAP_RUNTIME_VISUAL_PRODUCTION_VALIDATOR_GATE_CONTRACT=FAIL")
            print(f"  Reason: {gate_marker}")
            print("\nSome contracts failed.")
            return 1

        print(f"\n{gate_marker}")

        # Phase 3: Production template validation
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
        if synthetic_all_pass and gate_passed and prod_passed:
            print("\nAll contracts passed.")
            return 0
        else:
            print("\nSome contracts failed.")
            return 1


if __name__ == "__main__":
    sys.exit(main())
