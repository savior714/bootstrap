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

TEMP_TEMPLATE_SOURCE_ROOTS = (
    "copier.yml",
    "template",
)

TEMP_TEMPLATE_REQUIRED_SOURCE_MISSING = "TEMP_TEMPLATE_REQUIRED_SOURCE_MISSING"
TEMP_TEMPLATE_CANDIDATE_SOURCE_MISSING = "TEMP_TEMPLATE_CANDIDATE_SOURCE_MISSING"
TEMP_TEMPLATE_UNRELATED_SOURCE_COPIED = "TEMP_TEMPLATE_UNRELATED_SOURCE_COPIED"
TEMP_TEMPLATE_SOURCE_GIT_METADATA_COPIED = "TEMP_TEMPLATE_SOURCE_GIT_METADATA_COPIED"
TEMP_TEMPLATE_REPOSITORY_NOT_CLEAN = "TEMP_TEMPLATE_REPOSITORY_NOT_CLEAN"
TEMP_TEMPLATE_INITIAL_TAG_MISSING = "TEMP_TEMPLATE_INITIAL_TAG_MISSING"


def run_cmd(cmd: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)
    if check and result.returncode != 0:
        print(f"COMMAND_FAILED: {' '.join(cmd)}", file=sys.stderr)
        print(f"STDOUT: {result.stdout}", file=sys.stderr)
        print(f"STDERR: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    return result


def check_copier_version() -> None:
    result = run_cmd(["copier", "--version"], check=False)
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

    run_cmd(["git", "init"], cwd=repo_dir)
    run_cmd(["git", "config", "user.name", "Bootstrap Validator"], cwd=repo_dir)
    run_cmd(["git", "config", "user.email", "bootstrap-validator@example.invalid"], cwd=repo_dir)

    for relative_path in TEMP_TEMPLATE_SOURCE_ROOTS:
        source = template_dir / relative_path
        destination = repo_dir / relative_path
        if not source.exists():
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
        if source.is_dir():
            shutil.copytree(source, destination)
        else:
            shutil.copy2(source, destination)

    run_cmd(["git", "add", "."], cwd=repo_dir)
    run_cmd(["git", "commit", "-m", "Initial commit from working tree"], cwd=repo_dir)
    run_cmd(["git", "tag", "v0.0.1"], cwd=repo_dir)

    return repo_dir


def run_copier_copy(template_src: Path, destination: Path, profile: dict[str, Any]) -> None:
    import yaml as yml

    data_file = Path(tempfile.mktemp(suffix=".yml"))
    with open(data_file, "w") as f:
        yml.dump(profile, f)

    cmd = [
        "copier",
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
    cmd = ["copier", "update", "--defaults", "--vcs-ref", "v0.0.2", "--conflict", "inline", "."]

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

    if "commands" in harness:
        print("BOOTSTRAP_V2_COPIER_CLI_CONTRACT=FAIL")
        print("FIRST_FAILURE=COMMAND_SSOT_HARNESS_COMMAND_AUTHORITY_PRESENT")
        print("DETAIL=harness has top-level commands key")
        print(f"COPIER_VERSION={TARGET_COPIER_VERSION}")
        sys.exit(1)

    for cmd_key in ["lint", "typecheck", "targeted_test", "release_check"]:
        if cmd_key in harness:
            print("BOOTSTRAP_V2_COPIER_CLI_CONTRACT=FAIL")
            print("FIRST_FAILURE=COMMAND_SSOT_HARNESS_COMMAND_AUTHORITY_PRESENT")
            print(f"DETAIL=harness has executable command key: {cmd_key}")
            print(f"COPIER_VERSION={TARGET_COPIER_VERSION}")
            sys.exit(1)

    project_section = harness.get("project", {})
    if "package_tool" not in project_section:
        print("BOOTSTRAP_V2_COPIER_CLI_CONTRACT=FAIL")
        print("FIRST_FAILURE=COMMAND_SSOT_HARNESS_PACKAGE_TOOL_METADATA_MISSING")
        print("DETAIL=harness project.package_tool missing")
        print(f"COPIER_VERSION={TARGET_COPIER_VERSION}")
        sys.exit(1)

    if project_section["package_tool"] != profile["package_tool"]:
        print("BOOTSTRAP_V2_COPIER_CLI_CONTRACT=FAIL")
        print("FIRST_FAILURE=COMMAND_SSOT_HARNESS_PACKAGE_TOOL_METADATA_MISMATCH")
        print(f"DETAIL=harness package_tool mismatch: expected {profile['package_tool']}, got {project_section['package_tool']}")
        print(f"COPIER_VERSION={TARGET_COPIER_VERSION}")
        sys.exit(1)

    profile_path = destination / "agents/project/PROFILE.md"
    if not profile_path.exists():
        print("BOOTSTRAP_V2_COPIER_CLI_CONTRACT=FAIL")
        print("FIRST_FAILURE=COMMAND_SSOT_PROJECT_PROFILE_MISSING")
        print("DETAIL=agents/project/PROFILE.md not found")
        print(f"COPIER_VERSION={TARGET_COPIER_VERSION}")
        sys.exit(1)

    profile_content = profile_path.read_text(encoding="utf-8")

    if "유일한 SSOT" not in profile_content and "실행 command" not in profile_content:
        print("BOOTSTRAP_V2_COPIER_CLI_CONTRACT=FAIL")
        print("FIRST_FAILURE=COMMAND_SSOT_PROJECT_PROFILE_COMMAND_SSOT_DECLARATION_MISSING")
        print("DETAIL=PROFILE.md missing SSOT declaration")
        print(f"COPIER_VERSION={TARGET_COPIER_VERSION}")
        sys.exit(1)

    if profile == FULL_PROFILE:
        if "uv run ruff check ." not in profile_content:
            print("BOOTSTRAP_V2_COPIER_CLI_CONTRACT=FAIL")
            print("FIRST_FAILURE=COMMAND_SSOT_PROJECT_PROFILE_COMMAND_MISSING")
            print("DETAIL=full PROFILE missing lint command")
            print(f"COPIER_VERSION={TARGET_COPIER_VERSION}")
            sys.exit(1)
        if "uv run mypy ." not in profile_content:
            print("BOOTSTRAP_V2_COPIER_CLI_CONTRACT=FAIL")
            print("FIRST_FAILURE=COMMAND_SSOT_PROJECT_PROFILE_COMMAND_MISSING")
            print("DETAIL=full PROFILE missing typecheck command")
            print(f"COPIER_VERSION={TARGET_COPIER_VERSION}")
            sys.exit(1)
        if "uv run pytest tests/unit/test_target.py" not in profile_content:
            print("BOOTSTRAP_V2_COPIER_CLI_CONTRACT=FAIL")
            print("FIRST_FAILURE=COMMAND_SSOT_PROJECT_PROFILE_COMMAND_MISSING")
            print("DETAIL=full PROFILE missing targeted test command")
            print(f"COPIER_VERSION={TARGET_COPIER_VERSION}")
            sys.exit(1)
        if "uv run pytest" not in profile_content:
            print("BOOTSTRAP_V2_COPIER_CLI_CONTRACT=FAIL")
            print("FIRST_FAILURE=COMMAND_SSOT_PROJECT_PROFILE_COMMAND_MISSING")
            print("DETAIL=full PROFILE missing release check command")
            print(f"COPIER_VERSION={TARGET_COPIER_VERSION}")
            sys.exit(1)
    else:
        if "NOT_CONFIGURED" not in profile_content:
            print("BOOTSTRAP_V2_COPIER_CLI_CONTRACT=FAIL")
            print("FIRST_FAILURE=COMMAND_SSOT_PROJECT_PROFILE_COMMAND_MISSING")
            print("DETAIL=simple PROFILE missing NOT_CONFIGURED")
            print(f"COPIER_VERSION={TARGET_COPIER_VERSION}")
            sys.exit(1)

    agents_path = destination / "AGENTS.md"
    if not agents_path.exists():
        print("BOOTSTRAP_V2_COPIER_CLI_CONTRACT=FAIL")
        print("FIRST_FAILURE=COMMAND_SSOT_AGENTS_MISSING")
        print("DETAIL=AGENTS.md not found")
        print(f"COPIER_VERSION={TARGET_COPIER_VERSION}")
        sys.exit(1)

    agents_content = agents_path.read_text(encoding="utf-8")

    if "agents/project/PROFILE.md" not in agents_content:
        print("BOOTSTRAP_V2_COPIER_CLI_CONTRACT=FAIL")
        print("FIRST_FAILURE=COMMAND_SSOT_AGENTS_PROJECT_PROFILE_COMMAND_AUTHORITY_MISSING")
        print("DETAIL=AGENTS.md missing PROFILE.md command authority reference")
        print(f"COPIER_VERSION={TARGET_COPIER_VERSION}")
        sys.exit(1)

    if "프로젝트 명령은 `.agent-harness.yml` 과 `agents/project/PROFILE.md`" in agents_content:
        print("BOOTSTRAP_V2_COPIER_CLI_CONTRACT=FAIL")
        print("FIRST_FAILURE=COMMAND_SSOT_AGENTS_DUPLICATE_COMMAND_AUTHORITY_PRESENT")
        print("DETAIL=AGENTS.md has stale dual-source command authority instruction")
        print(f"COPIER_VERSION={TARGET_COPIER_VERSION}")
        sys.exit(1)


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

        result = run_cmd(["git", "status", "--porcelain"], cwd=temp_template, check=False)
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

    validate_temp_template_source_isolation_contract()
    print("COPIER_TEMP_TEMPLATE_SOURCE_ISOLATION_CONTRACT=PASS")

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

            print("BOOTSTRAP_V2_COPIER_CLI_CONTRACT=PASS")

        finally:
            shutil.rmtree(template_repo, ignore_errors=True)


if __name__ == "__main__":
    main()
