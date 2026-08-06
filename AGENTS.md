# Bootstrap Agent Harness — Repository Execution Contract

이 저장소는 여러 프로젝트에 재사용할 repository-native agent harness를 만든다.
일반 작업은 이 문서에서 시작하고, 변경 경로에 직접 필요한 문서만 추가로 읽는다.

## 1. 우선순위

1. 현재 사용자 지시
2. 이 `AGENTS.md`
3. `docs/ARCHITECTURE.md`
4. 변경 경로와 가장 가까운 코드·테스트·문서
5. 도구 기본 동작

확인되지 않은 규칙은 추측하지 않는다.

## 2. 단일 작업 원칙

- 한 작업 = 한 failure domain = 한 검증 가능한 가설 = 한 판정 기준
- 여러 문제가 발견되면 최초 failure만 현재 작업에서 다룬다.
- 무관한 개선과 legacy 정리는 별도 작업으로 남긴다.
- 수정 전 재현 조건과 PASS/FAIL 기준을 정한다.
- 수정 후 현재 가설만 targeted validation으로 검증한다.
- 현재 작업 결과는 `PRIMARY_CRITERION + DIRECT_IMPACT_CLOSURE`로만 판정한다.
- 현재 변경이 정상이어도 실패할 수 있는 broad smoke·full suite·release gate는 현재 작업의 primary criterion으로 사용하지 않는다.
- broad verification에서 발견된 독립 실패는 현재 PASS를 취소하지 않고 `DISCOVERED_FAILURE`로 분리한다.
- `BLOCKED`는 `DECISION_REQUIRED`, primary criterion 판정 불가, semantic overlap, safety boundary 위반에만 사용한다.
- remote advance, non-fast-forward, unrelated dirty, unrelated full-suite failure와 새 독립 결함은 blocker가 아니라 재적용·게시 재시도·후속 failure domain이다.

## 3. Canonical architecture

### v2 canonical

- `copier.yml`: 질문과 Copier 설정 SSOT
- `template/`: 신규 프로젝트에 렌더링되는 template-managed core
- `docs/ARCHITECTURE.md`: core/overlay/versioning 설계
- `chatgpt/PROJECT_INSTRUCTIONS.md`: ChatGPT 프로젝트용 지침 원본

### v1 legacy

다음 경로는 기존 EMR export 설치기다.

- `manifest.json`
- `bootstrap.sh`
- `templates/`

명시적인 migration 작업 전에는 삭제·대규모 수정하지 않는다.
v2 구현에 필요한 내용을 legacy에서 복사하더라도 EMR 고유 규칙을 그대로 가져오지 않는다.

## 4. Git 정책

- 영구 브랜치는 `main` 하나다.
- PR과 GitHub Actions를 기본 workflow로 사용하지 않는다.
- force push, rebase, history rewrite를 하지 않는다.
- write 전 최신 `origin/main`과 변경 대상 overlap을 확인한다.
- stage와 commit은 exact path만 포함한다.
- 한 작업은 원자적 commit 하나를 기본으로 한다.
- unrelated dirty state를 삭제·stash·restore하지 않는다.
- 비중첩 remote advance는 최신 main에 재적용하고 primary/direct verification만 다시 실행한 뒤 게시를 재시도한다.

## 5. Template 설계 원칙

- root `AGENTS.md`는 짧은 지도와 불변조건만 포함한다.
- 세부 규칙은 `agents/workflows/`, 프로젝트 정보는 `agents/project/`에 둔다.
- template-managed core와 project-owned overlay를 분리한다.
- 공통 규칙은 독립된 두 프로젝트에서 반복된 뒤에만 core로 승격한다.
- 특정 프레임워크·EMR·시험 프로젝트의 고유 규칙을 universal core에 넣지 않는다.
- 실제 존재하지 않는 command와 path를 생성하지 않는다.
- 작은 작업의 기본 gate로 full release suite를 강제하지 않는다.
- source acceptance와 runtime acceptance를 분리한다.
- 단일 작업 프롬프트는 700줄을 넘지 않는다.

## 6. 검증

문서·template 변경의 최소 검증:

1. `copier.yml` YAML parse
2. Jinja template parse
3. 참조 경로 존재 확인
4. template render smoke
5. 생성 결과에 미치환 placeholder가 없는지 확인
6. template-managed와 project-owned 경계 확인
7. Markdown 링크와 구조 확인

검증 계층:

- V0 `BASELINE`: 수정 전 결함 재현
- V1 `PRIMARY`: 단일 가설 판정
- V2 `DIRECT`: 수정 파일과 직접 영향 범위 closure
- V3 `SYSTEM_SMOKE`: 독립 결함 탐색; 현재 작업 PASS를 취소하지 않음
- V4 `RELEASE`: 명시적인 release candidate에서만 수행

Copier task나 migration처럼 명령 실행이 필요한 기능은 별도 failure domain으로 추가한다.
검증 우회를 PASS로 재분류하지 않는다.

## 7. 완료 조건

- 단일 판정 기준 PASS
- 직접 영향 범위 closure PASS
- 의도한 파일만 변경
- legacy v1 비의도 변경 없음
- commit과 push 성공
- `HEAD == origin/main`
- blocker 없음

## 8. 완료 보고

- `RESULT: PASS | BLOCKED`
- `PRIMARY_VERIFY: PASS | FAIL | NOT_RUN`
- `DIRECT_VERIFY: PASS | FAIL | NOT_RUN`
- `PUBLISH: PUBLISHED | NOT_APPLICABLE | BLOCKED`
- `DISCOVERED_FAILURE: <독립 failure domain 또는 NONE>`
- 변경 파일
- legacy 영향 여부
- 실제 게시된 경우 commit SHA
- 허용된 blocker가 있는 경우에만 blocker와 다음 단일 결정
