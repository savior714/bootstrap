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

COPIER_COMMAND = ("uv", "run", "copier")

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def evaluate_local_copier_toolchain_contract(
    command: tuple[str, ...],
    version_line: str,
) -> tuple[bool, str | None]:
    """Evaluate local copier toolchain contract.

    Contract:
    - command must be exactly ("uv", "run", "copier")
    - version_line must contain "9.17.0"

    Returns:
        (True, None) if contract passes
        (False, error_code) if contract fails
    """
    if command != ("uv", "run", "copier"):
        return False, "COPIER_COMMAND_NOT_LOCAL"

    if "9.17.0" not in version_line:
        return False, "COPIER_VERSION_MISMATCH"

    return True, None


def evaluate_actual_local_toolchain_result(
    *,
    exit_code: int,
    command: tuple[str, ...],
    version_line: str,
) -> tuple[bool, str | None]:
    """Evaluate actual local toolchain result from command execution.

    This is the production result evaluator used after actual command execution.
    It separates synthetic self-check from actual validation.

    Returns:
        (True, None) if actual validation passes
        (False, error_code) if actual validation fails
    """
    if exit_code != 0:
        return False, "LOCAL_COPIER_VERSION_COMMAND_FAILED"

    if not command[:3] == ("uv", "run", "copier"):
        return False, "COPIER_COMMAND_NOT_LOCAL"

    if "9.17.0" not in version_line:
        return False, "COPIER_VERSION_MISMATCH"

    return True, None


def validate_local_copier_toolchain_contract() -> tuple[bool, str | None]:
    """Self-check: validate local copier toolchain contract with deterministic test cases.

    This is a pure synthetic probe that tests the evaluation logic without actual command execution.
    It returns None for production marker to prevent premature PASS emission.

    Returns:
        (True, None) if all synthetic test cases pass
        (False, error_code) if any case fails
    """
    test_cases = [
        # Case 1: Valid local command and version
        (
            "VALID_LOCAL_COMMAND_AND_VERSION",
            ("uv", "run", "copier"),
            "copier 9.17.0",
            True,
            None,
        ),
        # Case 2: uvx command should fail
        (
            "UVX_COMMAND",
            ("uvx", "copier"),
            "copier 9.17.0",
            False,
            "COPIER_COMMAND_NOT_LOCAL",
        ),
        # Case 3: bare copier command should fail
        (
            "BARE_COPIER_COMMAND",
            ("copier",),
            "copier 9.17.0",
            False,
            "COPIER_COMMAND_NOT_LOCAL",
        ),
        # Case 4: wrong version should fail
        (
            "WRONG_VERSION",
            ("uv", "run", "copier"),
            "copier 9.16.0",
            False,
            "COPIER_VERSION_MISMATCH",
        ),
        # Case 5: empty version should fail
        (
            "EMPTY_VERSION",
            ("uv", "run", "copier"),
            "",
            False,
            "COPIER_VERSION_MISMATCH",
        ),
    ]

    for case_name, command, version, expected_pass, expected_error in test_cases:
        passed, error = evaluate_local_copier_toolchain_contract(command, version)
        if passed != expected_pass:
            return False, f"{case_name}: expected pass={expected_pass}, got {passed}"
        if expected_pass and error is not None:
            return False, f"{case_name}: expected no error, got {error}"
        if not expected_pass and error != expected_error:
            return False, f"{case_name}: expected error={expected_error}, got {error}"

    return True, None


def build_local_copier_invocation(
    args: tuple[str, ...],
    *,
    timeout: int,
) -> tuple[tuple[str, ...], Path, int]:
    """Build local Copier invocation spec.

    Returns:
        (command, cwd, timeout) tuple for local Copier execution.
    """
    return (
        (*COPIER_COMMAND, *args),
        REPOSITORY_ROOT,
        timeout,
    )


def run_local_copier(
    args: tuple[str, ...],
    *,
    timeout: int,
) -> tuple[int, str, str]:
    """Run Copier command with local invocation spec.

    Wrapper that enforces repository-root CWD and uv run copier command prefix.
    """
    command, cwd, resolved_timeout = build_local_copier_invocation(
        args,
        timeout=timeout,
    )
    return run_cmd(
        list(command),
        cwd=cwd,
        timeout=resolved_timeout,
    )


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


class ProductionTempRepoMaterializationError(RuntimeError):
    """Raised when a required filesystem materialization step for production temp repo fails."""

    def __init__(self, failure_code: str, detail: str) -> None:
        super().__init__(detail)
        self.failure_code = failure_code
        self.detail = detail


class ProductionTempRepoGitSetupError(RuntimeError):
    """Raised when a required git setup step for production temp repo fails."""

    def __init__(self, failure_code: str, detail: str) -> None:
        super().__init__(detail)
        self.failure_code = failure_code
        self.detail = detail


class SyntheticFixtureMaterializationError(RuntimeError):
    """Raised when a required filesystem materialization step for synthetic fixture fails."""

    def __init__(self, failure_code: str, detail: str) -> None:
        super().__init__(detail)
        self.failure_code = failure_code
        self.detail = detail


class SyntheticFixtureGitSetupError(RuntimeError):
    """Raised when a required git setup step for synthetic fixture fails."""

    def __init__(self, failure_code: str, detail: str) -> None:
        super().__init__(detail)
        self.failure_code = failure_code
        self.detail = detail


class SyntheticCopierDataFileMaterializationError(RuntimeError):
    """Raised when a required data file write step for synthetic Copier copy fails."""

    def __init__(self, failure_code: str, detail: str) -> None:
        super().__init__(detail)
        self.failure_code = failure_code
        self.detail = detail


class SyntheticCopierDataFileCleanupError(RuntimeError):
    """Raised when a required data file cleanup step for synthetic Copier copy fails."""

    def __init__(self, failure_code: str, detail: str) -> None:
        super().__init__(detail)
        self.failure_code = failure_code
        self.detail = detail


class ProductionCopierDataFileMaterializationError(RuntimeError):
    """Raised when a required data file write step for production Copier copy fails."""

    def __init__(self, failure_code: str, detail: str) -> None:
        super().__init__(detail)
        self.failure_code = failure_code
        self.detail = detail


class ProductionCopierDataFileCleanupError(RuntimeError):
    """Raised when a required data file cleanup step for production Copier copy fails."""

    def __init__(self, failure_code: str, detail: str) -> None:
        super().__init__(detail)
        self.failure_code = failure_code
        self.detail = detail


def run_required_temp_repo_git_step(
    *,
    command: list[str],
    cwd: Path,
    failure_code: str,
) -> None:
    """Run a required git step and raise on failure.

    Args:
        command: Git command to execute
        cwd: Working directory for the command
        failure_code: Stable failure code to use if command fails

    Raises:
        ProductionTempRepoGitSetupError: If command exits with non-zero code
    """
    exit_code, stdout, stderr = run_cmd(command, cwd=cwd)

    if exit_code != 0:
        detail = stderr.strip() or stdout.strip() or f"exit code {exit_code}"
        raise ProductionTempRepoGitSetupError(failure_code, detail)


def run_required_synthetic_fixture_git_step(
    *,
    command: list[str],
    cwd: Path,
    failure_code: str,
) -> None:
    """Run a required git step for synthetic fixture and raise on failure.

    Args:
        command: Git command to execute
        cwd: Working directory for the command
        failure_code: Stable failure code to use if command fails

    Raises:
        SyntheticFixtureGitSetupError: If command exits with non-zero code
    """
    exit_code, stdout, stderr = run_cmd(command, cwd=cwd)

    if exit_code != 0:
        detail = stderr.strip() or stdout.strip() or f"exit code {exit_code}"
        raise SyntheticFixtureGitSetupError(failure_code, detail)


def create_fixture(fixture_dir: Path) -> None:
    """Create minimal fixture structure.

    Performs five filesystem materialization steps in sequence:
    1. Create fixture root directory
    2. Write copier.yml
    3. Create template directory
    4. Write answers template
    5. Write conditional template

    Each step is wrapped in fail-closed exception handling.
    Any failure raises SyntheticFixtureMaterializationError with a stable failure code.

    Raises:
        SyntheticFixtureMaterializationError: If any materialization step fails
    """
    # Step 1: Create fixture root directory
    try:
        fixture_dir.mkdir(parents=True, exist_ok=False)
    except Exception as e:
        raise SyntheticFixtureMaterializationError(
            "SYNTHETIC_FIXTURE_DIRECTORY_CREATE_FAILED",
            str(e),
        )

    # Step 2: Write copier.yml
    copier_yml = fixture_dir / "copier.yml"
    try:
        copier_yml.write_text(
            """_min_copier_version: "9.1.0"
_subdirectory: template
_answers_file: .copier-answers.yml

has_runtime_visual:
  type: bool
  default: false
"""
        )
    except Exception as e:
        raise SyntheticFixtureMaterializationError(
            "SYNTHETIC_FIXTURE_COPIER_YML_WRITE_FAILED",
            str(e),
        )

    # Step 3: Create template directory
    template_dir = fixture_dir / "template"
    try:
        template_dir.mkdir()
    except Exception as e:
        raise SyntheticFixtureMaterializationError(
            "SYNTHETIC_FIXTURE_TEMPLATE_DIRECTORY_CREATE_FAILED",
            str(e),
        )

    # Step 4: Write answers template
    answers_template = template_dir / "{{_copier_conf.answers_file}}.jinja"
    try:
        answers_template.write_text("# Changes here will be overwritten by Copier\n{{ _copier_answers|to_nice_yaml -}}\n")
    except Exception as e:
        raise SyntheticFixtureMaterializationError(
            "SYNTHETIC_FIXTURE_ANSWERS_TEMPLATE_WRITE_FAILED",
            str(e),
        )

    # Step 5: Write conditional template
    conditional_filename = "{% if has_runtime_visual %}runtime-visual.md{% endif %}.jinja"
    template_file = template_dir / conditional_filename
    try:
        template_file.write_text("BOOTSTRAP_RUNTIME_VISUAL_CONDITIONAL_SENTINEL\n")
    except Exception as e:
        raise SyntheticFixtureMaterializationError(
            "SYNTHETIC_FIXTURE_CONDITIONAL_TEMPLATE_WRITE_FAILED",
            str(e),
        )


def init_fixture_git(fixture_dir: Path) -> None:
    """Initialize fixture as Git repo, config identity, commit, and tag."""
    run_required_synthetic_fixture_git_step(
        command=["git", "init"],
        cwd=fixture_dir,
        failure_code="SYNTHETIC_FIXTURE_GIT_INIT_FAILED",
    )
    run_required_synthetic_fixture_git_step(
        command=["git", "config", "user.name", "Validator"],
        cwd=fixture_dir,
        failure_code="SYNTHETIC_FIXTURE_GIT_CONFIG_NAME_FAILED",
    )
    run_required_synthetic_fixture_git_step(
        command=["git", "config", "user.email", "validator@localhost"],
        cwd=fixture_dir,
        failure_code="SYNTHETIC_FIXTURE_GIT_CONFIG_EMAIL_FAILED",
    )
    run_required_synthetic_fixture_git_step(
        command=["git", "add", "."],
        cwd=fixture_dir,
        failure_code="SYNTHETIC_FIXTURE_GIT_ADD_FAILED",
    )
    run_required_synthetic_fixture_git_step(
        command=["git", "commit", "-m", "Initial fixture for conditional path test"],
        cwd=fixture_dir,
        failure_code="SYNTHETIC_FIXTURE_GIT_COMMIT_FAILED",
    )
    run_required_synthetic_fixture_git_step(
        command=["git", "tag", "v0.0.1"],
        cwd=fixture_dir,
        failure_code="SYNTHETIC_FIXTURE_GIT_TAG_FAILED",
    )


def write_synthetic_copier_data_file(
    *,
    data_file: Path,
    has_runtime_visual: bool,
    failure_code: str,
) -> None:
    """Write synthetic Copier data file with fail-closed exception handling.

    Args:
        data_file: Path to the data file to write
        has_runtime_visual: Boolean value for has_runtime_visual
        failure_code: Stable failure code to use if write fails

    Raises:
        SyntheticCopierDataFileMaterializationError: If write fails
    """
    try:
        data_file.write_text(
            "has_runtime_visual: "
            f"{str(has_runtime_visual).lower()}\n"
        )
    except Exception as error:
        raise SyntheticCopierDataFileMaterializationError(
            failure_code,
            str(error),
        )


def cleanup_synthetic_copier_data_file(
    *,
    data_file: Path,
    failure_code: str,
) -> None:
    """Cleanup synthetic Copier data file with fail-closed exception handling.

    Args:
        data_file: Path to the data file to cleanup
        failure_code: Stable failure code to use if cleanup fails

    Raises:
        SyntheticCopierDataFileCleanupError: If cleanup fails
    """
    try:
        data_file.unlink(missing_ok=True)
    except Exception as error:
        raise SyntheticCopierDataFileCleanupError(
            failure_code,
            str(error),
        )


def run_copier_copy(
    fixture_path: Path,
    data: dict[str, bool],
    dest_dir: Path,
) -> tuple[int, str, str]:
    """Run copier copy with given data."""
    # Create temp data file
    data_file = dest_dir.parent / f"data_{dest_dir.name}.yml"
    has_runtime_visual = data["has_runtime_visual"]
    write_failure_code = (
        "SYNTHETIC_COPIER_TRUE_DATA_FILE_WRITE_FAILED"
        if has_runtime_visual
        else "SYNTHETIC_COPIER_FALSE_DATA_FILE_WRITE_FAILED"
    )
    cleanup_failure_code = (
        "SYNTHETIC_COPIER_TRUE_DATA_FILE_CLEANUP_FAILED"
        if has_runtime_visual
        else "SYNTHETIC_COPIER_FALSE_DATA_FILE_CLEANUP_FAILED"
    )
    write_synthetic_copier_data_file(
        data_file=data_file,
        has_runtime_visual=has_runtime_visual,
        failure_code=write_failure_code,
    )

    exit_code, stdout, stderr = run_local_copier(
        args=(
            "copy",
            "--defaults",
            "--vcs-ref", "v0.0.1",
            "--data-file", str(data_file),
            str(fixture_path),
            str(dest_dir),
        ),
        timeout=120,
    )

    # Cleanup temp data file
    cleanup_synthetic_copier_data_file(
        data_file=data_file,
        failure_code=cleanup_failure_code,
    )

    return exit_code, stdout, stderr


def cleanup_production_copier_data_file(
    *,
    data_file: Path,
    failure_code: str,
) -> None:
    """Cleanup production Copier data file with fail-closed exception handling.

    Args:
        data_file: Path to the data file to cleanup
        failure_code: Stable failure code to use if cleanup fails

    Raises:
        ProductionCopierDataFileCleanupError: If cleanup fails
    """
    try:
        data_file.unlink(missing_ok=True)
    except Exception as error:
        raise ProductionCopierDataFileCleanupError(
            failure_code,
            str(error),
        )


def materialize_production_copier_data_files(
    parent_dir: Path,
) -> tuple[Path, Path]:
    """Materialize production Copier data files with fail-closed writes.

    Creates true_data.yml and false_data.yml in parent_dir before any production
    Copier invocation. Write failures raise ProductionCopierDataFileMaterializationError
    with stable failure codes.

    Args:
        parent_dir: Parent directory where data files will be created

    Returns:
        (true_data_file, false_data_file) tuple of Paths

    Raises:
        ProductionCopierDataFileMaterializationError: If either write fails
    """
    true_data_file = parent_dir / "true_data.yml"
    false_data_file = parent_dir / "false_data.yml"

    # Write true_data.yml first
    try:
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
    except Exception as error:
        raise ProductionCopierDataFileMaterializationError(
            "PRODUCTION_COPIER_TRUE_DATA_FILE_WRITE_FAILED",
            str(error),
        )

    # Write false_data.yml second
    try:
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
    except Exception as error:
        raise ProductionCopierDataFileMaterializationError(
            "PRODUCTION_COPIER_FALSE_DATA_FILE_WRITE_FAILED",
            str(error),
        )

    return true_data_file, false_data_file


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
    Create a temporary directory with production template files for validation.

    Does NOT initialize git repository. Only performs filesystem materialization.

    Returns the path to the temp directory.

    Raises:
        ProductionTempRepoMaterializationError: If any filesystem materialization step fails
    """
    import shutil

    temp_repo = tmp_dir / "production-template"

    # Step 1: Create directory (fail-closed)
    try:
        temp_repo.mkdir()
    except Exception as e:
        raise ProductionTempRepoMaterializationError(
            "PRODUCTION_TEMP_REPO_DIRECTORY_CREATE_FAILED", str(e)
        )

    # Step 2: Copy copier.yml (fail-closed, required)
    copier_yml_src = working_tree_root / "copier.yml"
    try:
        shutil.copy2(copier_yml_src, temp_repo / "copier.yml")
    except Exception as e:
        raise ProductionTempRepoMaterializationError(
            "PRODUCTION_TEMP_REPO_COPIER_YML_COPY_FAILED", str(e)
        )

    # Step 3: Copy template/ (fail-closed, required)
    template_src = working_tree_root / "template"
    try:
        shutil.copytree(template_src, temp_repo / "template")
    except Exception as e:
        raise ProductionTempRepoMaterializationError(
            "PRODUCTION_TEMP_REPO_TEMPLATE_COPY_FAILED", str(e)
        )

    return temp_repo


def init_production_temp_repo_git(temp_repo: Path) -> None:
    """Initialize production temp repo as git repository.

    Performs required git steps: init, config, add, commit, tag.

    Raises:
        ProductionTempRepoGitSetupError: If any git setup step fails
    """
    run_required_temp_repo_git_step(
        command=["git", "init"],
        cwd=temp_repo,
        failure_code="PRODUCTION_TEMP_REPO_GIT_INIT_FAILED",
    )
    run_required_temp_repo_git_step(
        command=["git", "config", "user.name", "Validator"],
        cwd=temp_repo,
        failure_code="PRODUCTION_TEMP_REPO_GIT_CONFIG_NAME_FAILED",
    )
    run_required_temp_repo_git_step(
        command=["git", "config", "user.email", "validator@localhost"],
        cwd=temp_repo,
        failure_code="PRODUCTION_TEMP_REPO_GIT_CONFIG_EMAIL_FAILED",
    )
    run_required_temp_repo_git_step(
        command=["git", "add", "."],
        cwd=temp_repo,
        failure_code="PRODUCTION_TEMP_REPO_GIT_ADD_FAILED",
    )
    run_required_temp_repo_git_step(
        command=["git", "commit", "-m", "Production template for validation"],
        cwd=temp_repo,
        failure_code="PRODUCTION_TEMP_REPO_GIT_COMMIT_FAILED",
    )
    run_required_temp_repo_git_step(
        command=["git", "tag", "v0.0.1"],
        cwd=temp_repo,
        failure_code="PRODUCTION_TEMP_REPO_GIT_TAG_FAILED",
    )


def evaluate_checkout_portability_contract(
    *,
    repository_root: Path,
    copier_yml_is_file: bool,
    template_is_dir: bool,
    invocation_command: tuple[str, ...],
    invocation_cwd: Path,
) -> tuple[bool, str | None]:
    """Evaluate checkout portability contract.

    Pure evaluator that checks:
    1. repository_root contains copier.yml
    2. repository_root contains template/
    3. invocation command starts with ("uv", "run", "copier")
    4. invocation cwd equals repository_root

    Returns:
        (True, None) if contract passes
        (False, error_code) if contract fails
    """
    if not copier_yml_is_file:
        return False, "VALIDATOR_REPOSITORY_ROOT_INVALID"

    if not template_is_dir:
        return False, "VALIDATOR_REPOSITORY_ROOT_INVALID"

    if not invocation_command[:3] == ("uv", "run", "copier"):
        return False, "PORTABLE_COPIER_COMMAND_PREFIX_INVALID"

    if invocation_cwd != repository_root:
        return False, "PORTABLE_COPIER_CWD_INVALID"

    return True, None


def validate_checkout_portability_marker_isolation_contract() -> tuple[bool, str | None]:
    """Self-check: validate checkout portability marker isolation contract.

    Tests that portability evaluation is independent of synthetic/gate/prod results.

    Returns:
        (True, None) if all test cases pass
        (False, error_code) if any case fails
    """
    test_cases = [
        # Case 1: Valid baseline
        (
            "VALID_BASELINE",
            True,
            True,
            ("uv", "run", "copier", "--version"),
            REPOSITORY_ROOT,
            True,
            None,
        ),
        # Case 2: Missing copier.yml
        (
            "MISSING_COPIER_YML",
            False,
            True,
            ("uv", "run", "copier", "--version"),
            REPOSITORY_ROOT,
            False,
            "VALIDATOR_REPOSITORY_ROOT_INVALID",
        ),
        # Case 3: Missing template
        (
            "MISSING_TEMPLATE",
            True,
            False,
            ("uv", "run", "copier", "--version"),
            REPOSITORY_ROOT,
            False,
            "VALIDATOR_REPOSITORY_ROOT_INVALID",
        ),
        # Case 4: uvx command
        (
            "UVX_COMMAND",
            True,
            True,
            ("uvx", "copier", "--version"),
            REPOSITORY_ROOT,
            False,
            "PORTABLE_COPIER_COMMAND_PREFIX_INVALID",
        ),
        # Case 5: bare copier command
        (
            "BARE_COPIER_COMMAND",
            True,
            True,
            ("copier", "--version"),
            REPOSITORY_ROOT,
            False,
            "PORTABLE_COPIER_COMMAND_PREFIX_INVALID",
        ),
        # Case 6: wrong cwd
        (
            "WRONG_CWD",
            True,
            True,
            ("uv", "run", "copier", "--version"),
            Path("/tmp"),
            False,
            "PORTABLE_COPIER_CWD_INVALID",
        ),
    ]

    for (
        case_name,
        has_copier_yml,
        has_template,
        command,
        cwd,
        expected_pass,
        expected_error,
    ) in test_cases:
        passed, error = evaluate_checkout_portability_contract(
            repository_root=REPOSITORY_ROOT,
            copier_yml_is_file=has_copier_yml,
            template_is_dir=has_template,
            invocation_command=command,
            invocation_cwd=cwd,
        )

        if passed != expected_pass:
            return False, f"{case_name}: expected pass={expected_pass}, got {passed}"

        if expected_pass and error is not None:
            return False, f"{case_name}: expected no error, got {error}"

        if not expected_pass and error != expected_error:
            return False, f"{case_name}: expected error={expected_error}, got {error}"

    # Isolation cases: portability should remain True regardless of synthetic/gate/prod
    # This proves portability evaluator doesn't depend on unrelated contract results
    portability_passed, _ = evaluate_checkout_portability_contract(
        repository_root=REPOSITORY_ROOT,
        copier_yml_is_file=True,
        template_is_dir=True,
        invocation_command=("uv", "run", "copier", "--version"),
        invocation_cwd=REPOSITORY_ROOT,
    )

    if not portability_passed:
        return False, "ISOLATION_BASELINE_PORTABILITY_FAILED"

    return True, None


def read_required_production_output_text(
    *,
    path: Path,
    failure_code: str,
    label: str,
    failures: list[str],
    diagnostics: list[str],
) -> str | None:
    try:
        return path.read_text()
    except Exception as error:
        failures.append(failure_code)
        diagnostics.append(f"{label} read failed: {error}")
        return None


def scan_production_output_relative_paths(
    *,
    root: Path,
    pattern: str,
    failure_code: str,
    label: str,
    failures: list[str],
    diagnostics: list[str],
    name_contains: str | None = None,
) -> list[str] | None:
    try:
        relative_paths: list[str] = []

        for path in root.rglob(pattern):
            if name_contains is not None and name_contains not in path.name:
                continue

            relative_paths.append(str(path.relative_to(root)))

        return relative_paths
    except Exception as error:
        failures.append(failure_code)
        diagnostics.append(f"{label} scan failed: {error}")
        return None


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
    - true_context_routing_exists
    - true_context_routing_workflow_reference_ok
    - true_context_routing_profile_reference_ok
    - true_context_routing_stale_text_absent
    - false_context_routing_exists
    - false_context_routing_runtime_visual_absent
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
        true_workflow_sentinel_ok = False
        true_workflow_disabled_absent = False
        true_workflow_jinja_resolved = False
    else:
        content = read_required_production_output_text(
            path=true_workflow,
            failure_code="PRODUCTION_TRUE_WORKFLOW_READ_FAILED",
            label="WORKFLOW.md",
            failures=failures,
            diagnostics=diagnostics,
        )
        if content is not None:
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
        else:
            true_workflow_sentinel_ok = False
            true_workflow_disabled_absent = False
            true_workflow_jinja_resolved = False

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
        true_profile_status_ok = False
        true_profile_disabled_absent = False
        true_profile_jinja_resolved = False
    else:
        content = read_required_production_output_text(
            path=true_profile,
            failure_code="PRODUCTION_TRUE_PROFILE_READ_FAILED",
            label="PROFILE.md",
            failures=failures,
            diagnostics=diagnostics,
        )
        if content is not None:
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
        else:
            true_profile_status_ok = False
            true_profile_disabled_absent = False
            true_profile_jinja_resolved = False

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
    runtime_visual_paths = scan_production_output_relative_paths(
        root=dest_false,
        pattern="*",
        failure_code="PRODUCTION_FALSE_RUNTIME_VISUAL_PATH_SCAN_FAILED",
        label="Runtime-visual path",
        failures=failures,
        diagnostics=diagnostics,
        name_contains="runtime-visual",
    )

    false_runtime_visual_paths_absent = runtime_visual_paths is not None and len(runtime_visual_paths) == 0
    if runtime_visual_paths is not None and not false_runtime_visual_paths_absent:
        failures.append("PRODUCTION_FALSE_RUNTIME_VISUAL_PATH_EXISTS")
        diagnostics.append(f"Stray runtime-visual paths: {runtime_visual_paths}")

    # Check for .gitkeep in false destination
    gitkeep_paths = scan_production_output_relative_paths(
        root=dest_false,
        pattern=".gitkeep",
        failure_code="PRODUCTION_FALSE_GITKEEP_SCAN_FAILED",
        label=".gitkeep",
        failures=failures,
        diagnostics=diagnostics,
    )

    false_gitkeep_paths_absent = gitkeep_paths is not None and len(gitkeep_paths) == 0
    if gitkeep_paths is not None and not false_gitkeep_paths_absent:
        failures.append("PRODUCTION_FALSE_GITKEEP_EXISTS")
        diagnostics.append(f".gitkeep paths: {gitkeep_paths}")

    # Check for orphan .jinja files in true destination
    true_orphan_jinja = scan_production_output_relative_paths(
        root=dest_true,
        pattern="*.jinja",
        failure_code="PRODUCTION_TRUE_ORPHAN_JINJA_SCAN_FAILED",
        label="True orphan Jinja",
        failures=failures,
        diagnostics=diagnostics,
    )

    # Check for orphan .jinja files in false destination
    false_orphan_jinja = scan_production_output_relative_paths(
        root=dest_false,
        pattern="*.jinja",
        failure_code="PRODUCTION_FALSE_ORPHAN_JINJA_SCAN_FAILED",
        label="False orphan Jinja",
        failures=failures,
        diagnostics=diagnostics,
    )

    # Combine results only if both scans succeeded
    orphan_jinja_absent = (
        true_orphan_jinja is not None
        and false_orphan_jinja is not None
        and len(true_orphan_jinja) == 0
        and len(false_orphan_jinja) == 0
    )

    if true_orphan_jinja is not None and false_orphan_jinja is not None:
        orphan_jinja: list[str] = []
        for path in true_orphan_jinja:
            if path not in orphan_jinja:
                orphan_jinja.append(path)
        for path in false_orphan_jinja:
            if path not in orphan_jinja:
                orphan_jinja.append(path)
    else:
        orphan_jinja = []

    if not orphan_jinja_absent and true_orphan_jinja is not None and false_orphan_jinja is not None:
        failures.append("PRODUCTION_ORPHAN_JINJA_EXISTS")
        diagnostics.append(f"Orphan .jinja paths: {orphan_jinja}")

    # Context routing checks for true destination
    true_context_routing = dest_true / "agents/registry/CONTEXT_ROUTING.md"
    true_context_routing_exists = true_context_routing.exists()

    # Initialize booleans to False, set to True only when checks pass
    true_context_routing_workflow_reference_ok = False
    true_context_routing_profile_reference_ok = False
    true_context_routing_stale_text_absent = False

    if not true_context_routing_exists:
        failures.append("PRODUCTION_TRUE_CONTEXT_ROUTING_MISSING")
        diagnostics.append("CONTEXT_ROUTING.md does not exist in true dest")
        true_context_routing_workflow_reference_ok = False
        true_context_routing_profile_reference_ok = False
        true_context_routing_stale_text_absent = False
    else:
        routing_content = read_required_production_output_text(
            path=true_context_routing,
            failure_code="PRODUCTION_TRUE_CONTEXT_ROUTING_READ_FAILED",
            label="CONTEXT_ROUTING.md (true)",
            failures=failures,
            diagnostics=diagnostics,
        )
        if routing_content is not None:
            true_context_routing_workflow_reference_ok = "agents/modules/runtime-visual/WORKFLOW.md" in routing_content
            if not true_context_routing_workflow_reference_ok:
                failures.append("PRODUCTION_TRUE_CONTEXT_ROUTING_WORKFLOW_REFERENCE_MISSING")
                diagnostics.append("runtime-visual WORKFLOW.md reference not found in CONTEXT_ROUTING.md")

            true_context_routing_profile_reference_ok = "agents/project/runtime-visual/PROFILE.md" in routing_content
            if not true_context_routing_profile_reference_ok:
                failures.append("PRODUCTION_TRUE_CONTEXT_ROUTING_PROFILE_REFERENCE_MISSING")
                diagnostics.append("runtime-visual PROFILE.md reference not found in CONTEXT_ROUTING.md")

            true_context_routing_stale_text_absent = "별도 runtime workflow module이 포함되지 않" not in routing_content
            if not true_context_routing_stale_text_absent:
                failures.append("PRODUCTION_TRUE_CONTEXT_ROUTING_STALE_FOUNDATION_TEXT_PRESENT")
                diagnostics.append("Stale foundation text found in CONTEXT_ROUTING.md")
        else:
            true_context_routing_workflow_reference_ok = False
            true_context_routing_profile_reference_ok = False
            true_context_routing_stale_text_absent = False

    # Context routing checks for false destination
    false_context_routing = dest_false / "agents/registry/CONTEXT_ROUTING.md"
    false_context_routing_exists = false_context_routing.exists()

    # Initialize boolean to False, set to True only when check passes
    false_context_routing_runtime_visual_absent = False

    if not false_context_routing_exists:
        failures.append("PRODUCTION_FALSE_CONTEXT_ROUTING_MISSING")
        diagnostics.append("CONTEXT_ROUTING.md does not exist in false dest")
        false_context_routing_runtime_visual_absent = False
    else:
        false_routing_content = read_required_production_output_text(
            path=false_context_routing,
            failure_code="PRODUCTION_FALSE_CONTEXT_ROUTING_READ_FAILED",
            label="CONTEXT_ROUTING.md (false)",
            failures=failures,
            diagnostics=diagnostics,
        )
        if false_routing_content is not None:
            false_context_routing_runtime_visual_absent = "runtime-visual" not in false_routing_content
            if not false_context_routing_runtime_visual_absent:
                failures.append("PRODUCTION_FALSE_CONTEXT_ROUTING_RUNTIME_VISUAL_REFERENCE_PRESENT")
                diagnostics.append("runtime-visual reference found in false CONTEXT_ROUTING.md")
        else:
            false_context_routing_runtime_visual_absent = False

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
            true_context_routing_exists,
            true_context_routing_workflow_reference_ok,
            true_context_routing_profile_reference_ok,
            true_context_routing_stale_text_absent,
            false_context_routing_exists,
            false_context_routing_runtime_visual_absent,
        ]
    )

    return passed, diagnostics, failures


def render_local_toolchain_contract_lines(
    *,
    passed: bool,
    error_code: str | None,
) -> list[str]:
    """Render local toolchain contract marker lines.

    Pure function that generates exact marker output for local toolchain results.

    Args:
        passed: Whether the local toolchain validation passed
        error_code: Error code if validation failed (must be provided if passed=False)

    Returns:
        List of marker lines to output

    Raises:
        ValueError: If passed=True but error_code is provided, or passed=False but error_code is missing/empty
    """
    if passed and error_code is not None:
        raise ValueError("passed=True but error_code is provided")
    if not passed and (error_code is None or error_code == ""):
        raise ValueError("passed=False but error_code is missing or empty")

    if passed:
        return ["BOOTSTRAP_COPIER_LOCAL_TOOLCHAIN_CONTRACT=PASS"]
    else:
        return [
            "BOOTSTRAP_COPIER_LOCAL_TOOLCHAIN_CONTRACT=FAIL",
            f"FIRST_FAILURE={error_code}",
        ]


def evaluate_local_toolchain_marker_exclusivity(
    *,
    lines: list[str],
    expected_pass: bool,
    expected_error: str | None,
) -> tuple[bool, str | None]:
    """Evaluate exclusivity of PASS/FAIL markers.

    Pure function that checks marker sequence exclusivity.

    Args:
        lines: List of marker lines to evaluate
        expected_pass: Whether success was expected
        expected_error: Expected error code if failure was expected

    Returns:
        (True, None) if exclusivity contract passes
        (False, error_code) if exclusivity contract fails
    """
    PASS_LINE = "BOOTSTRAP_COPIER_LOCAL_TOOLCHAIN_CONTRACT=PASS"
    FAIL_LINE = "BOOTSTRAP_COPIER_LOCAL_TOOLCHAIN_CONTRACT=FAIL"
    FIRST_FAILURE_PREFIX = "FIRST_FAILURE="

    pass_count = 0
    fail_count = 0
    first_failure_count = 0
    first_failure_value: str | None = None

    for line in lines:
        if line == PASS_LINE:
            pass_count += 1
        elif line == FAIL_LINE:
            fail_count += 1
        elif line.startswith(FIRST_FAILURE_PREFIX):
            first_failure_count += 1
            first_failure_value = line[len(FIRST_FAILURE_PREFIX) :]

    if expected_pass:
        # Success expectation: exactly 1 PASS, 0 FAIL, 0 FIRST_FAILURE
        if pass_count != 1:
            return False, f"expected PASS count=1, got {pass_count}"
        if fail_count != 0:
            return False, f"expected FAIL count=0, got {fail_count}"
        if first_failure_count != 0:
            return False, f"expected FIRST_FAILURE count=0, got {first_failure_count}"
    else:
        # Failure expectation: exactly 0 PASS, 1 FAIL, 1 FIRST_FAILURE
        if pass_count != 0:
            return False, f"expected PASS count=0, got {pass_count}"
        if fail_count != 1:
            return False, f"expected FAIL count=1, got {fail_count}"
        if first_failure_count != 1:
            return False, f"expected FIRST_FAILURE count=1, got {first_failure_count}"
        if first_failure_value != expected_error:
            return False, f"expected FIRST_FAILURE={expected_error}, got {first_failure_value}"

    return True, None


def validate_local_toolchain_pass_fail_exclusivity_contract() -> tuple[bool, str | None]:
    """Self-check: validate pass/fail exclusivity contract with deterministic test cases.

    Tests that marker rendering and exclusivity evaluation work correctly.

    Returns:
        (True, None) if all test cases pass
        (False, error_code) if any case fails
    """
    # Valid cases: renderer + evaluator should pass
    valid_cases = [
        ("SUCCESS", True, None),
        ("COMMAND_FAILURE", False, "LOCAL_COPIER_VERSION_COMMAND_FAILED"),
        ("UVX_COMMAND", False, "COPIER_COMMAND_NOT_LOCAL"),
        ("VERSION_MISMATCH", False, "COPIER_VERSION_MISMATCH"),
    ]

    for case_name, passed, error_code in valid_cases:
        lines = render_local_toolchain_contract_lines(passed=passed, error_code=error_code)
        exclusivity_passed, exclusivity_error = evaluate_local_toolchain_marker_exclusivity(
            lines=lines,
            expected_pass=passed,
            expected_error=error_code,
        )
        if not exclusivity_passed:
            return False, f"{case_name}: expected exclusivity PASS, got FAIL: {exclusivity_error}"

    # Invalid sequence cases: evaluator should reject
    invalid_cases = [
        ("DUPLICATE_PASS", ["PASS", "PASS"], True, None),
        ("PASS_AND_FAIL", ["PASS", "FAIL", "FIRST_FAILURE=ERROR"], True, None),
        ("MISSING_FIRST_FAILURE", ["FAIL"], False, "TEST_ERROR"),
        ("DUPLICATE_FAIL", ["FAIL", "FIRST_FAILURE=A", "FAIL", "FIRST_FAILURE=B"], False, "A"),
        ("WRONG_FIRST_FAILURE", ["FAIL", "FIRST_FAILURE=WRONG"], False, "EXPECTED"),
        ("UNEXPECTED_FIRST_FAILURE_ON_SUCCESS", ["PASS", "FIRST_FAILURE=ERROR"], True, None),
    ]

    for case_name, marker_type, expected_pass, expected_error in invalid_cases:
        # Build lines from marker type
        lines = []
        for m in marker_type:
            if m == "PASS":
                lines.append("BOOTSTRAP_COPIER_LOCAL_TOOLCHAIN_CONTRACT=PASS")
            elif m == "FAIL":
                lines.append("BOOTSTRAP_COPIER_LOCAL_TOOLCHAIN_CONTRACT=FAIL")
            elif m.startswith("FIRST_FAILURE="):
                lines.append(m)

        exclusivity_passed, exclusivity_error = evaluate_local_toolchain_marker_exclusivity(
            lines=lines,
            expected_pass=expected_pass,
            expected_error=expected_error,
        )
        if exclusivity_passed:
            return False, f"{case_name}: expected exclusivity FAIL, got PASS"

    return True, None


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
                    "true_context_routing_content": "| agents/modules/runtime-visual/WORKFLOW.md |\n| agents/project/runtime-visual/PROFILE.md |\n",
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
                    "true_context_routing_content": "| agents/modules/runtime-visual/WORKFLOW.md |\n| agents/project/runtime-visual/PROFILE.md |\n",
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
                    "true_context_routing_content": "| agents/modules/runtime-visual/WORKFLOW.md |\n| agents/project/runtime-visual/PROFILE.md |\n",
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
                    "true_context_routing_content": "| agents/modules/runtime-visual/WORKFLOW.md |\n| agents/project/runtime-visual/PROFILE.md |\n",
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
                    "true_context_routing_content": "| agents/modules/runtime-visual/WORKFLOW.md |\n| agents/project/runtime-visual/PROFILE.md |\n",
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
                    "true_context_routing_content": "| agents/modules/runtime-visual/WORKFLOW.md |\n| agents/project/runtime-visual/PROFILE.md |\n",
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
                    "true_context_routing_content": "| agents/modules/runtime-visual/WORKFLOW.md |\n| agents/project/runtime-visual/PROFILE.md |\n",
                    "false_stray_paths": False,
                    "false_gitkeep": True,
                    "orphan_jinja": False,
                },
                False,
            ),
            # Case 8: True context routing missing workflow reference → FAIL
            (
                "TRUE_ROUTING_WORKFLOW_REFERENCE_MISSING",
                True,
                {
                    "true_workflow_content": "RUNTIME_VISUAL_CORE_VERSION=1\n",
                    "true_profile_content": "PROFILE_STATUS: INCOMPLETE\n",
                    "true_context_routing_content": "| agents/project/runtime-visual/PROFILE.md |\n",
                    "false_stray_paths": False,
                    "false_gitkeep": False,
                    "orphan_jinja": False,
                },
                False,
            ),
            # Case 9: True context routing missing profile reference → FAIL
            (
                "TRUE_ROUTING_PROFILE_REFERENCE_MISSING",
                True,
                {
                    "true_workflow_content": "RUNTIME_VISUAL_CORE_VERSION=1\n",
                    "true_profile_content": "PROFILE_STATUS: INCOMPLETE\n",
                    "true_context_routing_content": "| agents/modules/runtime-visual/WORKFLOW.md |\n",
                    "false_stray_paths": False,
                    "false_gitkeep": False,
                    "orphan_jinja": False,
                },
                False,
            ),
            # Case 10: True context routing stale foundation text → FAIL
            (
                "TRUE_ROUTING_STALE_FOUNDATION_TEXT_PRESENT",
                True,
                {
                    "true_workflow_content": "RUNTIME_VISUAL_CORE_VERSION=1\n",
                    "true_profile_content": "PROFILE_STATUS: INCOMPLETE\n",
                    "true_context_routing_content": (
                        "agents/modules/runtime-visual/WORKFLOW.md\n"
                        "agents/project/runtime-visual/PROFILE.md\n"
                        "별도 runtime workflow module이 포함되지 않으므로\n"
                    ),
                    "false_stray_paths": False,
                    "false_gitkeep": False,
                    "orphan_jinja": False,
                },
                False,
            ),
            # Case 11: False context routing has runtime-visual reference → FAIL
            (
                "FALSE_ROUTING_RUNTIME_VISUAL_REFERENCE_PRESENT",
                True,
                {
                    "true_workflow_content": "RUNTIME_VISUAL_CORE_VERSION=1\n",
                    "true_profile_content": "PROFILE_STATUS: INCOMPLETE\n",
                    "true_context_routing_content": "| agents/modules/runtime-visual/WORKFLOW.md |\n| agents/project/runtime-visual/PROFILE.md |\n",
                    "false_context_routing_content": "runtime-visual\n",
                    "false_stray_paths": False,
                    "false_gitkeep": False,
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

            # Create true destination context routing
            if "true_context_routing_content" in config:
                context_routing_dir = dest_true / "agents/registry"
                context_routing_dir.mkdir(parents=True, exist_ok=True)
                context_routing = context_routing_dir / "CONTEXT_ROUTING.md"
                context_routing.write_text(config["true_context_routing_content"])

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

            # Create false destination context routing
            if "false_context_routing_content" in config:
                context_routing_dir = dest_false / "agents/registry"
                context_routing_dir.mkdir(parents=True, exist_ok=True)
                context_routing = context_routing_dir / "CONTEXT_ROUTING.md"
                context_routing.write_text(config["false_context_routing_content"])
            else:
                # Always create an empty context routing for false case if not specified
                context_routing_dir = dest_false / "agents/registry"
                context_routing_dir.mkdir(parents=True, exist_ok=True)
                context_routing = context_routing_dir / "CONTEXT_ROUTING.md"
                context_routing.write_text("")

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
    true_data_file: Path,
    false_data_file: Path,
) -> tuple[bool, list[str]]:
    """
    Validate production template with true and false profiles.

    Args:
        temp_repo: Path to temp repo with production template
        dest_true: Destination for true profile
        dest_false: Destination for false profile
        true_data_file: Pre-materialized true data file path
        false_data_file: Pre-materialized false data file path

    Returns (passed, diagnostic_messages).
    """
    # True profile copy
    exit_code_true, stdout_true, stderr_true = run_local_copier(
        args=(
            "copy",
            "--defaults",
            "--vcs-ref", "v0.0.1",
            "--data-file", str(true_data_file),
            str(temp_repo),
            str(dest_true),
        ),
        timeout=120,
    )

    # Cleanup true data file
    cleanup_production_copier_data_file(
        data_file=true_data_file,
        failure_code="PRODUCTION_COPIER_TRUE_DATA_FILE_CLEANUP_FAILED",
    )

    # False profile copy
    exit_code_false, stdout_false, stderr_false = run_local_copier(
        args=(
            "copy",
            "--defaults",
            "--vcs-ref", "v0.0.1",
            "--data-file", str(false_data_file),
            str(temp_repo),
            str(dest_false),
        ),
        timeout=120,
    )

    # Cleanup false data file
    cleanup_production_copier_data_file(
        data_file=false_data_file,
        failure_code="PRODUCTION_COPIER_FALSE_DATA_FILE_CLEANUP_FAILED",
    )

    # Emit cleanup contract PASS marker before output evaluation
    print("BOOTSTRAP_PRODUCTION_COPIER_DATA_FILE_CLEANUP_CONTRACT=PASS")

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
    # Phase 0: Repository root preflight and portability contract evaluation
    copier_yml_path = REPOSITORY_ROOT / "copier.yml"
    template_dir_path = REPOSITORY_ROOT / "template"

    # Build representative invocation spec for portability evaluation
    version_command, version_cwd, _ = build_local_copier_invocation(
        ("--version",),
        timeout=30,
    )

    # Evaluate checkout portability contract
    portability_passed, portability_error = evaluate_checkout_portability_contract(
        repository_root=REPOSITORY_ROOT,
        copier_yml_is_file=copier_yml_path.is_file(),
        template_is_dir=template_dir_path.is_dir(),
        invocation_command=version_command,
        invocation_cwd=version_cwd,
    )

    if not portability_passed:
        print("BOOTSTRAP_COPIER_VALIDATOR_CHECKOUT_PORTABILITY_CONTRACT=FAIL")
        print(f"FIRST_FAILURE={portability_error}")
        return 1

    # Phase 0.5: Portability marker isolation self-check
    isolation_passed, isolation_error = validate_checkout_portability_marker_isolation_contract()
    if not isolation_passed:
        print(
            "BOOTSTRAP_COPIER_CHECKOUT_PORTABILITY_"
            "MARKER_ISOLATION_CONTRACT=FAIL"
        )
        print(f"FIRST_FAILURE={isolation_error}")
        return 1

    # Phase 0.1: Local toolchain contract self-check (synthetic probe only)
    self_check_passed, _ = validate_local_copier_toolchain_contract()
    if self_check_passed:
        print("COPIER_LOCAL_TOOLCHAIN_SYNTHETIC_PROBE=PASS")
    if not self_check_passed:
        print("BOOTSTRAP_COPIER_LOCAL_TOOLCHAIN_CONTRACT=FAIL")
        print("FIRST_FAILURE=LOCAL_TOOLCHAIN_SELF_CHECK_FAILED")
        return 1

    # Phase 1: Parser contract self-check
    parser_contract_pass = validate_answers_parser_contract()
    if parser_contract_pass:
        print("BOOTSTRAP_COPIER_ANSWERS_EXACT_KEY_CONTRACT=PASS")
    if not parser_contract_pass:
        print("BOOTSTRAP_COPIER_ANSWERS_EXACT_KEY_CONTRACT=FAIL")
        print("FIRST_FAILURE=PARSER_CONTRACT_SELF_CHECK_FAILED")
        return 1

    # Phase 2: Actual local toolchain validation with real command execution
    exit_code, stdout, stderr = run_local_copier(
        args=("--version",),
        timeout=30,
    )
    contract_passed, error_code = evaluate_actual_local_toolchain_result(
        exit_code=exit_code,
        command=tuple(version_command),
        version_line=stdout.strip(),
    )
    if not contract_passed:
        marker_lines = render_local_toolchain_contract_lines(passed=False, error_code=error_code)
        for line in marker_lines:
            print(line)
        if error_code == "LOCAL_COPIER_VERSION_COMMAND_FAILED":
            print(f"  Error: {stderr}")
        return 1

    # Actual validation succeeded: emit production PASS markers
    marker_lines = render_local_toolchain_contract_lines(passed=True, error_code=None)
    for line in marker_lines:
        print(line)
    print(f"Copier version: {stdout.strip()}")
    print("COPIER_COMMAND=uv run copier")
    print("BOOTSTRAP_COPIER_VALIDATOR_CHECKOUT_PORTABILITY_CONTRACT=PASS")
    print("BOOTSTRAP_COPIER_CHECKOUT_PORTABILITY_MARKER_ISOLATION_CONTRACT=PASS")
    print(f"COPIER_VERSION={TARGET_COPIER_VERSION}")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create fixture for synthetic conditional path test
        fixture_dir = tmpdir_path / "fixture"

        # Phase 1: Synthetic fixture materialization (fail-closed)
        try:
            create_fixture(fixture_dir)
        except SyntheticFixtureMaterializationError as e:
            print("BOOTSTRAP_SYNTHETIC_FIXTURE_MATERIALIZATION_CONTRACT=FAIL")
            print(f"FIRST_FAILURE={e.failure_code}")
            print(f"  Detail: {e.detail}")
            return 1

        print("BOOTSTRAP_SYNTHETIC_FIXTURE_MATERIALIZATION_CONTRACT=PASS")

        # Phase 2: Synthetic fixture Git setup
        try:
            init_fixture_git(fixture_dir)
        except SyntheticFixtureGitSetupError as e:
            print("BOOTSTRAP_SYNTHETIC_FIXTURE_GIT_SETUP_CONTRACT=FAIL")
            print(f"FIRST_FAILURE={e.failure_code}")
            print(f"  Detail: {e.detail}")
            return 1

        print("BOOTSTRAP_SYNTHETIC_FIXTURE_GIT_SETUP_CONTRACT=PASS")

        # Create destinations for synthetic test
        true_dest_synthetic = tmpdir_path / "true-dest"
        false_dest_synthetic = tmpdir_path / "false-dest"

        # Run copier for synthetic test
        print("\n=== Running synthetic conditional path test ===")
        try:
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
        except SyntheticCopierDataFileMaterializationError as error:
            print(
                "BOOTSTRAP_SYNTHETIC_COPIER_"
                "DATA_FILE_MATERIALIZATION_CONTRACT=FAIL"
            )
            print(f"FIRST_FAILURE={error.failure_code}")
            print(f"  Detail: {error.detail}")
            return 1
        except SyntheticCopierDataFileCleanupError as error:
            print(
                "BOOTSTRAP_SYNTHETIC_COPIER_"
                "DATA_FILE_CLEANUP_CONTRACT=FAIL"
            )
            print(f"FIRST_FAILURE={error.failure_code}")
            print(f"  Detail: {error.detail}")
            return 1

        print(
            "BOOTSTRAP_SYNTHETIC_COPIER_"
            "DATA_FILE_CLEANUP_CONTRACT=PASS"
        )
        print(
            "BOOTSTRAP_SYNTHETIC_COPIER_"
            "DATA_FILE_MATERIALIZATION_CONTRACT=PASS"
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

        # Phase 3.1: Materialization
        try:
            temp_repo = create_production_temp_repo(REPOSITORY_ROOT, tmpdir_path)
        except ProductionTempRepoMaterializationError as e:
            print("BOOTSTRAP_PRODUCTION_TEMP_REPO_MATERIALIZATION_CONTRACT=FAIL")
            print(f"FIRST_FAILURE={e.failure_code}")
            print(f"  Detail: {e.detail}")
            return 1

        print("BOOTSTRAP_PRODUCTION_TEMP_REPO_MATERIALIZATION_CONTRACT=PASS")

        # Phase 3.2: Git setup
        try:
            init_production_temp_repo_git(temp_repo)
        except ProductionTempRepoGitSetupError as e:
            print("BOOTSTRAP_PRODUCTION_TEMP_REPO_GIT_SETUP_CONTRACT=FAIL")
            print(f"FIRST_FAILURE={e.failure_code}")
            print(f"  Detail: {e.detail}")
            return 1

        print("BOOTSTRAP_PRODUCTION_TEMP_REPO_GIT_SETUP_CONTRACT=PASS")

        # Create destinations for production test
        dest_true_prod = tmpdir_path / "true-prod"
        dest_false_prod = tmpdir_path / "false-prod"

        # Phase 3.3: Materialize production Copier data files (fail-closed)
        try:
            true_data_file, false_data_file = materialize_production_copier_data_files(
                tmpdir_path
            )
        except ProductionCopierDataFileMaterializationError as e:
            print("BOOTSTRAP_PRODUCTION_COPIER_DATA_FILE_MATERIALIZATION_CONTRACT=FAIL")
            print(f"FIRST_FAILURE={e.failure_code}")
            print(f"  Detail: {e.detail}")
            return 1

        print("BOOTSTRAP_PRODUCTION_COPIER_DATA_FILE_MATERIALIZATION_CONTRACT=PASS")

        try:
            prod_passed, prod_issues = validate_production_template(
                temp_repo,
                dest_true_prod,
                dest_false_prod,
                true_data_file,
                false_data_file,
            )
        except ProductionCopierDataFileCleanupError as e:
            print("BOOTSTRAP_PRODUCTION_COPIER_DATA_FILE_CLEANUP_CONTRACT=FAIL")
            print(f"FIRST_FAILURE={e.failure_code}")
            print(f"  Detail: {e.detail}")
            return 1

        print("\n=== Production Validation Results ===")
        for issue in prod_issues:
            print(f"  {issue}")

        if prod_passed:
            print("\nBOOTSTRAP_RUNTIME_VISUAL_PRODUCTION_CONDITIONAL_PATH_CONTRACT=PASS")
        else:
            print("\nBOOTSTRAP_RUNTIME_VISUAL_PRODUCTION_CONDITIONAL_PATH_CONTRACT=FAIL")

        # Phase 4: Pass/fail exclusivity contract self-check
        print("\n=== Running pass/fail exclusivity contract self-check ===")
        exclusivity_passed, exclusivity_error = validate_local_toolchain_pass_fail_exclusivity_contract()

        if not exclusivity_passed:
            print("LOCAL_TOOLCHAIN_PASS_FAIL_EXCLUSIVITY_CONTRACT=FAIL")
            print(f"FIRST_FAILURE={exclusivity_error}")
            return 1

        print("LOCAL_TOOLCHAIN_PASS_FAIL_EXCLUSIVITY_CONTRACT=PASS")

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
