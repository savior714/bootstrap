"""Tests for Agent Execution Pack HARD gate on active root blueprints."""

from __future__ import annotations

import unittest
from pathlib import Path

from scripts.plan_loop.plan_lint import lint_plan_text
from scripts.plan_loop.plan_lint.fixer import fix_plan_text
from scripts.plan_loop.plan_lint.structural import _lint_active_root_blueprint_governance


def _minimal_active_body(*, with_pack: bool = False) -> str:
    pack = """
## Agent Execution Pack

> **Execute 읽기 범위**: Execute·경량 모델은 Blueprint에서 **이 절부터** `Agent Completion Contract`·각 Task `Pre-read`·아래 실행 절만 Read한다.

Pack 구성 — `Impact Scope` · `실행 순서·선행` 표 · `Execution Plan` Task 블록만 포함한다.

""" if with_pack else ""
    return f"""<!-- Language: ko -->

# 🗺️ Project Blueprint: Pack gate 테스트

## 문서 메타
- **SSOT Check**: ok
- **Project Status Link**: ok
- **Architectural Goal**: ok
- **Linear-Policy**: internal

## 📎 관련 명세

| 문서 | 범위 |
| :--- | :--- |
| `docs/specs/ui/SPEC_ui_test.md` | test |

## 📋 업무 요약 (협업용)

### 개요

테스트.

### staff·경영에서 바뀌는 점

- 없음

### 끝났을 때 확인할 것

- 없음

## 🧭 Context Pre-read Gate (실행 전 필수)

### Read SSOT

- 단일 Task 실행: Pre-read만.

## 🔍 Diagnosis & Findings

- **현상**: x

## 🏗️ Architectural Deepening

- **Seam**: x

## 📜 Conceptual Sketch

```
sketch
```

## 🛡️ Risk & Strategy

- **Risk**: x — **Strategy**: y
{pack}
## 🔍 Impact Scope

| f | r |
| :--- | :--- |
| a | b |

## Agent Completion Contract

| 허용 | 금지 |
| :--- | :--- |
| plan-task-close | 직접 수정 |

## 🛠️ Step-by-Step Execution Plan

> **에이전트 스코프**: Verify → Conclusion → done → plan-lint

#### Task 1.1: Fix [Unit: Atomic]
- Task-ID: [TST-001] | Status: todo | RetryPolicy: none
- **Pre-read**: none
- **Action**: Edit
- **Target**: file.py
- **Goal**: fix the module export
- **Diagnostics**: 0
- **Verify**: `just lint`
- **Conclusion**: [판정 — 비개발자용 요약. 검증 결과]
- **Dependency**: None

## 🔁 Conclusion & Summary

- **Roll-up**: pending

## ✅ Definition of Done (DoD)

- `just plan-lint docs/plans/PLAN_pack_gate_test.md`
"""


class TestExecutionPackGate(unittest.TestCase):
    def test_missing_execution_pack_fails_active_root(self):
        body = _minimal_active_body(with_pack=False)
        path = Path("docs/plans/PLAN_pack_gate_test.md")
        issues, _ = _lint_active_root_blueprint_governance(body, path)
        self.assertTrue(any("Agent Execution Pack" in i for i in issues), issues)

    def test_execution_pack_before_impact_passes_governance(self):
        body = _minimal_active_body(with_pack=True)
        path = Path("docs/plans/PLAN_pack_gate_test.md")
        issues, _ = _lint_active_root_blueprint_governance(body, path)
        pack_issues = [i for i in issues if "Agent Execution Pack" in i]
        self.assertEqual(pack_issues, [], issues)

    def test_fixer_inserts_execution_pack_before_impact(self):
        body = _minimal_active_body(with_pack=False)
        path = Path("docs/plans/PLAN_pack_gate_fix_test.md")
        fixed, fixes = fix_plan_text(body, file_path=path)
        self.assertTrue(any("Agent Execution Pack" in f for f in fixes), fixes)
        issues, _ = lint_plan_text(fixed, file_path=path)
        pack_issues = [i for i in issues if "Agent Execution Pack" in i]
        self.assertEqual(pack_issues, [], issues)

    def test_archive_path_skips_execution_pack_gate(self):
        body = _minimal_active_body(with_pack=False)
        path = Path("docs/plans/archive/frontend/PLAN_pack_gate_test.md")
        issues, _ = _lint_active_root_blueprint_governance(body, path)
        self.assertEqual(issues, [])


if __name__ == "__main__":
    unittest.main()
