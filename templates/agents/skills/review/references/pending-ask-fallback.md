# pending_ask fallback (Close when AskQuestion unavailable)

메인 Cursor 채팅에서는 **AskQuestion/`question` tool call**이 close SSOT입니다.  
Task subagent·일부 runtime에 도구가 **없으면** 아래 `pending_ask`로 **동일 수렴 의도**를 남깁니다 — eval·handoff·로컬 LLM 리포트 export 공통.

> **금지**: close 옵션 없이 종료 · 권장 수정 요약과 `recommended` 불일치 · `(권장)` 2개 이상

---

## 1. 언제 쓰는가

| 상황 | close 방식 |
| :--- | :--- |
| AskQuestion/`question` **호출 가능** | tool call (SKILL §Close turn) |
| 도구 **미노출**·호출 **실패** | `report.md` **YAML frontmatter** `pending_ask` (본 절 §2) |
| 채팅-only 리뷰 | tool call 우선; 실패 시 frontmatter **+** 본문 `## Close (pending_ask)` 중복 허용 |

`tool_log.json`에 `askquestion_attempts: [{ "status": "skipped"|"failed", "reason": "..." }]` 기록.

---

## 2. report.md frontmatter (MUST)

리뷰 본문 **맨 위**에 YAML frontmatter. 옵션·`(권장)`·마무리 슬롯은 SKILL §Close turn 표와 **동일**.

### 일반 `/review` · 실질 이슈 **있음**

```yaml
---
pending_ask:
  recommended: "지금 바로 소규모만 고치기"   # §권장 수정 요약과 일치하는 action 한 줄
  reason: "High 1건 domain 국소 수정 가능"   # 10단어 이내
  options:
    - label: "지금 바로 소규모만 고치기 (권장)"
      action: fix-first
    - label: "리뷰·수정 범위 더 discuss하기"
      action: discuss
    - label: "권장 수정을 실행 계획(Blueprint)으로 정리하기"
      action: plan
    - label: "여기서 마무리"
      action: close
---
```

`(권장)`이 Blueprint면 1번 슬롯을 Blueprint로, **마무리는 항상 마지막**.

### 일반 · 실질 이슈 **없음**

```yaml
---
pending_ask:
  recommended: "여기서 마무리"
  reason: "High/Medium 없음"
  options:
    - label: "여기서 마무리 (권장)"
      action: close
    - label: "다른 변경 범위 리뷰"
      action: review-other
---
```

### Post-execute (plan Execute 직후)

Blueprint `(권장)` **금지** — SKILL §Post-execute close 옵션:

```yaml
---
pending_ask:
  recommended: "지금 바로 소규모만 고치기"
  reason: "Execute 직후 국소 fix"
  post_execute: true
  options:
    - label: "지금 바로 소규모만 고치기 (권장)"
      action: fix-first
    - label: "리뷰·수정 범위 더 discuss하기"
      action: discuss
    - label: "Findings를 새 실행 계획으로 정리하기"
      action: plan-new-slug
    - label: "여기서 마무리"
      action: close
---
```

---

## 3. 본문 duplicate (권장)

frontmatter 외에 Findings·권장 수정 요약 **아래** 짧은 섹션:

```markdown
## Close (pending_ask)

AskQuestion 미노출 — 위 frontmatter `pending_ask`와 동일. 권장: **{recommended}** — {reason}
```

채팅 턴에서는 **AskQuestion 성공 시** frontmatter 생략 가능.

---

## 4. action 값 (고정)

| action | 의미 |
| :--- | :--- |
| `fix-first` | 소규모 즉시 fix |
| `discuss` | `/discuss` |
| `plan` | same-session Blueprint |
| `plan-new-slug` | Post-execute 새 slug PLAN |
| `close` | 마무리 |
| `review-other` | 다른 diff `/review` |

---

## 5. Final check

- [ ] `recommended` ↔ 권장 수정 요약 **일치**
- [ ] `(권장)` **1개**, 마무리 **마지막**(이슈 있을 때)
- [ ] Post-execute면 Blueprint가 1번 `(권장)` **아님**
