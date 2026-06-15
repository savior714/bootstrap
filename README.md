# Bootstrap Kernel Package (SSOT)

`Desktop/Dev/bootstrap`는 **설치 키트의 단일 원본(SSOT)** 입니다.  
EMR 저장소(`../emr`)의 거버넌스·검증 커널을 `templates/`로 동기화해, `game` 등 다른 프로젝트에 이식합니다.

## 디렉터리 역할

| 경로 | 역할 |
| :--- | :--- |
| `manifest.json` | 동기화 대상·placeholder 정책 SSOT |
| `templates/` | `bootstrap.sh`가 복사하는 설치 키트 |
| `bootstrap.sh` | 대상 프로젝트 루트에 템플릿 설치 |
| `Justfile.snippet` | `templates/` 안 — 대상 `Justfile`에 병합 |

> EMR repo 안의 `emr/dev/bootstrap`는 **사용하지 않습니다** (제거됨). symlink 없음.

## 유지보수 (EMR 저장소에서 실행)

```bash
cd ../emr

# 변경 예상만 보기
just bootstrap-sync

# ../bootstrap/templates 갱신
just bootstrap-sync apply=1

# CI/PR — drift 검사
just bootstrap-sync check=1
```

동기화 실행기: [`../emr/scripts/bootstrap/sync.py`](../emr/scripts/bootstrap/sync.py)  
소스: EMR live (`AGENTS.md`, `.agents/core/`, `verify.sh` 등) → 출력: `../bootstrap/templates/`

## 새 프로젝트에 설치

```bash
/path/to/Dev/bootstrap/bootstrap.sh /path/to/new-project
cd /path/to/new-project
# Justfile.snippet 병합 + {{PLACEHOLDER}} 치환 후
just verify
```

예: game 프로젝트

```bash
../bootstrap/bootstrap.sh ../game
```

> **주의**: 대상 repo 루트의 **옛 `bootstrap.sh`(safe_copy 스캐폴드)** 는 쓰지 마세요.  
> SSOT는 `../bootstrap/bootstrap.sh` (rsync + `uv sync`) 입니다.  
> pytest는 `uv run pytest` — `pip install pytest` 불필요.

## 포함 범위

| 영역 | 설명 |
| :--- | :--- |
| `AGENTS.md`, `PROJECT_RULES.md` | 거버넌스 진입점 (placeholder) |
| `.agents/core` | 실행 규칙 |
| `.agents/registry/` (4종 md) | 커널 subset 색인 — 미동기화 워크플로·스킬 참조 없음 |
| `verify.sh`, `scripts/verify/` | 검증 커널 |
| `tools/tdd_gate_plugin.py` | Red-first TDD 게이트 |
| `docs/design.md` | 디자인 토큰 starter (없을 때만 seed) |

**미포함**: EMR 의료 도메인, `PROJECT_SKILL_ROUTING.json`, 앱 소스.

## 설치 후 체크리스트

### 1. Placeholder 치환

| Placeholder | 예시 |
| :--- | :--- |
| `{{PROJECT_NAME}}` | `AidenGame` |
| `{{FRONTEND_APP_PATH}}` | 프로젝트 프론트 경로 |
| `{{BACKEND_PORT}}` | `8000` |

```bash
rg '\{\{[A-Z_]+\}\}' AGENTS.md PROJECT_RULES.md Justfile.snippet docs/ .agents/ || echo "placeholder 없음"
```

### 2. Justfile.snippet 병합

`verify` / `ci` / `lint-turn-end` 레시피를 프로젝트 `Justfile`에 합칩니다.

### 3. 검증

```bash
just verify
```

## 주의

- 민감 정보는 `sync.py`가 export 전 차단합니다.
- 큰 diff 시 EMR `/bootstrap` 워크플로에 따라 사용자 확인 후 `apply=1` 하세요.

## 프로젝트 SSOT (seed-only)

설치 시 **파일이 없을 때만** seed 됩니다 — 기존 프로젝트 파일은 덮어쓰지 않습니다.

| 경로 | 설명 |
| :--- | :--- |
| `docs/design.md` | 디자인 토큰 starter (범용 팔레트·호출 규칙 — EMR 와이어프레임 미포함) |
| `docs/agent-context/memory/MEMORY.md` | 세션 SSOT 인덱스 (≤200줄) |
| `docs/agent-context/memory/changelog/` | 오래된 세션 로그 아카이브 |
| `docs/agent-context/memory/PROJECT_REFACTORING_BACKLOG.md` | discuss 앵커용 백로그 |

소스: EMR `scripts/bootstrap/scaffold/docs/design.md` (live `docs/design.md` 아님).

`docs/memory/` (구버전)가 있으면 내용을 `MEMORY.md`로 옮긴 뒤 삭제하세요.
