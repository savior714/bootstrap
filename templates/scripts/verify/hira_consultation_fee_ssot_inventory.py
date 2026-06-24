#!/usr/bin/env python3
"""HIRA consultation fee SSOT inventory — fails on legacy primary consultation codes."""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC_PATH = REPO_ROOT / "docs/specs/medical/SPEC_MED_hira_consultation_fee_master_ssot.md"
SEED_PATH = REPO_ROOT / "scripts/seed/seed_hira_fee_master.py"
ACCOUNTS_PATH = REPO_ROOT / "src/application/services/billing/billing_service_accounts.py"

PRIMARY_CODES = ("AA100", "AA102")
LEGACY_CODE_RE = re.compile(r"\bAA154\b|\bAA254\b")

# Directories scanned for legacy consultation codes (post-HFSS broad migration).
SCAN_DIRS: tuple[Path, ...] = (
    REPO_ROOT / "{{FRONTEND_APP_PATH}}/src/mocks",
    REPO_ROOT / "{{FRONTEND_APP_PATH}}/src/features/billing",
    REPO_ROOT / "{{FRONTEND_APP_PATH}}/src/app",
    REPO_ROOT / "tests/unit/application/services",
    REPO_ROOT / "tests/unit/domain/fhir",
    REPO_ROOT / "tests/services",
    REPO_ROOT / "tests/api",
    REPO_ROOT / "tests/e2e",
    REPO_ROOT / "tests/integration",
    REPO_ROOT / "scripts/seed",
)

# Paths allowed to reference AA154/AA254 (legacy row, API smoke, DUR drug codes, sync dedup).
ALLOWLIST_REL: frozenset[str] = frozenset(
    {
        "scripts/seed/seed_hira_fee_master.py",
        "src/application/services/billing/consultation_fee_sync.py",
        "tests/services/test_consultation_fee_sync.py",
        "scripts/verify/hira_consultation_fee_ssot_inventory.py",
        "tests/unit/infrastructure/external/test_hira_client_dur.py",
        "tests/unit/infrastructure/test_lst_mtls.py",
        "tests/integration/contracts/test_hira_schema.py",
        "tests/unit/infrastructure/external/test_hira_master.py",
        "src/infrastructure/external/hira_client.py",
        "scripts/manual/e2e/verify_hira_master_sync.py",
        "docs/specs/medical/SPEC_MED_hira_consultation_fee_master_ssot.md",
    }
)

SCAN_SUFFIXES = (".py", ".ts", ".tsx")


def _fail(messages: list[str]) -> int:
    for line in messages:
        print(f"[FAIL] {line}", file=sys.stderr)
    return 1


def _ok(message: str) -> None:
    print(f"[OK] {message}")


def check_spec_exists() -> list[str]:
    errors: list[str] = []
    if not SPEC_PATH.is_file():
        errors.append(f"Missing SPEC: {SPEC_PATH.relative_to(REPO_ROOT)}")
        return errors
    text = SPEC_PATH.read_text(encoding="utf-8")
    for code in PRIMARY_CODES:
        if code not in text:
            errors.append(f"SPEC must mention primary code {code}")
    return errors


def check_seed_rows() -> list[str]:
    errors: list[str] = []
    if not SEED_PATH.is_file():
        errors.append(f"Missing seed: {SEED_PATH.relative_to(REPO_ROOT)}")
        return errors
    text = SEED_PATH.read_text(encoding="utf-8")
    for code in PRIMARY_CODES:
        if f'("{code}"' not in text and f"('{code}'" not in text:
            errors.append(f"seed_hira_fee_master missing row for {code}")
    return errors


def check_accounts_no_auto_aa154() -> list[str]:
    errors: list[str] = []
    if not ACCOUNTS_PATH.is_file():
        errors.append(f"Missing accounts module: {ACCOUNTS_PATH.relative_to(REPO_ROOT)}")
        return errors
    text = ACCOUNTS_PATH.read_text(encoding="utf-8")
    if 'fee_code="AA154"' in text or "fee_code='AA154'" in text:
        errors.append("billing_service_accounts must not auto-add AA154 consultation fee")
    return errors


def check_legacy_primary_references() -> list[str]:
    errors: list[str] = []
    for root in SCAN_DIRS:
        if not root.is_dir():
            errors.append(f"Missing scan directory: {root.relative_to(REPO_ROOT)}")
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in SCAN_SUFFIXES:
                continue
            rel = path.relative_to(REPO_ROOT).as_posix()
            if rel in ALLOWLIST_REL:
                continue
            text = path.read_text(encoding="utf-8")
            if LEGACY_CODE_RE.search(text):
                errors.append(f"{rel} contains legacy consultation code AA154 or AA254")
    return errors


def main() -> int:
    errors: list[str] = []
    errors.extend(check_spec_exists())
    errors.extend(check_seed_rows())
    errors.extend(check_accounts_no_auto_aa154())
    errors.extend(check_legacy_primary_references())

    if errors:
        return _fail(errors)

    _ok("SPEC present with AA100/AA102")
    _ok("seed contains AA100 and AA102 rows")
    _ok("billing_service_accounts has no AA154 auto-charge")
    _ok("scan dirs free of AA154/AA254 (allowlist excluded)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
