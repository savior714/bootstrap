# Context7 Library Check (review — always-on)

리뷰마다 **Context7 MCP**로 최신 라이브러리·프레임워크 문서를 조회한다. 소형·로컬 LLM도 학습 시점과 무관하게 **현재 API·deprecation·권장 패턴**을 근거로 삼게 한다.

> **범위**: API 계약·deprecation·보안·수명주기(lifecycle) — **스타일 nitpick·포맷은 §Ignore 유지**.

---

## 0. 우선순위 (판단 순서)

1. **실행 증거** — `git diff`, vitest, just (review Iron Law)
2. **프로젝트 SSOT** — [code_quality_lifecycle.md](../../../core/code_quality_lifecycle.md) R-1~R-5 · [error_patterns.md](../../../core/error_patterns.md)
3. **Context7** — 1·2와 diff가 **충돌·의심**할 때 Finding evidence에 인용; 이슈 없으면 「확인만」 기록

Context7만으로 High/Medium을 올리지 않는다 — **diff의 구체 코드·실행 경로**와 연결될 때만.

---

## 1. MCP 호출 (MUST — 매 리뷰)

**서버**: `user-context7`

| 순서 | 도구 | 역할 |
| :--- | :--- | :--- |
| 1 | `resolve-library-id` | diff 기준 **주 라이브러리 1개** ID 확정 |
| 2 | `query-docs` | diff 패턴에 맞는 **구체 질문 1~2개** (리뷰당 **최대 2회**) |

호출 전 MCP descriptor Read (`mcps/user-context7/tools/*.json`).  
`CallMcpTool`로 invoke.

### MCP 없음 / 실패

| 상황 | 행동 |
| :--- | :--- |
| MCP 미설치·비활성 | **실행한 검증**에 `Context7: SKIP (MCP unavailable)` 기록 후 나머지 리뷰 진행 |
| resolve 실패 | `Context7: SKIP (library not found: {name})` + EMR 기본 fallback 1회 재시도 (§2 표) |
| query 빈 응답 | `Context7: no match` 기록 — 추측 Finding **금지** |

**생략 금지**: diff가 도메인-only여도 §2로 주 라이브러리를 정해 **최소 1회 query-docs**는 시도한다.

---

## 2. 주 라이브러리 선정 (diff → libraryName)

Gather( diff Read ) 직후, **아래 첫 매칭 1개**를 주 라이브러리로 고른다.

| diff 신호 | libraryName | query 초점 |
| :--- | :--- | :--- |
| `{{FRONTEND_APP_PATH}}/**` · `*.tsx` · Next route/handler | `Next.js` | App Router, RSC, cookies, middleware, auth |
| React hooks·컴포넌트 (Next 외 packages/ui) | `React` | hooks lifecycle, concurrent, 19.x patterns |
| `*.test.ts(x)` · vitest · MSW | `Vitest` | mock boundaries, fake timers, RTL integration |
| `apps/server/**` · FastAPI · Python route | `FastAPI` | dependency injection, exception handlers, security |
| SQLAlchemy · Alembic · migration | `SQLAlchemy` | session/transaction, async patterns |
| FHIR · HAPI (import/path 힌트) | `HAPI FHIR` | security, scope, REST conventions |
| TypeScript types only · shared packages | `TypeScript` | strict patterns, utility types (로직 리스크 한정) |
| **매칭 없음** | `Next.js` | EMR FE 기본 스택 — 「현재 버전 일반 보안·데이터 fetching 주의점」 |

버전: `{{FRONTEND_APP_PATH}}/package.json` 등에서 **major.minor** 확인 후 resolve 결과에 version suffix가 있으면 사용.

---

## 3. query-docs 작성 규칙

### MUST

- **추상 패턴**으로 질문 — diff에 쓰인 API·훅·옵션 **이름**만 포함
- 리뷰 Focus와 연결 — auth, cookie, async, error handling, deprecation
- 질문 예: `Next.js App Router httpOnly cookie set options and security recommendations`  
  `React 19 useEffect cleanup for async subscriptions in client components`

### MUST NOT

- API 키·토큰·환경 변수·환자/사용자 데이터·**전체 diff 붙여넣기**
- 「best practices」만 묻는 포괄 질문 (lint/스타일 nitpick 유발)
- 리뷰당 `query-docs` **3회 초과** (Context7 상한 준수)

### diff → query 매핑 (템플릿)

Gather 후 아래를 채워 **query-docs 1회**에 넣는다:

```text
Library: {libraryName} ({version if known})
Patterns in diff: {comma-separated API/hook names — no secrets}
Review focus: {auth | async | error-handling | deprecation | data-fetching | other}
Question: For {patterns}, what are current recommended usage, deprecations, and security pitfalls?
```

변경이 **2개 이상 스택**에 걸치면: 주 라이브러리 1회 + **부 라이브러리 1회** (최대 2 query-docs).

---

## 4. Findings 반영

| Context7 결과 | Finding |
| :--- | :--- |
| diff 코드가 **deprecated·금지 패턴**과 일치 | Medium 이상 + evidence에 `Context7: …` 1줄 |
| **보안·auth** 권고와 diff 불일치 | High 후보 — 실행 경로·코드 줄과 함께 |
| 문서만 권장, diff와 **무관** | Finding **올리지 않음** — 검증 표에만 `Context7: checked, no diff impact` |
| 문서와 diff **모호** | Low 또는 기록만 — 추측 High **금지** |

evidence 형식:

```text
Context7 (/vercel/next.js): {한 줄 요약} — diff: {file:line or pattern}
```

---

## 5. 실행한 검증 표 (필수 행)

매 리뷰 **실행한 검증** 표에 최소 1행:

| 예시 | 의미 |
| :--- | :--- |
| `Context7 resolve Next.js → query-docs (cookies) — no diff impact` | always-on 완료 |
| `Context7 resolve React → query-docs (useEffect) — Medium evidence` | 이슈 연결 |
| `Context7: SKIP (MCP unavailable)` | fallback |

---

## 6. 다른 스킬과 경계

| 주제 | SSOT |
| :--- | :--- |
| React/Next **성능·번들** | [vercel-react-best-practices](../../frontend/vercel-react-best-practices/SKILL.md) — Context7로 중복 nitpick 금지 |
| **구조·결합** R-1~R-5 | [code_quality_lifecycle.md](../../../core/code_quality_lifecycle.md) |
| 테스트 **품질** | [test-analysis](../../test-analysis/SKILL.md) |

Context7은 **「최신 외부 API·프레임워크 계약」** 보조. 프로젝트 게이트·just lint 결과가 있으면 **lint가 SSOT**.
