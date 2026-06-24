---
scope: detail
domain: core
parent: agents/core/error_patterns.md
lazy_load: true
---
<!-- Language: ko -->

> **역할**: WRONG/CORRECT 예시 전용. 규범(도구 분기·Editing Rules·패치 전제조건·MCP 호출 정책)은 [routing.md](../../routing.md) §1 SSOT — 본문에 재서술하지 않는다.
> **도구**: Cursor `Read`/`Write`/`StrReplace` · MCP `desktop-commander_*` — routing §1.1 표 · MCP 이름은 세션 `mcps/` 디스크립터 SSOT.

## 4. 도구 사용 실수

### 4.1 Write/write_file 부패 (os.getenv corruption / Read 라인 번호 아티팩트)

**증상 A**: `Write`/`write_file`로 파일을 쓰면 `os.getenv("TELEGRAM_TOKEN", "")` 같은 긴 함수 호출이 잘림.

**증상 B**: `Read`/`read_file` 출력의 라인 번호 접두사(예: `'560|'`)를 `oldString`에 그대로 포함시켜 파일에 아티팩트 삽입.

**원인 A**: 일부 쓰기 경로가 긴 문자열을 처리할 때 truncation 발생.

**원인 B**: 읽기 도구 출력에는 라인 번호 접두사가 붙지만, `StrReplace`/`edit_block`은 실제 파일 콘텐츠(라인 번호 없음)와 매칭해야 함.

```
❌ WRONG A: Write로 os.getenv 포함 파일 쓰기
Write(path, 'os.getenv("TELEGRAM_TOKEN", "")')
# → "*** \"\")" 이렇게 잘림

✅ CORRECT A: 부분 수정은 StrReplace
StrReplace({ "filePath": "path", "oldString": "old_value", "newString": 'os.getenv("TELEGRAM_TOKEN", "")' })

✅ CORRECT A: MCP
desktop-commander_write_file(path, content)

❌ WRONG B: Read 출력의 라인 번호를 oldString에 포함
# Read 출력: "    560|const x = 1"
StrReplace({ "filePath": "path", "oldString": "    560|const x = 1", "newString": "..." })
# → 파일에 "    560|const x = 1" 이렇게 기록됨

✅ CORRECT B: StrReplace 전 Read로 최신 상태 재확인
# - Read 출력의 라인 번호 접두사(숫자+|)를 oldString에서 반드시 제거
# - 도구 출력을 직접 oldString으로 쓰지 않고, 디스크 본문에서 공백·들여쓰기·줄바꿈까지 완벽히 일치 복사
```

### 4.2 Biome auto-fix (--auto-fix)로 import 이름 변경

**증상**: `frontend_biome_gate.sh --auto-fix` 후 TypeScript 에러 발생.

**원인**: biome이 import 이름을 재작성함 (예: `useLayoutPresetStore` → `useLayoutPreset`).

```
❌ WRONG: --auto-fix 사용
frontend_biome_gate.sh --auto-fix
# → import 이름이 변경됨

✅ CORRECT: single-file format만 사용
pnpm exec biome format --write <single-file>

✅ CORRECT: baseline 업데이트는 --update-baseline
frontend_biome_gate.sh --update-baseline
```

---

### 4.4 MCP 도구명 underscore/hyphen 불일치

**증상**: `Model tried to call unavailable tool 'desktop_commander_read_text_file'`

**원인**: 모델이 underscore 버전(`desktop_commander_read_file`) 또는 `_text_` variant(`read_text_file`)를 호출하지만, 실제 MCP 서버는 hyphen 버전(`desktop-commander_read_file`)만 노출.

```
❌ WRONG: underscore + _text_ variant 호출
desktop_commander_read_text_file(path)  # Tool not found
desktop_commander_write_text_file(path, content)  # Tool not found

✅ CORRECT: SSOT 참조 + hyphen 버전 사용
# 1. 세션 mcps/<server>/tools/*.json 디스크립터에서 정확한 도구명 확인 (또는 just mcp-tools-validate)
# 2. 실제 호출:
desktop-commander_read_file(path)
desktop-commander_write_file(path, content)
```

**대응** (예시 맥락):
1. MCP 도구명 — 세션 `mcps/` 디스크립터 또는 `just mcp-tools-validate`
2. 하위 호환성 별칭(underscore, `_text_`)은 존재하지 않음

### 4.5 Cursor SchemaError + 레거시 별칭 (아카이브 tri-runtime 축소)

**증상**: `unavailable tool 'read_file'` / `SchemaError(Missing key at ["oldString"])` / `Missing key at ["filePath"]`

**원인**: 레거시 도구명·잘못된 키 casing·필수 3키 누락. SSOT: [runtime_edit_tools.md §1](../../runtime_edit_tools.md).

1. **레거시 도구 이름** (`read_file`, `edit`, `view_file` 등) — Cursor는 `Read`/`StrReplace`/`Write`.
2. **부분 수정** 시 `filePath`/`oldString`/`newString` 중 하나 누락.
3. **path 키** 사용 — Cursor StrReplace는 `filePath`.
4. **신규 파일**에 부분 수정 도구 호출.

```
❌ WRONG: StrReplace에 newString만 (Missing key at ["oldString"])
StrReplace({ "filePath": "src/foo.ts", "newString": "const x = 2" })

❌ WRONG: path 키 사용 (Cursor는 filePath)
StrReplace({ "path": "src/foo.ts", "oldString": "const x = 1", "newString": "const x = 2" })

❌ WRONG: 레거시 edit 도구
edit({ filePath: "...", newString: "..." })

✅ CORRECT: Cursor — [routing.md §1.1](../../routing.md) · CamelCase 3키
Read(path="src/foo.ts")
StrReplace({ "filePath": "src/foo.ts", "oldString": "const x = 1", "newString": "const x = 2" })

✅ CORRECT: Blueprint MCP Task (별도 snake_case 계약)
desktop-commander_read_file → desktop-commander_edit_block(old_str, new_str)

✅ CORRECT: 신규 파일 — Write
Write(path="src/foo.ts", contents="export const x = 1
")

> **아카이브 (2026-06 이전)**: OpenCode `edit` · Antigravity `replace_file_content` — tri-runtime 제거됨.
```

**규범**: [runtime_edit_tools.md](../../runtime_edit_tools.md) · [routing.md §1.1](../../routing.md) · [editing §1.6](editing.md) · MCP — `mcps/` 또는 `just mcp-tools-validate`.

---

