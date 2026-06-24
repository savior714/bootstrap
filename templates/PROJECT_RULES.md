# PROJECT_RULES.md — Policy Hub (Bootstrap Kernel)

## 0. Purpose
본 문서는 프로젝트 정책·스택·품질·아키텍처 제약(What)을 정의한다.
에이전트 실행 방식은 `AGENTS.md`를 따르며, 도메인별 세부 규칙은 프로젝트가 `agents/domains/`에 추가할 때 위임한다.

---
# 1. Architecture Rules
프로젝트 아키텍처·의존 방향·레이어 규칙을 여기에 기입한다. DDD·클린 아키텍처 등을 쓸 경우 `agents/domains/backend/` 등에 상세 규칙을 두고 본 절에서 pointer만 둔다.

---
# 2. Stack & Runtime Policy
**프로젝트가 설치 후 반드시 기입할 placeholder 스택 SSOT.**

| 항목 | 기입 예시 |
| :--- | :--- |
| 프로젝트명 | `{{PROJECT_NAME}}` |
| 프론트엔드 경로 | `{{FRONTEND_APP_PATH}}/` |
| 백엔드 포트 | `:{{BACKEND_PORT}}` |
| 로컬 dev URL | `{{FRONTEND_DEV_URL}}` |
| 패키지 스코프 | `{{NPM_SCOPE}}/` |

Tech stack allowlist·런타임 아키텍처 명세는 `docs/specs/technical/` 또는 `docs/ops/rules/`에 프로젝트가 추가한다.

---
# 3. Verification & Quality Policy
- **Plan-First**: 복합 작업 전 `/plan`·`just plan-lint` PASS — [planning.md](agents/core/planning.md) · [AGENTS.md §2.2](AGENTS.md).
- **TDD Red-First**: 구현 전 실패 테스트 — 프로젝트가 `agents/domains/testing/tdd.md`를 추가하면 따른다.
- **Strict Lint/Type**: 프로젝트 스택의 linter·type checker 통과 필수. 우회 금지.
- **Code Quality Lifecycle**: 설계·구현·리뷰·테스트 시점별 체크 — [agents/core/code_quality_lifecycle.md](agents/core/code_quality_lifecycle.md).
- **Risky Operations (HITL)**: 삭제·배포·`git push` 등 되돌리기 어려운 에이전트 작업은 사용자 승인 후 실행.
- **Information Integrity & Honesty**: 확인 전 단정 금지 — [execution.md](agents/core/execution.md) §2.10.
- **Recommendation Accountability**: **아키텍처·스택·워크플로·보안 정책 변경**을 제안할 때만 rationale·risk·evidence URL 3항을 포함한다.

---
# 4. Frontend & Security Policy
프론트엔드·보안 domain MUST는 프로젝트가 `agents/domains/frontend/` · `agents/domains/<security>/` 등에 추가한다.

### 4.1 에이전트·채널 시크릿 (ZERO-LEAK, 재발 금지)
**최우위 강제**: 에이전트·자동화·도구 출력으로 **API 키·액세스 토큰·비밀번호·`.env` 등 비밀값 원문** 노출을 **절대 금지**한다.
- **MUST NOT**: `.env`, 키·토큰 파일을 읽어 응답·도구 결과에 포함하는 행위.
- **MUST**: 비밀값이 필요하면 사용자에게 안전한 제공 경로를 먼저 묻는다.
- **MUST**: 쉘에서 키를 쓸 때 echo·print·로그에 절대 쓰지 않는다.
- **유출 의심 시**: 값을 반복 인용하지 말고 **즉시 키 회전**을 안내한다.
실행 절차 SSOT: [agents/core/execution.md](agents/core/execution.md) §2.9

---
# 5. Documentation & Communication
한국어 우선·Language Gate·SSOT 보존 — 프로젝트가 `agents/domains/documentation/markdown.md`를 추가하면 따른다.

---
# 6. SSOT Hub
| Purpose | SSOT |
|---|---|
| Project overview | `README.md` |
| Execution protocol | `AGENTS.md` |
| Project policy | `PROJECT_RULES.md` |
| Requirements contract | `tests/` |
| Session memory | `docs/agent-context/memory/` |
| Rule registry | [agents/registry/RULE_INDEX.md](agents/registry/RULE_INDEX.md) |

---
# 8. Licensing & Open Source Policy
- **License Purity**: SSPL·BSL 등 폐쇄적 라이선스 스택 도입을 원칙적으로 금지한다.
- **Exceptions**: 필수 도입 시 심층 분석 문서를 `docs/knowledge/research/`에 저장하고 사용자 승인 후 도입한다.
