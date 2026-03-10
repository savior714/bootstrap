# memory.md — Bootstrap DevEnv 작업 로그

---

## [2026-03-10] 초기 디버깅 및 정리

### 발견된 문제
1. **창 즉시 종료 (더블클릭)**: admin self-elevation 후 원본 창이 닫히는 정상 동작이나 혼란 유발 → README에 명시
2. **PS5 파싱 오류**: UTF-8 no BOM 파일을 PS5가 ANSI(CP949)로 읽어 `>>>` 문자열을 리다이렉션 연산자로 오인
   - 증상: `Missing file specification after redirection operator` at line 229
   - 해결: PS1 파일을 **UTF-8 with BOM**으로 재저장

### 변경 사항
| 파일 | 변경 내용 |
|------|----------|
| `Bootstrap-DevEnv.ps1` | PS7 패키지 그룹(#2) 제거, Desc 필드 제거, UTF-8 BOM 적용 |
| `bootstrap.bat` | pwsh 감지 로직 제거 → `powershell.exe` 고정, PS7 echo 제거 |
| `README.md` | 관리자 실행 필수 안내, PS7 행 제거, 용도 열 제거 |
| `docs/CRITICAL_LOGIC.md` | SSOT 신규 작성 |
| `docs/memory.md` | 작업 로그 신규 작성 |

---

## [2026-03-10] 추가 기능 및 정리

### 변경 사항
| 파일 | 변경 내용 |
|------|----------|
| `Bootstrap-DevEnv.ps1` | 그룹 번호 재정렬(1~8 연속), pwsh verCheck 제거, `Add-ToUserPath` 함수 추가, Java/Android PATH 자동 등록 |
| `README.md` | 그룹 번호 테이블 동기화 |
| `docs/CRITICAL_LOGIC.md` | Post-install 자동화 항목 상세 업데이트 |
