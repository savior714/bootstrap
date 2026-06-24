---
scope: registry
domain: core
---
<!-- Language: ko -->

# Agent Rule Index (Bootstrap Kernel)

Bootstrap 커널에 **실제로 포함된** 규칙 파일만 색인합니다.  
EMR 의료·FHIR·프론트엔드·인프라 도메인 규칙은 미포함 — 프로젝트별 `agents/domains/`에 추가하세요.

## Constitution (Root)

| 파일 | 설명 |
| :--- | :--- |
| [AGENTS.md](../../AGENTS.md) | 우선순위, 전역 게이트, 레지스트리 진입점 |
| [PROJECT_RULES.md](../../PROJECT_RULES.md) | 아키텍처 정책, 기술 스택, 품질 게이트 |

## Registry & Metadata

| 파일 | 설명 |
| :--- | :--- |
| [LOAD_ORDER.md](LOAD_ORDER.md) | 세션 로딩 Phase |
| [CONTEXT_ROUTING.md](CONTEXT_ROUTING.md) | 경로·Tier 라우팅 |
| [WORKFLOW_AND_SKILL_INDEX.md](WORKFLOW_AND_SKILL_INDEX.md) | 워크플로·스킬 표 (커널 subset) |
| [RULE_INDEX.md](RULE_INDEX.md) | 본 문서 |

## Core Instruction (`agents/core/`)

동기화 대상 전체 — 예: `execution.md`, `verification.md`, `planning.md`, `reporting.md`, `routing.md`, `principles.md`, `error_patterns.md`, `code_quality_lifecycle.md`, `runtime_edit_tools.md` 등.

## Domain Rules (커널 포함)

| 분류 | 파일 | 설명 |
| :--- | :--- | :--- |
| **Testing** | [testing/playwright.md](../domains/testing/playwright.md) | Playwright E2E |

## Workflows & Skills (커널 포함)

- **워크플로 13종**: `archive`, `diagnose`, `discover`, `discuss`, `git`, `go`, `improve-codebase-architecture`, `investigate`, `plan`, `playwright`, `refactor`, `review`, `sync`
- **스킬 8종**: `diagnose`, `discover`, `discuss`, `improve-codebase-architecture`, `investigate`, `refactor`, `review`, `sync`

상세 표: [WORKFLOW_AND_SKILL_INDEX.md](WORKFLOW_AND_SKILL_INDEX.md).

## 프로젝트 확장 (미포함 · 선택)

| 항목 | 비고 |
| :--- | :--- |
| `PROJECT_SKILL_ROUTING.json` | 기계 intent 라우팅 — EMR 확장 |
| `SKILL_CATALOG.json` | 스킬 카탈로그 — EMR 확장 |
| `agents/domains/**` | frontend, backend, medical, infra 등 |
| `agents/adaptive/**` | 인지 로깅·자기 진화 |

---

**Last Updated**: 2026-06-12 · Bootstrap kernel subset
