<!-- Language: en -->
# Development

This document owns the repository's **development execution contract**: how work is bounded, executed in a workspace, and closed/published. `docs/operations/TESTING.md` owns evidence semantics; this document does not restate them.

## 1. Before mutation

- Inspect the current repository state and the directly applicable authority before editing.
- If the prompt's premise conflicts with current evidence, investigate the mismatch rather than forcing the requested patch.
- Immediately before execution, re-read the relevant current truth; re-derive the task when a material premise (target ownership, contract, proof criterion) has changed. Unrelated upstream movement is information, not invalidation.

## 2. Work bounding

- Close one coherent bounded problem / safe state transition at a time.
- Keep strongly coupled changes together when they close one root cause; split independent state transitions apart.
- Do not absorb a newly discovered independent problem into the current task; report it instead.
- No speculative abstraction, no unrelated cleanup, no manufactured follow-up work merely because improvement is possible.

### Complexity admission

> Add durable abstractions, frameworks, services, queues, registries, checkers, harnesses, or other machinery only when current evidence shows the actual problem cannot be safely closed through a simpler existing path and the added mechanism has a concrete expected benefit.

This is a decision criterion, not a scoring system, registry, or governance process. Prefer deletion and contraction over accumulation.

## 3. Workspace

Use the simplest safe workspace. The current checkout is fine when ownership and dirty state make it safe; a branch or worktree is an optional implementation choice when isolation materially improves safety. Workspace mechanics are not semantic authority. Never reset, stash, clean, or overwrite state that another session or the user intends to preserve.

## 4. Prompts and artifacts

Prompts are disposable execution artifacts, not canonical project state. Investigation scratch work stays temporary; promote only durable verified conclusions to their actual authority owner. Do not store task queues, receipts, or execution progress in repository documentation.

## 5. Proof and stopping

- Obtain proof proportional to the changed behavior, risk, and fan-out; `TESTING.md` owns what counts as faithful evidence.
- Stop when the done condition is proven. Do not append unrelated scans, suites, or governance after success.

## 6. Publication closure

Before publication, fetch fresh upstream state and determine whether intervening changes materially affect the task. Overlapping semantic movement requires re-checking meaning and proof before proceeding; unrelated movement does not. §6 classifies semantic re-check requirements and the next bounded transition; it never authorizes bypassing a `BLOCKED` Git Safety result. §8 still owns Git publication safety.

### 6.1 Three freshness lifecycles (independent states)

Publication, semantic, and proof freshness are independent states with separate owners:

- **publication/topology freshness**: whether the candidate can publish FF-only onto the current fresh remote. Owned by Git Safety (§8) as objective topology evidence; the remote owns the final truth (read back after publication).
- **semantic freshness**: whether task meaning / requirement / contract / authority is still valid. Owned by the task framer/executor via transient classification (§6.4).
- **proof freshness**: whether the test / fixture / runtime / build / authority an existing proof depended on was actually affected. Owned by the proof runtime (actual PASS/FAIL) plus executor classification (§6.4).

Forbidden inferences (never derive these from SHA movement alone):

- `REMOTE_ADVANCED -> TASK_INVALID`
- `DIVERGED -> SEMANTIC_STALE`
- `TOPOLOGY_STALE -> PROOF_STALE`
- `UNKNOWN -> FULL_REBUILD`
- `MISSING_METADATA -> READMIT`

Remote topology movement alone does not reopen semantic work and is not semantic invalidation; whether intervening movement matters is decided by §6.4 (only overlapping semantic movement requires re-checking meaning and proof).

### 6.2 `SEMANTIC_READY != PUBLISHABLE`

- `SEMANTIC_READY`: the bounded semantic change is complete, the required task proof is complete, and the semantic result is fixed — but this says nothing about being publishable onto the fresh remote right now.
- `PUBLISHABLE`: fresh remote authority was re-confirmed, the candidate/current semantic delta is valid on the publication topology, the required final integrity / directly affected proof is complete, and a non-force FF publication may be attempted immediately.

Never discard `SEMANTIC_READY` on topology movement alone.

### 6.3 JIT publication binding

Keep semantic work and the final publication commit identity separate for as long as possible:

task admission → semantic mutation → relevant proof → `SEMANTIC_READY` → fresh remote check immediately before publication → freshness classification (§6.4) → final JIT topology binding onto the fresh trunk only if needed → directly affected integrity/proof only → `PUBLISHABLE` → FF-only publication → remote read-back.

One topology-binding cost for a genuinely needed child commit on the fresh trunk is allowed. Topology-only advance never justifies re-implementing semantics from scratch, re-running broad proof, or blindly restarting the task on a fresh base.

### 6.4 Freshness classification

Classify with the transient WATCH_SURFACES (§6.6) and direct repository evidence:

- **topology-only movement** (remote moved; semantic owners and proof owners unaffected): preserve semantic work, reuse existing proof, preserve the old candidate/reference, perform only the final JIT topology binding plus final integrity / directly affected proof, then publish.
- **semantic-owner movement** (requirement / public contract / schema meaning / architecture authority / workflow semantics / relevant API behavior / directly depended-on policy actually changed): `READMIT`. Never blind-salvage.
- **proof-owner-only movement** (meaning unchanged; relevant test / fixture / validation rule / build config / runtime provider / generated artifact owner / proof command affected): preserve the semantic result and re-run only the affected targeted proof.
- **uncertainty**: `UNKNOWN -> FULL_REBUILD` is forbidden. Shrink uncertainty with the nearest relevant targeted proof or a bounded read-only classification. `READMIT` only when real semantic impact is proven.

### 6.5 Recover-or-Preserve (legacy / thin-metadata work)

Missing transient metadata never implies rebuild. First attempt read-only reconstruction of `DIRECT_PATHS`, `SEMANTIC_OWNERS`, and `PROOF_OWNERS` from current repository evidence; when reconstruction suffices, run normal §6.4 classification. When it does not, preserve the semantic result, preserve known-scope proof, keep the candidate reference-only, and stop only publication as `CONTINUABLE` pending freshness classification. Never invalidate finished semantic work for lack of information alone.

### 6.6 WATCH_SURFACES are transient handoff evidence

`DIRECT_PATHS`, `SEMANTIC_OWNERS`, and `PROOF_OWNERS` are transient handoff/execution evidence owned by the development contract / task framer / executor. They are not a durable project-wide dependency graph, not a new registry, queue, scheduler, lease, or candidate database. Do not persist them beyond the execution that needs them and do not invent project-specific dependency vocabulary for the kernel.

### 6.7 Second-advance circuit breaker

After the final JIT binding, another writer may advance the remote before publication. That lost race is not a task failure: keep `SEMANTIC_READY`, keep classified proof evidence, keep the old candidate/reference, and end the current publication attempt. Never start a bind → proof → advance → bind → proof loop inside the same attempt; the next publication attempt restarts from fresh authority.

### 6.8 Responsibility boundary

- **Git Safety (§8)** owns only objective Git/repository facts: repository identity, task/worktree identity, fresh remote revision, candidate identity/containment, ancestor/descendant/diverged relations, FF publication admissibility, fail-closed task selection, and objective topology evidence. It never infers or persists semantic/proof impact, dependency graphs, queues, schedulers, leases, or rematerialization policy; one `REMOTE_ADVANCED` never commands a rebuild.
- **Development contract / task framer / executor** owns the transient classification above.
- **Proof runtime** owns actual PASS/FAIL.
- **Remote** owns final publication truth; always read back.

For publication-intended work, when the current user instruction authorizes it and no local-only restriction exists:

- ordinary safe non-force fast-forward publication plus remote read-back is part of normal closure;
- an unpublished local candidate is not the normal terminal success state.

Canonical terminal outcomes:

- `COMPLETE / PUBLISHED` — the intended change is safely published and read back from the remote;
- `COMPLETE / NO_CHANGE` — proof shows no mutation was required; this is a legitimate terminal result;
- `COMPLETE / LOCAL_ONLY` — only when the task explicitly requested local-only work.

If publication cannot safely complete, report `CONTINUABLE` or `BLOCKED` with the concrete cause and exact resume point. Destructive or history-rewriting Git operations, force pushes, and external side effects (deployment, provider mutations) require explicit user authority.

## 7. Concurrency

Independent work may proceed independently when mutation, authority, and evidence boundaries are independent. Add coordination machinery only after direct recurring evidence demonstrates that ordinary repository-native practice cannot preserve the required semantics at lower cost.

Under the Git Safety Baseline (§8), publication-intended mutation targeting one shared canonical branch is not an independent mutation topology: with immutable admitted BASE plus fast-forward-only publication and no history reconciliation, only work admitted after the current BASE can publish directly, and any sibling admitted from an older BASE stops being fast-forward-publishable once the first publishes (unless its HEAD already contains the current base by direct containment evidence, §8). By default, do not pre-materialize a second final JIT publication binding against the same canonical branch while an earlier publication attempt is still in flight; serialize that mutation/materialization boundary at publication time only and admit the next binding only after the earlier attempt has closed or blocked. Concurrent semantic development toward the same branch stays permitted: semantic work is preserved across topology contention via §6 freshness classification, never serialized into a global queue, and never restarted merely because `origin/main` advanced. This is a runtime/repository admission discipline, not a helper-enforced mutex (git-safety `create` does not refuse admission merely because another record exists). Read-only investigation remains parallel, as does mutation against independent repositories / independent publication destinations. Remote topology movement alone does not reopen semantic work; whether intervening movement matters is decided by §6 (only overlapping semantic movement requires re-checking meaning and proof).

## 8. Git Safety Baseline (conditional)

Applies only when this repository is agent-mutable **and** uses a shared remote. Local-only scratch repositories are out of scope and must not gain coupling to this section.

Before repository mutation:

1. admit a fresh remote base: `./scripts/git-safety create <task-id>`;
2. work only in the admitted task-owned worktree;
3. do not bypass a `BLOCKED` Git Safety result with raw Git (`git worktree add`, manual branches, or direct checkout mutation are not substitutes);
4. before publication, re-check fresh topology for the same task: `./scripts/git-safety pre-publish <task-id>` (pass the same `<task-id>` used at `create`; do not rely on singleton auto-selection — an omitted `<task-id>` is inferred only when the invocation repository (`--repo`, default `.`) is exactly one admitted task worktree, otherwise the helper fails closed with `TASK_ID_REQUIRED` (lone unrelated admission) or `AMBIGUOUS_TASK` and never reports that unrelated admission's `REMOTE_ADVANCED` as the invocation verdict) — the reported `CANDIDATE_HEAD` is the admitted task-owned worktree HEAD only, never the invoking checkout/main HEAD, and the verdict covers only that task candidate. Publication is fast-forward-only and the helper never merges, rebases, cherry-picks, or force-pushes. A `BLOCKED` result never authorizes raw-Git publication of any candidate (including a different local HEAD that appears fast-forward-safe); publish only the admitted task worktree HEAD after `PUBLISHABLE_FF` for that same task, or admit a fresh task for the intended candidate and re-prove.

`./scripts/git-safety` is the stable entrypoint; any convenience alias delegates to it and owns no independent semantics. If the helper reports missing/incompatible/unverifiable implementation, re-apply the bootstrap `scripts/` starter per the output's `REMEDIATION`, never a local safety reimplementation.
