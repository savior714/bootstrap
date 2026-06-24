# pending_ask fallback (diagnose Close)

AskQuestion/`question` **미노출·실패** 시 close 수렴. 공통 YAML·슬롯 규칙: [review/pending-ask-fallback.md](../../review/references/pending-ask-fallback.md) §1·§2·§4.

diagnose **action**·옵션 라벨만 아래 SSOT.

---

## Fix 완료 (Phase 6 직후)

```yaml
---
pending_ask:
  recommended: "마무리"
  reason: "루프 PASS·회귀 테스트 Green"
  options:
    - label: "마무리 (권장)"
      action: close
    - label: "spec sync / knowledge-asset 이어하기"
      action: sync
    - label: "관련 테스트 품질 점검"
      action: test-analysis
---
```

`(권장)`이 sync면 1번 슬롯을 sync로.

---

## 미재현·원인 미확정 (§Escalation Close)

```yaml
---
pending_ask:
  recommended: "CI 실패 로그 URL/스크린 붙여주시면 이어서 조사"
  reason: "로컬 0% flake·CI fingerprint 필요"
  options:
    - label: "CI 실패 로그 URL/스크린 붙여주시면 이어서 조사 (권장)"
      action: investigate-resume
    - label: "bash 100회 더 돌려 flake rate 측정"
      action: escalation-loop
    - label: "지금은 여기서 마무리 (시도 로그만)"
      action: close
---
```

---

## Investigate 모드 종료 (수정 금지)

```yaml
---
pending_ask:
  recommended: "마무리"
  reason: "원인·범위 보고 완료"
  options:
    - label: "마무리 (권장)"
      action: close
    - label: "고정 원하면 diagnose 이어하기"
      action: diagnose
---
```

`tool_log.json` `askquestion_attempts` 기록. eval·subagent 리포트는 **항상** frontmatter.
