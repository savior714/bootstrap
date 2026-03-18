# 🛡️ AI Command Protocol — Zero-Error Terminal Guide

> **용도**: AI 에이전트(Antigravity, Cursor, Claude Code 등)가 PowerShell/Node.js 명령어를 실행할 때 반복 발생하는 오류를 원천 차단하기 위한 실증 기반 참조 문서.
> **적용 범위**: 이 파일을 프로젝트의 `docs/` 폴더에 두면 AI가 온보딩 시 자동으로 읽어 동일한 안전망이 작동합니다.

---

## 1. File Guard — `cd`는 폴더 전용

### 증상
```
cd '...memory.md' 경로는 존재하지 않으므로 찾을 수 없습니다.
```

### 원인
`Set-Location` (`cd`)은 **디렉토리 전용** 명령어입니다. 파일 경로를 전달하면 PowerShell이 해당 이름의 폴더를 찾으려다 실패합니다.

### 올바른 명령

```powershell
# ❌ 잘못된 예시
cd 'c:\develop\project\docs\memory.md'

# ✅ 파일 내용 읽기
Get-Content -LiteralPath 'c:\develop\project\docs\memory.md' -TotalCount 50

# ✅ 파일이 있는 폴더로 이동
Set-Location 'c:\develop\project\docs'
```

---

## 2. Pipeline Guard — `Join-Path` 파이프 금지

### 증상
```
입력을 매개 변수에 바인딩할 수 없습니다. 매개 변수 "Path" 값 "..."을(를) "System.String" 형식으로 변환할 수 없습니다.
```

### 원인
`Join-Path`의 출력은 파이프라인으로 전달할 때 `Get-Content`가 어느 매개변수(`-Path` vs `-LiteralPath`)에 바인딩할지 결정하지 못하거나, 타입 변환에 실패합니다.

### 올바른 명령

```powershell
# ❌ 잘못된 예시
Join-Path "docs" "memory.md" | Get-Content

# ✅ 괄호(서브 익스프레션)로 실행 순서 명시
Get-Content (Join-Path "docs" "memory.md") -TotalCount 30

# ✅ 변수를 통한 명시적 분리 (가독성 우선)
$path = Join-Path $PSScriptRoot "docs" "memory.md"
Get-Content -LiteralPath $path -TotalCount 30
```

---

## 3. CLI Arg Guard — `next lint` 인자 오해석

### 증상
```
Invalid project directory provided, it must be an absolute path: C:\...\frontend\lint
```

### 원인
`npm run lint`를 루트에서 실행하면 내부적으로 `next lint`가 호출됩니다. 이때 `--` 이후의 인자를 Next.js가 **"검사할 디렉토리 경로"**로 해석하여 `frontend/lint` 폴더를 찾으려다 실패합니다.

### 올바른 명령

```powershell
# ❌ 잘못된 예시 (루트에서 실행, 인자 충돌)
npm run lint -- frontend

# ✅ 대상 디렉토리로 먼저 이동 후 실행
Set-Location frontend; npm run lint

# ✅ package.json scripts에 경로 고정 (근본 해결)
# frontend/package.json:
# "scripts": { "lint": "next lint", "type-check": "tsc --noEmit" }
```

> **추천**: 서브패키지의 `package.json`에 `lint`, `type-check` 스크립트를 명시하여 루트에서 인자를 전달할 필요를 없애는 것이 가장 안전합니다.

---

## 4. npx Guard — 로컬 미설치 패키지 실행 차단

### 증상
```
This is not the tsc command you are looking for
```

### 원인
`npx`는 로컬 `node_modules`에 해당 패키지가 없을 경우 보안상 실행을 차단합니다. 즉, 현재 프로젝트에 `typescript`가 설치되어 있지 않은 상태입니다.

### 올바른 명령

```powershell
# ❌ 잘못된 예시 (로컬에 typescript 없으면 차단)
npx tsc --noEmit

# ✅ 패키지명을 명시하여 강제 실행
npx -p typescript tsc --noEmit

# ✅ package.json에 type-check 스크립트 정의 (근본 해결)
# "scripts": { "type-check": "tsc --noEmit" }
# 이후: npm run type-check

# ✅ 특정 tsconfig를 명시하는 경우
npx -p typescript tsc --noEmit --project frontend/tsconfig.json
```

---

## 요약 대조표

| # | 오류 유형 | 핵심 원인 | 즉각 해결책 |
|---|-----------|-----------|-------------|
| 1 | **파일에 `cd`** | `cd`는 폴더 전용 | `Get-Content -LiteralPath` |
| 2 | **파이프라인 바인딩** | 타입/바인딩 불일치 | `Get-Content (Join-Path ...)` |
| 3 | **`next lint` 인자** | CLI가 인자를 경로로 오해 | `cd target; npm run lint` |
| 4 | **`npx` 차단** | 로컬 패키지 미설치 | `npx -p typescript tsc` |

---

## 프로젝트 레벨 예방 설정

새 프로젝트에서 위 오류를 **구조적으로 예방**하려면 아래 설정을 심어두세요.

### `package.json` (서브패키지 기준)

```json
{
  "scripts": {
    "lint": "next lint",
    "type-check": "tsc --noEmit",
    "validate": "npm run lint && npm run type-check"
  }
}
```

### `.npmrc` (루트)

```ini
# 버전 고정 및 로컬 우선 실행
save-exact=true
prefer-offline=true
```

---

> **참조 문서**: [AI_GUIDELINES.md](../AI_GUIDELINES.md) 섹션 2 (TPG Protocol) / [.antigravityrules](../.antigravityrules) 섹션 3
