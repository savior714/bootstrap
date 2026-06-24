#!/usr/bin/env python3
"""Verify MSW demo coverage manifest against handler registry and BFF routes."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = Path(__file__).with_name("msw_demo_coverage_manifest.json")
HANDLERS_DIR = ROOT / "{{FRONTEND_APP_PATH}}/src/mocks/handlers"
BILLING_HANDLERS_DIR = ROOT / "{{FRONTEND_APP_PATH}}/src/features/billing/services/billingMockHandlers"


def load_handler_source() -> str:
    chunks: list[str] = []
    for base in (HANDLERS_DIR, BILLING_HANDLERS_DIR):
        if not base.exists():
            continue
        for path in sorted(base.rglob("*.ts")):
            chunks.append(path.read_text(encoding="utf-8"))
    chunks.append((ROOT / "{{FRONTEND_APP_PATH}}/src/mocks/handlers.ts").read_text(encoding="utf-8"))
    chunks.append(
        (ROOT / "{{FRONTEND_APP_PATH}}/src/features/billing/services/mockHandlers.ts").read_text(
            encoding="utf-8"
        )
    )
    return "\n".join(chunks)


def path_pattern_in_source(source: str, api_path: str) -> bool:
    # `/api/v1/billing/ai-insights` -> look for billing/ai-insights in template
    normalized = api_path.removeprefix("/api/v1/")
    escaped = re.escape(normalized).replace(re.escape(":accountId"), r"[^`\"]+")
    escaped = escaped.replace(re.escape(":patientId"), r"[^`\"]+")
    escaped = escaped.replace(re.escape(":encounterId"), r"[^`\"]+")
    pattern = re.compile(rf"`\$\{{API_PATH\}}/{escaped}`|`\$\{{API_PATH\}}/{normalized}`")
    if pattern.search(source):
        return True
    # fallback: plain string without API_PATH prefix
    return normalized in source


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    source = load_handler_source()
    failures: list[str] = []

    for entry in manifest.get("msw", []):
        method = entry["method"]
        path = entry["path"]
        if not path_pattern_in_source(source, path):
            failures.append(f"MSW missing: {method} {path}")

    for rel in manifest.get("bff_routes", []):
        if not (ROOT / rel).is_file():
            failures.append(f"BFF route missing: {rel}")

    if failures:
        print("[FAIL] MSW demo coverage gaps:")
        for line in failures:
            print(f"  - {line}")
        return 1

    print("[PASS] MSW demo coverage manifest satisfied")
    return 0


if __name__ == "__main__":
    sys.exit(main())
