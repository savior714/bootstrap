#!/usr/bin/env python3
"""Bootstrap v2 Copier CLI Contract Validator.

Validates Copier copy/update lifecycle for v2 foundation.
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml

TARGET_COPIER_VERSION = "9.17.0"

COPIER_COMMAND = ("uv", "run", "--frozen", "copier")

SIMPLE_PROFILE = {
    "project_name": "Simple Smoke",
    "project_slug": "simple-smoke",
    "canonical_branch": "main",
    "main_only": True,
    "package_tool": "other",
    "lint_command": "",
    "typecheck_command": "",
    "targeted_test_command": "",
    "release_check_command": "",
    "has_runtime_visual": False,
    "has_database": False,
    "has_content_provenance": False,
    "regulated_domain": False,
}

FULL_PROFILE = {
    "project_name": "Full Capability Smoke",
    "project_slug": "full-capability-smoke",
    "canonical_branch": "main",
    "main_only": True,
    "package_tool": "uv",
    "lint_command": "uv run ruff check .",
    "typecheck_command": "uv run mypy .",
    "targeted_test_command": "uv run pytest tests/unit/test_target.py",
    "release_check_command": "uv run pytest",
    "has_runtime_visual": True,
    "has_database": True,
    "has_content_provenance": True,
    "regulated_domain": True,
}

REQUIRED_GENERATED_PATHS = [
    ".copier-answers.yml",
    ".agent-harness.yml",
    "AGENTS.md",
    "agents/project/PROFILE.md",
    "docs/product/ACTIVE_SCOPE.md",
]

JINJA_MARKERS = ["{{", "{%", "{#"]

RUNTIME_VISUAL_PROFILE_PATH = (
    "agents/project/runtime-visual/PROFILE.md"
)

RUNTIME_VISUAL_PROFILE_ARCHITECTURE_BULLET = (
    "- `agents/project/runtime-visual/PROFILE.md` "
    "— `has_runtime_visual=true` 프로젝트"
)

OVERLAY_FILES = [
    "agents/project/PROFILE.md",
    "agents/project/runtime-visual/PROFILE.md",
    "docs/product/ACTIVE_SCOPE.md",
]

OVERLAY_SENTINELS = {
    "agents/project/PROFILE.md": "BOOTSTRAP_VALIDATOR_PROFILE_OVERLAY_SENTINEL",
    "agents/project/runtime-visual/PROFILE.md": "BOOTSTRAP_VALIDATOR_RUNTIME_VISUAL_PROFILE_OVERLAY_SENTINEL",
    "docs/product/ACTIVE_SCOPE.md": "BOOTSTRAP_VALIDATOR_ACTIVE_SCOPE_OVERLAY_SENTINEL",
}

TEMPLATE_CORE_SENTINEL = "BOOTSTRAP_VALIDATOR_TEMPLATE_CORE_V2_SENTINEL"
RUNTIME_VISUAL_PROFILE_TEMPLATE_SENTINEL = (
    "BOOTSTRAP_VALIDATOR_RUNTIME_VISUAL_PROFILE_UPDATE_SENTINEL"
)

COMMAND_SSOT_HARNESS_COMMAND_AUTHORITY_PRESENT = "COMMAND_SSOT_HARNESS_COMMAND_AUTHORITY_PRESENT"
COMMAND_SSOT_HARNESS_PACKAGE_TOOL_METADATA_MISSING = "COMMAND_SSOT_HARNESS_PACKAGE_TOOL_METADATA_MISSING"
COMMAND_SSOT_HARNESS_PACKAGE_TOOL_METADATA_MISMATCH = "COMMAND_SSOT_HARNESS_PACKAGE_TOOL_METADATA_MISMATCH"
COMMAND_SSOT_PROJECT_PROFILE_COMMAND_MISSING = "COMMAND_SSOT_PROJECT_PROFILE_COMMAND_MISSING"
COMMAND_SSOT_PROJECT_PROFILE_COMMAND_SSOT_DECLARATION_MISSING = "COMMAND_SSOT_PROJECT_PROFILE_COMMAND_SSOT_DECLARATION_MISSING"
COMMAND_SSOT_AGENTS_PROJECT_PROFILE_COMMAND_AUTHORITY_MISSING = "COMMAND_SSOT_AGENTS_PROJECT_PROFILE_COMMAND_AUTHORITY_MISSING"
COMMAND_SSOT_AGENTS_DUPLICATE_COMMAND_AUTHORITY_PRESENT = "COMMAND_SSOT_AGENTS_DUPLICATE_COMMAND_AUTHORITY_PRESENT"

RUNTIME_VISUAL_PROFILE_OWNERSHIP_DECLARATION_MISSING = "RUNTIME_VISUAL_PROFILE_OWNERSHIP_DECLARATION_MISSING"
RUNTIME_VISUAL_PROFILE_ARCHITECTURE_OWNERSHIP_MISSING = "RUNTIME_VISUAL_PROFILE_ARCHITECTURE_OWNERSHIP_MISSING"
RUNTIME_VISUAL_PROFILE_ARCHITECTURE_MISCLASSIFIED = "RUNTIME_VISUAL_PROFILE_ARCHITECTURE_MISCLASSIFIED"
RUNTIME_VISUAL_PROFILE_SKIP_IF_EXISTS_MISSING = "RUNTIME_VISUAL_PROFILE_SKIP_IF_EXISTS_MISSING"
RUNTIME_VISUAL_PROFILE_SKIP_IF_EXISTS_DUPLICATE = "RUNTIME_VISUAL_PROFILE_SKIP_IF_EXISTS_DUPLICATE"
RUNTIME_VISUAL_PROFILE_SKIP_IF_EXISTS_INVALID = "RUNTIME_VISUAL_PROFILE_SKIP_IF_EXISTS_INVALID"

TEMP_TEMPLATE_SOURCE_ROOTS = (
    "copier.yml",
    "template",
)

TEMP_TEMPLATE_REQUIRED_SOURCE_MISSING = "TEMP_TEMPLATE_REQUIRED_SOURCE_MISSING"
TEMP_TEMPLATE_REQUIRED_SOURCE_COPY_FAILED = (
    "TEMP_TEMPLATE_REQUIRED_SOURCE_COPY_FAILED"
)
TEMP_TEMPLATE_CANDIDATE_SOURCE_MISSING = "TEMP_TEMPLATE_CANDIDATE_SOURCE_MISSING"
TEMP_TEMPLATE_UNRELATED_SOURCE_COPIED = "TEMP_TEMPLATE_UNRELATED_SOURCE_COPIED"
TEMP_TEMPLATE_SOURCE_GIT_METADATA_COPIED = "TEMP_TEMPLATE_SOURCE_GIT_METADATA_COPIED"
TEMP_TEMPLATE_REPOSITORY_NOT_CLEAN = "TEMP_TEMPLATE_REPOSITORY_NOT_CLEAN"
TEMP_TEMPLATE_INITIAL_TAG_MISSING = "TEMP_TEMPLATE_INITIAL_TAG_MISSING"

TEMP_TEMPLATE_GIT_INIT_FAILED = "TEMP_TEMPLATE_GIT_INIT_FAILED"
TEMP_TEMPLATE_GIT_CONFIG_NAME_FAILED = "TEMP_TEMPLATE_GIT_CONFIG_NAME_FAILED"
TEMP_TEMPLATE_GIT_CONFIG_EMAIL_FAILED = "TEMP_TEMPLATE_GIT_CONFIG_EMAIL_FAILED"
TEMP_TEMPLATE_GIT_ADD_FAILED = "TEMP_TEMPLATE_GIT_ADD_FAILED"
TEMP_TEMPLATE_GIT_COMMIT_FAILED = "TEMP_TEMPLATE_GIT_COMMIT_FAILED"
TEMP_TEMPLATE_GIT_TAG_FAILED = "TEMP_TEMPLATE_GIT_TAG_FAILED"

TEMP_TEMPLATE_STATUS_INSPECTION_FAILED = (
    "TEMP_TEMPLATE_STATUS_INSPECTION_FAILED"
)


def run_temp_template_git_step(
    *,
    cmd: list[str],
    repo_dir: Path,
    failure_code: str,
    label: str,
) -> None:
    try:
        result = run_cmd(cmd, cwd=repo_dir, check=False)
    except Exception as error:
        shutil.rmtree(repo_dir, ignore_errors=True)
        print("BOOTSTRAP_V2_COPIER_CLI_CONTRACT=FAIL")
        print(f"FIRST_FAILURE={failure_code}")
        print(f"DETAIL={label} invocation failed: {error}")
        print(f"COPIER_VERSION={TARGET_COPIER_VERSION}")
        sys.exit(1)

    if result.returncode == 0:
        return

    shutil.rmtree(repo_dir, ignore_errors=True)
    print("BOOTSTRAP_V2_COPIER_CLI_CONTRACT=FAIL")
    print(f"FIRST_FAILURE={failure_code}")
    print(
        "DETAIL="
        f"{label} failed with exit code {result.returncode}"
    )
    print(f"COPIER_VERSION={TARGET_COPIER_VERSION}")

    if result.stdout:
        print(f"STDOUT: {result.stdout}", file=sys.stderr)
    if result.stderr:
        print(f"STDERR: {result.stderr}", file=sys.stderr)

    sys.exit(1)


def run_cmd(cmd: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)
    if check and result.returncode != 0:
        print(f"COMMAND_FAILED: {' '.join(cmd)}", file=sys.stderr)
        print(f"STDOUT: {result.stdout}", file=sys.stderr)
        print(f"STDERR: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    return result


def check_copier_version() -> None:
    result = run_cmd([*COPIER_COMMAND, "--version"], check=False)
    if result.returncode != 0:
        print("BOOTSTRAP_V2_COPIER_CLI_CONTRACT=FAIL")
        print("FIRST_FAILURE=COPIER_VERSION_MISMATCH")
        print("DETAIL=copier CLI not available")
        print(f"COPIER_VERSION=unknown")
        sys.exit(1)

    match = re.search(r"copier\s+(\d+\.\d+\.\d+)", result.stdout)
    if not match:
        print("BOOTSTRAP_V2_COPIER_CLI_CONTRACT=FAIL")
        print("FIRST_FAILURE=COPIER_VERSION_MISMATCH")
        print("DETAIL=could not parse copier version")
        print(f"COPIER_VERSION=unknown")
        sys.exit(1)

    actual = match.group(1)
    if actual != TARGET_COPIER_VERSION:
        print("BOOTSTRAP_V2_COPIER_CLI_CONTRACT=FAIL")
        print("FIRST_FAILURE=COPIER_VERSION_MISMATCH")
        print(f"DETAIL=expected {TARGET_COPIER_VERSION}, got {actual}")
        print(f"COPIER_VERSION={actual}")
        sys.exit(1)


def setup_temp_template(template_dir: Path) -> Path:
    repo_dir = Path(tempfile.mkdtemp(prefix="bootstrap-v2-template-"))

    run_temp_template_git_step(
        cmd=["git", "init"],
        repo_dir=repo_dir,
        failure_code=TEMP_TEMPLATE_GIT_INIT_FAILED,
        label="temp template git init",
    )
    run_temp_template_git_step(
        cmd=["git", "config", "user.name", "Bootstrap Validator"],
        repo_dir=repo_dir,
        failure_code=TEMP_TEMPLATE_GIT_CONFIG_NAME_FAILED,
        label="temp template git user.name config",
    )
    run_temp_template_git_step(
        cmd=["git", "config", "user.email", "bootstrap-validator@example.invalid"],
        repo_dir=repo_dir,
        failure_code=TEMP_TEMPLATE_GIT_CONFIG_EMAIL_FAILED,
        label="temp template git user.email config",
    )

    for relative_path in TEMP_TEMPLATE_SOURCE_ROOTS:
        source = template_dir / relative_path
        destination = repo_dir / relative_path
        if not source.exists():
            shutil.rmtree(repo_dir, ignore_errors=True)
            print("BOOTSTRAP_V2_COPIER_CLI_CONTRACT=FAIL")
            print("FIRST_FAILURE=TEMP_TEMPLATE_REQUIRED_SOURCE_MISSING")
            print(f"DETAIL=required source {relative_path} not found")
            print(f"COPIER_VERSION={TARGET_COPIER_VERSION}")
            sys.exit(1)
        if destination.exists():
            if destination.is_dir():
                shutil.rmtree(destination)
            else:
                destination.unlink()
        try:
            if source.is_dir():
                shutil.copytree(source, destination)
            else:
                shutil.copy2(source, destination)
        except Exception as error:
            shutil.rmtree(repo_dir, ignore_errors=True)
            print("BOOTSTRAP_V2_COPIER_CLI_CONTRACT=FAIL")
            print(f"FIRST_FAILURE={TEMP_TEMPLATE_REQUIRED_SOURCE_COPY_FAILED}")
            print(
                "DETAIL="
                f"required source {relative_path} copy failed: {error}"
            )
            print(f"COPIER_VERSION={TARGET_COPIER_VERSION}")
            sys.exit(1)

    run_temp_template_git_step(
        cmd=["git", "add", "."],
        repo_dir=repo_dir,
        failure_code=TEMP_TEMPLATE_GIT_ADD_FAILED,
        label="temp template git add",
    )
    run_temp_template_git_step(
        cmd=["git", "commit", "-m", "Initial commit from working tree"],
        repo_dir=repo_dir,
        failure_code=TEMP_TEMPLATE_GIT_COMMIT_FAILED,
        label="temp template git commit",
    )
    run_temp_template_git_step(
        cmd=["git", "tag", "v0.0.1"],
        repo_dir=repo_dir,
        failure_code=TEMP_TEMPLATE_GIT_TAG_FAILED,
        label="temp template git tag",
    )

    return repo_dir


def run_copier_copy(template_src: Path, destination: Path, profile: dict[str, Any]) -> None:
    cmd = [
        *COPIER_COMMAND,
        "copy",
        "--defaults",
        "--vcs-ref",
        "v0.0.1",
        "-f",
        str(template_src),
        str(destination),
    ]

    for key, value in profile.items():
        cmd.extend(["-d", f"{key}={value}"])

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=".")
    if result.returncode != 0:
        print("BOOTSTRAP_V2_COPIER_CLI_CONTRACT=FAIL")
        print("FIRST_FAILURE=SIMPLE_COPY_FAILED" if profile == SIMPLE_PROFILE else "FIRST_FAILURE=FULL_COPY_FAILED")
        print(f"DETAIL=copier copy failed with exit code {result.returncode}")
        print(f"COPIER_VERSION={TARGET_COPIER_VERSION}")
        if result.stderr:
            print(f"STDERR: {result.stderr}", file=sys.stderr)
        sys.exit(1)


def validate_copier_answers(destination: Path, profile: dict[str, Any]) -> None:
    answers_file = destination / ".copier-answers.yml"
    if not answers_file.exists():
        print("BOOTSTRAP_V2_COPIER_CLI_CONTRACT=FAIL")
        print("FIRST_FAILURE=SIMPLE_RENDER_CONTRACT_FAILED" if profile == SIMPLE_PROFILE else "FIRST_RENDER_CONTRACT_FAILED")
        print("DETAIL=.copier-answers.yml not found")
        print(f"COPIER_VERSION={TARGET_COPIER_VERSION}")
        sys.exit(1)

    with open(answers_file) as f:
        answers = yaml.safe_load(f)

    if answers.get("project_name") != profile["project_name"]:
        print("BOOTSTRAP_V2_COPIER_CLI_CONTRACT=FAIL")
        print("FIRST_FAILURE=SIMPLE_RENDER_CONTRACT_FAILED" if profile == SIMPLE_PROFILE else "FULL_RENDER_CONTRACT_FAILED")
        print(f"DETAIL=project_name mismatch: expected {profile['project_name']}, got {answers.get('project_name')}")
        print(f"COPIER_VERSION={TARGET_COPIER_VERSION}")
        sys.exit(1)

    if answers.get("project_slug") != profile["project_slug"]:
        print("BOOTSTRAP_V2_COPIER_CLI_CONTRACT=FAIL")
        print("FIRST_FAILURE=SIMPLE_RENDER_CONTRACT_FAILED" if profile == SIMPLE_PROFILE else "FULL_RENDER_CONTRACT_FAILED")
        print(f"DETAIL=project_slug mismatch")
        print(f"COPIER_VERSION={TARGET_COPIER_VERSION}")
        sys.exit(1)

    for key in ["has_runtime_visual", "has_database", "has_content_provenance", "regulated_domain"]:
        if answers.get(key) != profile[key]:
            print("BOOTSTRAP_V2_COPIER_CLI_CONTRACT=FAIL")
            print("FIRST_FAILURE=SIMPLE_RENDER_CONTRACT_FAILED" if profile == SIMPLE_PROFILE else "FULL_RENDER_CONTRACT_FAILED")
            print(f"DETAIL={key} mismatch: expected {profile[key]}, got {answers.get(key)}")
            print(f"COPIER_VERSION={TARGET_COPIER_VERSION}")
            sys.exit(1)

    for path in REQUIRED_GENERATED_PATHS:
        if not (destination / path).exists():
            print("BOOTSTRAP_V2_COPIER_CLI_CONTRACT=FAIL")
            print("FIRST_FAILURE=SIMPLE_RENDER_CONTRACT_FAILED" if profile == SIMPLE_PROFILE else "FULL_RENDER_CONTRACT_FAILED")
            print(f"DETAIL=required path {path} not found")
            print(f"COPIER_VERSION={TARGET_COPIER_VERSION}")
            sys.exit(1)


def validate_yaml_files(destination: Path) -> None:
    yaml_files = []
    for pattern in ["**/*.yml", "**/*.yaml"]:
        yaml_files.extend(destination.glob(pattern))

    if not yaml_files:
        print("BOOTSTRAP_V2_COPIER_CLI_CONTRACT=FAIL")
        print("FIRST_FAILURE=GENERATED_YAML_PARSE_FAILED")
        print("DETAIL=no YAML files found")
        print(f"COPIER_VERSION={TARGET_COPIER_VERSION}")
        sys.exit(1)

    for yaml_file in yaml_files:
        try:
            with open(yaml_file, encoding="utf-8") as f:
                list(yaml.safe_load_all(f))
        except Exception as e:
            print("BOOTSTRAP_V2_COPIER_CLI_CONTRACT=FAIL")
            print("FIRST_FAILURE=GENERATED_YAML_PARSE_FAILED")
            print(f"DETAIL=failed to parse {yaml_file}: {e}")
            print(f"COPIER_VERSION={TARGET_COPIER_VERSION}")
            sys.exit(1)


def check_unresolved_markers(destination: Path) -> None:
    for item in destination.rglob("*"):
        if item.is_dir() or ".git" in str(item):
            continue
        if not item.is_file():
            continue

        try:
            content = item.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue

        for marker in JINJA_MARKERS:
            if marker in content:
                print("BOOTSTRAP_V2_COPIER_CLI_CONTRACT=FAIL")
                print("FIRST_FAILURE=UNRESOLVED_TEMPLATE_MARKER_FOUND")
                print(f"DETAIL={marker} found in {item}")
                print(f"COPIER_VERSION={TARGET_COPIER_VERSION}")
                sys.exit(1)


def get_file_sha256(file_path: Path) -> str:
    import hashlib

    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        sha256.update(f.read())
    return sha256.hexdigest()


def setup_full_destination_git(destination: Path) -> None:
    run_cmd(["git", "init"], cwd=destination)
    run_cmd(["git", "config", "user.name", "Bootstrap Validator"], cwd=destination)
    run_cmd(["git", "config", "user.email", "bootstrap-validator@example.invalid"], cwd=destination)
    run_cmd(["git", "add", "."], cwd=destination)
    run_cmd(["git", "commit", "-m", "Initial generated commit"], cwd=destination)

    result = run_cmd(["git", "status", "--porcelain"], cwd=destination, check=False)
    if result.stdout.strip():
        print("BOOTSTRAP_V2_COPIER_CLI_CONTRACT=FAIL")
        print("FIRST_FAILURE=GENERATED_PROJECT_GIT_NOT_CLEAN")
        print("DETAIL=generated repository has uncommitted changes")
        print(f"COPIER_VERSION={TARGET_COPIER_VERSION}")
        sys.exit(1)


def apply_overlay_sentinels(destination: Path) -> dict[str, str]:
    for file_path in OVERLAY_FILES:
        full_path = destination / file_path
        sentinel = OVERLAY_SENTINELS[file_path]
        with open(full_path, "a", encoding="utf-8") as f:
            f.write("\n" + sentinel + "\n")

    run_cmd(["git", "add"] + OVERLAY_FILES, cwd=destination)
    run_cmd(["git", "commit", "-m", "Add overlay sentinels"], cwd=destination)

    result = run_cmd(["git", "status", "--porcelain"], cwd=destination, check=False)
    if result.stdout.strip():
        print("BOOTSTRAP_V2_COPIER_CLI_CONTRACT=FAIL")
        print("FIRST_FAILURE=GENERATED_PROJECT_GIT_NOT_CLEAN")
        print("DETAIL=overlay modification left uncommitted changes")
        print(f"COPIER_VERSION={TARGET_COPIER_VERSION}")
        sys.exit(1)

    sha_map = {}
    for file_path in OVERLAY_FILES:
        full_path = destination / file_path
        sha_map[file_path] = get_file_sha256(full_path)

    return sha_map


def update_template_core(template_repo: Path) -> None:
    jinja_file = template_repo / "template" / "AGENTS.md.jinja"
    if not jinja_file.exists():
        print("BOOTSTRAP_V2_COPIER_CLI_CONTRACT=FAIL")
        print("FIRST_FAILURE=TEMPLATE_CORE_UPDATE_MISSING")
        print("DETAIL=template/AGENTS.md.jinja not found")
        print(f"COPIER_VERSION={TARGET_COPIER_VERSION}")
        sys.exit(1)

    with open(jinja_file, "a", encoding="utf-8") as f:
        f.write("\n" + TEMPLATE_CORE_SENTINEL + "\n")

    runtime_profile_file = (
        template_repo
        / "template"
        / "agents"
        / "project"
        / "{% if has_runtime_visual %}runtime-visual{% endif %}"
        / "{% if has_runtime_visual %}PROFILE.md{% endif %}.jinja"
    )
    if not runtime_profile_file.exists():
        print("BOOTSTRAP_V2_COPIER_CLI_CONTRACT=FAIL")
        print("FIRST_FAILURE=RUNTIME_VISUAL_PROFILE_TEMPLATE_UPDATE_MISSING")
        print("DETAIL=runtime visual profile template source not found")
        print(f"COPIER_VERSION={TARGET_COPIER_VERSION}")
        sys.exit(1)

    with open(runtime_profile_file, "a", encoding="utf-8") as f:
        f.write("\n" + RUNTIME_VISUAL_PROFILE_TEMPLATE_SENTINEL + "\n")

    run_cmd(["git", "add", "template/AGENTS.md.jinja"], cwd=template_repo)
    run_cmd(
        ["git", "add", "template/agents/project/{% if has_runtime_visual %}runtime-visual{% endif %}/{% if has_runtime_visual %}PROFILE.md{% endif %}.jinja"],
        cwd=template_repo,
    )
    run_cmd(["git", "commit", "-m", "Add template core and runtime profile sentinels"], cwd=template_repo)
    run_cmd(["git", "tag", "v0.0.2"], cwd=template_repo)


def run_copier_update(destination: Path, template_src: Path) -> None:
    cmd = [*COPIER_COMMAND, "update", "--defaults", "--vcs-ref", "v0.0.2", "--conflict", "inline", "."]

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=destination)
    if result.returncode != 0:
        print("BOOTSTRAP_V2_COPIER_CLI_CONTRACT=FAIL")
        print("FIRST_FAILURE=COPIER_UPDATE_FAILED")
        print(f"DETAIL=copier update failed with exit code {result.returncode}")
        print(f"COPIER_VERSION={TARGET_COPIER_VERSION}")
        if result.stderr:
            print(f"STDERR: {result.stderr}", file=sys.stderr)
        sys.exit(1)


def validate_overlay_preserved(destination: Path, original_shas: dict[str, str]) -> None:
    for file_path in OVERLAY_FILES:
        current_sha = get_file_sha256(destination / file_path)
        if current_sha != original_shas[file_path]:
            if file_path == RUNTIME_VISUAL_PROFILE_PATH:
                print("BOOTSTRAP_V2_COPIER_CLI_CONTRACT=FAIL")
                print("FIRST_FAILURE=RUNTIME_VISUAL_PROFILE_UPDATE_CHANGED")
                print(f"DETAIL={file_path} changed during update")
                print(f"COPIER_VERSION={TARGET_COPIER_VERSION}")
                sys.exit(1)
            else:
                print("BOOTSTRAP_V2_COPIER_CLI_CONTRACT=FAIL")
                print("FIRST_FAILURE=PROJECT_OVERLAY_CHANGED")
                print(f"DETAIL={file_path} changed during update")
                print(f"COPIER_VERSION={TARGET_COPIER_VERSION}")
                sys.exit(1)

        sentinel = OVERLAY_SENTINELS[file_path]
        content = (destination / file_path).read_text(encoding="utf-8")
        if sentinel not in content:
            if file_path == RUNTIME_VISUAL_PROFILE_PATH:
                print("BOOTSTRAP_V2_COPIER_CLI_CONTRACT=FAIL")
                print("FIRST_FAILURE=RUNTIME_VISUAL_PROFILE_PROJECT_SENTINEL_MISSING")
                print(f"DETAIL={file_path} sentinel missing after update")
                print(f"COPIER_VERSION={TARGET_COPIER_VERSION}")
                sys.exit(1)
            else:
                print("BOOTSTRAP_V2_COPIER_CLI_CONTRACT=FAIL")
                print("FIRST_FAILURE=PROJECT_OVERLAY_CHANGED")
                print(f"DETAIL={file_path} sentinel missing after update")
                print(f"COPIER_VERSION={TARGET_COPIER_VERSION}")
                sys.exit(1)

    runtime_profile_content = (destination / RUNTIME_VISUAL_PROFILE_PATH).read_text(encoding="utf-8")
    if RUNTIME_VISUAL_PROFILE_TEMPLATE_SENTINEL in runtime_profile_content:
        print("BOOTSTRAP_V2_COPIER_CLI_CONTRACT=FAIL")
        print("FIRST_FAILURE=RUNTIME_VISUAL_PROFILE_TEMPLATE_SENTINEL_APPLIED")
        print(f"DETAIL={RUNTIME_VISUAL_PROFILE_PATH} should not contain template update sentinel")
        print(f"COPIER_VERSION={TARGET_COPIER_VERSION}")
        sys.exit(1)

    result = run_cmd(["find", ".", "-name", "*.rej"], cwd=destination, check=False)
    rej_files = [f for f in result.stdout.strip().split("\n") if f]
    if rej_files:
        print("BOOTSTRAP_V2_COPIER_CLI_CONTRACT=FAIL")
        print("FIRST_FAILURE=UPDATE_CONFLICT_FOUND")
        print(f"DETAIL=found .rej files: {rej_files}")
        print(f"COPIER_VERSION={TARGET_COPIER_VERSION}")
        sys.exit(1)

    result = run_cmd(["grep", "-r", "<<<<<<<", ".", "--include=*.md"], cwd=destination, check=False)
    if result.stdout.strip():
        print("BOOTSTRAP_V2_COPIER_CLI_CONTRACT=FAIL")
        print("FIRST_FAILURE=UPDATE_CONFLICT_FOUND")
        print("DETAIL=conflict markers found in generated files")
        print(f"COPIER_VERSION={TARGET_COPIER_VERSION}")
        sys.exit(1)


def validate_template_core_applied(destination: Path) -> None:
    agents_md = destination / "AGENTS.md"
    if not agents_md.exists():
        print("BOOTSTRAP_V2_COPIER_CLI_CONTRACT=FAIL")
        print("FIRST_FAILURE=TEMPLATE_CORE_UPDATE_MISSING")
        print("DETAIL=AGENTS.md not found after update")
        print(f"COPIER_VERSION={TARGET_COPIER_VERSION}")
        sys.exit(1)

    content = agents_md.read_text(encoding="utf-8")
    if TEMPLATE_CORE_SENTINEL not in content:
        print("BOOTSTRAP_V2_COPIER_CLI_CONTRACT=FAIL")
        print("FIRST_FAILURE=TEMPLATE_CORE_UPDATE_MISSING")
        print("DETAIL=template core sentinel not found in AGENTS.md")
        print(f"COPIER_VERSION={TARGET_COPIER_VERSION}")
        sys.exit(1)

    answers_file = destination / ".copier-answers.yml"
    with open(answers_file) as f:
        answers = yaml.safe_load(f)

    if answers.get("_commit") != "v0.0.2":
        print("BOOTSTRAP_V2_COPIER_CLI_CONTRACT=FAIL")
        print("FIRST_FAILURE=TEMPLATE_CORE_UPDATE_MISSING")
        print(f"DETAIL=_commit not updated to v0.0.2, got {answers.get('_commit')}")
        print(f"COPIER_VERSION={TARGET_COPIER_VERSION}")
        sys.exit(1)

    validate_yaml_files(destination)
    check_unresolved_markers(destination)


def find_forbidden_command_keys(
    value: object,
    *,
    path: tuple[str, ...] = (),
) -> list[tuple[str, ...]]:
    """Recursively scan harness for executable command keys."""
    found: list[tuple[str, ...]] = []
    command_keys = {"commands", "lint", "typecheck", "targeted_test", "release_check"}

    if isinstance(value, dict):
        for key, val in value.items():
            current_path = path + (key,)
            if key in command_keys:
                found.append(current_path)
            found.extend(find_forbidden_command_keys(val, path=current_path))
    elif isinstance(value, list):
        for idx, item in enumerate(value):
            current_path = path + (f"[{idx}]",)
            found.extend(find_forbidden_command_keys(item, path=current_path))

    return found


def evaluate_project_command_ssot_contract(
    *,
    harness: object,
    profile_content: str,
    agents_content: str,
    profile: dict[str, Any],
) -> list[str]:
    """Pure evaluator for project command SSOT contract.

    Returns empty list for PASS, or list of failure codes for FAIL.
    """
    failures: list[str] = []

    harness_dict = harness if isinstance(harness, dict) else {}

    forbidden_paths = find_forbidden_command_keys(harness_dict)
    if forbidden_paths:
        failures.append(COMMAND_SSOT_HARNESS_COMMAND_AUTHORITY_PRESENT)

    project_section = harness_dict.get("project", {})
    if "package_tool" not in project_section:
        failures.append(COMMAND_SSOT_HARNESS_PACKAGE_TOOL_METADATA_MISSING)
    elif project_section["package_tool"] != profile.get("package_tool"):
        failures.append(COMMAND_SSOT_HARNESS_PACKAGE_TOOL_METADATA_MISMATCH)

    exact_ssot_decl_1 = "이 section 이 프로젝트 실행 command 의 유일한 SSOT 다."
    exact_ssot_decl_2 = ".agent-harness.yml 은 실행 command authority 가 아니다."
    if exact_ssot_decl_1 not in profile_content or exact_ssot_decl_2 not in profile_content:
        failures.append(COMMAND_SSOT_PROJECT_PROFILE_COMMAND_SSOT_DECLARATION_MISSING)

    expected_rows = {
        "lint": f"- Lint: `{profile.get('lint_command') or 'NOT_CONFIGURED'}`",
        "typecheck": f"- Typecheck: `{profile.get('typecheck_command') or 'NOT_CONFIGURED'}`",
        "targeted_test": f"- Targeted test: `{profile.get('targeted_test_command') or 'NOT_CONFIGURED'}`",
        "release_check": f"- Release check: `{profile.get('release_check_command') or 'NOT_CONFIGURED'}`",
    }

    missing_rows: list[str] = []
    for key, row in expected_rows.items():
        if row not in profile_content:
            missing_rows.append(key)
    if missing_rows:
        failures.append(COMMAND_SSOT_PROJECT_PROFILE_COMMAND_MISSING)

    exact_agents_line = "프로젝트 실행 명령은 `agents/project/PROFILE.md` 에서 확인한다."
    if exact_agents_line not in agents_content:
        failures.append(COMMAND_SSOT_AGENTS_PROJECT_PROFILE_COMMAND_AUTHORITY_MISSING)

    for line in agents_content.splitlines():
        has_harness = ".agent-harness.yml" in line
        has_profile = "agents/project/PROFILE.md" in line
        has_command = "명령" in line or "command" in line
        if has_harness and has_profile and has_command:
            failures.append(COMMAND_SSOT_AGENTS_DUPLICATE_COMMAND_AUTHORITY_PRESENT)
            break

    return failures


def extract_markdown_section(
    content: str,
    *,
    heading: str,
    next_heading: str,
) -> str:
    """Extract content between two markdown headings."""
    lines = content.splitlines()
    in_section = False
    section_lines: list[str] = []

    for line in lines:
        if line.startswith(f"### {heading}"):
            in_section = True
            continue
        if in_section and line.startswith("### "):
            break
        if in_section:
            section_lines.append(line)

    return "\n".join(section_lines)


def evaluate_runtime_visual_profile_ownership_ssot_contract(
    *,
    skip_if_exists: object,
    architecture_content: str,
    runtime_profile_content: str,
) -> list[str]:
    """Pure evaluator for runtime visual profile ownership SSOT contract.

    Returns empty list for PASS, or list of failure codes for FAIL.
    """
    failures: list[str] = []

    if not isinstance(skip_if_exists, list):
        failures.append(RUNTIME_VISUAL_PROFILE_SKIP_IF_EXISTS_INVALID)
        return failures

    skip_count = skip_if_exists.count(RUNTIME_VISUAL_PROFILE_PATH)
    if skip_count == 0:
        failures.append(RUNTIME_VISUAL_PROFILE_SKIP_IF_EXISTS_MISSING)
    elif skip_count > 1:
        failures.append(RUNTIME_VISUAL_PROFILE_SKIP_IF_EXISTS_DUPLICATE)

    core_section = extract_markdown_section(
        architecture_content,
        heading="Template-managed core",
        next_heading="Project-owned overlay",
    )
    overlay_section = extract_markdown_section(
        architecture_content,
        heading="Project-owned overlay",
        next_heading="Core 승격 기준",
    )

    if RUNTIME_VISUAL_PROFILE_PATH in core_section:
        failures.append(RUNTIME_VISUAL_PROFILE_ARCHITECTURE_MISCLASSIFIED)

    overlay_lines = {
        line.rstrip()
        for line in overlay_section.splitlines()
    }

    if RUNTIME_VISUAL_PROFILE_ARCHITECTURE_BULLET not in overlay_lines:
        failures.append(RUNTIME_VISUAL_PROFILE_ARCHITECTURE_OWNERSHIP_MISSING)

    exact_decl_1 = "이 파일은 **project-owned overlay**다."
    exact_decl_2 = "초기 생성 후 프로젝트가 직접 관리하며 Copier update 가 기존 내용을 덮어쓰지 않는다."
    if exact_decl_1 not in runtime_profile_content or exact_decl_2 not in runtime_profile_content:
        failures.append(RUNTIME_VISUAL_PROFILE_OWNERSHIP_DECLARATION_MISSING)

    return failures


def validate_runtime_visual_profile_ownership_ssot_validator_gate_contract() -> None:
    """Validate the runtime visual profile ownership SSOT validator gate contract."""

    test_cases: list[tuple[str, dict, list[str]]] = []

    valid_skip_list = [
        "agents/project/PROFILE.md",
        "agents/project/runtime-visual/PROFILE.md",
        "docs/product/ACTIVE_SCOPE.md",
    ]
    valid_architecture = (
        "### Template-managed core\n"
        "\n"
        "Some content\n"
        "\n"
        "### Project-owned overlay\n"
        "\n"
        "- `agents/project/PROFILE.md`\n"
        "- `agents/project/runtime-visual/PROFILE.md` — `has_runtime_visual=true` 프로젝트\n"
        "- `docs/product/ACTIVE_SCOPE.md`\n"
        "\n"
        "### Core 승격 기준\n"
    )
    valid_runtime_profile = (
        "이 파일은 **project-owned overlay**다.\n"
        "초기 생성 후 프로젝트가 직접 관리하며 Copier update 가 기존 내용을 덮어쓰지 않는다.\n"
    )
    test_cases.append((
        "valid_case",
        {
            "skip_if_exists": valid_skip_list,
            "architecture_content": valid_architecture,
            "runtime_profile_content": valid_runtime_profile,
        },
        [],
    ))

    skip_missing = [
        "agents/project/PROFILE.md",
        "docs/product/ACTIVE_SCOPE.md",
    ]
    test_cases.append((
        "skip_path_missing",
        {
            "skip_if_exists": skip_missing,
            "architecture_content": valid_architecture,
            "runtime_profile_content": valid_runtime_profile,
        },
        [RUNTIME_VISUAL_PROFILE_SKIP_IF_EXISTS_MISSING],
    ))

    skip_duplicate = [
        "agents/project/PROFILE.md",
        "agents/project/runtime-visual/PROFILE.md",
        "agents/project/runtime-visual/PROFILE.md",
        "docs/product/ACTIVE_SCOPE.md",
    ]
    test_cases.append((
        "skip_path_duplicate",
        {
            "skip_if_exists": skip_duplicate,
            "architecture_content": valid_architecture,
            "runtime_profile_content": valid_runtime_profile,
        },
        [RUNTIME_VISUAL_PROFILE_SKIP_IF_EXISTS_DUPLICATE],
    ))

    arch_missing_bullet = (
        "### Template-managed core\n"
        "\n"
        "Some content\n"
        "\n"
        "### Project-owned overlay\n"
        "\n"
        "- `agents/project/PROFILE.md`\n"
        "- `docs/product/ACTIVE_SCOPE.md`\n"
        "\n"
        "### Core 승격 기준\n"
    )
    test_cases.append((
        "architecture_ownership_missing",
        {
            "skip_if_exists": valid_skip_list,
            "architecture_content": arch_missing_bullet,
            "runtime_profile_content": valid_runtime_profile,
        },
        [RUNTIME_VISUAL_PROFILE_ARCHITECTURE_OWNERSHIP_MISSING],
    ))

    arch_misclassified = (
        "### Template-managed core\n"
        "\n"
        "- `agents/project/runtime-visual/PROFILE.md`\n"
        "\n"
        "### Project-owned overlay\n"
        "\n"
        "- `agents/project/PROFILE.md`\n"
        "- `agents/project/runtime-visual/PROFILE.md` — `has_runtime_visual=true` 프로젝트\n"
        "\n"
        "### Core 승격 기준\n"
    )
    test_cases.append((
        "architecture_misclassified",
        {
            "skip_if_exists": valid_skip_list,
            "architecture_content": arch_misclassified,
            "runtime_profile_content": valid_runtime_profile,
        },
        [RUNTIME_VISUAL_PROFILE_ARCHITECTURE_MISCLASSIFIED],
    ))

    weak_declaration = (
        "프로젝트 고유 파일이다.\n"
    )
    test_cases.append((
        "declaration_missing",
        {
            "skip_if_exists": valid_skip_list,
            "architecture_content": valid_architecture,
            "runtime_profile_content": weak_declaration,
        },
        [RUNTIME_VISUAL_PROFILE_OWNERSHIP_DECLARATION_MISSING],
    ))

    architecture_prose_reference_only = (
        "### Template-managed core\n"
        "\n"
        "Some content\n"
        "\n"
        "### Project-owned overlay\n"
        "\n"
        "이 section では agents/project/runtime-visual/PROFILE.md 를 설명한다.\n"
        "\n"
        "### Core 승격 기준\n"
    )
    test_cases.append((
        "architecture_prose_reference_only",
        {
            "skip_if_exists": valid_skip_list,
            "architecture_content": architecture_prose_reference_only,
            "runtime_profile_content": valid_runtime_profile,
        },
        [RUNTIME_VISUAL_PROFILE_ARCHITECTURE_OWNERSHIP_MISSING],
    ))

    all_passed = True
    for case_name, inputs, expected_failures in test_cases:
        result = evaluate_runtime_visual_profile_ownership_ssot_contract(**inputs)
        if set(result) != set(expected_failures):
            print(f"VALIDATOR_GATE_CASE_FAIL: {case_name}")
            print(f"EXPECTED={expected_failures}")
            print(f"ACTUAL={result}")
            all_passed = False

    if all_passed:
        print("RUNTIME_VISUAL_PROFILE_OWNERSHIP_SSOT_VALIDATOR_GATE_CONTRACT=PASS")
        print("RUNTIME_VISUAL_PROFILE_ARCHITECTURE_BULLET_GUARD_CONTRACT=PASS")
    else:
        sys.exit(1)


def validate_runtime_visual_profile_ownership_ssot(destination: Path) -> None:
    """Production wrapper for runtime visual profile ownership SSOT validation."""

    copier_yml_path = Path("copier.yml")
    if not copier_yml_path.exists():
        print("BOOTSTRAP_V2_COPIER_CLI_CONTRACT=FAIL")
        print("FIRST_FAILURE=COPIER_YML_NOT_FOUND")
        print("DETAIL=copier.yml not found in workspace root")
        print(f"COPIER_VERSION={TARGET_COPIER_VERSION}")
        sys.exit(1)

    with open(copier_yml_path) as f:
        copier_config = yaml.safe_load(f)

    skip_if_exists = copier_config.get("_skip_if_exists", [])
    architecture_path = Path("docs/ARCHITECTURE.md")
    if not architecture_path.exists():
        print("BOOTSTRAP_V2_COPIER_CLI_CONTRACT=FAIL")
        print("FIRST_FAILURE=ARCHITECTURE_NOT_FOUND")
        print("DETAIL=docs/ARCHITECTURE.md not found")
        print(f"COPIER_VERSION={TARGET_COPIER_VERSION}")
        sys.exit(1)

    architecture_content = architecture_path.read_text(encoding="utf-8")

    runtime_profile_path = destination / RUNTIME_VISUAL_PROFILE_PATH
    if not runtime_profile_path.exists():
        print("BOOTSTRAP_V2_COPIER_CLI_CONTRACT=FAIL")
        print("FIRST_FAILURE=RUNTIME_VISUAL_PROFILE_NOT_FOUND")
        print(f"DETAIL={RUNTIME_VISUAL_PROFILE_PATH} not found in destination")
        print(f"COPIER_VERSION={TARGET_COPIER_VERSION}")
        sys.exit(1)

    runtime_profile_content = runtime_profile_path.read_text(encoding="utf-8")

    failures = evaluate_runtime_visual_profile_ownership_ssot_contract(
        skip_if_exists=skip_if_exists,
        architecture_content=architecture_content,
        runtime_profile_content=runtime_profile_content,
    )

    if failures:
        failure_code = failures[0]
        print("BOOTSTRAP_V2_COPIER_CLI_CONTRACT=FAIL")
        print(f"FIRST_FAILURE={failure_code}")
        if failure_code == RUNTIME_VISUAL_PROFILE_SKIP_IF_EXISTS_INVALID:
            print("DETAIL=_skip_if_exists is not a list")
        elif failure_code == RUNTIME_VISUAL_PROFILE_SKIP_IF_EXISTS_MISSING:
            print("DETAIL=runtime visual profile path missing from _skip_if_exists")
        elif failure_code == RUNTIME_VISUAL_PROFILE_SKIP_IF_EXISTS_DUPLICATE:
            print("DETAIL=runtime visual profile path duplicated in _skip_if_exists")
        elif failure_code == RUNTIME_VISUAL_PROFILE_ARCHITECTURE_OWNERSHIP_MISSING:
            print("DETAIL=runtime visual profile path missing from Project-owned overlay section")
        elif failure_code == RUNTIME_VISUAL_PROFILE_ARCHITECTURE_MISCLASSIFIED:
            print("DETAIL=runtime visual profile path incorrectly listed under Template-managed core")
        elif failure_code == RUNTIME_VISUAL_PROFILE_OWNERSHIP_DECLARATION_MISSING:
            print("DETAIL=runtime visual profile missing exact ownership declaration")
        print(f"COPIER_VERSION={TARGET_COPIER_VERSION}")
        sys.exit(1)


def validate_project_command_ssot_validator_gate_contract() -> None:
    """Validate the project command SSOT validator gate contract."""

    test_cases: list[tuple[str, dict, list[str]]] = []

    valid_simple_harness = {
        "project": {"package_tool": "other"},
    }
    valid_simple_profile = (
        "이 section 이 프로젝트 실행 command 의 유일한 SSOT 다.\n"
        ".agent-harness.yml 은 실행 command authority 가 아니다.\n"
        "- Lint: `NOT_CONFIGURED`\n"
        "- Typecheck: `NOT_CONFIGURED`\n"
        "- Targeted test: `NOT_CONFIGURED`\n"
        "- Release check: `NOT_CONFIGURED`\n"
    )
    valid_simple_agents = (
        "프로젝트 실행 명령은 `agents/project/PROFILE.md` 에서 확인한다.\n"
    )
    test_cases.append((
        "valid_simple",
        {
            "harness": valid_simple_harness,
            "profile_content": valid_simple_profile,
            "agents_content": valid_simple_agents,
            "profile": SIMPLE_PROFILE,
        },
        [],
    ))

    valid_full_harness = {
        "project": {"package_tool": "uv"},
    }
    valid_full_profile = (
        "이 section 이 프로젝트 실행 command 의 유일한 SSOT 다.\n"
        ".agent-harness.yml 은 실행 command authority 가 아니다.\n"
        "- Lint: `uv run ruff check .`\n"
        "- Typecheck: `uv run mypy .`\n"
        "- Targeted test: `uv run pytest tests/unit/test_target.py`\n"
        "- Release check: `uv run pytest`\n"
    )
    valid_full_agents = (
        "프로젝트 실행 명령은 `agents/project/PROFILE.md` 에서 확인한다.\n"
    )
    test_cases.append((
        "valid_full",
        {
            "harness": valid_full_harness,
            "profile_content": valid_full_profile,
            "agents_content": valid_full_agents,
            "profile": FULL_PROFILE,
        },
        [],
    ))

    nested_harness = {
        "project": {"package_tool": "other"},
        "metadata": {
            "commands": {
                "lint": "forbidden",
            },
        },
    }
    test_cases.append((
        "nested_harness_commands",
        {
            "harness": nested_harness,
            "profile_content": valid_simple_profile,
            "agents_content": valid_simple_agents,
            "profile": SIMPLE_PROFILE,
        },
        [COMMAND_SSOT_HARNESS_COMMAND_AUTHORITY_PRESENT],
    ))

    simple_missing_typecheck = (
        "이 section 이 프로젝트 실행 command 의 유일한 SSOT 다.\n"
        ".agent-harness.yml 은 실행 command authority 가 아니다.\n"
        "- Lint: `NOT_CONFIGURED`\n"
        "- Targeted test: `NOT_CONFIGURED`\n"
        "- Release check: `NOT_CONFIGURED`\n"
    )
    test_cases.append((
        "simple_missing_typecheck_row",
        {
            "harness": valid_simple_harness,
            "profile_content": simple_missing_typecheck,
            "agents_content": valid_simple_agents,
            "profile": SIMPLE_PROFILE,
        },
        [COMMAND_SSOT_PROJECT_PROFILE_COMMAND_MISSING],
    ))

    full_missing_release = (
        "이 section 이 프로젝트 실행 command 의 유일한 SSOT 다.\n"
        ".agent-harness.yml 은 실행 command authority 가 아니다.\n"
        "- Lint: `uv run ruff check .`\n"
        "- Typecheck: `uv run mypy .`\n"
        "- Targeted test: `uv run pytest tests/unit/test_target.py`\n"
    )
    test_cases.append((
        "full_missing_release_row",
        {
            "harness": valid_full_harness,
            "profile_content": full_missing_release,
            "agents_content": valid_full_agents,
            "profile": FULL_PROFILE,
        },
        [COMMAND_SSOT_PROJECT_PROFILE_COMMAND_MISSING],
    ))

    weak_declaration_profile = (
        "실행 command 를 확인한다.\n"
        "- Lint: `NOT_CONFIGURED`\n"
        "- Typecheck: `NOT_CONFIGURED`\n"
        "- Targeted test: `NOT_CONFIGURED`\n"
        "- Release check: `NOT_CONFIGURED`\n"
    )
    test_cases.append((
        "weak_generic_profile_declaration",
        {
            "harness": valid_simple_harness,
            "profile_content": weak_declaration_profile,
            "agents_content": valid_simple_agents,
            "profile": SIMPLE_PROFILE,
        },
        [COMMAND_SSOT_PROJECT_PROFILE_COMMAND_SSOT_DECLARATION_MISSING],
    ))

    generic_agents_ref = (
        "프로젝트 고유 정보는 agents/project/PROFILE.md 가 소유한다.\n"
    )
    test_cases.append((
        "generic_profile_reference_only",
        {
            "harness": valid_simple_harness,
            "profile_content": valid_simple_profile,
            "agents_content": generic_agents_ref,
            "profile": SIMPLE_PROFILE,
        },
        [COMMAND_SSOT_AGENTS_PROJECT_PROFILE_COMMAND_AUTHORITY_MISSING],
    ))

    stale_dual_source = (
        "프로젝트 실행 명령은 `agents/project/PROFILE.md` 에서 확인한다.\n"
        "프로젝트 명령은 `.agent-harness.yml`과 `agents/project/PROFILE.md`에서 확인한다.\n"
    )
    test_cases.append((
        "actual_stale_dual_source",
        {
            "harness": valid_simple_harness,
            "profile_content": valid_simple_profile,
            "agents_content": stale_dual_source,
            "profile": SIMPLE_PROFILE,
        },
        [COMMAND_SSOT_AGENTS_DUPLICATE_COMMAND_AUTHORITY_PRESENT],
    ))

    all_passed = True
    for case_name, inputs, expected_failures in test_cases:
        result = evaluate_project_command_ssot_contract(**inputs)
        if set(result) != set(expected_failures):
            print(f"VALIDATOR_GATE_CASE_FAIL: {case_name}")
            print(f"EXPECTED={expected_failures}")
            print(f"ACTUAL={result}")
            all_passed = False

    if all_passed:
        print("PROJECT_COMMAND_SSOT_VALIDATOR_GATE_CONTRACT=PASS")
    else:
        sys.exit(1)


def validate_project_command_ssot(destination: Path, profile: dict[str, Any]) -> None:
    harness_path = destination / ".agent-harness.yml"
    if not harness_path.exists():
        print("BOOTSTRAP_V2_COPIER_CLI_CONTRACT=FAIL")
        print("FIRST_FAILURE=COMMAND_SSOT_HARNESS_MISSING")
        print("DETAIL=.agent-harness.yml not found")
        print(f"COPIER_VERSION={TARGET_COPIER_VERSION}")
        sys.exit(1)

    with open(harness_path) as f:
        harness = yaml.safe_load(f)

    profile_path = destination / "agents/project/PROFILE.md"
    if not profile_path.exists():
        print("BOOTSTRAP_V2_COPIER_CLI_CONTRACT=FAIL")
        print("FIRST_FAILURE=COMMAND_SSOT_PROJECT_PROFILE_MISSING")
        print("DETAIL=agents/project/PROFILE.md not found")
        print(f"COPIER_VERSION={TARGET_COPIER_VERSION}")
        sys.exit(1)

    profile_content = profile_path.read_text(encoding="utf-8")

    agents_path = destination / "AGENTS.md"
    if not agents_path.exists():
        print("BOOTSTRAP_V2_COPIER_CLI_CONTRACT=FAIL")
        print("FIRST_FAILURE=COMMAND_SSOT_AGENTS_MISSING")
        print("DETAIL=AGENTS.md not found")
        print(f"COPIER_VERSION={TARGET_COPIER_VERSION}")
        sys.exit(1)

    agents_content = agents_path.read_text(encoding="utf-8")

    failures = evaluate_project_command_ssot_contract(
        harness=harness,
        profile_content=profile_content,
        agents_content=agents_content,
        profile=profile,
    )

    if failures:
        failure_code = failures[0]
        print("BOOTSTRAP_V2_COPIER_CLI_CONTRACT=FAIL")
        print(f"FIRST_FAILURE={failure_code}")
        if failure_code == COMMAND_SSOT_HARNESS_COMMAND_AUTHORITY_PRESENT:
            print("DETAIL=harness contains executable command keys at nested paths")
        elif failure_code == COMMAND_SSOT_HARNESS_PACKAGE_TOOL_METADATA_MISSING:
            print("DETAIL=harness project.package_tool missing")
        elif failure_code == COMMAND_SSOT_HARNESS_PACKAGE_TOOL_METADATA_MISMATCH:
            print(f"DETAIL=harness package_tool mismatch")
        elif failure_code == COMMAND_SSOT_PROJECT_PROFILE_COMMAND_SSOT_DECLARATION_MISSING:
            print("DETAIL=PROFILE.md missing exact SSOT declarations")
        elif failure_code == COMMAND_SSOT_PROJECT_PROFILE_COMMAND_MISSING:
            print("DETAIL=PROFILE.md missing expected command rows")
        elif failure_code == COMMAND_SSOT_AGENTS_PROJECT_PROFILE_COMMAND_AUTHORITY_MISSING:
            print("DETAIL=AGENTS.md missing exact command authority line")
        elif failure_code == COMMAND_SSOT_AGENTS_DUPLICATE_COMMAND_AUTHORITY_PRESENT:
            print("DETAIL=AGENTS.md has stale dual-source command authority")
        print(f"COPIER_VERSION={TARGET_COPIER_VERSION}")
        sys.exit(1)


def validate_temp_template_git_setup_fail_closed_contract() -> None:
    import io
    from contextlib import redirect_stderr, redirect_stdout

    def fail_gate(detail: str) -> None:
        print("BOOTSTRAP_V2_COPIER_CLI_CONTRACT=FAIL")
        print(f"DETAIL={detail}")
        sys.exit(1)

    test_cases = [
        (
            ["git", "init"],
            TEMP_TEMPLATE_GIT_INIT_FAILED,
            "temp template git init",
        ),
        (
            ["git", "config", "user.name", "Bootstrap Validator"],
            TEMP_TEMPLATE_GIT_CONFIG_NAME_FAILED,
            "temp template git user.name config",
        ),
        (
            [
                "git",
                "config",
                "user.email",
                "bootstrap-validator@example.invalid",
            ],
            TEMP_TEMPLATE_GIT_CONFIG_EMAIL_FAILED,
            "temp template git user.email config",
        ),
        (
            ["git", "add", "."],
            TEMP_TEMPLATE_GIT_ADD_FAILED,
            "temp template git add",
        ),
        (
            ["git", "commit", "-m", "Initial commit from working tree"],
            TEMP_TEMPLATE_GIT_COMMIT_FAILED,
            "temp template git commit",
        ),
        (
            ["git", "tag", "v0.0.1"],
            TEMP_TEMPLATE_GIT_TAG_FAILED,
            "temp template git tag",
        ),
    ]

    original_run_cmd = globals()["run_cmd"]

    for expected_cmd, expected_code, expected_label in test_cases:
        repo_dir = Path(tempfile.mkdtemp(prefix="bootstrap-v2-git-probe-"))
        calls: list[tuple[list[str], Path | None, bool]] = []

        def stub_run_cmd(
            cmd: list[str],
            cwd: Path | None = None,
            check: bool = True,
        ) -> subprocess.CompletedProcess:
            calls.append((list(cmd), cwd, check))
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=17,
                stdout="simulated stdout",
                stderr="simulated stderr",
            )

        globals()["run_cmd"] = stub_run_cmd

        try:
            stdout_buffer = io.StringIO()
            stderr_buffer = io.StringIO()

            with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
                run_temp_template_git_step(
                    cmd=expected_cmd,
                    repo_dir=repo_dir,
                    failure_code=expected_code,
                    label=expected_label,
                )

            fail_gate(f"gate did not exit on nonzero command: {expected_cmd}")

        except SystemExit as e:
            if e.code != 1:
                fail_gate(f"wrong exit code {e.code} for {expected_cmd}")

            if repo_dir.exists():
                fail_gate(f"repo_dir residue after failure: {expected_cmd}")

            stdout_text = stdout_buffer.getvalue()
            stderr_text = stderr_buffer.getvalue()

            if len(calls) != 1:
                fail_gate(f"expected 1 call, got {len(calls)} for {expected_cmd}")

            actual_cmd, actual_cwd, actual_check = calls[0]

            if actual_cmd != expected_cmd:
                fail_gate(f"cmd mismatch: expected {expected_cmd}, got {actual_cmd}")

            if actual_cwd != repo_dir:
                fail_gate(f"cwd mismatch: expected {repo_dir}, got {actual_cwd}")

            if actual_check is not False:
                fail_gate(f"check should be False, got {actual_check}")

            fail_marker_count = stdout_text.count("BOOTSTRAP_V2_COPIER_CLI_CONTRACT=FAIL")
            if fail_marker_count != 1:
                fail_gate(f"FAIL marker count {fail_marker_count} != 1 for {expected_cmd}")

            first_failure_count = stdout_text.count(f"FIRST_FAILURE={expected_code}")
            if first_failure_count != 1:
                fail_gate(f"FIRST_FAILURE count {first_failure_count} != 1 for {expected_cmd}")

            detail_expected = f"{expected_label} failed with exit code 17"
            if detail_expected not in stdout_text:
                fail_gate(f"DETAIL missing '{detail_expected}' for {expected_cmd}")

            version_count = stdout_text.count(f"COPIER_VERSION={TARGET_COPIER_VERSION}")
            if version_count != 1:
                fail_gate(f"COPIER_VERSION count {version_count} != 1 for {expected_cmd}")

            if f"STDOUT: simulated stdout" not in stderr_text:
                fail_gate(f"stderr missing stdout capture for {expected_cmd}")

            if f"STDERR: simulated stderr" not in stderr_text:
                fail_gate(f"stderr missing stderr capture for {expected_cmd}")

        finally:
            globals()["run_cmd"] = original_run_cmd
            shutil.rmtree(repo_dir, ignore_errors=True)

    test_invocation_repo = Path(tempfile.mkdtemp(prefix="bootstrap-v2-git-invocation-probe-"))
    calls: list[tuple[list[str], Path | None, bool]] = []

    def invocation_exception_stub(
        cmd: list[str],
        cwd: Path | None = None,
        check: bool = True,
    ) -> subprocess.CompletedProcess:
        calls.append((list(cmd), cwd, check))
        raise OSError("simulated git spawn failure")

    globals()["run_cmd"] = invocation_exception_stub

    try:
        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()

        with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
            run_temp_template_git_step(
                cmd=["git", "init"],
                repo_dir=test_invocation_repo,
                failure_code=TEMP_TEMPLATE_GIT_INIT_FAILED,
                label="temp template git init",
            )

        fail_gate("invocation exception case did not exit")

    except SystemExit as e:
        if e.code != 1:
            fail_gate(f"wrong exit code {e.code} for invocation exception")

        if test_invocation_repo.exists():
            fail_gate("repo_dir residue after invocation exception")

        stdout_text = stdout_buffer.getvalue()
        stderr_text = stderr_buffer.getvalue()

        if len(calls) != 1:
            fail_gate(f"expected 1 call, got {len(calls)} for invocation exception")

        actual_cmd, actual_cwd, actual_check = calls[0]

        if actual_cmd != ["git", "init"]:
            fail_gate(f"cmd mismatch for invocation exception: {actual_cmd}")

        if actual_cwd != test_invocation_repo:
            fail_gate(f"cwd mismatch for invocation exception: {actual_cwd}")

        if actual_check is not False:
            fail_gate(f"check should be False for invocation exception")

        fail_marker_count = stdout_text.count("BOOTSTRAP_V2_COPIER_CLI_CONTRACT=FAIL")
        if fail_marker_count != 1:
            fail_gate(f"FAIL marker count {fail_marker_count} != 1 for invocation exception")

        first_failure_count = stdout_text.count(f"FIRST_FAILURE={TEMP_TEMPLATE_GIT_INIT_FAILED}")
        if first_failure_count != 1:
            fail_gate(f"FIRST_FAILURE count {first_failure_count} != 1 for invocation exception")

        if "temp template git init invocation failed" not in stdout_text:
            fail_gate("DETAIL missing 'temp template git init invocation failed'")

        if "simulated git spawn failure" not in stdout_text:
            fail_gate("DETAIL missing 'simulated git spawn failure'")

    finally:
        globals()["run_cmd"] = original_run_cmd
        shutil.rmtree(test_invocation_repo, ignore_errors=True)

    test_success_repo = Path(tempfile.mkdtemp(prefix="bootstrap-v2-git-success-probe-"))
    calls = []

    def success_stub_run_cmd(
        cmd: list[str],
        cwd: Path | None = None,
        check: bool = True,
    ) -> subprocess.CompletedProcess:
        calls.append((list(cmd), cwd, check))
        return subprocess.CompletedProcess(
            args=cmd,
            returncode=0,
            stdout="",
            stderr="",
        )

    globals()["run_cmd"] = success_stub_run_cmd

    try:
        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()

        with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
            run_temp_template_git_step(
                cmd=["git", "init"],
                repo_dir=test_success_repo,
                failure_code=TEMP_TEMPLATE_GIT_INIT_FAILED,
                label="temp template git init",
            )

        stdout_text = stdout_buffer.getvalue()
        stderr_text = stderr_buffer.getvalue()

        if not test_success_repo.exists():
            fail_gate("success case repo_dir missing")

        if len(calls) != 1:
            fail_gate(f"expected 1 call, got {len(calls)} for success case")

        actual_cmd, actual_cwd, actual_check = calls[0]

        if actual_cmd != ["git", "init"]:
            fail_gate(f"cmd mismatch for success case: {actual_cmd}")

        if actual_cwd != test_success_repo:
            fail_gate(f"cwd mismatch for success case: {actual_cwd}")

        if actual_check is not False:
            fail_gate(f"check should be False for success case")

        if stdout_text:
            fail_gate(f"success case stdout should be empty, got: {stdout_text}")

        if stderr_text:
            fail_gate(f"success case stderr should be empty, got: {stderr_text}")

        fail_marker_count = stdout_text.count("BOOTSTRAP_V2_COPIER_CLI_CONTRACT=FAIL")
        if fail_marker_count != 0:
            fail_gate(f"FAIL marker count {fail_marker_count} != 0 for success case")

        first_failure_count = stdout_text.count("FIRST_FAILURE=")
        if first_failure_count != 0:
            fail_gate(f"FIRST_FAILURE count {first_failure_count} != 0 for success case")

    finally:
        globals()["run_cmd"] = original_run_cmd
        shutil.rmtree(test_success_repo, ignore_errors=True)


def validate_temp_template_source_isolation_contract() -> None:
    fixture_dir = Path(tempfile.mkdtemp(prefix="bootstrap-v2-isolation-fixture-"))
    temp_template = None
    try:
        copier_yml = fixture_dir / "copier.yml"
        shutil.copy2("copier.yml", copier_yml)

        template_dir = fixture_dir / "template"
        template_dir.mkdir()
        candidate_sentinel = template_dir / "CANDIDATE_WORKTREE_SENTINEL.txt"
        candidate_sentinel.write_text("CANDIDATE_SOURCE_TEST_CONTENT\n")

        unrelated_sentinel = fixture_dir / "UNRELATED_WORKTREE_SENTINEL.txt"
        unrelated_sentinel.write_text("UNRELATED_SOURCE_TEST_CONTENT\n")

        git_dir = fixture_dir / ".git"
        git_dir.mkdir()
        git_sentinel = git_dir / "SOURCE_GIT_METADATA_SENTINEL.txt"
        git_sentinel.write_text("SOURCE_GIT_METADATA_TEST_CONTENT\n")

        temp_template = setup_temp_template(fixture_dir)

        if not (temp_template / "copier.yml").exists():
            print("COPIER_TEMP_TEMPLATE_SOURCE_ISOLATION_CONTRACT=FAIL")
            print("FIRST_FAILURE=TEMP_TEMPLATE_COPIER_YML_MISSING")
            print("DETAIL=copier.yml not copied to temp template")
            sys.exit(1)

        if not (temp_template / "template" / "CANDIDATE_WORKTREE_SENTINEL.txt").exists():
            print("COPIER_TEMP_TEMPLATE_SOURCE_ISOLATION_CONTRACT=FAIL")
            print("FIRST_FAILURE=TEMP_TEMPLATE_CANDIDATE_SENTINEL_MISSING")
            print("DETAIL=candidate sentinel not copied to temp template")
            sys.exit(1)

        if (temp_template / "UNRELATED_WORKTREE_SENTINEL.txt").exists():
            print("COPIER_TEMP_TEMPLATE_SOURCE_ISOLATION_CONTRACT=FAIL")
            print("FIRST_FAILURE=TEMP_TEMPLATE_UNRELATED_SOURCE_COPIED")
            print("DETAIL=unrelated root content was copied to temp template")
            sys.exit(1)

        git_metadata_path = temp_template / ".git" / "SOURCE_GIT_METADATA_SENTINEL.txt"
        if git_metadata_path.exists():
            print("COPIER_TEMP_TEMPLATE_SOURCE_ISOLATION_CONTRACT=FAIL")
            print("FIRST_FAILURE=TEMP_TEMPLATE_SOURCE_GIT_METADATA_COPIED")
            print("DETAIL=source .git metadata was copied to temp template")
            sys.exit(1)

        if not (temp_template / ".git").exists():
            print("COPIER_TEMP_TEMPLATE_SOURCE_ISOLATION_CONTRACT=FAIL")
            print("FIRST_FAILURE=TEMP_TEMPLATE_GIT_MISSING")
            print("DETAIL=temp template .git directory not created")
            sys.exit(1)

        try:
            result = run_cmd(
                ["git", "status", "--porcelain"],
                cwd=temp_template,
                check=False,
            )
        except Exception as error:
            print("COPIER_TEMP_TEMPLATE_SOURCE_ISOLATION_CONTRACT=FAIL")
            print(f"FIRST_FAILURE={TEMP_TEMPLATE_STATUS_INSPECTION_FAILED}")
            print(
                "DETAIL="
                f"temp template git status invocation failed: {error}"
            )
            print(f"COPIER_VERSION={TARGET_COPIER_VERSION}")
            sys.exit(1)

        if result.returncode != 0:
            print("COPIER_TEMP_TEMPLATE_SOURCE_ISOLATION_CONTRACT=FAIL")
            print(f"FIRST_FAILURE={TEMP_TEMPLATE_STATUS_INSPECTION_FAILED}")
            print(
                "DETAIL="
                f"temp template git status failed with exit code "
                f"{result.returncode}"
            )
            print(f"COPIER_VERSION={TARGET_COPIER_VERSION}")

            if result.stdout:
                print(f"STDOUT: {result.stdout}", file=sys.stderr)
            if result.stderr:
                print(f"STDERR: {result.stderr}", file=sys.stderr)

            sys.exit(1)

        if result.stdout.strip():
            print("COPIER_TEMP_TEMPLATE_SOURCE_ISOLATION_CONTRACT=FAIL")
            print("FIRST_FAILURE=TEMP_TEMPLATE_REPOSITORY_NOT_CLEAN")
            print("DETAIL=temp template has uncommitted changes")
            sys.exit(1)

        result = run_cmd(["git", "tag", "-l"], cwd=temp_template, check=False)
        if "v0.0.1" not in result.stdout:
            print("COPIER_TEMP_TEMPLATE_SOURCE_ISOLATION_CONTRACT=FAIL")
            print("FIRST_FAILURE=TEMP_TEMPLATE_INITIAL_TAG_MISSING")
            print("DETAIL=v0.0.1 tag not found in temp template")
            sys.exit(1)

    finally:
        if temp_template:
            shutil.rmtree(temp_template, ignore_errors=True)
        shutil.rmtree(fixture_dir, ignore_errors=True)


def main() -> None:
    check_copier_version()

    validate_temp_template_git_setup_fail_closed_contract()
    print("TEMP_TEMPLATE_GIT_SETUP_FAIL_CLOSED_CONTRACT=PASS")

    validate_temp_template_source_isolation_contract()
    print("COPIER_TEMP_TEMPLATE_SOURCE_ISOLATION_CONTRACT=PASS")

    validate_project_command_ssot_validator_gate_contract()

    validate_runtime_visual_profile_ownership_ssot_validator_gate_contract()

    with tempfile.TemporaryDirectory(prefix="bootstrap-v2-dest-") as tmpdir:
        tmpdir = Path(tmpdir)
        simple_dest = tmpdir / "simple"
        full_dest = tmpdir / "full"

        template_repo = setup_temp_template(Path("."))

        try:
            run_copier_copy(template_repo, simple_dest, SIMPLE_PROFILE)
            validate_copier_answers(simple_dest, SIMPLE_PROFILE)
            validate_project_command_ssot(simple_dest, SIMPLE_PROFILE)
            print("SIMPLE_PROFILE_COPY=PASS")

            run_copier_copy(template_repo, full_dest, FULL_PROFILE)
            validate_copier_answers(full_dest, FULL_PROFILE)
            validate_project_command_ssot(full_dest, FULL_PROFILE)
            print("FULL_PROFILE_COPY=PASS")

            validate_yaml_files(simple_dest)
            validate_yaml_files(full_dest)
            print("GENERATED_YAML_PARSE=PASS")

            check_unresolved_markers(simple_dest)
            check_unresolved_markers(full_dest)
            print("UNRESOLVED_TEMPLATE_MARKERS=0")

            setup_full_destination_git(full_dest)
            original_shas = apply_overlay_sentinels(full_dest)

            update_template_core(template_repo)

            run_copier_update(full_dest, template_repo)

            validate_overlay_preserved(full_dest, original_shas)
            print("PROJECT_OVERLAY_UPDATE_PRESERVED=PASS")
            print("RUNTIME_VISUAL_PROFILE_UPDATE_PRESERVED=PASS")

            validate_template_core_applied(full_dest)
            print("TEMPLATE_CORE_UPDATE_APPLIED=PASS")

            print("PROJECT_COMMAND_SINGLE_SOURCE_OF_TRUTH_CONTRACT=PASS")

            validate_runtime_visual_profile_ownership_ssot(full_dest)
            print("RUNTIME_VISUAL_PROFILE_OWNERSHIP_SSOT_CONTRACT=PASS")

            print("BOOTSTRAP_V2_COPIER_CLI_CONTRACT=PASS")

        finally:
            shutil.rmtree(template_repo, ignore_errors=True)


if __name__ == "__main__":
    main()
