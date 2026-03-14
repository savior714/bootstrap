# memory.md — Bootstrap DevEnv 작업 로그

---

## [2026-03-10] 초기 디버깅 및 정리

### 발견된 문제

1. **창 즉시 종료 (더블클릭)**: admin self-elevation 후 원본 창이 닫히는 정상 동작이나 혼란 유발 → README에 명시
2. **PS5 파싱 오류**: UTF-8 no BOM 파일을 PS5가 ANSI(CP949)로 읽어 `>>>` 문자열을 리다이렉션 연산자로 오인
   - 증상: `Missing file specification after redirection operator` at line 229
   - 해결: PS1 파일을 **UTF-8 with BOM**으로 재저장

### 초기 변경 사항

| 파일 | 변경 내용 |
| :--- | :--- |
| `Bootstrap-DevEnv.ps1` | PS7 패키지 그룹(#2) 제거, Desc 필드 제거, UTF-8 BOM 적용 |
| `bootstrap.bat` | pwsh 감지 로직 제거 → `powershell.exe` 고정, PS7 echo 제거 |
| `README.md` | 관리자 실행 필수 안내, PS7 행 제거, 용도 열 제거 |
| `docs/CRITICAL_LOGIC.md` | SSOT 신규 작성 |
| `docs/memory.md` | 작업 로그 신규 작성 |

---

## [2026-03-11] 추가 기능 및 정리

### 추가 변경 사항

| 파일 | 변경 내용 |
| :--- | :--- |
| `Bootstrap-DevEnv.ps1` | 그룹 번호 재정렬(1~8 연속), pwsh verCheck 제거, `Add-ToUserPath` 함수 추가, Java/Android PATH 자동 등록 |
| `README.md` | 그룹 번호 테이블 동기화 |
| `docs/CRITICAL_LOGIC.md` | Post-install 자동화 항목 상세 업데이트 |

---

## [2026-03-14] Antigravity 환경 무결성 검증 엔진 (Integrity Engine)

### 인테그리티 변경 사항

| 파일 | 변경 내용 |
| :--- | :--- |
| `scripts/check-env.ps1` | 초기 환경 검증 엔진 구축 (Node, Git, npm, pnpm, yarn 가용성 검증) |
| `scripts/check-env.ps1` | 핵심 설정(.npmrc, .gitconfig) 무결성 검증 로직 추가 (Task 2) |
| `scripts/check-env.ps1` | 파일 시스템 및 인코딩 무결성(UTF-8 no BOM) 검증 로직 추가 (Task 3) |
| `scripts/check-env.ps1` | IDE(VSCode) 설정 무결성 검증 로직 추가 및 settings.json 생성 (Task 4) |
| `scripts/check-env.ps1` | 기술 스택 Dry-Run 검증 로직 추가 (tsc, eslint, prettier) (Task 5) |
| `shared_lint_rules.json` | 신규 생성 규칙 (no-console, semi) |
| `eslint.config.js` | 신규 생성 규칙 (no-console, semi) |
| `scripts/check-env.ps1` | 공유 린트 정책 동기화 검증 로직 추가 (Task 7) |
| `scripts/check-env.ps1` | 통합 보고서(env_report.json) 생성 및 복구 제안 로직 추가 (Task 8) |

### 진행 상황

- [x] Task 1: `scripts/check-env.ps1` 초기 구조 및 Core CLI/Runtime 검증 구현
- [x] Task 2: 핵심 설정 파일(.npmrc, .gitconfig) 무결성 검증
- [x] Task 3: 파일 시스템 및 인코딩 무결성 스캔 로직 추가
- [x] Task 4: IDE(VSCode/Antigravity) 설정 동기화 검증
- [x] Task 5: 기술 스택 헬스체크 (Dry-Run) 및 바이너리 검증
- [x] Task 6: 네트워크 환경 및 레지스트리 도달성 검증
- [x] Task 7: 공유 린트 정책(Shared Policy) 동기화 검증
- [x] Task 8: 통합 보고서(`env_report.json`) 생성 및 자동 복구 제안
- [x] Git Push: 모든 변경 사항을 SSOT 문서에 반영하고 원격 저장소에 푸시
