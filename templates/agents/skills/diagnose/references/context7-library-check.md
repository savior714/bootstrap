# Context7 Library Check (diagnose — always-on)

버그 고정 세션마다 **Context7 MCP**로 최신 라이브러리·프레임워크 문서를 조회한다. 소형·로컬 LLM도 **현재 API·타이밍·deprecation·디버깅 함정**을 가설·근본 원인 근거로 쓸 수 있게 한다.

> **범위**: 재현 루프·계측 **이전/병행** — Context7은 **가설(Phase 3)·근본 원인** 보조. **추측 패치·루프 생략 대체 아님** (diagnose Iron Law).

---

## 0. 우선순위 (판단 순서)

1. **Phase 1~2 루프** — pass/fail 신호·재현 증거 (Iron Law #1)
2. **프로젝트 SSOT** — [error_patterns.md](../../../core/error_patterns.md) · [RES_COMMON_ERROR_RESOLUTIONS.md](../../../../docs/knowledge/RES_COMMON_ERROR_RESOLUTIONS.md) · hub jsonl
3. **Context7** — 루프·로그와 **맞물리는** framework 함정·lifecycle·breaking change를 Phase 3 가설·Root Cause에 1줄 인용

Context7만으로 근본 원인 확정 **금지** — **반증 가능 probe(Phase 4)** 또는 루프 결과와 연결될 때만.

---

## 1. MCP 호출 (MUST — 매 diagnose)

**서버**: `user-context7`

| 순서 | 도구 | 역할 |
| :--- | :--- | :--- |
| 1 | `resolve-library-id` | 증상·실패 파일 기준 **주 라이브러리 1개** |
| 2 | `query-docs` | 증상 패턴에 맞는 **디버깅·함정 질문 1~2개** (세션당 **최대 2회**) |

호출 **시점**: Phase 2 재현 확인 직후 · Phase 3 가설 **직전** (재현 0%면 escalation ladder 시도 **후** — 미재현만으로 Context7 생략 **금지**).

Descriptor Read → `CallMcpTool`.

### MCP 없음 / 실패

| 상황 | 행동 |
| :--- | :--- |
| MCP 미설치·비활성 | **실행한 검증**에 `Context7: SKIP (MCP unavailable)` — Phase 3+ **계속** |
| resolve 실패 | SKIP + §2 fallback 1회 재시도 |
| query 빈 응답 | `Context7: no match` — 추측 fix **금지** |

**always-on**: 도메인-only 버그·BE-only도 §2 fallback으로 **query-docs ≥1회** 시도.

---

## 2. 주 라이브러리 선정 (증상·실패 경로 → libraryName)

Phase 1 루프·실패 테스트·스택·`rg` Read로 좁힌 **파일/스택** 기준, **첫 매칭 1개**.

| 신호 | libraryName | query 초점 (디버그) |
| :--- | :--- | :--- |
| Next route·middleware·cookie·RSC | `Next.js` | App Router caching, cookies, server/client boundary |
| React hooks·effect·timer·stale | `React` | useEffect cleanup, strict mode double invoke, stale closure |
| vitest·RTL·MSW·fake timers | `Vitest` | vi.useFakeTimers, waitFor, mock hoisting, pool isolation |
| Playwright·e2e | `Playwright` | flakiness, auto-wait, network idle |
| FastAPI·Python API | `FastAPI` | Depends lifecycle, exception handlers, async session |
| SQLAlchemy·transaction | `SQLAlchemy` | session commit/rollback, async greenlet |
| Zustand·persist | `Zustand` | persist rehydrate race, setState timing |
| FHIR·HAPI | `HAPI FHIR` | interceptor, scope, bundle parsing |
| **매칭 없음** | `Next.js` | EMR FE — 일반 data-fetching·auth 디버깅 함정 |

버전: `package.json` major.minor → resolve version suffix 사용.

---

## 3. query-docs 작성 (디버그 템플릿)

### MUST

- **증상·API 이름만** — 스택 3줄·환자 데이터·토큰·전체 로그 붙여넣기 **금지**
- **반증 가능** — "If X then Y" 가설과 연결될 질문
- 예: `Vitest vi.useFakeTimers with setInterval — cleanup order and flakiness`  
  `React 19 useEffect strict mode double mount interval leaks`

### MUST NOT

- 루프 없이 「how to fix」만 요청 (Phase 5 선행)
- 세션당 `query-docs` **3회 초과**

```text
Library: {libraryName}
Symptom: {one line — e.g. timer fires after unmount}
Loop: {vitest file | bash N× | hub fingerprint}
Question: Known pitfalls, lifecycle, and debugging steps for {API/pattern} causing {symptom}?
```

스택 2개 이상: 주 1회 + 부 1회 (max 2 query-docs).

---

## 4. Phase 3~5 반영

| Context7 결과 | diagnose 사용 |
| :--- | :--- |
| 문서상 **known pitfall**이 코드·루프와 일치 | 가설 순위 ↑ · Root Cause evidence 1줄 `Context7: …` |
| **deprecation**이 증상 설명 | fix 방향 힌트 — **회귀 테스트 후** Phase 5 |
| 문서와 **무관** | 가설에 **올리지 않음** — 검증 표 `checked, no impact` |
| 문서만 있고 루프 **반증 안 됨** | Phase 5 fix **보류** — instrument probe 먼저 |

evidence:

```text
Context7 (/reactjs/react.dev): {한 줄} — probe: {Phase 4 plan or loop result}
```

---

## 5. 실행한 검증 표 (필수 행)

| 예시 | 의미 |
| :--- | :--- |
| `Context7 Vitest → fake timers + setInterval pitfalls — hypothesis H2` | always-on + 가설 연결 |
| `Context7 Next.js → checked, no impact` | always-on 완료 |
| `Context7: SKIP (MCP unavailable)` | fallback |

---

## 6. 스킬 경계

| 주제 | SSOT |
| :--- | :--- |
| 조사만·패치 없음 | [investigate](../../investigate/SKILL.md) |
| PR diff 리뷰 | [review](../../review/SKILL.md) |
| hub raw body | diagnose Phase 4 · [diagnose.md](../../../workflows/diagnose.md) |
| 테스트 품질 | [test-analysis](../../test-analysis/SKILL.md) |

Context7은 **외부 framework 디버그 지식** 보조 — **재현 루프가 SSOT**.
