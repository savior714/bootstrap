---
situation: 무코드 방향 합의
# trigger: /discuss  ← catalog metadata only; Read this file before executing (error_patterns §16.1)
level: Recommended
description: 코드 변경 없이 프로젝트 전체 파악 → AskQuestion(`question` 병용) → DISCUSS 노트 (조사 게이트 스킵·fallback·메뉴 A/B, assess 없음)
version: 1.1.4
last_updated: 2026-06-14
scope: workflow
domain: workflow
---
<!-- Language: ko -->

# Discuss (`/discuss`)

**프로토콜 SSOT**: [.agents/skills/discuss/SKILL.md](../skills/discuss/SKILL.md) — 실행 전 Read.

**코드를 건드리지 않고** 프로젝트 전체를 둘러보며 **개선 방향**을 대화로 합의한다. 산출물은 [docs/discussions/](../../docs/discussions/) 하위 `DISCUSS_*.md`. 방향·범위 확정 후 → [/plan](plan.md). feature 정밀 분석 → [/assess](assess.md) **별도**(discuss 메뉴에 넣지 않음).

## Reference (SKILL에서 lazy Read)

| 시점 | 파일 |
| :--- | :--- |
| 매 AskQuestion 전 | [turn-decision-tree.md](../skills/discuss/references/turn-decision-tree.md) — §턴 판별 · §Typed Answer · §도구 불가 fallback |
| scan/direction 본 분기 | [askquestion-two-turn-examples.md](../skills/discuss/references/askquestion-two-turn-examples.md) |
| converge / close / plan 핸드오프 | [close-handoff.md](../skills/discuss/references/close-handoff.md) |
| Blueprint 허용 판단 | [ambiguity-zero-gate.md](../skills/discuss/references/ambiguity-zero-gate.md) |
| 질문·라벨·엣지 뱅크 | [plain-language-questions.md](../skills/discuss/references/plain-language-questions.md) |

## Anti-pattern at write (요약)

- **증상**: 사용자 선택 없이 종료, mermaid/긴 표, 텍스트 A/B/C만 제시, 구체 스코프인데 조사 게이트만 던지기.
- ❌ WRONG: `AskQuestion`/`question`(병용) 없이 handoff·close · converge에서 «계획으로» `(권장)` · handed-off에 Blueprint 재안내 · 메뉴 B에 Task 1.1만.
- ✅ CORRECT: close 턴 마지막에 표준 메뉴 A/B로 수렴, 본문 18줄 이내; converge «계획» 후 same-session plan → 메뉴 B만.
- 포맷 SSOT: [`docs/agent-context/ANTI_PATTERN_FORMAT.md`](../../docs/agent-context/ANTI_PATTERN_FORMAT.md)

## 철칙 요약 (상세는 SKILL)

1. **Anti-rush** — `[열림]` 0개·방향만 잡혀도 «계획으로» `(권장)` 금지; Ambiguity-Zero 7/7·사용자 종료 신호 전까지 합의 쌓기.
2. **무코드** — 소스 수정 금지, `DISCUSS_*.md`만 편집.
3. **한 턴 = 한 결정** — 옵션 시 `AskQuestion`/`question`(병용) 필수; 도구 불가 시 **fallback 3종**(`pending_ask` + 채팅 최소 형식).
4. **조사 게이트** — scan/direction 턴1 `research-gate` → 턴2 본 AskQuestion; **스코프 이미 좁으면 스킵 MAY**(화면·경로·DISCUSS·증상+영역).
5. **권장 + 이유** — §1·[확정] 우선 2단계 `(권장)`; `direction`·`converge`마다 «이번 discuss에서 끝까지: …» 인용.
6. **옵션 순서** — 2단계 선정 **후** `(권장)` **항상 1번**, **마무리 항상 마지막** (`options[]` 재정렬; plain-language 역할≠표시 슬롯).
7. **엣지 선제** — direction 중 2~3턴마다 예외·빈 상태 등 1턴; §3 엣지 → plan Trace 이관.
8. **표준 메뉴** — 텍스트 close·산출물·재진입 = 메뉴 A/B; **메뉴 B 3옵션**(PLAN 전체 · 새 주제 · 마무리); assess·Task 1.1만 **금지**.
9. **텍스트 답 = 유효 선택** — [turn-decision-tree.md §Typed Answer](../skills/discuss/references/turn-decision-tree.md).
