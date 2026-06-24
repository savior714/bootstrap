---
situation: "리팩토링 방향성 및 뼈대 설계 (무코드)"
# trigger: /refactor  ← catalog metadata only; Read this file before executing (error_patterns/detail/workflow.md#161)
level: Recommended
description: "파편화된 리팩토링 스킬 통합, 진단→심화→검증(RGR) 3단계 가이드 기반 리팩토링 설계 SSOT"
version: 1.1.0
last_updated: 2026-06-19
scope: workflow
domain: workflow
---
<!-- Language: ko -->

# `/refactor` Workflow SSOT

파편화된 리팩토링 기능들을 통합하여, **무코드(Meta-Only) 원칙** 하에 `진단(Diagnose) → 심화(Deepen) → 검증 설계(RGR)` 3단계 가이드를 제공하는 단일 진입점입니다. 

**에이전트는 `/refactor` 호출 시 반드시 본 문서 및 연결된 `SKILL.md`를 최우선으로 따른다.**

## 실행 규칙 및 상세 가이드

본 워크플로우의 모든 세부 정책과 대화 프로토콜(3단계 가이드, `/plan` 핸드오프 조건 등)은 아래 스킬 명세서에 정의되어 있습니다. 에이전트는 본격적인 대화 시작 전 반드시 아래 스킬 파일을 Read해야 합니다.

- **스킬 명세 SSOT**: [`agents/skills/refactor/SKILL.md`](../skills/refactor/SKILL.md)
- **Plan 핸드오프 SSOT**: [`agents/skills/refactor/references/handoff-to-plan.md`](../skills/refactor/references/handoff-to-plan.md) — same-session Blueprint · `plan-lint` PASS

## 역할과 경계 (Scope & Boundary)

- **허용 (이번 세션에서 하는 일)**: 프로젝트의 상태를 진단하고, 얕은 설계를 깊게 심화시키며, 테스트 기반 변경 계획을 수립하는 무코드 대화. 3단계 합의 후 **같은 세션**에서 `docs/plans/PLAN_*.md` 작성·`plan-lint` PASS까지(plan 작성 모드).
- **금지 (이번 세션에서 하지 않는 일)**: 애플리케이션 소스 코드(`.ts`, `.tsx`, `.py` 등)의 실제 수정. 구현·Task 실행은 Blueprint **Execute** 단계([plan.md](plan.md))에서만.

## AskQuestion/`question`(병용) 문자열 가드

- `AskQuestion`/`question`(병용)의 질문 본문/선택지에는 literal `\n` 문자열을 포함하지 않는다.
- 줄바꿈이 필요하면 이스케이프 텍스트(`\\n`)가 아니라 실제 줄바꿈 문자로 작성한다.
