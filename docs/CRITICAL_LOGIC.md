# CRITICAL_LOGIC.md — Bootstrap DevEnv 규칙 SSOT

> 이 파일은 bootstrap_repo의 모든 설계 결정과 규칙의 유일한 기준(Single Source of Truth)입니다.

---

## 1. 실행 환경 표준

| 항목 | 결정 | 이유 |
|------|------|------|
| 런처 | `bootstrap.bat` 우클릭 → **관리자 권한으로 실행** | 스크립트 내 admin self-elevation 시 원본 창이 닫히는 현상 방지 |
| PowerShell | **`powershell.exe` (PS5) 고정** | PS7 미사용 환경. pwsh 감지 로직 제거됨 |
| PS1 인코딩 | **UTF-8 with BOM** | PS5가 BOM 없는 UTF-8을 ANSI(CP949)로 읽어 파싱 오류 발생 → BOM 필수 |
| bat 인코딩 | **ANSI (CP949)** | Windows cmd 호환성 |

---

## 2. 패키지 그룹 구성 (현행)

| # | 항목 | 기본 선택 |
|---|------|:---:|
| 1 | Core — Git, Python 3.14, Node.js LTS, Rust (rustup), uv | ✅ |
| 3 | VS Build Tools 2022 (MSVC + Windows SDK 26100) | ✅ |
| 4 | Windows Terminal | ✅ |
| 5 | Go | ⬜ |
| 6 | Java (Temurin JDK 17 LTS) | ⬜ |
| 7 | Android Studio | ⬜ |
| 8 | Docker Desktop | ⬜ |
| 9 | Supabase CLI | ⬜ |

**제거된 항목:**
- ~~PowerShell 7 (pwsh)~~ — PS7 미사용 환경이므로 제거 (그룹 #2였음)

---

## 3. 설계 결정 사항

### Admin 자동 승격 구조
- `Bootstrap-DevEnv.ps1` 실행 시 admin 아닐 경우 `Start-Process powershell -Verb RunAs`로 재실행 후 `exit 0`
- 이로 인해 **원본 bat 창이 닫히고 UAC 창 + 새 창이 열리는 것은 정상 동작**
- 해결책: bat 파일을 처음부터 관리자 권한으로 실행

### 메뉴 UI
- `$Host.UI.RawUI.ReadKey` 기반 인터랙티브 메뉴
- 숫자 키로 토글, `A`/`N`으로 전체 선택/해제, `Enter`로 설치 시작
- 그룹별 설명(Desc) 라인은 불필요하여 제거됨

### Post-install 자동화
- **Rust**: rustup stable toolchain 자동 설치
- **Java**: `JAVA_HOME` 환경변수 자동 설정 (`C:\Program Files\Eclipse Adoptium\jdk-17*`)
- **Android Studio**: `ANDROID_HOME` 수동 설정 안내만 출력

---

## 4. 별도 설치 도구 (스크립트 외)

- Antigravity IDE
- VS Code / Cursor AI
