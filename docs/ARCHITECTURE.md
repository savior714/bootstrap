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

`.agent-harness.yml` 은 template-managed machine-readable structure, Git, capability, context metadata 를 소유한다.
실행 command 는 소유하지 않는다.

### Project-owned overlay

초기 생성 후 각 프로젝트가 관리한다.

- `agents/project/PROFILE.md`
- `agents/project/runtime-visual/PROFILE.md` — `has_runtime_visual=true` 프로젝트
- `docs/product/ACTIVE_SCOPE.md`

`copier.yml`의 `_skip_if_exists`가 overlay 파일을 보존한다.
공통 template는 프로젝트 고유 아키텍처·명령·도메인 정책을 직접 덮어쓰지 않는다.

실행 command 는 `agents/project/PROFILE.md` 만 소유한다.
`.agent-harness.yml` 에 실행 command 를 중복 저장하지 않는다.

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

## 7. Legacy v1 deprecation boundary

### Status

- v1 은 deprecated 다.
- v1 은 compatibility-only 다.
- Copier v2 가 신규 프로젝트의 canonical 경로다.

### Retained paths

```text
manifest.json
bootstrap.sh
templates/
```

### 허용되는 v1 유지보수

- 기존 EMR bootstrap 호환성을 깨는 명확한 회귀 수정
- 보안 또는 데이터 무결성 문제 수정
- v1 자체의 실행 불능을 복구하는 최소 수정

### 금지되는 v1 개발

- 신규 프로젝트에서 v1 사용
- 신규 capability 추가
- v2 기능의 routine backport
- v1/v2 구조의 지속적인 동기화
- 설명 정리를 이유로 한 실행 로직 refactor

### Archive 의미

현재 archive 는 물리적 이동이 아니라 논리적 archival 상태다.
파일과 templates/는 기존 경로에 그대로 둔다.

### 제거 gate

다음 조건을 모두 만족하기 전에는 v1 을 삭제하거나 이동하지 않는다.

- 기존 EMR consumer migration 완료
- EMR 에서 v1 bootstrap 의존성이 제거되었다는 별도 검증
- legacy 제거를 다루는 별도 failure domain 승인

이 문서 변경이 v1 제거 승인을 의미하지 않는다.
