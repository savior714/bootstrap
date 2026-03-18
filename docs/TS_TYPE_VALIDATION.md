# TypeScript Type Validation Protocol — 3-IDE Unified Strategy

> **SSOT**: 이 문서는 Antigravity / VSCode / Cursor AI 세 환경에서 동일하게 적용되는
> TypeScript 타입 검증 비용 최적화 전략의 단일 기준(Single Source of Truth)입니다.
>
> **핵심 원칙**: LLM은 "검증(Validation)"이 아닌 "수정(Fix)"에만 집중시킨다.
> 컴파일러(`tsc`)가 할 수 있는 일을 LLM 토큰으로 대체하지 않는다.

---

## 0. 왜 타입 검증이 토큰을 낭비하는가?

| 안티패턴 | 원인 | 토큰 낭비 규모 |
| :--- | :--- | :---: |
| 전체 파일을 컨텍스트에 주입 | 구현부(impl)까지 포함된 `.ts` 파일 전달 | ~80% 과잉 |
| LLM을 컴파일러로 사용 | "이 코드 타입 맞아?"라고 질문 | ~60% 과잉 |
| 복잡한 Conditional Type 직접 해석 | `infer`, `extends` 체인을 LLM이 추론 | ~40% 과잉 |
| 에러 없는 파일까지 전달 | `tsc` 필터링 없이 전체 소스 전달 | ~90% 과잉 |

---

## 1. Infrastructure: 컴파일러 체인 우선 (Tool-First)

### 1-1. Error-Only Context 패턴

```bash
# ✅ LLM에게 전달할 정보만 추출하는 표준 명령
npx -p typescript tsc --noEmit 2>&1 | grep -E "error TS[0-9]+" | head -30
```

**LLM 프롬프트 구성 규칙:**
- `tsc --noEmit` 결과 → **에러 라인만** 슬라이싱
- 에러 라인 ±5줄 코드 컨텍스트만 추가 (구현부 전체 X)
- 에러가 0개이면 LLM에 아무것도 보내지 않음

### 1-2. package.json 필수 스크립트 (3개 환경 공통)

```json
{
  "scripts": {
    "type-check": "tsc --noEmit",
    "type-check:watch": "tsc --noEmit --watch",
    "type-check:strict": "tsc --noEmit --strict",
    "validate": "npm run type-check && npm run lint"
  }
}
```

### 1-3. tsconfig.json 필수 설정

```json
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true
  }
}
```

> **근거**: strict 모드를 사전에 켜두면 LLM이 수정해야 할 에러가 명시적으로 드러나며,
> 암묵적 `any` 통과로 인한 후속 에러 폭발을 방지합니다.

---

## 2. Domain: Zod 스키마 우선 설계

### 2-1. Schema-First 원칙

```typescript
// ❌ 안티패턴: 인터페이스 먼저 → LLM이 매번 타입 추론
interface User {
  id: string;
  age: number;
  role: 'admin' | 'user';
}

// ✅ 표준: Zod 스키마 먼저 → 타입은 자동 추출
import { z } from 'zod';

export const UserSchema = z.object({
  id: z.string().uuid(),
  age: z.number().int().min(0).max(150),
  role: z.enum(['admin', 'user']),
});

export type User = z.infer<typeof UserSchema>;
// 런타임 검증 + 정적 타입 = 동시 보장
```

### 2-2. LLM에게 전달할 컨텍스트 계층

| 단계 | 전달 대상 | 설명 |
| :---: | :--- | :--- |
| **1단계** | Zod 스키마 정의부만 | 구현부 제외, 스키마 파일만 전달 |
| **2단계** | `tsc` 에러 메시지 + ±5줄 | 에러 라인 주변 코드만 슬라이싱 |
| **3단계** | 직접 의존 타입만 | `import type` 체인 1단계까지만 |

---

## 3. Application: 환경별 구성

### 3-1. Antigravity IDE

`.antigravityrules`에 추가할 내용 → Section 6 참조 (이 문서 하단).

**에이전트 실행 패턴:**

```json
// ✅ 타입 에러만 추출하는 Antigravity run_command
{
  "CommandLine": "powershell -NoProfile -Command \"npx -p typescript tsc --noEmit 2>&1 | Select-String 'error TS' | Select-Object -First 20\"",
  "Cwd": "c:\\your-project"
}
```

### 3-2. VSCode

`.vscode/tasks.json`에 추가 (자동 타입 체크 태스크):

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "TypeScript: Type Check",
      "type": "shell",
      "command": "npm run type-check",
      "group": { "kind": "build", "isDefault": false },
      "presentation": { "reveal": "silent", "panel": "shared" },
      "problemMatcher": "$tsc"
    },
    {
      "label": "TypeScript: Errors Only (for LLM)",
      "type": "shell",
      "command": "npx -p typescript tsc --noEmit 2>&1 | findstr /R \"error TS\"",
      "group": "build",
      "presentation": { "reveal": "always", "panel": "dedicated" }
    }
  ]
}
```

`.vscode/settings.json`에 추가할 필수 항목:

```json
{
  "typescript.tsdk": "node_modules/typescript/lib",
  "typescript.enablePromptUseWorkspaceTsdk": true,
  "typescript.preferences.quoteStyle": "single",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": "explicit",
    "source.fixAll.eslint": "explicit"
  },
  "typescript.validate.enable": true,
  "typescript.surveys.enabled": false
}
```

### 3-3. Cursor AI

`.cursorrules`에 추가할 타입 검증 섹션:

```
## TypeScript Type Validation Protocol

### Context Injection Rules (Token Optimization)
- NEVER send entire .ts files for type checking
- ALWAYS run `npm run type-check` first; only send error lines + ±5 surrounding lines
- For type fixes: send ONLY the failing function + its direct type imports
- Strip all comments and blank lines from type definitions before sending

### Schema-First Enforcement
- Always define Zod schemas BEFORE TypeScript interfaces
- Use `z.infer<typeof Schema>` instead of duplicate interface definitions
- Runtime validation (Zod) = Static types (TypeScript) = Single source of truth

### Forbidden Patterns
- DO NOT ask Cursor to "check if this type is correct" — run tsc first
- DO NOT send full files when only 1-2 functions have type errors
- DO NOT use `as any` or `@ts-ignore` — fix the root type issue

### Error-Fix Workflow
1. Run: `npm run type-check` → capture stderr only
2. Identify: error code (TS2345, TS2339, etc.) + line range
3. Send: error message + ±5 lines + direct type dependencies only
4. Fix: LLM proposes fix → re-run tsc to verify
```

---

## 4. 타입 에러 코드별 최소 컨텍스트 전략

| 에러 코드 | 에러 명 | 필요 컨텍스트 |
| :--- | :--- | :--- |
| `TS2345` | Argument type mismatch | 함수 시그니처 + 호출 라인만 |
| `TS2339` | Property does not exist | 해당 타입 정의 + 접근 라인만 |
| `TS2322` | Type not assignable | 할당 라인 + 양쪽 타입 정의만 |
| `TS2304` | Cannot find name | import 구문 + 선언 파일만 |
| `TS7006` | Implicit any | 함수 파라미터 라인만 |
| `TS2365` | Operator not applicable | 비교 연산 라인 + typeof 확인 라인 |

---

## 5. 자동화 스크립트: Error-Slice Extractor

```powershell
# scripts/type-check-slice.ps1
# tsc 에러를 LLM 최소 컨텍스트로 슬라이싱하는 스크립트

param(
  [string]$ProjectPath = ".",
  [int]$ContextLines = 5
)

$errors = powershell -NoProfile -Command "cd '$ProjectPath'; npx -p typescript tsc --noEmit 2>&1"
$errorLines = $errors | Select-String "error TS\d+"

if ($errorLines.Count -eq 0) {
  Write-Host "✅ No type errors found." -ForegroundColor Green
  exit 0
}

Write-Host "🔴 Type Errors ($($errorLines.Count) found) — Minimal LLM Context:" -ForegroundColor Red
$errorLines | ForEach-Object { Write-Host $_.Line -ForegroundColor Yellow }
```

---

## 6. `.antigravityrules` 추가 섹션 (복사용)

```
# 6. TypeScript Type Validation Protocol (Token Optimization)
# [MANDATORY] LLM MUST NOT perform type checking. tsc is the type checker.
# - ALWAYS run `npm run type-check` before asking LLM to fix types.
# - ONLY send: tsc error lines + ±5 surrounding code lines to LLM context.
# - FORBIDDEN: sending entire .ts files for type analysis.
# - FORBIDDEN: using `any`, `@ts-ignore`, or type assertions to bypass errors.
# - Schema-First: Zod schema MUST precede TypeScript interface definitions.
# - Minimum Context: error code + failing line + direct type import chain (1 level).
# - Verification: after LLM fix, re-run `npm run type-check` to confirm 0 errors.
```

---

> **참조 문서**: [AI_GUIDELINES.md](../AI_GUIDELINES.md) | [AI_COMMAND_PROTOCOL.md](AI_COMMAND_PROTOCOL.md)
> **고급 패턴**: [TS_ADVANCED_PATTERNS.md](TS_ADVANCED_PATTERNS.md) — DDD 타입 분리, Symbol Reference, Type Flatten
> **바이브 코딩**: [VIBE_CODING_PROTOCOL.md](VIBE_CODING_PROTOCOL.md) — Validate-and-Prune, L1/L2/L3, Agent-to-Agent Protocol
> **관련 스크립트**: `scripts/type-check-slice.ps1` | `scripts/types-extractor.ts`
> **관련 설정**: `.antigravityrules` §6~§7 | `.cursorrules` §2~§3 | `.vscode/tasks.json`
