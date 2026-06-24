"""Reusable Implementation Review (-098) and Closeout (-099) Task blocks for Blueprints."""

from __future__ import annotations

import re

from scripts.docs.plan_yaml_frontmatter import derive_plan_id_from_path

_TASK_ID_PREFIX_RE = re.compile(r"Task-ID:\s*\[([A-Z][A-Z0-9]{1,})-\d{3}\]", re.IGNORECASE)


def derive_task_id_prefix_from_plan_text(text: str) -> str:
    """Infer Task-ID prefix from the first Task block (e.g. SLC from [SLC-010])."""
    match = _TASK_ID_PREFIX_RE.search(text)
    if match:
        return match.group(1).upper()
    plan_id = derive_plan_id_from_path("PLAN_placeholder.md")
    _ = plan_id  # fallback only when no tasks yet
    return "PLN"


def derive_review_task_ids(plan_path: str, *, plan_text: str | None = None) -> tuple[str, str]:
    """Return (review_task_id, closeout_task_id) like SLC-098 / SLC-099."""
    prefix = derive_task_id_prefix_from_plan_text(plan_text or "") if plan_text else "PLN"
    if prefix == "PLN":
        stem = derive_plan_id_from_path(plan_path)
        bits = stem.split("-")
        if len(bits) >= 2 and bits[0] == "PLAN":
            prefix = bits[1][:3].upper()
    return f"{prefix}-098", f"{prefix}-099"


def render_implementation_review_section_placeholder() -> str:
    return """## 🔍 Implementation Review

- **High**: Review Task -098 Execute 전 미작성
- **Medium**: Review Task -098 Execute 전 미작성
- **Low**: Review Task -098 Execute 전 미작성
- **권장 수정 요약**: Review Task -098 Execute 전 미작성
"""


def render_implementation_review_task_block(
    *,
    task_id: str,
    plan_path: str,
    dependency: str,
    linear_issue: str = "TEM-XXX",
    phase_label: str = "Implementation review",
    task_heading: str = "5.1",
    phase_num: int = 8,
) -> str:
    return f"""### Phase {phase_num} — {phase_label}

#### Task {task_heading}: Implementation Review 작성 [Unit: Atomic]
- Task-ID: [{task_id}] | Linear-Issue: {linear_issue} | Status: todo | Priority: 3 | Labels: Improvement | RetryPolicy: none
- **Pre-read**: 이 Task만 — `write`/`patch` 전 **전부** Read
  1. `[project_skill]` `agents/skills/review/SKILL.md`
  2. `[spec]` `agents/skills/plan/references/handoff-from-execute-to-review.md`
  3. `[spec]` `{plan_path}`
  4. `[rule]` `agents/core/error_patterns/detail/editing.md`
- **Action**: Edit File | **Target**: `{plan_path}`
- **Closeout**: `{plan_path}` (Task {task_id} `Conclusion`·`Status`)
- **Goal**: review/SKILL.md Iron Law·Agent-executable verification으로 세션 구현 diff를 diff-first 리뷰하고 Findings를 Implementation Review 절에 기록한다.
- **Diagnostics**: closeout 전 구현 변경분 전체 점검 — review SKILL MUST
- **Verify**: `just plan-review-gate plan={plan_path}`
- **Conclusion**: [판정 — 비개발자용 요약. 검증 결과]
- **Dependency**: {dependency}
"""


def render_closeout_task_block(
    *,
    task_id: str,
    plan_path: str,
    review_task_id: str,
    linear_issue: str = "TEM-XXX",
    phase_label: str = "Blueprint closeout",
    task_heading: str = "6.1",
    phase_num: int = 9,
) -> str:
    return f"""### Phase {phase_num} — {phase_label}

#### Task {task_heading}: Roll-up 작성 및 plan-close [Unit: Atomic]
- Task-ID: [{task_id}] | Linear-Issue: {linear_issue} | Status: todo | Priority: 3 | Labels: Improvement | RetryPolicy: none
- **Pre-read**: 이 Task만 — `write`/`patch` 전 **전부** Read
  1. `[spec]` `{plan_path}`
  2. `[rule]` `agents/domains/documentation/markdown.md`
  3. `[project_skill]` `agents/skills/frontend/vercel-react-best-practices/SKILL.md`
  4. `[project_skill]` `agents/skills/frontend/vercel-composition-patterns/SKILL.md`
  5. `[error_pattern_detail]` `agents/core/error_patterns/detail/editing.md`
- **Action**: Edit File | **Target**: `{plan_path}`
- **Closeout**: `{plan_path}` (Task {task_id} `Conclusion`·`Status`)
- **Goal**: 선행 Task Conclusion을 근거로 Conclusion and Summary Roll-up 1문단을 실측으로 작성한다.
- **Diagnostics**: Blueprint closeout — Review Task {review_task_id} 완료 후 Roll-up 작성
- **Verify**: `just plan-close plan={plan_path}`
- **Conclusion**: [판정 — 비개발자용 요약. 검증 결과]
- **Dependency**: {review_task_id}
"""


def render_review_closeout_tail(
    *,
    plan_path: str,
    last_impl_task_id: str,
    linear_issue: str = "TEM-XXX",
    review_phase: str = "Implementation review",
    closeout_phase: str = "Blueprint closeout",
    plan_text: str | None = None,
    review_task_id: str | None = None,
    closeout_task_id: str | None = None,
) -> str:
    """Append review + closeout phases and Implementation Review section."""
    inferred_review, inferred_closeout = derive_review_task_ids(plan_path, plan_text=plan_text)
    review_id = review_task_id or inferred_review
    closeout_id = closeout_task_id or inferred_closeout
    parts = [
        render_implementation_review_task_block(
            task_id=review_id,
            plan_path=plan_path,
            dependency=last_impl_task_id,
            linear_issue=linear_issue,
            phase_label=review_phase,
        ),
        render_closeout_task_block(
            task_id=closeout_id,
            plan_path=plan_path,
            review_task_id=review_id,
            linear_issue=linear_issue,
            phase_label=closeout_phase,
        ),
        render_implementation_review_section_placeholder(),
    ]
    return "\n".join(parts)
