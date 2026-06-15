---
scope: registry
domain: core
---
<!-- Language: ko -->

# 워크플로 · 스킬 색인 (Bootstrap Kernel)

**Bootstrap 커널**에 포함된 슬래시 워크플로·프로세스 스킬만 나열합니다.  
EMR 전용 워크플로(`/assess`, `/linear`, `/bootstrap` 등)·FE 스킬·`PROJECT_SKILL_ROUTING.json`은 **미포함** — 프로젝트별로 추가하세요.

| 레지스트리 | 역할 |
| :--- | :--- |
| [LOAD_ORDER.md](LOAD_ORDER.md) | 세션 로딩 Phase |
| [CONTEXT_ROUTING.md](CONTEXT_ROUTING.md) | 경로·Tier 라우팅 |
| [RULE_INDEX.md](RULE_INDEX.md) | 규칙 파일 색인 |

---

## 워크플로 (슬래시 라우터)

| Workflow | Usage | 스킬 | 라우터 (부록) |
| :--- | :--- | :--- | :--- |
| `/plan` | 통합 심층 설계 및 태스크 분해 | — | [plan.md](../workflows/plan.md) |
| `/diagnose` | 문제 진단 및 재현 (6-phase SSOT) | [diagnose/SKILL.md](../skills/diagnose/SKILL.md) | [diagnose.md](../workflows/diagnose.md) |
| `/investigate` | 경량 조사·원인 파악 | [investigate/SKILL.md](../skills/investigate/SKILL.md) | [investigate.md](../workflows/investigate.md) |
| `/review` | 코드·PR 리뷰 | [review/SKILL.md](../skills/review/SKILL.md) | [review.md](../workflows/review.md) |
| `/discuss` | 무코드 방향 합의 | [discuss/SKILL.md](../skills/discuss/SKILL.md) | [discuss.md](../workflows/discuss.md) |
| `/sync` · `/spec-sync` | 스펙·Plan Conclusion 역검증 | [sync/SKILL.md](../skills/sync/SKILL.md) | [sync.md](../workflows/sync.md) |
| `/discover` | 기술 부채 탐색 → Blueprint | [discover/SKILL.md](../skills/discover/SKILL.md) | [discover.md](../workflows/discover.md) |
| `/refactor` | 무코드 리팩토링 3단 | [refactor/SKILL.md](../skills/refactor/SKILL.md) | [refactor.md](../workflows/refactor.md) |
| `/improve-codebase-architecture` | Shallow→Deep 모듈 진단 | [improve-codebase-architecture/SKILL.md](../skills/improve-codebase-architecture/SKILL.md) | [improve-codebase-architecture.md](../workflows/improve-codebase-architecture.md) |
| `/playwright` | UI 탐색·E2E 문제 발견 | — | [playwright.md](../workflows/playwright.md) |
| `/go` | 세션 산출물 동기화·이관 | — | [go.md](../workflows/go.md) |
| `/git` | 커밋·슬라이스·푸시 | — | [git.md](../workflows/git.md) |
| `/archive` | 완료 Blueprint → archive | — | [archive.md](../workflows/archive.md) |

**스킬 열 `—`**: 워크플로 pointer만 Read. E2E 규칙: [testing/playwright.md](../domains/testing/playwright.md).

---

## 키워드 → Read (수동 자기 규제)

슬래시·키워드는 **IDE가 자동 실행하지 않음**. 아래 경로를 **Read** 후 실행 ([error_patterns §16.1](../core/error_patterns/detail/workflow.md)).

| 키워드 (예) | Read |
| :--- | :--- |
| plan, blueprint, 설계 | [workflows/plan.md](../workflows/plan.md) |
| review, 리뷰 | [workflows/review.md](../workflows/review.md) · [skills/review/SKILL.md](../skills/review/SKILL.md) |
| debug, diagnose, 재현 | [workflows/diagnose.md](../workflows/diagnose.md) · [skills/diagnose/SKILL.md](../skills/diagnose/SKILL.md) |
| investigate, 원인 파악 | [workflows/investigate.md](../workflows/investigate.md) · [skills/investigate/SKILL.md](../skills/investigate/SKILL.md) |
| spec-sync, 스펙 drift | [skills/sync/SKILL.md](../skills/sync/SKILL.md) · [workflows/sync.md](../workflows/sync.md) |
| discuss, DISCUSS_ | [skills/discuss/SKILL.md](../skills/discuss/SKILL.md) · [workflows/discuss.md](../workflows/discuss.md) |
| discover, 기술 부채 | [workflows/discover.md](../workflows/discover.md) · [skills/discover/SKILL.md](../skills/discover/SKILL.md) |
| refactor, 리팩토링 설계 | [workflows/refactor.md](../workflows/refactor.md) · [skills/refactor/SKILL.md](../skills/refactor/SKILL.md) |
| shallow→deep, 모듈 깊이 | [workflows/improve-codebase-architecture.md](../workflows/improve-codebase-architecture.md) · [skills/improve-codebase-architecture/SKILL.md](../skills/improve-codebase-architecture/SKILL.md) |
| playwright, e2e | [workflows/playwright.md](../workflows/playwright.md) · [domains/testing/playwright.md](../domains/testing/playwright.md) |
| archive, blueprint 이관 | [workflows/archive.md](../workflows/archive.md) |
| git, commit-gate | [workflows/git.md](../workflows/git.md) |
| 완료, 마무리, /go | [reporting.md](../core/reporting.md) §1.0 · [workflows/go.md](../workflows/go.md) |
| anti-pattern, wrong/correct | [error_patterns.md](../core/error_patterns.md) |

**Diagnose vs investigate**: 실패 **재현·근본 원인** → diagnose. 로그·코드만 **가설·범위** → investigate.

---

## 프로세스 스킬 (`.agents/skills`)

| 트리거 / 상황 | SSOT 스킬 | 라우터 (부록) |
| :--- | :--- | :--- |
| `/diagnose` | [diagnose/SKILL.md](../skills/diagnose/SKILL.md) | [diagnose.md](../workflows/diagnose.md) |
| `/investigate` | [investigate/SKILL.md](../skills/investigate/SKILL.md) | [investigate.md](../workflows/investigate.md) |
| `/review` | [review/SKILL.md](../skills/review/SKILL.md) | [review.md](../workflows/review.md) |
| `/spec-sync` | [sync/SKILL.md](../skills/sync/SKILL.md) | [sync.md](../workflows/sync.md) |
| `/discuss` | [discuss/SKILL.md](../skills/discuss/SKILL.md) | [discuss.md](../workflows/discuss.md) |
| `/refactor` | [refactor/SKILL.md](../skills/refactor/SKILL.md) | [refactor.md](../workflows/refactor.md) |
| `/discover` | [discover/SKILL.md](../skills/discover/SKILL.md) | [discover.md](../workflows/discover.md) |
| `/improve-codebase-architecture` | [improve-codebase-architecture/SKILL.md](../skills/improve-codebase-architecture/SKILL.md) | [improve-codebase-architecture.md](../workflows/improve-codebase-architecture.md) |

스킬·워크플로 추가 시 본 문서·`manifest.json`·EMR 소스 `.agents/registry/`를 함께 갱신하세요.

---

**Last Updated**: 2026-06-12 · Bootstrap kernel subset
