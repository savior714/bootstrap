---
scope:
- '*'
always_apply: true
priority: 1
domain: core
verify_with:
- agent-meta-prohibitions-check
- error-patterns-sort-check
patterns_file: agents/core/error_patterns/patterns.yaml
---

<!-- Language: ko -->

# Error Patterns — 에이전트가 자주 하는 실수

**normative SSOT (always-on)**: [AGENTS.md §2.1](../../AGENTS.md#21-editing--routing-normative) · [AGENTS.md §2.6 메타 금지 12](../../AGENTS.md#26-메타-금지-12) — 디스크 SSOT · 고유 블록 지정 · 기존 파일 Write 금지 · 게이트 PASS 전 진행 금지 등 전체 MUST 목록.

**lazy (편집·`just route` 직전)**: TOP 4·5–9 WRONG/CORRECT · symptom별 예시 — [error_patterns_routing.md](error_patterns_routing.md) · `error_patterns/detail/`.

편집 도구 스키마: [runtime_edit_tools.md](runtime_edit_tools.md) · Cursor 상세: [routing.md §1](routing.md).

## Quick Reference — TOP 4 (lazy → AGENTS normative)

1. **읽기 → 전체 쓰기** — [AGENTS §2.1](../../AGENTS.md#21-editing--routing-normative) · [editing §1.1](error_patterns/detail/editing.md)
2. **고유 블록 미지정** — [AGENTS §2.6](../../AGENTS.md#26-메타-금지-12) · [editing §1.2](error_patterns/detail/editing.md)
3. **실패 후 동일 old 재시도** — [editing §1.3](error_patterns/detail/editing.md)
4. **부분 수정 후 검증 누락** — [editing §1.3](error_patterns/detail/editing.md)

TOP 5–9: [error_patterns_routing.md](error_patterns_routing.md)

## 🚫 메타 금지 12

→ **본문 normative는 [AGENTS.md §2.6](../../AGENTS.md#26-메타-금지-12)**. 본 절은 always-on T0 stub · `patterns.yaml` 부모 · detail lazy 인덱스.

## Zero-Leak

→ [PROJECT_RULES.md §4.1](../../PROJECT_RULES.md) · [AGENTS.md §2.4](../../AGENTS.md#24-secrets-zero-leak).
