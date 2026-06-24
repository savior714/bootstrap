---
name: review
description: >
  PR·브랜치·스테이징 변경분을 diff-first로 리뷰한다 — 정확성·회귀·권한·보안·부작용에 집중하고
  스타일 nitpick은 생략한다. 매 리뷰 Context7 MCP로 최신 라이브러리·프레임워크 문서를 조회해
  deprecation·API·보안 권고를 diff와 대조한다(도메인-only diff 포함 — always-on).
  에이전트가 git diff·Context7·관련 테스트·just를 직접 실행해 근거를 확보한 뒤
  High/Medium/Low로 보고하고 이슈별·전체 권장 수정안(권장+이유)을 제시한 뒤
  close 턴 AskQuestion으로 후속(plan/discuss/fix/마무리)을 수렴한다. AskQuestion 불가 시 pending_ask frontmatter.
  Use for /review, 코드 리뷰, PR 검토, 변경분 점검, merge 전 검토, 회귀 리스크.
  테스트 실패 원인 조사는 investigate/diagnose. 테스트 파일 품질 분석은 test-analysis.
license: MIT
metadata:
  version: "1.4.1"
disable-model-invocation: true
---

<!-- Language: ko -->

# Review

**변경분 리뷰** — 에이전트가 **직접 diff·테스트·검증**한 뒤 근거 기반으로 보고한다.

**하지 않는 것**: 실패 테스트 **원인 추적** 루프, 테스트 파일 **품질 분석** 전체, 스타일 nitpick.

> **이웃 스킬**: PR·diff 리뷰 → **review** · 실패 원인 조사 → [investigate](../investigate/SKILL.md) · 수정+고정 → [diagnose](../diagnose/SKILL.md) · 테스트 품질 → [test-analysis](../test-analysis/SKILL.md)

---

# Response Language (MUST)

세션 채팅·리뷰 보고 **한국어**. 코드·로그·파일 경로는 영문 가능.

---

# Skill Boundary (MUST)

| 사용자 요청 | 이 스킬 | 대안 |
| :--- | :--- | :--- |
| PR·브랜치·스테이징 **변경분** 리뷰, merge 전 점검 | ✅ review | — |
| 테스트 **실패**·flaky·CI red 원인 찾기 | — | [investigate](../investigate/SKILL.md) → 필요 시 [diagnose](../diagnose/SKILL.md) |
| 특정 **테스트 파일** 품질·커버리지·assertion 구조 점검 | — | [test-analysis](../test-analysis/SKILL.md) |
| 변수명·포맷만 불만, 로직 변경 없음 | ✅ review — **로직·리스크만**, naming nitpick 생략 | — |
| 명세↔코드 drift·code lock | 보조 | [sync](../sync/SKILL.md) |

**오분기 시**: 리뷰를 시작하지 말고, 위 표의 대안 스킬을 **한 줄로 안내**하고 사용자 의도를 확인한다.

---

# Iron Law

1. **추측 금지** — "probably safe", "looks okay" 같은 표현 금지.
2. **diff-first** — 변경 범위 밖 파일은 리뷰하지 않는다.
3. **실행 후 보고** — 아래 §Agent-executable verification(**Context7 always-on** 포함)을 시도한 뒤 발견을 쓴다.
4. **Context7 always-on** — Gather 직후 [context7-library-check.md](references/context7-library-check.md) — **매 리뷰** `resolve-library-id` + `query-docs` ≥1회. MCP 불가 시 SKIP 기록만, 나머지 생략 **금지**.
5. **close 수렴** — 리뷰 본문 후 **같은 턴** AskQuestion/`question`(병용) 필수 (Cursor).

---

# Agent-executable verification (MUST)

보고 전에 아래를 **직접** 수행한다. "로컬에서 확인해주세요"로 넘기지 않는다.

| 유형 | EMR 예시 |
| :--- | :--- |
| 변경 범위 | `git diff <base>...HEAD` 또는 `git diff` (스테이징·워킹트리) |
| **Context7 (always-on)** | MCP `user-context7`: `resolve-library-id` → `query-docs` — [context7-library-check.md](references/context7-library-check.md). **실행한 검증** 표에 결과·SKIP 필수 |
| 관련 테스트 | 변경 파일과 매칭되는 `vitest run <file>` — 실패 시 **증거로 기록**, 원인 추적은 investigate로 handoff |
| 레시피 | `just --list`로 존재 확인 후 `just lint-*`, `just test-*` 등 **변경과 연관된** 검증 |
| 코드 추적 | Read, `rg`로 호출 경로·권한 체크·null 경로 추적 |
| 구조 체크 | [code_quality_lifecycle.md](../../core/code_quality_lifecycle.md) §3 R-1~R-5 |

### 보고서에 넣을 섹션: **실행한 검증**

최소 1행 표. 예: `git diff`, `Context7 Next.js query-docs (cookies)`, `vitest run Foo.test.tsx` PASS/FAIL, `just plan-lint` 등.

### 사용자에게만 요청 (극히 좁게)

| 항목 | 전제 |
| :--- | :--- |
| 프로덕션 전용 런타임 로그 | 로컬·docker·hub로 **대체 불가** 입증 후 |
| 외부 배포 환경 재현 | 로컬 vitest·MSW로 **동일 시나리오 재현 불가** 후 |
| 의도적 동작 변경 여부 | diff·코드만으로 **제품 의도**를 알 수 없을 때 |

**금지**: diff도 안 읽고, 관련 테스트도 안 돌리고 "확인 불가"로 마무리.

---

# Core Rules

## Anti-pattern at write

**Symptom**: 리뷰가 추측 위주이거나 close 없이 멈춤.

**Cause**: evidence·실행 검증·AskQuestion 생략.

❌ WRONG: "probably safe", close 없이 "/plan 하세요"만 안내

✅ CORRECT: 실패 시나리오 + 코드 근거 + **실행한 검증** + **권장 수정 요약** + close AskQuestion

Reference: [`docs/agent-context/ANTI_PATTERN_FORMAT.md`](../../../docs/agent-context/ANTI_PATTERN_FORMAT.md)

## 권장안 제시 (MUST)

discuss [§권장 + 이유](../discuss/SKILL.md)와 동일한 **수준**으로, 리뷰 본문·close 모두에서 권장안을 드러낸다.

| 구간 | MUST |
| :--- | :--- |
| **이슈별** | High·Medium마다 `suggested fix` — 수정 경로가 2개 이상이면 **하나에 `(권장)`** + 나머지는 대안 1줄 |
| **본문 마무리** | Findings 직후 **「권장 수정 요약」** 1~2줄 — `(권장)` 후속(Blueprint / 소규모 fix / discuss) + **이유 10단어 이내** |
| **close AskQuestion** | §Close turn `(권장)` 선정 후 `options[]` **1번=권장 · 마지막=마무리**(이슈 있을 때) |

**`(권장)` 선정 (close)** — discuss 2단계와 동일 우선순위:

1. 리뷰 **권장 수정 요약**과 **일치**하는 후속 1개
2. 동률·미정이면 — High 건수·파일 수·동작 변경 폭 → Blueprint vs 소규모 fix vs discuss
3. 실질 이슈 없음 → **마무리** `(권장)` · 다른 범위 리뷰는 마지막

**금지**: 이슈만 나열하고 수정안·후속 `(권장)` 없이 close · `(권장)` 2개 이상 · 마무리를 1·2번 슬롯에 두기(이슈 있을 때).

## Diff-first

```bash
git diff <base>...HEAD
```

- 변경점·깨질 수 있는 것·의도치 않은 부작용에 집중
- 변경 0건이어도 사용자가 지정한 파일은 **정적 리뷰** 가능 — "현재 상태 잠재 리스크"로 구분

## Evidence Required

모든 이슈에:

1. 왜 중요한지
2. 어떻게 실패하는지 (실행 경로·조건)
3. 코드/실행 근거 (파일·라인·테스트 결과)

## Focus Areas

우선순위: auth/permission · null/undefined · async · stale state · race · transaction · silent failure · hidden regression · input validation · API contract · prompt injection · missing error handling

**구조·결합**: [code_quality_lifecycle.md](../../core/code_quality_lifecycle.md) §3 R-1~R-5

## Ignore

포맷 · naming 취향 · lint 수준 · 주관적 스타일 — formatter/linter에 맡김.

---

# Review Process

0. **경로 분류** — standalone `/review` vs **plan Execute 직후**(Post-execute). 후자는 [plan/handoff-from-execute-to-review.md](../plan/references/handoff-from-execute-to-review.md) · §Post-execute close — Blueprint `(권장)` **금지**.
1. **경계 확인** — §Skill Boundary. 오분기면 대안 안내 후 중단.
2. **Gather** — `git diff`, 변경 파일 Read.
3. **Context7 (always-on, MUST)** — [context7-library-check.md](references/context7-library-check.md): diff → 주 라이브러리 → `resolve-library-id` → `query-docs` ≥1회. 도메인-only diff도 §2 fallback으로 **생략 금지**.
4. **Run verification** — 관련 vitest/just (§Agent-executable).
5. **Trace** — 실행 경로·권한·엣지 케이스 · Context7 결과와 diff **대조**.
6. **Findings** — High / Medium / Low (아래 형식) + 이슈별 `suggested fix`.
7. **권장 수정 요약** — Findings 직후 1~2줄 (§권장안 제시).
8. **Final check** — 추측 제거, Context7-only Finding 없음 확인, High/Medium마다 actionable·`(권장)` fix·close `(권장)` 후속 일치 확인.
9. **Close** — 본문 후 AskQuestion (§Close turn). 도구 불가 시 [pending-ask-fallback.md](references/pending-ask-fallback.md) frontmatter **필수**.

---

# Finding Format

각 이슈는 **issue → evidence → suggested fix** 순. fix는 **구체적**(파일·함수·패턴 수준).

### High Risk

- issue · impact · evidence · **suggested fix** `(권장)` (복수 경로 시 1개만 태그) · 대안(있을 때)

### Medium Risk

- issue · edge case · evidence · **suggested fix** `(권장)` (복수 경로 시 1개만 태그) · 대안(있을 때)

### Low Risk

의미 있을 때만 — fix는 선택, 있으면 `(권장)` 1개.

### 권장 수정 요약 (Findings 직후, MUST)

```text
권장: {Blueprint | 소규모 즉시 fix | discuss} — {한 줄 이유}
```

예: `권장: Blueprint — High 2건이 auth·트랜잭션 경로를 건드림`

---

# Fix-first Principle

명백하고 국소적·저위험이면 **직접 수정** 가능.

먼저 물어볼 것: 아키텍처·스키마·동작 변경·destructive 작업.

---

# Close turn (세션 종료)

리뷰 본문을 **한 턴에 제시**한 뒤, **같은 턴 마지막**에 `AskQuestion`/`question`(병용).

### Handoff (권장 수정·후속 1건 이상)

| 옵션 (비개발자 라벨) | 내부 |
| :--- | :--- |
| 권장 수정을 실행 계획(Blueprint)으로 정리하기 `(권장)` | same-session `/plan` |
| 리뷰·수정 범위 더 discuss하기 | `/discuss` |
| 지금 바로 소규모만 고치기 | Fix-first |
| 여기서 마무리 | 종료 |

복수 파일·동작 변경이면 Blueprint `(권장)`. 단일 1~2줄 버그면 「지금 바로 소규모만 고치기」 `(권장)` 가능. High만 있고 범위·트레이드오프 불명확하면 「더 discuss」 `(권장)` 가능.

### 옵션 표시 순서 (AskQuestion UX) (MUST)

[AGENTS.md §1.3](../../../AGENTS.md#13-quick-pick--interactive-refine) · discuss §옵션 표시 순서와 동일.

| 슬롯 | 내용 |
| :--- | :--- |
| **1번** | `(권장)` 후속 — 라벨 끝 `(권장)` |
| **중간** | 나머지 비권장 옵션 |
| **마지막** | **여기서 마무리** (실질 이슈 **있을 때** 필수) |

**이슈 있음** — `(권장)`·마무리 슬롯 예:

| `(권장)` | 1번 | 2번 | 마지막 |
| :--- | :--- | :--- | :--- |
| Blueprint | Blueprint `(권장)` | discuss · 소규모 fix | 마무리 |
| 소규모 fix | 소규모 fix `(권장)` | Blueprint · discuss | 마무리 |
| discuss | discuss `(권장)` | Blueprint · 소규모 fix | 마무리 |

**실질 이슈 없음** — 마무리 `(권장)` = **1번**, 다른 범위 리뷰 = 2번(마지막).

채팅 본문에 **권장 수정 요약** 1줄 + close 직전 **권장 후속 1줄(이유)** 포함. `options[]` 순서와 채팅 A/B/C **일치**.

### 실질 이슈 없음

| 옵션 | 내부 |
| :--- | :--- |
| 마무리 `(권장)` | 종료 |
| 다른 변경 범위 리뷰 | 새 diff로 `/review` |

### Fast-path

사용자가 이미 plan·Blueprint 연속을 선택했으면 handoff **생략** → [plan.md](../../workflows/plan.md).

### Post-execute review (plan Execute 직후 MUST)

**SSOT**: [plan/handoff-from-execute-to-review.md](../plan/references/handoff-from-execute-to-review.md)

discuss · assess · discover emit 등 **모든 Blueprint handoff**에서 메뉴 B **Execute**를 끝낸 뒤 — 구현 Task ≥1 `done`이면 **본 review 스킬**로 same-session diff 점검. plan Phase E3에서 **생략 금지**.

| 구간 | close `(권장)` |
| :--- | :--- |
| **일반** `/review` (Execute 없음) | Findings·범위에 따라 Blueprint · discuss · fix · 마무리 |
| **Post-execute** (Execute 직후) | **Blueprint를 1번 `(권장)`에 두지 않음** — fix · discuss · **새 slug PLAN** · 마무리 |

**Post-execute close 옵션** (실질 이슈 **있을 때** — `(권장)` 1번 · 마무리 마지막):

| 옵션 (비개발자 라벨) | 내부 |
| :--- | :--- |
| 지금 바로 소규모만 고치기 `(권장)` | Fix-first — 국소 High/Medium |
| 리뷰·수정 범위 더 discuss하기 | `/discuss` |
| Findings를 **새** 실행 계획으로 정리하기 | same-session plan — **새 slug** PLAN (동일 PLAN 재작성 **금지**) |
| 여기서 마무리 | 종료 |

**Post-execute · 실질 이슈 없음**: 마무리 `(권장)` **1번** / 다른 변경 범위 리뷰 **마지막**.

**금지**: Execute closeout 후 review 생략 · Post-execute에서 「이 PLAN Blueprint 만들기」 `(권장)` (이미 실행 완료).

### Same-session plan

**핸드오프 SSOT**: [references/handoff-to-plan.md](references/handoff-to-plan.md) · 공통: [plan/handoff-contract.md](../plan/references/handoff-contract.md).

plan 선택 시 같은 세션에서 `PLAN_*.md` + `just plan-lint` PASS → **산출물 요약 턴** + 메뉴 B. Task는 리뷰 High/Medium 근거. **사용자에게 `/plan` 입력을 시키지 않음**.

### Cursor 강제

- close 턴은 **반드시** AskQuestion/`question` tool call.
- 텍스트만 "선택지를 골라주세요" 하고 종료 = 정책 위반.

### AskQuestion unavailable — pending_ask (MUST)

도구 미노출·호출 실패 시 close를 **생략하지 않는다**. SSOT: [pending-ask-fallback.md](references/pending-ask-fallback.md).

| MUST | 내용 |
| :--- | :--- |
| **frontmatter** | `report.md` 맨 위 YAML `pending_ask` — `recommended` · `reason` · `options[]` (`label` + `action`) |
| **슬롯** | §Close turn과 동일 — `(권장)` 1번 · 마무리 마지막(이슈 있을 때) |
| **일치** | `recommended` ↔ Findings 직후 **권장 수정 요약** |
| **로그** | `tool_log.json` `askquestion_attempts` — `skipped`/`failed` + reason |
| **Post-execute** | Blueprint `(권장)` **금지** — fallback 템플릿 §Post-execute |

채팅 턴에서 AskQuestion **성공**하면 frontmatter 생략 가능. eval·subagent·리포트 export는 **항상** frontmatter.

### 금지

- `/plan` 명령만 남기고 선택 없이 종료
- 리뷰 본문 없이 handoff만
- close 턴 AskQuestion **또는** pending_ask frontmatter 없이 종료
- literal `\n` in AskQuestion strings

# Final Rule

**diff 읽고, Context7 조회하고, 테스트 돌리고, 근거·권장 수정으로 리뷰하고, close에서 수렴한다.** 원인 추적은 investigate.
