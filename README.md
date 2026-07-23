# Agent Harness Bootstrap

새 프로젝트와 기존 프로젝트에 **짧고 일관된 repository-native agent workflow**를 설치하고,
버전 단위로 업데이트하기 위한 Copier template 저장소입니다.

## 현재 전환 상태

이 저장소에는 두 세대가 공존합니다.

### v2 — canonical, 개발 시작

```text
copier.yml
template/
docs/ARCHITECTURE.md
chatgpt/PROJECT_INSTRUCTIONS.md
```

v2의 목표:

- 공통 계약을 저장소 문서로 이전
- 한 작업 = 한 failure domain = 한 가설 = 한 판정 기준
- targeted validation과 release validation 분리
- main-only Git, dirty ownership, overlap 기반 remote advance
- source task와 runtime acceptance 분리
- template-managed core와 project-owned overlay 분리
- Copier answers와 Git tag를 이용한 재현 가능한 생성·업데이트

### v1 — legacy, 당분간 보존

```text
manifest.json
bootstrap.sh
templates/
```

v1은 EMR live governance를 export하는 기존 설치기입니다.
v2가 생성·업데이트 smoke test를 통과하고 실제 프로젝트 migration이 완료될 때까지 삭제하지 않습니다.

## v2 디렉터리

| 경로 | 역할 |
|---|---|
| `copier.yml` | Copier 설정과 capability 질문 |
| `template/AGENTS.md.jinja` | 생성 프로젝트의 always-on 실행 계약 |
| `template/.agent-harness.yml.jinja` | machine-readable project manifest |
| `template/agents/registry/CONTEXT_ROUTING.md.jinja` | 경로·의미 기반 최소 context routing |
| `template/agents/workflows/git.md.jinja` | main-only Git·dirty·overlap 계약 |
| `template/agents/project/PROFILE.md.jinja` | project-owned overlay |
| `template/agents/prompts/TASK_DELTA_TEMPLATE.md` | 짧은 작업 프롬프트 형식 |
| `template/docs/product/ACTIVE_SCOPE.md.jinja` | 프로젝트 활성 범위 |
| `docs/ARCHITECTURE.md` | 설계와 migration 원칙 |
| `chatgpt/PROJECT_INSTRUCTIONS.md` | ChatGPT 프로젝트 설정용 지침 |

## 생성 예시

첫 stable tag가 발행되기 전에는 로컬 checkout에서 smoke test만 수행합니다.

```bash
uvx copier copy \
  --vcs-ref main \
  /path/to/bootstrap \
  /tmp/bootstrap-smoke
```

stable release 이후:

```bash
uvx copier copy \
  --vcs-ref v2.0.0 \
  gh:savior714/bootstrap \
  /path/to/new-project
```

생성 프로젝트는 `.copier-answers.yml`을 Git에 보존해야 이후 `copier update`가 가능합니다.

## 개발 순서

1. **Foundation** — Copier config와 universal core
2. **Validator** — YAML/Jinja/render/contract 검증
3. **Optional modules** — runtime-visual, database-migration, content-provenance, regulated-domain
4. **Pilot migration** — `savior714/study`
5. **Second pilot** — `savior714/emr`
6. **Stable release** — SemVer tag와 update contract

한 단계는 하나의 failure domain으로 진행합니다.

## ChatGPT 프로젝트

ChatGPT 사이드바에서 `Bootstrap` 프로젝트를 수동 생성하고,
`chatgpt/PROJECT_INSTRUCTIONS.md` 내용을 프로젝트 지침에 넣습니다.
이 저장소와 관련된 기존 채팅은 해당 프로젝트로 이동해 컨텍스트를 모읍니다.

ChatGPT UI 프로젝트 생성은 GitHub repository 작업과 별도이며 자동화하지 않습니다.
