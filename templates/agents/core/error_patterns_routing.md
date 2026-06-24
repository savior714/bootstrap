---
scope:
- '*'
always_apply: false
priority: 1
domain: core
verify_with:
- agent-meta-prohibitions-check
---
<!-- Language: ko -->

# Error Patterns — 라우팅 인덱스 (lazy-load)

**always-on 헤더**: [error_patterns.md](error_patterns.md). `just route` 시 `must_read`에 자동 추가될 수 있음.

## Detail 인덱스

| Detail | § | 트리거 (경로 패턴) |
| :--- | :--- | :--- |
| [editing.md](error_patterns/detail/editing.md) | §1, §1.11, §3, §7 | **모든** 편집 경로 · `*.tsx`/`*.jsx` |
| [testing.md](error_patterns/detail/testing.md) | §2 | `tests/**`, `*.test.*`, `test_*` |
| [tools.md](error_patterns/detail/tools.md) | §3 | `agents/**` |
| [blueprint.md](error_patterns/detail/blueprint.md) | §4 | `docs/plans/**` |
| [workflow.md](error_patterns/detail/workflow.md) | §5, §16 | `docs/discussions/**`, `agents/workflows/**` |

> `error_patterns/detail/*.md` — `.cursorignore` 대상일 수 있음. Permission denied 시 shell(`cat`/`rg`)로 확인.

## 부록: 희귀 패턴 (archive)

| id | 이름 | 아카이브 |
| :--- | :--- | :--- |
| 8.1 | dependency-injector mixin 상속 실패 | [incidents.md §8](error_patterns_archive/incidents.md) |
| 9.1 | Path.parents[N] repo root 오계산 | [incidents.md §9](error_patterns_archive/incidents.md) |
| 10.1 | plan-lint Status 파싱 충돌 | [incidents.md §10](error_patterns_archive/incidents.md) |
| 11.1 | plan-task-close shell 해석 | [incidents.md §11](error_patterns_archive/incidents.md) |
| 12.1 | DISCUSS dual `---` YAML 파싱 | [incidents.md §12](error_patterns_archive/incidents.md) |
| 13.1 | docs-discuss-lifecycle 오인 | [incidents.md §13](error_patterns_archive/incidents.md) |
| 14.1 | macOS 시스템 Python PATH | [incidents.md §14](error_patterns_archive/incidents.md) |
| 15.1 | session index misuse (폐기) | [incidents.md §15](error_patterns_archive/incidents.md) *(역사 참고)* |
