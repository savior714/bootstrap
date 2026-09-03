# Bootstrap

A deliberately thin starter kit for agent-driven software repositories.

This repository is **not** a runtime harness. It does not own or manage an agent's execution lifecycle. There is no runner, daemon, queue, scheduler, registry, admission protocol, candidate-ref system, publication coordinator, executor adapter, or central policy sync.

## Purpose

Bootstrap a repository with the smallest durable development kernel needed for reliable agent work:

- `AGENTS.md` — precedence, authority routing, and decision boundary
- `docs/operations/DEVELOPMENT.md` — bounded repository-native execution and publication closure
- `docs/operations/TESTING.md` — evidence and validation semantics
- `scripts/git-safety` — conditional Git Safety Baseline entrypoint (agent-mutable + shared-remote repositories only): fresh remote BASE admission into a task-owned worktree before mutation; no daemon, queue, scheduler, lock, or reconciliation engine

The reusable templates live under [`scaffold/`](scaffold/).

## Repository-first initialization

Before bootstrapping anything:

1. Inspect the current working location and repository state.
2. If an existing repository is present, join its repo-local authority and current structure. Do not overwrite or bypass it merely to impose this scaffold.
3. If this is a genuinely new standalone project, create only the minimum structure required for the present objective.
4. Do not invent scaffolding, architecture, or harness machinery before demonstrated need.

See [`BOOTSTRAP.md`](BOOTSTRAP.md) for the application procedure.

## Ownership after bootstrap

Once copied into a target repository, the files belong to that repository. This repository does not remain a runtime dependency or policy authority for the target.

Future changes here do **not** automatically propagate to previously bootstrapped repositories. Re-admit a newer rule into an existing repository only when that repository has a concrete reason to adopt it.

## Expansion rule

Keep this kit small. Add a new durable rule or artifact only after repeated real development friction shows that the existing simpler path is insufficient and the addition is expected to reduce interpretation, rework, or proof cost.
