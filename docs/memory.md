# memory.md — Bootstrap DevEnv 작업 로그

---

## [누적 요약] 2026-03-10 ~ 2026-03-15

| 날짜 | 주요 작업 |
| --- | --- |
| 2026-03-10 | PS5 BOM 파싱 오류 해결, 창 종료 원인 README 명시 |
| 2026-03-11 | 그룹 번호 재정렬(1~8), `Add-ToUserPath` 추가, Java/Android PATH 자동 등록 |
| 2026-03-14 | `check-env.ps1` 8단계 Integrity Engine 구축, `OrderedDictionary` 버그 수정 |
| 2026-03-14 | Config 외부화: `config/paths.ps1`, `config/packages.json`, `.env.example` 신규 생성 |
| 2026-03-14 | `AI_GUIDELINES.md` 마스터 가이드라인 승격, CLAUDE.md 상속 구조 도입 |
| 2026-03-14 | Supabase CLI 자동 설치 제거 → npm 수동 설치 가이드로 대체 |
| 2026-03-14 | `Bootstrap-DevEnv.ps1` Git Identity 대화형 설정 로직 추가 |
| 2026-03-15 | Terminal Protocol 정밀화: NoProfile, 체이닝 금지, TERMINAL_RECOVERY_MARKER, Self-Verification |
| 2026-03-15 | Safe Raw IO 수칙 추가(`Test-Path` + Null 인덱싱 방지), PS Boolean 오용 사례 명문화 |
| 2026-03-15 | `CRITICAL_LOGIC.md` Terminal Protocol 및 Coding Rules SSOT 반영 후 Git Push |

**안정 상태**: `AI_GUIDELINES.md` 82줄 / `CRITICAL_LOGIC.md` 최신화 / `Bootstrap-DevEnv.ps1` ~350줄

---

## [2026-03-16] AI_GUIDELINES.md — Terminal Protocol Architect Version 통합

### 작업 내용

| 파일 | 변경 내용 |
| --- | --- |
| `AI_GUIDELINES.md` | Terminal Protocol 8개 신규 항목 흡수 (82줄 → 127줄) |
| `docs/plans/strengthen_ai_guidelines.md` | 블루프린트 생성 및 Task 1~8 전체 실행 완료 |

### 반영된 항목 (Gap Analysis 기준)

| # | 항목 | 위치 |
| --- | --- | --- |
| 1 | 세션 초기화 완전화: `InputEncoding`, `PSDefaultParameterValues`, `Clear-Host` | Section 2 |
| 2 | Cmdlet 파라미터 Pre-Validation (`ContainsKey()` 패턴) | Section 2 |
| 3 | 설정 파일 기반 의사결정 (`tsconfig.json`, `package.json`, `node_modules` 확인) | Section 2 |
| 4 | 컨텍스트 캐싱 원칙 + 파일 메타데이터 해시 경량 대조 | Section 2 |
| 5 | Catch Block Hygiene (TS6133 방지) + Import Zero-Tolerance | Section 5 |
| 6 | 긴급 복구 SOP 3단계 (RECOVERY_MARKER, `-NoProfile`, 로그 파일 우회) | Section 8 |
| 7 | Linux→PowerShell 명령어 매핑 테이블 (7항목) | Section 2 |

### 진행 상황

- [x] Task 1~7: AI_GUIDELINES.md 항목 통합 (Edit × 7)
- [x] Task 8: 최종 검토 — 127줄, 중복 없음
- [/] `/git` 워크플로우 실행 중
