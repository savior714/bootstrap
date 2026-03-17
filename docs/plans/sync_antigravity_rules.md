# 🗺️ Project Blueprint: .antigravityrules 정합성 검토 및 최신화
 
> 생성 일시: 2026-03-17 11:18 | 상태: 설계 승인 대기
 
## 🎯 Architectural Goal
 
- `.antigravityrules` 내의 **인코딩 규칙**을 `AI_GUIDELINES.md`의 **UTF-8 no BOM** 원칙과 일치시킴.
- **TPG Protocol** 강화에 따라 초기 세션에서 강제해야 할 터미널 환경 변수(`TERM=dumb`, `NO_COLOR=1`)를 명문화.
- 불필요한 중복을 제거하고 '물리적 제약(Physical Constraint)' 및 '런타임 포인터'로서의 역할 강화.
 
## 🛠️ Step-by-Step Execution Plan
 
### 📦 Task List
 
- [x] **Task 1: .antigravityrules 수정 — 인코딩 및 TPG 환경 변수 보완**
  - **Tool**: `Edit`
  - **Target**: `c:\develop\bootstrap\.antigravityrules`
  - **Goal**:
    - PowerShell 인코딩 문구를 `UTF-8 no BOM`으로 수정.
    - 터미널 초기화 항목에 `TERM=dumb`, `NO_COLOR=1` 추가.
  - **Dependency**: None
 
- [x] **Task 2: 최종 무결성 검증**
  - **Tool**: `Terminal`
  - **Goal**: `AI_GUIDELINES.md`의 인코딩 수칙과 `.antigravityrules`의 기술 방식이 상충하지 않는지 최종 대조.
  - **Dependency**: Task 1
 
## ⚠️ 기술적 제약 및 규칙 (SSOT)
 
- **SSOT Alignment**: `.antigravityrules`는 항상 `AI_GUIDELINES.md`의 하위 집합(Physical Layer)이어야 함.
- **Precision**: 문구 수정 시 에이전트가 런타임에 오해할 소지가 없는 명확한 키워드 사용.
 
## ✅ Definition of Done
 
1. [ ] `.antigravityrules`의 인코딩 기준이 **UTF-8 no BOM**으로 변경됨.
2. [ ] 터미널 초기화 규칙에 TPG Protocol의 핵심 환경 변수가 포함됨.
3. [ ] 전체 파일 라인이 최적화된 상태를 유지함.
