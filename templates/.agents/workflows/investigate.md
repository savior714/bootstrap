---
situation: "버그 원인 파악 및 디버깅"
# trigger: /investigate  ← catalog metadata only; Read this file before executing (error_patterns §16.1)
level: Recommended
description: "경량 조사 — 에이전트 직접 실행·hub/DB 조회 (수정·루프 작성은 diagnose)"
version: 1.3.0
last_updated: 2026-06-13
scope: workflow
domain: workflow
---

<!-- Language: ko -->

# Investigate (`/investigate`)

**프로토콜 SSOT**: [.agents/skills/investigate/SKILL.md](../skills/investigate/SKILL.md) — 실행 전 Read.

**경계**: 재현 루프·수정·회귀 테스트 → [`/diagnose`](diagnose.md). PR 리뷰 → [`/review`](review.md).

## 언어 정책 (MUST)

- `/investigate` 세션의 **모든 채팅 응답은 한국어**로 작성한다.
- 가설·신호·다음 단계 보고 형식도 한국어 섹션 제목·본문을 따른다.
- 코드·로그·경로·식별자는 영문 유지 가능. **영문-only 단락·결론은 금지**.

## Handoff

| 상황 | 다음 |
| :--- | :--- |
| 수정·루프·회귀 테스트 필요 | `/diagnose` |
| 구조·모듈 깊이 이슈 | `/improve-codebase-architecture` 또는 `/plan` |
| 조사만으로 충분 | 사용자 확인 후 종료 |
