#!/usr/bin/env python3
"""Simulate new-session context loading tiers and verify normative inline policy.

Models Cursor IDE injection (T0) + documented Phase 1–5 from LOAD_ORDER.md.
Does not call Cursor APIs — validates repo SSOT and route engine output.

Usage:
  uv run python scripts/agent/simulate_session_load.py
  uv run python scripts/agent/simulate_session_load.py --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.agent.context_t0_estimate import T0_FILES, estimate_t0  # noqa: E402
from scripts.agent.route_budget import estimate_must_read_tokens, estimate_tokens  # noqa: E402
from scripts.agent.route_bundle import get_route_bundle  # noqa: E402
from scripts.agent.route_parsing import get_always_load_rules  # noqa: E402

PHASE2_LAZY = (
    "agents/registry/LOAD_ORDER.md",
    "agents/registry/CONTEXT_ROUTING.md",
)

# Normative markers — must exist inline (not pointer-only) in always-on docs.
AGENTS_NORMATIVE_MARKERS = (
    "## 2.1 Editing & Routing",
    "## 2.7 Verification First",
    "## 2.8 TDD Red-First",
    "메타 금지 12",
    "연속 작업 2+",
    "honesty > correctness > speed",
)

PROJECT_RULES_NORMATIVE_MARKERS = (
    "## 3.1 Plan-First",
    "## 3.2 TDD Red-First",
    "## 3.3 Verification First",
    "## 3.4 HITL",
    "## 3.5 Information Integrity",
)

STUB_SHOULD_POINT_AGENTS = (
    "agents/core/principles.md",
    "agents/core/error_patterns.md",
    "agents/core/orchestration.md",
)

STUB_SHOULD_NOT_DUPLICATE = (
    (
        "agents/core/principles.md",
        r"^-\s+구현 전 가정은 명시",
        "principles stub must not duplicate AGENTS §1.1 bullets",
    ),
    (
        "agents/core/error_patterns.md",
        r"^2\.\s+\*\*단일 매칭\*\*",
        "error_patterns stub must not duplicate full meta-11 list",
    ),
)

SCENARIOS: tuple[tuple[str, tuple[str, ...], bool], ...] = (
    (
        "renderer_edit",
        ("{{FRONTEND_APP_PATH}}/src/components/consultation/DiagnosisPanel.tsx",),
        False,
    ),
    (
        "plan_edit",
        ("docs/plans/archive/blueprints/PLAN_medical_benefit_reception_type.md",),
        False,
    ),
    (
        "renderer_edit_full",
        ("{{FRONTEND_APP_PATH}}/src/components/consultation/DiagnosisPanel.tsx",),
        True,
    ),
)


def _read(rel: str) -> str:
    return (REPO / rel).read_text(encoding="utf-8")


def _file_entry(rel: str) -> dict[str, Any]:
    full = REPO / rel
    return {
        "path": rel,
        "exists": full.is_file(),
        "tokens": estimate_tokens(full) if full.is_file() else 0,
        "bytes": full.stat().st_size if full.is_file() else 0,
    }


def _check_markers(text: str, markers: tuple[str, ...]) -> dict[str, bool]:
    return {m: m in text for m in markers}


def _phase_t0() -> dict[str, Any]:
    agents = _read("AGENTS.md")
    project_rules = _read("PROJECT_RULES.md")
    marker_ok = _check_markers(agents, AGENTS_NORMATIVE_MARKERS)
    pr_marker_ok = _check_markers(project_rules, PROJECT_RULES_NORMATIVE_MARKERS)
    t0 = estimate_t0(REPO)
    stubs: list[dict[str, Any]] = []
    for rel in STUB_SHOULD_POINT_AGENTS:
        body = _read(rel)
        stubs.append(
            {
                "path": rel,
                **_file_entry(rel),
                "points_to_agents": "AGENTS.md" in body and "SSOT" in body,
            }
        )
    stub_dup_failures: list[str] = []
    for rel, pattern, msg in STUB_SHOULD_NOT_DUPLICATE:
        if re.search(pattern, _read(rel), re.MULTILINE):
            stub_dup_failures.append(f"{rel}: {msg}")
    return {
        "label": "T0 — Cursor IDE always-applied",
        "files": [_file_entry(r) for r in T0_FILES],
        "total_tokens": t0["total_tokens"],
        "within_target": t0["within_target"],
        "agents_normative_markers": marker_ok,
        "agents_normative_all_ok": all(marker_ok.values()),
        "project_rules_normative_markers": pr_marker_ok,
        "project_rules_normative_all_ok": all(pr_marker_ok.values()),
        "stubs": stubs,
        "stubs_point_to_agents": all(s["points_to_agents"] for s in stubs),
        "stub_no_duplicate_ok": len(stub_dup_failures) == 0,
        "stub_duplicate_failures": stub_dup_failures,
    }


def _phase1() -> dict[str, Any]:
    return {
        "label": "Phase 1 — merged into T0 (2026-06-19)",
        "files": [],
        "total_tokens": 0,
        "note": "PROJECT_RULES.md is Cursor T0 always-applied — no separate honor-system Read.",
    }


def _phase2() -> dict[str, Any]:
    return {
        "label": "Phase 2 — lazy before edit/route",
        "files": [_file_entry(r) for r in PHASE2_LAZY],
        "total_tokens": sum(_file_entry(r)["tokens"] for r in PHASE2_LAZY),
        "always_load_rule_tokens": get_always_load_rules(str(REPO / "agents/registry/CONTEXT_ROUTING.md")),
        "note": "Loaded on edit intent — not automatic at session open.",
    }


def _phase_route(name: str, paths: tuple[str, ...], *, full: bool) -> dict[str, Any]:
    bundle = get_route_bundle(list(paths), repo_root=REPO, tight=not full)
    must_read = bundle.get("must_read", [])
    budget = estimate_must_read_tokens(must_read, repo_root=REPO, include_lazy_detail=False)
    return {
        "scenario": name,
        "edit_paths": list(paths),
        "mode": "full" if full else "tight",
        "rule_count": len(bundle.get("rules", [])),
        "must_read_count": len(must_read),
        "must_read_tokens": budget["total_tokens"],
        "must_read_paths": [e["path"] for e in must_read if e.get("installed", True)],
        "includes_always_load": not (not full),
    }


def run_simulation() -> dict[str, Any]:
    routes = [_phase_route(n, p, full=f) for n, p, f in SCENARIOS]
    t0 = _phase_t0()
    p1 = _phase1()
    checks = {
        "t0_budget_ok": t0["within_target"],
        "agents_normative_ok": t0["agents_normative_all_ok"],
        "project_rules_normative_ok": t0["project_rules_normative_all_ok"],
        "stubs_ok": t0["stubs_point_to_agents"] and t0["stub_no_duplicate_ok"],
    }
    all_ok = all(checks.values())
    return {
        "status": "PASS" if all_ok else "FAIL",
        "checks": checks,
        "phases": {
            "t0_cursor_injected": t0,
            "phase1_session_start": p1,
            "phase2_lazy_pre_edit": _phase2(),
        },
        "route_scenarios": routes,
        "expected_at_new_session": {
            "automatic": [f["path"] for f in t0["files"]],
            "agent_should_read": [],
            "lazy_until_edit": list(PHASE2_LAZY),
        },
    }


def _print_human(report: dict[str, Any]) -> None:
    print(f"\n{'=' * 60}")
    print(f"Session load simulation — {report['status']}")
    print(f"{'=' * 60}\n")

    exp = report["expected_at_new_session"]
    print("## 새 세션 직후 (의도)")
    print("  [자동 주입 — Cursor T0 · 5파일]")
    for p in exp["automatic"]:
        print(f"    • {p}")
    if exp["agent_should_read"]:
        print("  [에이전트가 Read해야 함]")
        for p in exp["agent_should_read"]:
            print(f"    • {p}")
    print("  [편집·route 전까지 lazy]")
    for p in exp["lazy_until_edit"]:
        print(f"    • {p}")

    t0 = report["phases"]["t0_cursor_injected"]
    print(f"\n## T0 ({t0['total_tokens']} tok, budget OK={t0['within_target']})")
    for f in t0["files"]:
        print(f"  {f['path']}: {f['tokens']} tok")
    print(f"  AGENTS normative markers: {'OK' if t0['agents_normative_all_ok'] else 'FAIL'}")
    for k, v in t0["agents_normative_markers"].items():
        if not v:
            print(f"    ✗ missing: {k!r}")
    print(
        f"  PROJECT_RULES §3 inline: "
        f"{'OK' if t0['project_rules_normative_all_ok'] else 'FAIL'}"
    )
    for k, v in t0["project_rules_normative_markers"].items():
        if not v:
            print(f"    ✗ missing: {k!r}")
    print(f"  T0 stubs → AGENTS: {'OK' if t0['stubs_point_to_agents'] else 'FAIL'}")
    if t0["stub_duplicate_failures"]:
        for msg in t0["stub_duplicate_failures"]:
            print(f"    ✗ {msg}")

    p1 = report["phases"]["phase1_session_start"]
    if p1.get("files"):
        print(f"\n## Phase 1 ({p1['total_tokens']} tok)")
        print(f"  §3 inline MUST: see T0 PROJECT_RULES")
    else:
        print(f"\n## Phase 1 — {p1.get('note', 'merged into T0')}")

    p2 = report["phases"]["phase2_lazy_pre_edit"]
    print(f"\n## Phase 2 lazy ({p2['total_tokens']} tok)")
    print(f"  always-load rules (on --full): {len(p2['always_load_rule_tokens'])} entries")

    print("\n## Route scenarios (must_read if agent runs just route)")
    for s in report["route_scenarios"]:
        print(
            f"  [{s['scenario']}/{s['mode']}] "
            f"{s['must_read_count']} files, ~{s['must_read_tokens']} tok"
        )
        for p in s["must_read_paths"][:8]:
            print(f"      • {p}")
        if len(s["must_read_paths"]) > 8:
            print(f"      … +{len(s['must_read_paths']) - 8} more")

    print("\n## Checks")
    for k, v in report["checks"].items():
        print(f"  {'✓' if v else '✗'} {k}")
    print()


def main() -> int:
    parser = argparse.ArgumentParser(description="Simulate session context loading tiers")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = run_simulation()
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        _print_human(report)
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
