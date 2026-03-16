# 🗺️ Project Blueprint: Antigravity Extension Stability & Loop Prevention

> 생성 일시: 2026-03-16 13:55 | 상태: 설계 승인 대기

## 🎯 Architectural Goal

- **Antigravity Extension**의 무한 루프(Silent Loop) 현상을 방지하기 위한 기술 지침을 `AI_GUIDELINES.md`에 통합.
- `.cursorrules` 설정을 통해 물리적 스캔 범위를 제한하여 시스템 안정성 및 응답성 확보.
- **SSOT**: `AI_GUIDELINES.md` (안정성 섹션 강화)

## 🛠️ Step-by-Step Execution Plan

### 📦 Task List

- [x] **Task 1: `AI_GUIDELINES.md` 보완 및 강화**
  - **Tool**: `Edit`
  - **Target**: `c:\develop\bootstrap\AI_GUIDELINES.md`
  - **Goal**: 루프 현상 식별(Symptoms), 원인(Cause), 방지법(Prevention)을 수칙화하여 추가.
  - **Dependency**: None

- [x] **Task 2: `.antigravityrules` 보완 및 설정**
  - **Tool**: `Edit`
  - **Target**: `c:\develop\bootstrap\.antigravityrules`
  - **Goal**: 루프를 유발하는 `node_modules`, `.git`, `dist` 등 대용량 경로를 명시적으로 제외하도록 보완.
  - **Dependency**: None

- [x] **Task 3: 환경 검증 및 세션 초기화 지침 확인**
  - **Tool**: `Read`
  - **Target**: `AI_GUIDELINES.md`
  - **Goal**: 추가된 지침에 따른 `Reload Window` 절차 명시 확인.
  - **Dependency**: Task 1

## ⚠️ 기술적 제약 및 규칙 (SSOT)

- **Encoding**: UTF-8 no BOM 준수.
- **Strict Isolation**: `node_modules` 등 제외 경로는 반드시 물리적 파일로 존재해야 함.

## ✅ Definition of Done

1. [ ] `AI_GUIDELINES.md`에 안정 지침이 시니어 아키텍트 톤으로 반영됨.
2. [ ] `.antigravityrules` 파일이 보완되어 스캔 루프 차단.
3. [ ] `memory.md`에 변경 사항 기록 완료.
