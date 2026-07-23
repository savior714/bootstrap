# Architecture

## 1. 목적

이 저장소는 특정 애플리케이션의 규칙 모음이 아니라,
여러 저장소가 소비할 수 있는 **versioned agent harness template**다.

긴 프롬프트를 반복 생성하는 대신, stable contract를 각 저장소에 설치하고
개별 작업은 delta-only prompt로 수행한다.

## 2. 소유권 모델

### Template-managed core

Copier update가 관리한다.

- `AGENTS.md`
- `.agent-harness.yml`
- `agents/registry/CONTEXT_ROUTING.md`
- `agents/workflows/git.md`
- `agents/prompts/TASK_DELTA_TEMPLATE.md`

### Project-owned overlay

초기 생성 후 각 프로젝트가 관리한다.

- `agents/project/PROFILE.md`
- `docs/product/ACTIVE_SCOPE.md`

`copier.yml`의 `_skip_if_exists`가 overlay 파일을 보존한다.
공통 template는 프로젝트 고유 아키텍처·명령·도메인 정책을 직접 덮어쓰지 않는다.

## 3. Core 승격 기준

다음 조건을 모두 만족할 때만 universal core에 규칙을 추가한다.

1. 독립된 두 프로젝트에서 같은 failure pattern이 반복됨
2. 프로젝트명·프레임워크·도메인을 제거해도 의미가 유지됨
3. binary criterion으로 검증 가능함
4. 기존 core 규칙과 충돌하지 않음
5. context 비용보다 재발 방지 효과가 큼

그 외 규칙은 optional module 또는 project overlay에 둔다.

## 4. Capability 기반 구성

기술 스택보다 운영 capability를 질문한다.

- authenticated runtime 또는 visual acceptance가 있는가
- database와 migration이 있는가
- 콘텐츠 provenance가 필요한가
- 규제·안전 도메인인가
- 실제 lint/typecheck/targeted/release command는 무엇인가

초기 foundation은 universal core만 생성한다.
Optional module은 각 module의 독립 검증이 준비된 뒤 추가한다.

## 5. 검증 계층

### Template source

- `copier.yml` parse
- Jinja parse
- template path integrity
- template-managed/project-owned ownership audit

### Render smoke

최소 두 profile을 렌더링한다.

- 단순 프로젝트: optional capability 모두 false
- 복합 프로젝트: capability 모두 true

판정:

- render 성공
- `.copier-answers.yml` 생성
- 미치환 Jinja/placeholder 없음
- Markdown 참조 경로 존재
- project overlay update 보존

### Consumer project

각 소비 프로젝트는 별도 atomic migration으로 도입한다.
template 저장소 변경과 consumer migration을 한 failure domain에 묶지 않는다.

## 6. Versioning

- patch: 문구·오탐·validator 수정
- minor: optional module 추가
- major: Git, ownership, closure 또는 evidence 의미 변경

이미 사용한 tag는 이동하지 않는다.
신규 생성과 update는 stable tag를 명시한다.

## 7. Legacy migration

기존 v1 경로는 v2가 검증되기 전까지 보존한다.

```text
manifest.json
bootstrap.sh
templates/
```

migration 순서:

1. v2 foundation
2. render validator
3. study pilot
4. EMR pilot
5. v1 deprecation notice
6. 별도 작업에서 legacy 제거 여부 결정
