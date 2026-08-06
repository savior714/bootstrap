# Atomic Task Delta Template

```text
TASK_ID:
<short stable id>

FAILURE_DOMAIN:
<one observable defect>

REPRODUCTION:
<one deterministic reproduction>

HYPOTHESIS:
<one falsifiable cause and minimum change>

WRITE_SET:
- <exact path>

FORBIDDEN_SET:
- <paths or behaviors not owned>

PRIMARY_VERIFY:
<one command or inspection that decides the hypothesis>

DIRECT_VERIFY:
<modified files and directly affected closure only>

OPTIONAL_SYSTEM_SMOKE:
<broader exploratory verification or NONE; failure does not cancel task PASS>

STEPS:
1. Read the closest implementation and test.
2. Reproduce the stated failure.
3. Apply the minimum change.
4. Run PRIMARY_VERIFY and judge only the stated hypothesis.
5. Run DIRECT_VERIFY for modified files and direct impact only.
6. Record any independent failure as DISCOVERED_FAILURE without fixing it.
7. Before publication, compare latest main by semantic overlap.
8. If there is no overlap, reapply, rerun PRIMARY_VERIFY and required DIRECT_VERIFY, then retry publication.
9. Commit and push according to repository AGENTS.md.

ACCEPTANCE:
<one binary primary criterion plus direct impact closure>

BLOCKED_ALLOWLIST:
- DECISION_REQUIRED
- PRIMARY_UNEVALUABLE: primary criterion cannot be evaluated and no equivalent validation exists
- SEMANTIC_OVERLAP: latest main invalidates the hypothesis, patch, or direct closure
- SAFETY_BOUNDARY: required safety, security, data-integrity, or domain boundary cannot be preserved

NOT_BLOCKERS:
- remote advance or non-fast-forward without semantic overlap
- unrelated dirty state outside WRITE_SET
- unrelated full-suite or system-smoke failure
- newly discovered independent defect
- another session publishing first

STOP:
- hypothesis rejected
- required change exceeds the decision boundary
- one BLOCKED_ALLOWLIST condition is met

REPORT:
RESULT: PASS | BLOCKED
PRIMARY_VERIFY: PASS | FAIL | NOT_RUN
DIRECT_VERIFY: PASS | FAIL | NOT_RUN
PUBLISH: PUBLISHED | NOT_APPLICABLE | BLOCKED
DISCOVERED_FAILURE: <independent failure or NONE>
COMMIT: <published commit only>
BLOCKER: <allowlisted blocker only>
```

공통 Git·runtime·완료 보고 규칙은 이 프롬프트에 다시 붙이지 않는다.
