# Bootstrap procedure

Use this repository only as a **one-time repository starter**. After application, normal repository-native development takes over.

## 1. Inspect before creating

First inspect the current working location and repository state.

- **Existing repository:** read its current repo-local authority and current structure first. Preserve valid existing ownership and adapt only where the portable kernel fills a real gap.
- **New standalone project:** create only the minimum repository structure needed for the present objective.

Do not create a parallel policy tree, wrapper runtime, generic architecture, or compatibility layer merely because this bootstrap exists.

## 2. Apply the portable kernel

For a new repository, copy the contents of `scaffold/` into the repository root:

```text
AGENTS.md
docs/
└── operations/
    ├── DEVELOPMENT.md
    └── TESTING.md
```

For an existing repository, merge the semantics into the existing owners instead of blindly duplicating files or authority.

## 3. Preserve the boundary

The portable kernel owns only:

- instruction precedence and authority routing;
- the boundary between ordinary agent-owned technical decisions and consequential user-owned decisions;
- bounded repository-native development and publication closure;
- evidence semantics.

It does **not** prescribe:

- product behavior or scope;
- language, framework, package manager, architecture, build system, or deployment topology;
- domain-specific safety rules;
- runners, daemons, queues, schedulers, lifecycle state, receipts, registries, candidate refs, or publication coordinators;
- automatic synchronization with this repository.

Project-specific truth must come from the target repository's actual product decisions, code, configuration, tests, runtime, and applicable authority.

## 4. Validate the bootstrap

Before calling bootstrap complete, verify that:

1. authority ownership is not duplicated;
2. no unrelated project-specific assumptions leaked in;
3. no runtime/control-plane machinery was introduced;
4. a capable agent can tell what it may decide, what requires user authority, how to bound work, and what evidence is required;
5. the bootstrap does not pre-select the product implementation stack.

Prefer contraction over adding explanation or machinery.

## 5. Stop

Once the target repository owns its kernel, bootstrap is complete. Do not keep this repository in the execution path.

Any later improvement to this kit should be justified by observed repeated friction from real repositories, not by hypothetical completeness.
