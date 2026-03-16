# 🗺️ Project Blueprint: Optimize Antigravity Rules & SSOT Alignment

> 생성 일시: 2026-03-16 | 상태: 설계 승인 대기

## 🎯 Architectural Goal

- **컨텍스트 효율화**: `.antigravityrules`에 중복된 내용을 삭제하고 `AI_GUIDELINES.md`를 참조하는 **포인터 방식** 도입.
- **안정성 확보**: 물리적 경로 차단(Strict Isolation)은 유지하여 **Silent Loop** 원천 차단.
- **SSOT 정렬**: `AI_GUIDELINES.md`를 모든 기술적 의사결정의 유일한 **상세 근거**로 확립.

## 🛠️ Step-by-Step Execution Plan

### 📦 Task List

- [x] **Task 1: .antigravityrules 재작성 (Optimization)**
  - **Tool**: `Write`
  - **Target**: `c:\develop\bootstrap\.antigravityrules`
  - **Goal**: 중복된 설명을 제거하고 런타임 제약과 물리적 차단 경로만 남김. 상세 규칙은 `AI_GUIDELINES.md`를 참조하도록 명시.
  - **Pseudocode**:
    ```text
    # 🚨 DO NOT REPLICATE AI_GUIDELINES.md HERE
    # Primary Rules: Refer to c:\develop\bootstrap\AI_GUIDELINES.md
    # 1. 1 Task = 1 Tool Call ONLY
    # 2. Wait for User Approval after EACH task
    # 3. Path Isolation: node_modules, .git, etc. (Strict)
    ```

- [x] **Task 2: AI_GUIDELINES.md 내 .antigravityrules 역할 명시**
  - **Tool**: `Edit`
  - **Target**: `c:\develop\bootstrap\AI_GUIDELINES.md`
  - **Goal**: `.antigravityrules`가 '런타임 제약 전용'임을 선언하여 문서 간 위계 정립.
  - **Dependency**: Task 1

- [x] **Task 3: 변경 사항 검증 및 memory.md 동기화**
  - **Tool**: `Bash`
  - **Command**: `Get-Content c:\develop\bootstrap\.antigravityrules`
  - **Goal**: 파일 손상 여부 확인 및 세션 핸드오프 준비.
  - **Dependency**: Task 2

## ⚠️ 기술적 제약 및 규칙 (SSOT)

- **DRY Principle**: 동일한 규칙 설명을 두 파일에 반복하지 않는다.
- **Priority**: `.antigravityrules`는 '지시'가 아닌 '제약'에 가깝게 작성한다.

## ✅ Definition of Done

1. [ ] `.antigravityrules` 파일이 20라인 이내로 최적화됨.
2. [ ] 에이전트가 `AI_GUIDELINES.md`를 주 참조 문서로 인식함을 확인.
3. [ ] `memory.md`에 규칙 정사(SSOT Sync) 기록 완료.
