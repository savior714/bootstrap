# 🗺️ Project Blueprint: Supabase CLI 자동 설치 제거 및 매뉴얼 안내 전환

> 생성 일시: 2026-03-14 19:10 | 상태: 설계 승인 대기

## 🎯 Architectural Goal

- **문제 상황**: `Supabase CLI`가 `winget` 공식 리포지토리에 존재하지 않아 자동 설치 시 에러(exit -1978335212) 발생.
- **해결 방안**: 자동 설치 리스트에서 제거하여 설치 스크립트의 신뢰성(Stability)을 확보하고, 대체 설치 방법(`npm`)을 문서화함.
- **SSOT**: `config/packages.json` 및 `Bootstrap-DevEnv.ps1`의 패키지 정의 정렬.

## 🛠️ Step-by-Step Execution Plan

### 📦 Task List

- [x] **Task 1: `config/packages.json`에서 Supabase CLI 제거**
  - **Tool**: `Edit`
  - **Target**: `c:\develop\bootstrap\config\packages.json`
  - **Goal**: 사용되지 않는 `Supabase.CLI` 정의 제거 (Group 8)
  - **Dependency**: None

- [x] **Task 2: `Bootstrap-DevEnv.ps1`에서 Supabase CLI 제거**
  - **Tool**: `Edit`
  - **Target**: `c:\develop\bootstrap\Bootstrap-DevEnv.ps1`
  - **Goal**: 하드코딩된 Group 8 및 관련 버전 체크 로직 제거
  - **Dependency**: Task 1 (Done)

- [x] **Task 3: `README.md`에 수동 설치 가이드 추가**
  - **Tool**: `Edit`
  - **Target**: `c:\develop\bootstrap\README.md`
  - **Goal**: `npm install -g supabase`를 통한 대체 설치 방법 안내 명시
  - **Dependency**: Task 2 (Done)

- [x] **Task 4: 환경 검증 및 memory.md 업데이트**
  - **Tool**: `Bash`
  - **Command**: `scripts/check-env.ps1` 실행 및 결과 기록
  - **Goal**: 변경 사항 반영 확인 및 SSOT 동기화
  - **Dependency**: Task 3 (Done)

## ⚠️ 기술적 제약 및 규칙 (SSOT)

- **Stability**: [Traffic Zero] 원칙에 따라 설치 실패 로그가 남지 않도록 보수적으로 관리.
- **Encoding**: 모든 수정 사항은 `UTF-8 no BOM`을 준수함.
- **Consistency**: `packages.json`과 `ps1` 스크립트 내의 그룹 번호를 일관성 있게 유지 (필요시 재정렬).

## ✅ Definition of Done

1. [ ] `Bootstrap-DevEnv.ps1` 실행 시 Supabase CLI 항목이 나타나지 않음.
2. [ ] `README.md`에 명확한 대체 설치 가이드가 존재함.
3. [ ] `check-env.ps1` 통과 및 `memory.md`에 작업 완료 기록.
