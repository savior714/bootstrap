# Dev Environment Bootstrap

Windows 11 개발환경 일괄 설치 스크립트. **winget** 기반으로 동작하며, 설치할 도구를 인터랙티브하게 선택할 수 있습니다.

## 대상 프로젝트 스택

`eco_pediatrics`, `cheonggu`, `law`, `golf_scoring`, `stock_vercel`, `blog`, `fmkorea`, `mail`, `myllm` 등 전체 개발 프로젝트를 커버합니다.

## 사용법

### 포맷된 새 PC에서 처음 설치

```bash
# 1. 이 레포를 클론
git clone https://github.com/savior714/bootstrap.git
cd bootstrap

# 2. bootstrap.bat 더블클릭 또는 아래 명령 실행
bootstrap.bat
```

> PowerShell 실행 정책 오류가 나는 경우:
> ```powershell
> powershell -ExecutionPolicy Bypass -File Bootstrap-DevEnv.ps1
> ```

## 설치 가능한 도구

실행 시 아래 목록에서 숫자 키로 토글 → `Enter`로 설치 시작합니다.
`A` = 전체 선택, `N` = 전체 해제

| # | 항목 | 기본 선택 | 용도 |
|---|------|:---:|------|
| 1 | **Core** — Git, Python 3.14, Node.js LTS, Rust (rustup), uv | ✅ | 모든 프로젝트 공통 |
| 2 | **PowerShell 7** (pwsh) | ✅ | PS5 인코딩/호환성 문제 해결 |
| 3 | **VS Build Tools 2022** (MSVC + Windows SDK) | ✅ | Tauri 빌드, Python 네이티브 확장 (pyiceberg 등) |
| 4 | **Windows Terminal** | ✅ | wt.exe 기반 런처 필수 |
| 5 | Go | ⬜ | Go 언어 런타임 |
| 6 | Java (Temurin JDK 17 LTS) | ⬜ | Java 런타임 |
| 7 | Android Studio | ⬜ | Capacitor (stock_vercel), Expo (golf_scoring) 모바일 빌드 |
| 8 | Docker Desktop | ⬜ | 컨테이너 런타임 |
| 9 | Supabase CLI | ⬜ | DB 마이그레이션 관리 |

## 설치 후 추가 설정

별도로 직접 설치해야 하는 도구:

- **Antigravity IDE**
- **VS Code** / **Cursor AI**

Android 개발 시 Android Studio 최초 실행 후 수동 설정:
```
ANDROID_HOME = C:\Users\<username>\AppData\Local\Android\Sdk
PATH에 추가: %ANDROID_HOME%\platform-tools
```

## 설치 완료 후

```bash
# 새 터미널을 열어 PATH 적용 후
# 프로젝트 레포 클론 → 해당 프로젝트의 eco.bat 실행
eco.bat   # [2] Environment Setup
```

## 요구사항

- Windows 11 (winget 내장)
- 인터넷 연결
- 관리자 권한 (스크립트 실행 시 자동 요청)

## 파일 구조

```
bootstrap/
├── bootstrap.bat          # 더블클릭 런처 (PS7/PS5 자동 감지)
├── Bootstrap-DevEnv.ps1   # 설치 로직 본체
└── README.md
```
