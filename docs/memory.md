# memory.md — Bootstrap DevEnv 작업 로그

---

## [요약] 2026-03-10 ~ 2026-03-14 누적 작업

| 날짜 | 주요 작업 |
|------|-----------|
| 2026-03-10 | 초기 디버깅: PS5 BOM 파싱 오류 해결, 창 종료 원인 README 명시 |
| 2026-03-11 | 그룹 번호 재정렬(1~8), `Add-ToUserPath` 함수 추가, Java/Android PATH 자동 등록 |
| 2026-03-14 | Integrity Engine(`check-env.ps1`) 8단계 구축: Core CLI, 설정 무결성, 인코딩, IDE, 기술스택, 네트워크, 린트, 보고서 |
| 2026-03-14 | 메뉴 버그 수정: `OrderedDictionary` `.ContainsKey()` → `.Contains()` |
| 2026-03-14 | AI 지침 표준화: `templates/AI_GUIDELINES.md`, `shared_lint_rules.json` 고도화 |
| 2026-03-14 | Terminal Interaction Protocol 수립 및 CRITICAL_LOGIC.md Section 8 SSOT 반영 |
| 2026-03-14 | Zero-Config Automation: `ANTIGRAVITY_BOOTSTRAP_PATH` 환경 변수 등록, PS Profile 주입 |
| 2026-03-14 | Terminal Protocol 정밀화: `init-terminal.ps1` 고도화, AI_GUIDELINES 패턴 명문화 |
| 2026-03-14 | ECO 브랜딩 제거: `Bootstrap-DevEnv.ps1` 5개 하드코딩 흔적 → Antigravity 대체 |

**현재 상태**: `CRITICAL_LOGIC.md` 139줄 / `shared_lint_rules.json` 307줄 / `Bootstrap-DevEnv.ps1` ~350줄

---

## [2026-03-14] 하드코딩 금지 및 설정 외부화 (Config Externalization)

### 작업 내용

| 파일 | 변경 내용 |
|------|-----------|
| `.gitignore` | `.env`, `.env.local`, `.env.*.local`, `*.secret`, `*.key` 패턴 추가 |
| `.env.example` | 신규 생성 — 환경 변수 키·설명·기본값 문서화 (Zero-Config 온보딩 기준) |
| `config/packages.json` | 신규 생성 — 패키지 그룹 메타데이터 외부화. `{WINDOWS_SDK_VER}` 플레이스홀더 |
| `config/paths.ps1` | 신규 생성 — 경로·버전 상수 SSOT. 환경 변수 Override 패턴 (PS5 호환) |
| `Bootstrap-DevEnv.ps1` | `config/paths.ps1` dot-source 주입, Java 경로·VS SDK 버전 상수화, `$WINGET_ALREADY_INSTALLED_CODE` 상수 추가 |
| `docs/CRITICAL_LOGIC.md` | Section 3 경로 참조를 `config/paths.ps1` 기준으로 업데이트 |

### 진행 상황

- [x] Task 1: `.gitignore` 시크릿 패턴 추가
- [x] Task 2: `.env.example` 생성
- [x] Task 3: `config/packages.json` 생성
- [x] Task 4: `config/paths.ps1` 생성
- [x] Task 5: `Bootstrap-DevEnv.ps1` UI 상수 블록 추가 및 매직 넘버 치환
- [x] Task 6: Java 경로 하드코딩 제거
- [x] Task 7: VS SDK 버전 하드코딩 제거
- [x] Task 8: `CRITICAL_LOGIC.md` SSOT 업데이트
- [x] Task 9: `memory.md` 요약 및 갱신
