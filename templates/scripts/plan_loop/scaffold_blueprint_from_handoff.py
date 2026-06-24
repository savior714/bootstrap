#!/usr/bin/env python3
"""Scaffold docs/plans/PLAN_*.md from an agent hand-off markdown file."""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.plan_loop.blueprint_tail_tasks import render_review_closeout_tail
from scripts.plan_loop.handoff_parser import (
    HandoffParseResult,
    default_verify_for_target,
    derive_task_prefix,
    parse_handoff_markdown,
    pick_target_for_phase,
)

_PLAN_DIR = _REPO_ROOT / "docs" / "plans"


def _collaboration_overview(title: str, origin: str) -> str:
    origin_line = origin or f"{title} 기능을 MVP에서 제품 수준으로 보완한다."
    return f"""### 개요

{origin_line}

### staff·경영에서 바뀌는 점

- 문서·검증·화면이 일관되게 정리된다.

### 끝났을 때 확인할 것

- Blueprint DoD 명령이 전부 통과한다.

### 이번에 안 하는 것

- hand-off 범위 밖 변경은 Execute 전 Edge Trace에 기록한다."""


def _spec_table_rows(spec_paths: list[str]) -> str:
    if not spec_paths:
        return "| `docs/specs/business/SPEC_biz_set_order.md` | (hand-off에서 spec 경로를 보강) |"
    rows = []
    for path in spec_paths[:6]:
        rows.append(f"| `{path}` | hand-off 관련 명세 |")
    return "\n".join(rows)


def _impact_scope_rows(paths: list[str]) -> str:
    if not paths:
        return "| (hand-off Bounded scope 경로 없음) | Execute 전 보강 |"
    return "\n".join(f"| `{p}` | hand-off bounded scope |" for p in paths[:24])


def _dod_block(commands: list[str]) -> str:
    if not commands:
        return "- `just plan-lint docs/plans/PLAN_<slug>.md`"
    return "\n".join(f"- `{cmd}`" for cmd in commands)


def _render_task_block(
    *,
    plan_path: str,
    phase: int,
    sub: int,
    task_id: str,
    title: str,
    target: str,
    goal: str,
    verify: str,
    dependency: str,
    labels: str = "Feature",
    diagnostics: str = "0",
) -> str:
    return f"""#### Task {phase}.{sub}: {title} [Unit: Atomic]
- Task-ID: [{task_id}] | Linear-Issue: TEM-XXX | Status: todo | Priority: 1 | Labels: {labels} | RetryPolicy: none
- **Pre-read**: 이 Task만 — `write`/`patch` 전 **전부** Read <!-- plan-task-preread:v1 paths=1 must_read_installed=1 -->
  1. `[spec]` `{target}`
- **Action**: Edit File | **Target**: `{target}`
- **Closeout**: `{plan_path}`
- **Goal**: {goal}
- **Diagnostics**: {diagnostics}
- **Verify**: `{verify}`
- **Conclusion**: [판정 — 비개발자용 요약. 검증 결과]
- **Dependency**: {dependency}
"""


def _build_execution_order_rows(
    prefix: str, task_ids: list[str], *, start_order: int = 1
) -> str:
    rows: list[str] = []
    prev = "None"
    for idx, task_id in enumerate(task_ids):
        order = start_order + idx
        rows.append(f"| {order} | {task_id} | hand-off 권장 순서 | {prev} | 산출 | — |")
        prev = task_id
    return "\n".join(rows)


def render_blueprint_markdown(
    *,
    slug: str,
    parsed: HandoffParseResult,
    prefix: str,
) -> str:
    plan_filename = f"PLAN_{slug}.md"
    plan_path = f"docs/plans/{plan_filename}"
    today = date.today().isoformat()
    plan_id = f"PLAN_{slug}"

    task_blocks: list[str] = []
    task_ids: list[str] = []

    task_ids.append(f"{prefix}-001")
    task_blocks.append(
        _render_task_block(
            plan_path=plan_path,
            phase=0,
            sub=1,
            task_id=f"{prefix}-001",
            title="Edge Case Trace 갭 감사",
            target=plan_path,
            goal="hand-off 갭·Edge Case Trace·실행 순서 표가 1:1로 맞는지 검토하고 누락 Task를 보완한다.",
            verify=f"just plan-lint {plan_path}",
            dependency="None",
            diagnostics="Phase 0 표준",
        )
    )

    next_num = 2
    prev_dep = f"{prefix}-001"

    if parsed.needs_policy_task:
        task_ids.append(f"{prefix}-002")
        task_blocks.append(
            _render_task_block(
                plan_path=plan_path,
                phase=1,
                sub=1,
                task_id=f"{prefix}-002",
                title="제품 정책 AskQuestion 답을 Blueprint에 기록한다",
                target=plan_path,
                goal="hand-off에 남은 미확정 정책을 AskQuestion으로 확정하고 Blueprint 제품 정책 절에 실측 값을 기록한다.",
                verify=f"just plan-lint {plan_path}",
                dependency=prev_dep,
                diagnostics="후속 UI Task 게이트",
            )
        )
        prev_dep = f"{prefix}-002"
        next_num = 3

    phase_idx = 1 if parsed.needs_policy_task else 0
    sub_idx = 2 if parsed.needs_policy_task else 1

    for phase_label in parsed.recommended_phases:
        if re_skip_phase(phase_label):
            continue
        task_num = next_num
        task_id = f"{prefix}-{task_num:03d}"
        target = pick_target_for_phase(phase_label, parsed.bounded_paths)
        if not target:
            target = plan_path
        verify = default_verify_for_target(target, plan_path)
        task_ids.append(task_id)
        task_blocks.append(
            _render_task_block(
                plan_path=plan_path,
                phase=phase_idx + 1,
                sub=sub_idx,
                task_id=task_id,
                title=_phase_task_title(phase_label),
                target=target,
                goal=_phase_task_goal(phase_label, target),
                verify=verify,
                dependency=prev_dep,
                diagnostics=f"hand-off 권장: {phase_label[:60]}",
            )
        )
        prev_dep = task_id
        next_num += 1
        sub_idx += 1

    if next_num == (3 if parsed.needs_policy_task else 2):
        task_id = f"{prefix}-{next_num:03d}"
        task_ids.append(task_id)
        fallback = parsed.bounded_paths[0] if parsed.bounded_paths else plan_path
        task_blocks.append(
            _render_task_block(
                plan_path=plan_path,
                phase=1,
                sub=1,
                task_id=task_id,
                title="hand-off bounded scope 1차 구현",
                target=fallback,
                goal=f"{fallback}에 hand-off MVP 보완 1차 변경을 반영한다.",
                verify=default_verify_for_target(fallback, plan_path),
                dependency=prev_dep,
            )
        )
        prev_dep = task_id

    last_impl = prev_dep
    review_id = f"{prefix}-098"
    closeout_id = f"{prefix}-099"
    task_ids.extend([review_id, closeout_id])
    tail = render_review_closeout_tail(
        plan_path=plan_path,
        last_impl_task_id=last_impl,
        plan_text="",
        review_task_id=f"{prefix}-098",
        closeout_task_id=f"{prefix}-099",
    )

    out_of_scope = parsed.out_of_scope_lines
    oos_section = ""
    if out_of_scope:
        oos_section = "\n".join(f"- {line}" for line in out_of_scope[:8])

    body = f"""---
id: {plan_id}
type: plan
status: active
last_verified: {today}
---

<!-- Language: ko -->

# 🗺️ Project Blueprint: {parsed.title} (TEM-XXX)

## 문서 메타
- **Last Verified**: {today} | **Tested Version**: N/A
- **Reference**: hand-off scaffold
- **SSOT Check**: N/A
- **Project Status Link**: N/A
- **Linear-Issue**: TEM-XXX
- **Priority**: 1
- **Labels**: Feature
- **Architectural Goal**: hand-off MVP 보완을 스펙·테스트·UX까지 제품 수준으로 정합화
- **Linear-Policy**: internal

## 📎 관련 명세

| 문서 | 범위 |
| :--- | :--- |
{_spec_table_rows(parsed.spec_paths)}

## 📋 업무 요약 (협업용)

> **독자**: 원장·원무·기획. 코드·경로·명령은 아래 기술 절.

{_collaboration_overview(parsed.title, parsed.origin_summary)}

## 🎯 Origin Intent

- **출처**: agent hand-off scaffold
- **원래 목적**: {parsed.title} MVP를 제품 수준으로 보완
- **완료 관찰**: DoD 명령 전부 통과

## ⚠️ Edge Case Trace

| 엣지 케이스 | 출처 | Task-ID / 범위 밖 | 비고 |
| :--- | :--- | :--- | :--- |
| hand-off 갭 보강 | Origin | {prefix}-001 | Execute 전 Trace 동기화 |

## 🧭 Context Pre-read Gate (실행 전 필수)

<!-- plan-preread:v1 paths=0 must_read_installed=0 -->
(planned: `just plan-preread {plan_path} --write`)

## 🔍 Diagnosis & Findings

- **현상**: MVP 구현 후 스펙·테스트·UX 갭 존재
- **근본 원인**: hand-off 기준 후속 hardening 미완료

## 🏗️ Architectural Deepening

- **Seam**: hand-off bounded scope 파일 경계
- **Leverage**: 스펙 선행 후 TDD·UI 정렬

## 📜 Conceptual Sketch

```
hand-off → 스펙 → 테스트 → UI → lint-turn-end
```

## 🛡️ Risk & Strategy

- **Risk**: 미확정 정책으로 UI 되돌림 | **Strategy**: 정책 Task 선행

## Agent Execution Pack

> **Execute 읽기 범위**: Agent Completion Contract·Task Pre-read·Impact Scope·실행 순서·Execution Plan만 Read.

## 🔍 Impact Scope

| 파일 | 변경 요약 |
| :--- | :--- |
{_impact_scope_rows(parsed.bounded_paths)}

## 실행 순서·선행

| 순서 | Task-ID | 왜 이 Task인가 (분해 논리) | 선행 | 한 줄 산출 | 병렬 |
| :---: | :--- | :--- | :--- | :--- | :---: |
{_build_execution_order_rows(prefix, task_ids)}

## Agent Completion Contract

| 허용 | 금지 |
| :--- | :--- |
| `just plan-task-close`로 Task Status·Conclusion 갱신 | Task Status/Conclusion 직접 수정 |
| Task Verify 후 `just plan-lint {plan_path}` | Conclusion 없이 done |

## 🛠️ Step-by-Step Execution Plan

> **에이전트 스코프**: Task 1개씩. Verify PASS → Conclusion → `just plan-task-close plan={plan_path} task=… conclusion="…"` → **`just plan-lint {plan_path}`**.

### Phase 0 — Edge case gap audit

{task_blocks[0]}

### Phase 1+ — hand-off 권장 순서

{chr(10).join(task_blocks[1:])}

{tail}

## 🔁 Conclusion & Summary

- **Roll-up**: {prefix}-099 Closeout 전 미작성

## ✅ Definition of Done (DoD)

{_dod_block(parsed.dod_commands).replace("PLAN_<slug>.md", plan_filename)}

## 검증 행렬

| Scope | Command |
| :--- | :--- |
| Blueprint | `just plan-lint {plan_path}` |
| Quality | `just plan-lint-quality {plan_path}` |
"""
    return body.replace("PLAN_<slug>.md", plan_filename)


def re_skip_phase(label: str) -> bool:
    lowered = label.lower()
    return any(
        token in lowered
        for token in ("lint-turn-end", "plan-lint", "마감만", "closeout only")
    )


def _phase_task_title(phase_label: str) -> str:
    cleaned = phase_label.split("(")[0].strip()
    if len(cleaned) > 48:
        cleaned = cleaned[:45] + "…"
    return cleaned


def _phase_task_goal(phase_label: str, target: str) -> str:
    return f"hand-off 권장 단계「{phase_label[:40]}」에 맞게 `{target}`를 수정한다."


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scaffold Blueprint from hand-off markdown.")
    parser.add_argument("--slug", required=True, help="Plan slug, e.g. order_set_scope_hardening")
    parser.add_argument("--handoff", required=True, type=Path, help="Path to hand-off markdown")
    parser.add_argument("--title", default=None, help="Override blueprint title")
    parser.add_argument("--prefix", default=None, help="Task-ID prefix, e.g. ORDS")
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write docs/plans/PLAN_<slug>.md (default: stdout)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing plan file when using --write",
    )
    args = parser.parse_args(argv)

    handoff_path = args.handoff
    if not handoff_path.is_file():
        print(f"[ERROR] hand-off file not found: {handoff_path}", file=sys.stderr)
        return 1

    slug = re.sub(r"^PLAN_", "", args.slug.strip(), flags=re.IGNORECASE)
    slug = slug.removesuffix(".md")
    text = handoff_path.read_text(encoding="utf-8")
    parsed = parse_handoff_markdown(text, slug=slug, title=args.title)
    prefix = derive_task_prefix(slug, override=args.prefix)
    rendered = render_blueprint_markdown(slug=slug, parsed=parsed, prefix=prefix)

    out_path = _PLAN_DIR / f"PLAN_{slug}.md"
    if args.write:
        _PLAN_DIR.mkdir(parents=True, exist_ok=True)
        if out_path.exists() and not args.force:
            print(f"[ERROR] {out_path} exists — use --force to overwrite", file=sys.stderr)
            return 1
        out_path.write_text(rendered, encoding="utf-8")
        print(f"[OK] wrote {out_path.relative_to(_REPO_ROOT)}")
        print(f"[next] just plan-preread {out_path.relative_to(_REPO_ROOT)} --write")
        print(f"[next] just plan-lint {out_path.relative_to(_REPO_ROOT)}")
        print(f"[next] just plan-lint-quality {out_path.relative_to(_REPO_ROOT)}")
        return 0

    sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
