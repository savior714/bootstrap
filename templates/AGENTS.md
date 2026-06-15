# AGENTS.md — Unified Execution Constitution (Bootstrap Kernel)

에이전트 **헌법 요약**입니다. 우선순위·게이트·레지스트리 진입점만 둡니다. 표·긴 스킬 목록은 레지스트리 파일로 위임합니다.

---

## 0. Priority / Rule Precedence

우선순위는 아래와 같습니다.

1. `PROJECT_RULES.md`
2. 본 문서 (`AGENTS.md`)
3. `.agents/core/*.md`
4. `.agents/domains/**/*.md` (프로젝트가 추가한 경우)
5. 기타 명세 및 가이드라인

충돌 시 위 순서를 따르며, 불명확하면 질문합니다.

---

## 1. Core Operating Principles

normative SSOT: [.agents/core/principles.md](.agents/core/principles.md)

- **Policy**: [PROJECT_RULES.md §3](PROJECT_RULES.md)
- **Think Before Coding · Quick Pick**: [principles.md §1.1](.agents/core/principles.md#11-think-before-coding)
- **Simplicity · Surgical · Goal-Driven**: [principles.md §1.2–§1.4](.agents/core/principles.md#12-simplicity-first)
- **Bug Fixes**: [/diagnose](.agents/workflows/diagnose.md) · [/investigate](.agents/workflows/investigate.md)
- **Merge & Review**: [/review](.agents/skills/review/SKILL.md)
- **Execution Rules**: [execution.md §2](.agents/core/execution.md)
- **Commit Gate Failure**: [error_patterns.md §10](.agents/core/error_patterns.md#10-커밋-게이트-실패시--no-verify-금지) — `--no-verify` 우회 절대 금지, 반드시 오류 수정 후 재시도
- **Edit Tool Schema**: [routing.md §1.1](.agents/core/routing.md#11-file-edit-tool-schema-편집-도구-ssot) (Cursor) · Tri-Runtime: [runtime_edit_tools.md](.agents/core/runtime_edit_tools.md) (Cursor · OpenCode · Antigravity)
- **Workaround Accountability**: [principles.md §1.6](.agents/core/principles.md#16-workaround-accountability--close-turn-reflection)
- **Code Quality Lifecycle** (설계→구현→리뷰→테스트): [code_quality_lifecycle.md](.agents/core/code_quality_lifecycle.md)

---

## 2. Execution Gates (pointer)

**메타 금지 11** normative SSOT: [error_patterns.md#메타-금지-11](.agents/core/error_patterns.md#메타-금지-11) (`always_apply`).

### 2.1 Editing / Routing

**규범 SSOT**: [routing.md](.agents/core/routing.md) §1 · §2. **WRONG/CORRECT 예시**: [error_patterns §1](.agents/core/error_patterns.md#1-파일-편집-실수) lazy-load.

**부분 수정 호출 전 (always-on, tri-runtime)**: 호스트 **읽기 도구**로 디스크 최신본 확보 → 대상 문자열이 파일에 **정확히 1번**인지 확인 → **old ≠ new** (같으면 호출 금지). `"No changes to apply"` 수신 시 동일 쌍 재호출 금지 → 재읽기 → 목표 내용 있으면 완료, 없으면 old/범위/new 변경 후 1회만 재시도. **도구 이름·키**: [runtime_edit_tools.md §1](.agents/core/runtime_edit_tools.md) (Cursor `StrReplace`/`old_string` · OpenCode `edit`/`oldString` · Antigravity `replace_file_content`/`TargetContent`). Terminal Response: [routing.md](.agents/core/routing.md) (Cursor) · [opencode_tools.md §edit](.agents/core/opencode_tools.md) (OpenCode).

### 2.2 Plan / Blueprint

- **Plan First**: 복합 작업은 `just plan-lint` PASS 전 구현 착수 금지 — [PROJECT_RULES.md §3](PROJECT_RULES.md) · [planning.md](.agents/core/planning.md).
- **Task closeout**: Blueprint Task `Status`/`Conclusion`은 **`just plan-task-close` CLI만** — 에디터 직접 수정 **절대 금지** — [plan.md §1.10](.agents/workflows/plan.md) · [error_patterns/detail/blueprint.md §5.6](.agents/core/error_patterns/detail/blueprint.md#56-task-statusconclusion-에디터-직접-수정).
- **DoD 재귀 금지**: DoD 섹션에 `just plan-close`를 verify 명령어로 포함하지 않음 — `plan_close_gate.py`가 이를 추출해 자기 자신을 호출하는 재귀 타임아웃을 유발함 — [error_patterns/detail/blueprint.md §5.7](.agents/core/error_patterns/detail/blueprint.md#57-dod에-just-plan-close-폰리만-폰리마이스통).
- **Archive**: `docs/plans/` 파일 이동 시 **반드시** [`.agents/workflows/archive.md`](.agents/workflows/archive.md) 먼저 Read → `scripts/archive_plans.py` 실행 — 수동 복사/삭제 **절대 금지** — [archive.md §실행 절차](.agents/workflows/archive.md).
- 상세: [planning.md](.agents/core/planning.md) · [workflows/plan.md](.agents/workflows/plan.md) · [archive.md](.agents/workflows/archive.md).

---

## 3. Dynamic Rules & Loading

**세션 시작**: `PROJECT_RULES.md` + [MEMORY.md](docs/agent-context/memory/MEMORY.md) 인덱스. **lazy** (편집·route 직전): [LOAD_ORDER.md](.agents/registry/LOAD_ORDER.md) Phase 2 · [CONTEXT_ROUTING.md](.agents/registry/CONTEXT_ROUTING.md) · `ROADMAP.md` (plan·roadmap·discuss 시).

편집 직전: `just route <paths> --json --write-manifest` → `must_read` Read → `just route-read` → `just route-gate-check`.

---

## 4. Verification

검증 수준·게이트: [verification.md](.agents/core/verification.md) — 세션 종료 `just lint-turn-end`. 시점별 품질 체크: [code_quality_lifecycle.md](.agents/core/code_quality_lifecycle.md).

### 4.1 Partial Edit Tool — 한글 콘텐츠 제한 (tri-runtime)

호스트 **부분 수정 도구**는 ASCII-only JSON 파싱에 최적화됨. 한글/특수문자 본문을 그대로 넣으면 **실패**할 수 있음.

**규칙**:
- 영문/코드 변경 → 세션에 노출된 **부분 수정 도구** 사용 ([runtime_edit_tools.md §1](.agents/core/runtime_edit_tools.md))
- 한글/특수문자 대량 → [runtime_edit_tools.md §4](.agents/core/runtime_edit_tools.md) 터미널 우회
- 한글 포함 대량 콘텐츠 → `bash`/`Shell` + `cat > file << 'EOF'`

### 4.2 Test — 메시지 전역 고유성

테스트 assertion 문자열은 페이지·출력 내 **단일 요소**만 매칭되도록 고유 식별자를 포함한다. 중복 라벨과 message가 겹치지 않게 하고, 필요 시 `data-testid`를 사용한다.

### 4.3 Plan — closeout 실행 순서 (커널)

`just plan-close`는 프로젝트 DoD에 명시된 검증 레시피를 순서대로 실행한다. **기본 커널**은 Linear 연동 없이 `plan-lint-ci` + `plan-close`만으로 충분하다.

```bash
just plan-lint-ci plan=docs/plans/<file>.md   # 1. Blueprint lint (Linear 생략)
just plan-close plan=docs/plans/<file>.md     # 2. plan close gate
```

프로젝트가 Linear를 쓰면 `Justfile`에 `linear-sync` 레시피를 추가하고 closeout 순서를 확장한다.

### 4.4 Plan — Conclusion 플레이스홀더 금지

`just plan-lint`는 각 Task의 `Conclusion` 필드를 검증한다. Conclusion은 최소 **25자 이상**, 실제 검증 결과(파일명·테스트 수·명령어 결과)를 포함한다. `[완료 시 기입]` 등 플레이스홀더는 금지.

### 4.5 Justfile — DoD 레시피 실존 검증

PLAN DoD의 `just <recipe>`는 실제 justfile에 존재해야 한다. PLAN 작성 시 `just --list`로 레시피 실존을 확인한다.

---

## 5. Reference Index

- **Policy / Core**: `PROJECT_RULES.md`, `.agents/core/`
- **Registry**: `.agents/registry/RULE_INDEX.md`
- **Specs**: `docs/specs/` (프로젝트가 추가한 경우)

에이전트 규칙 SSOT는 `PROJECT_RULES.md`, `.agents/core/` 및 `AGENTS.md`입니다.

중복 방지: `.cursor/rules/` 미사용. **`.cursor/commands/*.md`는 workflow pointer만** (본문 SSOT: `.agents/workflows/`). 슬래시·키워드 카탈로그: [WORKFLOW_AND_SKILL_INDEX.md](.agents/registry/WORKFLOW_AND_SKILL_INDEX.md).
