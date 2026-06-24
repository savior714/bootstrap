---
scope: detail
domain: core
parent: agents/core/error_patterns.md
lazy_load: true
---
<!-- Language: ko -->

> **역할**: WRONG/CORRECT 예시 전용. 규범은 [runtime_edit_tools.md](../../runtime_edit_tools.md) · Cursor 상세 [routing.md](../../routing.md) §1 — 본문에 재서술하지 않는다.
> **도구**: Cursor `Read`/`Write`/`StrReplace` ([runtime_edit_tools.md §1](../../runtime_edit_tools.md)). 아래 `StrReplace` 예시는 **`filePath`/`oldString`/`newString` CamelCase** 표기.

---

## 1. 편집 전 (Pre-edit)

#### 도구 선택 분기

**규칙**: **기존 파일** → 부분 수정만 · **신규 파일** → 골격 `Write` 1회 후 증분 · 한글 대량 → `bash`/`Shell` + `cat << 'EOF'`

> **Normative**: [routing.md §1.5](../../routing.md#15-atomic-edit-granularity-원자-편집-단위) · [runtime_edit_tools.md §1](../../runtime_edit_tools.md) · [§1.4](../../routing.md#14-editing-rules)

```
❌ WRONG: Write로 justfile 수정 (전체 덮어쓰기)
Write(path, "# new content")
# → 기존 1165줄이 모두 사라짐

✅ CORRECT: 부분 수정은 StrReplace (oldString 필수)
StrReplace(filePath="src/foo.ts", oldString="const x = 1", newString="const x = 2")

✅ CORRECT: 신규 파일만 Write (최소 골격) — 이후 로직은 함수 단위 부분 수정
Write(path="src/NewWidget.tsx", contents="export function NewWidget() { return null }\n")
# → 다음 턴: StrReplace로 props·render 한 함수씩 증분

✅ CORRECT: 한글 대량 콘텐츠는 bash + cat << 'EOF' (edit 도구 ASCII 최적화)
bash: cat > file << 'EOF'
# 한글 포함 본문
EOF
```

### 1.1 Read → Write 직행 (가장 흔함)

**증상**: `Read`(또는 `desktop-commander_read_file`) 출력을 그대로 `Write`/`write_file`에 넣으면 파일이 망가짐.

**원인**: 읽기 도구 출력에는 라인 번호 접두사가 붙습니다 (`    111|content`). 이를 쓰기 도구에 넣으면 파일에 라인 번호가 그대로 기록됩니다.

```
❌ WRONG: Read 출력 그대로 Write
Read(path) → "    111|const x = 1\n    112|const y = 2"
Write(path, "    111|const x = 1\n    112|const y = 2")
# 파일에 "    111|const x = 1" 이렇게 기록됨

✅ CORRECT: 부분 수정은 StrReplace (oldString 필수)
StrReplace(filePath="src/foo.ts", oldString="const x = 1", newString="const x = 2")

✅ CORRECT: Write 사용 시 디스크 본문만 (줄 번호 제외)
# Read 후 oldString은 도구 출력이 아닌 파일 본문에서 추출
```

### 1.2 StrReplace oldString 고유 블록 검증 안 함

**증상**: `StrReplace`가 "Found N matches" 에러를 반복하거나, `replace_all=true`로 파일이 망가짐.

**원인**: `oldString`이 파일에서 여러 곳에 등장하는데, **고유한 블록** 여부를 확인하지 않고 호출함.

```
❌ WRONG: oldString이 4군데 등장하는데 확인 안 함
StrReplace(filePath="src/foo.ts", oldString="Conclusion: [판정 — 비개발자용 요약. 검증 결과]", newString="...")
# Error: Found 4 matches
StrReplace(filePath="src/foo.ts", oldString="Conclusion: [판정 — 비개발자용 요약. 검증 결과]", newString="...")
# Error: Found 4 matches (같은 에러!)

✅ CORRECT: StrReplace 전 반드시 확인
assert oldString in content
assert content.count(oldString) == 1

✅ CORRECT: count > 1이면 oldString에 함수·블록 컨텍스트를 넣어 **고유한 블록**으로 만든 뒤 재시도
# Found 4 matches on "  return x;" → 함수 전체를 oldString으로
StrReplace(filePath="src/foo.ts", oldString="function calculate() {\n  return x;\n}", newString="function calculate() {\n  return y;\n}")
# 그래도 count > 1이면 편집 단위를 쪼개거나 사용자 에스컬레이션 — 기존 파일 Write 금지 ([routing.md §1.5](../../routing.md#15-atomic-edit-granularity-원자-편집-단위))
```

---

## 2. 편집 중 (In-edit)

### 1.3 StrReplace 실패 후 같은 oldString 재시도

**증상**: `StrReplace`가 "Could not find a match"를 반복.

**원인**: 외부 자동화(`just plan-task-close` 등)가 파일을 수정한 후, 에이전트가 stale content로 재시도함.

```
❌ WRONG: 외부 수정 후 stale content로 재시도
# just plan-task-close가 Conclusion을 채움
StrReplace(filePath="src/foo.ts", oldString="[placeholder]", newString="...")
# Error: Could not find a match

✅ CORRECT: 실패 시 반드시 재읽기
Read(path)  # → 현재 실제 상태 확인
# Conclusion이 이미 채워져 있으면 StrReplace 건너뜀
```

### 1.4 JSX/TSX StrReplace 누적으로 구조 망가짐

**증상**: 여러 StrReplace를 연속으로 적용하면 closing tag 순서가 뒤섞이거나 중복 태그가 생김.

**원인**: 각 StrReplace는 마지막 성공한 편집의 파일 상태를 기준으로 적용됨. 실패한 편집이나 부분 적용은 무시됨.

```
❌ WRONG: 여러 StrReplace 연속 (JSX)
StrReplace("targetType === 'X' && (", "...")  # 성공
StrReplace(")})" , ")}")  # 실패 (파일 상태 다름)
StrReplace("sibling", "...")  # 성공하지만 closing tag가 이미 망가짐

✅ CORRECT: 2회 이상 실패 시 **컴포넌트 함수 1개** 범위로 축소해 StrReplace (기존 파일 Write 금지)
Read(path)
# export function PatientRow() { ... } 블록만 oldString으로 — return/JSX 한 컴포넌트 단위
StrReplace(filePath="src/foo.tsx", oldString="export function PatientRow() {\n  ...\n}", newString="export function PatientRow() {\n  ...fixed...\n}")
```

### 1.6 SchemaError — 키 누락·혼동 (Cursor)

> **아카이브 (2026-06 이전 tri-runtime)**: OpenCode `edit`·Antigravity `replace_file_content` 등 다중 런타임 매트릭스는 [runtime_edit_tools.md §0–§2](../../runtime_edit_tools.md)에 역사적 맥락으로만 남긴다. **활성 가이드는 Cursor만.**

**증상**: `The edit tool was called with invalid arguments: SchemaError(Missing key at ["oldString"])` 또는 `Missing key at ["filePath"]`.

**핵심**: Cursor `StrReplace`는 **`filePath` + `oldString` + `newString` CamelCase 3키**가 모두 필요하다. 에러 메시지의 **따옴표 안 키 이름**이 누락·오타된 필드를 가리킨다.

#### 에러 → 원인 → 수정 (디코더)

전체 매트릭스: [runtime_edit_tools.md §2](../../runtime_edit_tools.md).

| 에러·증상 | 흔한 실수 | 올바른 호출 |
| :--- | :--- | :--- |
| `Missing key at ["oldString"]` | `newString`만 · `oldString` 키 누락 | `filePath`/`oldString`/`newString` 3키 모두 |
| `Missing key at ["filePath"]` | `path` 키만 사용 | `filePath` (CamelCase) |
| `unavailable tool 'edit'` | 레거시·타 런타임 도구 호출 | `StrReplace` |
| `Found N matches` | `oldString`이 **고유한 블록** 아님 | 주변 맥락 확장 또는 편집 단위 분할 |

#### Cursor 추가 패턴

1. **부분 수정인데 `oldString` 생략** — `newString`만 → SchemaError.
2. **3키 중 하나 누락** — `filePath`/`oldString`/`newString` **모두** 포함.
3. **신규 vs 부분 혼동** — 신규는 `Write`만.
4. **동일 SchemaError 2회** — [routing.md Repeated Tool Failure Rule](../../routing.md): 인자 순환 재시도 금지 → `Read` → [runtime_edit_tools.md](../../runtime_edit_tools.md) §1 대조.

```
❌ WRONG: newString만 (Missing key at ["oldString"])
StrReplace(filePath="src/foo.ts", newString="const x = 2")

❌ WRONG: oldString 키 누락
StrReplace(filePath="src/foo.ts", newString="const x = 2")

❌ WRONG: path 키 사용 (Missing key at ["filePath"])
StrReplace(path="src/foo.ts", oldString="const x = 1", newString="const x = 2")

✅ CORRECT: Cursor IDE — StrReplace + CamelCase 3키 (routing.md SSOT)
Read(path="src/foo.ts")
StrReplace(filePath="src/foo.ts", oldString="const x = 1", newString="const x = 2")

✅ CORRECT: 신규 파일 — oldString/newString 불필요
Write(path="src/foo.ts", contents="export const x = 1\n")
```

**교차 참조**: [runtime_edit_tools.md](../../runtime_edit_tools.md) · [tools §4.5](tools.md) · [routing.md §1.1](../../routing.md#11-file-edit-tool-schema)

#### StrReplace 매칭 실패 — 줄바꿈·CRLF 불일치

**증상**: `StrReplace`가 "Could not find a match"를 반환하거나, "No changes to apply"만 반복 (old/new는 다르게 생각했지만 실제로는 동일).

**원인**: `oldString`이 디스크 본문과 byte-identical하지 않음 — trailing newline 누락·추가, `\n` vs `\r\n`, 블록 끝 빈 줄 차이.

```
❌ WRONG: 메모리·이전 Read 출력으로 oldString 구성
StrReplace(filePath="src/foo.ts", oldString="Status: Active", newString="...")  # 파일은 "Status: Active\n\n"

✅ CORRECT: Read 직후 디스크 본문에서 그대로 추출
Read(path)
# 줄 번호 접두사 제외, trailing newline·CRLF 포함해 oldString 복사
StrReplace(filePath="src/foo.ts", oldString="Status: Active\n\n", newString="Status: Active\n")
```

**호출 전**: `oldString` ≠ `newString` — 같으면 호출하지 않는다 ([routing.md §1.2](../../routing.md)).

**`"No changes to apply"` vs `"Could not find a match"` 구분:**
- `"No changes to apply"` → old/new 동일 — 재시도 금지, 다음 단계
- `"Could not find a match"` → oldString 불일치 — 재읽기 후 **함수·컴포넌트 1개** 범위로 축소

#### StrReplace 실패 → 재읽기 → 범위 축소 의사결정 트리

**증상**: `StrReplace`가 "Could not find a match", "No changes to apply", "Found N matches"를 반복.

**원인**: stale content, 줄바꿈 불일치, old/new 동일, **고유한 블록** 미검증 등 다양한 원인이 중복됨.

**의사결정 트리:**
```
StrReplace 실패
  ├─ "No changes to apply" → old/new 동일 → 재시도 금지, 다음 단계
  │     └─ 원인: oldString과 newString이 실제로 동일하거나 이미 파일이 목표 상태
  ├─ "Could not find a match" → 재읽기 후 확인
  │     ├─ 이미 목표 상태 → 건너뜀 (외부 자동화 실행 후 stale content 재시도)
  │     └─ oldString 불일치 → **범위 축소**(함수·컴포넌트 1개) 후 재시도
  │           └─ 원인: trailing newline/CRLF 차이, byte-identical 아님
  └─ "Found N matches" → **고유한 블록** 확인
        ├─ count == 1 → oldString 완벽히 일치 복사 후 재시도
        └─ count > 1 → 컨텍스트 확장(함수 본문) 또는 **편집 단위 분할** — 기존 파일 `Write` 금지
```

**핵심 규칙:**
- 2회 이상 실패 시 범위 축소·단위 분할 — **기존 소스 파일 `Write` 에스컬레이션 금지** ([routing.md §1.5](../../routing.md#15-atomic-edit-granularity-원자-편집-단위))
- 외부 자동화(`just plan-task-close`) 실행 후 → 반드시 `Read`로 최신본 확인
- **"No changes to apply" vs "Could not find a match" 구분:**
  - `"No changes to apply"` → old/new 동일 — 재시도 금지, 다음 단계
  - `"Could not find a match"` → oldString 불일치 — 재읽기 후 **함수·컴포넌트 1개** 범위로 축소

**규범**: [routing.md §1.2·Terminal Response Rule](../../routing.md) · [error_patterns.md §메타 금지 9](../../error_patterns.md)

### 1.7 StrReplace 호출 전 필수 검증 (Cursor)

1. **최신본 확보**: `Read`로 최신 디스크 상태를 읽는다.
2. **고유한 블록**: `oldString`이 파일 내 **한 곳만** 매칭되게 주변 맥락을 포함한다. `count > 1`이면 블록을 넓히거나 편집 단위를 분할한다 — `content.count(oldString) == 1`로 확인.
3. **동일 체크 (old ≠ new)**: `oldString`과 `newString`이 같으면 호출하지 않는다.
4. **완벽히 일치 복사**: 공백·들여쓰기·줄바꿈(CRLF/LF)까지 디스크 본문과 동일하게 `oldString`을 구성한다.
5. **한글/인코딩 오류 방지**: 한글이 포함된 JSON 전송 시 `JSON parsing failed`가 나면 [runtime_edit_tools.md §4](../../runtime_edit_tools.md) 우회:
   - **영문/코드만 변경**: `StrReplace` 사용.
   - **한글 포함 다량 콘텐츠**: `bash` + `cat > file << 'EOF'` 혹은 `python3 -c` 스크립트.
   - **macOS `sed -i ''` 주의**: macOS sed는 한글과 함께 사용 시 깨질 수 있으므로 `cat << 'EOF'`를 권장.

**에러 메시지 구분:**
- `"No changes to apply"` (또는 동등한 변화 없음 상태) → 치환 대상과 결과가 이미 동일함. **재시도 금지**, 다음 단계 진행.
- `"Could not find a match"` → 치환 대상 불일치. 재읽기 후 **편집 단위 축소** — 기존 파일은 `Write` 전환 금지 ([§1.11](#111-원자-편집-단위--기존-파일-write-금지)).

**규범**: [routing.md §1.2·1.4](../../routing.md) · [error_patterns.md §메타 금지 9](../../error_patterns.md)

---

### 1.8 Antigravity (아카이브 — 2026-06 이전 tri-runtime)

> **역사적 패턴**: `replace_file_content` / `multi_replace_file_content` 범위·병렬 호출 오류 예시는 tri-runtime 시대 기록이다. Cursor-only 세션에서는 [runtime_edit_tools.md §1](../../runtime_edit_tools.md)만 따른다.

---

### 1.9 OpenCode (아카이브 — 2026-06 이전 tri-runtime)

> **역사적 패턴**: local LLM `edit`의 `replaceAll`·절대 경로 오류 예시는 tri-runtime 시대 기록이다. Cursor-only 세션에서는 `StrReplace` + `filePath`/`oldString`/`newString`만 따른다.

---

### 1.10 Cursor StrReplace 경로 및 oldString 고유 블록 오류

**증상**: `StrReplace` 호출 시 `Found N matches` 에러가 나면서 수정이 취소되거나, 경로 에러가 발생하여 실패함.

**원인**:
1. **경로 형식 오인**: `filePath`에 잘못된 형식 전달 (상대·절대 모두 허용이나 존재하지 않는 경로).
2. **고유성 미달**: 지정한 `oldString`이 파일 내에 중복(2회 이상) 존재하여 도구가 어떤 것을 수정할지 판단할 수 없음.

```
❌ WRONG: 존재하지 않는 경로
StrReplace(filePath="/wrong/path/src/foo.ts", oldString="const x = 1;", newString="const x = 2;")

❌ WRONG: 파일 내에 여러 번 나타나는 문자열을 단순하게 oldString으로 지정
StrReplace(filePath="src/foo.ts", oldString="  return x;", newString="  return y;") // Found 4 matches

✅ CORRECT: filePath 사용, **고유한 블록**으로 oldString 구성
StrReplace(
  filePath="src/foo.ts",
  oldString="function calculate() {\n  return x;\n}",
  newString="function calculate() {\n  return y;\n}"
)
```

### 1.11 원자 편집 단위 — 기존 파일 Write 금지

**증상**: 기존 `.ts`/`.tsx`/`.py` 파일을 `Write`로 통째로 덮어쓰거나, 서로 다른 함수 2개를 한 `StrReplace`에 넣어 diff가 비대해지고 인접 코드가 깨짐.

**원인**: 부분 수정 실패·JSX 복잡도·«빨리 끝내기»를 이유로 **편집 단위 규칙**([routing.md §1.5](../../routing.md#15-atomic-edit-granularity-원자-편집-단위))을 무시함.

**규범 SSOT**: [routing.md §1.5](../../routing.md#15-atomic-edit-granularity-원자-편집-단위) · [principles.md §1.3](../../principles.md#13-surgical-changes) · [code_quality_lifecycle.md §2 I-6](../../code_quality_lifecycle.md)

#### 1.11.1 기존 파일 전체 Write

```
❌ WRONG: Read 후 400줄 전체를 Write로 교체
Read(path="{{FRONTEND_APP_PATH}}/src/components/dashboard/TodayPatientTable.tsx")
Write(path="{{FRONTEND_APP_PATH}}/src/components/dashboard/TodayPatientTable.tsx", contents="<400 lines>")
# → import 정렬·인접 diff·리뷰 불가 · formatter와 충돌 · 메타 금지 1 재발

✅ CORRECT: 변경 대상 함수·컴포넌트 1개만 StrReplace
StrReplace(
  filePath="{{FRONTEND_APP_PATH}}/src/components/dashboard/TodayPatientTable.tsx",
  oldString="function sortPatients(rows: Row[]) {\n  ...\n}",
  newString="function sortPatients(rows: Row[]) {\n  ...fixed...\n}"
)
```

#### 1.11.2 여러 함수를 한 패치에 묶기

```
❌ WRONG: handleSave + handleCancel을 하나의 oldString에
StrReplace(
  filePath="src/foo.ts",
  oldString="const handleSave = () => { ... };\n\nconst handleCancel = () => { ... };",
  new_string="..."
)
# → 한 함수만 의도했는데 둘 다 바뀜 · 실패 시 원인 추적 어려움

✅ CORRECT: 함수마다 별도 호출 — 사이에 Read로 디스크 재확인
StrReplace(filePath="src/foo.ts", oldString="const handleSave = () => { ... }", newString="...")
Read(path)  # formatter·외부 수정 반영
StrReplace(filePath="src/foo.ts", oldString="const handleCancel = () => { ... }", newString="...")
```

#### 1.11.3 신규 파일 — 골격 Write 후 증분

```
❌ WRONG: 신규 컴포넌트 200줄을 첫 Write 한 방에
Write(path=".../CompleteStep.tsx", contents="<200 lines UI + hooks + i18n>")

✅ CORRECT: 골격 1회 → 섹션·함수 단위 증분
Write(path=".../CompleteStep.tsx", contents="export function CompleteStep() { return null }\n")
StrReplace(filePath=".../CompleteStep.tsx", oldString="...", newString="...")  # props 타입
StrReplace(filePath=".../CompleteStep.tsx", oldString="...", newString="...")  # render 본문
StrReplace(filePath=".../CompleteStep.tsx", oldString="...", newString="...")  # handler 1개
```

#### 1.11.4 부분 수정 실패 → Write 우회 (금지)

```
❌ WRONG: StrReplace 2회 실패 후 «그냥 Write»
# Error: Could not find a match (2nd time)
Write(path="src/foo.ts", contents="<reconstructed full file from memory>")

✅ CORRECT: 컴포넌트·함수 범위로 축소 후 재시도 · Blueprint면 Task 분할
Read(path)
StrReplace(filePath="src/foo.ts", oldString="export function Foo() {\n  return (\n    <div>...</div>\n  );\n}", newString="...")
# 여전히 blocked → 메인/사용자에 Blocker 보고 — 기존 파일 Write 아님
```

#### 1.11.5 Subagent · PLAN Execute

PLAN Task 구현 subagent도 동일 — handoff [orchestration.md §4](../../orchestration.md#4-handoff-계약-task-prompt-필수) gate 5.

#### 1.11.6 O2 Strengthened — 메인 «파일 1개 직접 수행» (금지)

```
❌ WRONG: 메인이 «파일 1개·함수 1개» 수정을 «단순»으로 직접 StrReplace
# → O2 Strengthened 위반 — [orchestration.md §8](../../orchestration.md#8-안티패턴)

✅ CORRECT: `general` Task spawn — 메인은 triage·handoff·합성만
```

**session_note**: 2026-06-17 — routing.md §1.5 도입 후 detail 예시 추가. 2026-06-20 — EDAL-005 Cursor CamelCase·고유한 블록 SSOT 정합.

---


## 3. React 실수

### 3.1 useEffect 내 setTimeout/debounce unmount 누락

**증상**: 페이지 이탈 후에도 timer/debounce가 실행됨.

**원인**: `useEffect`에서 timer 설정 후 cleanup(`return clear`) 생략.

**CORRECT**: `return () => clearTimeout(timer)` / `debounce.cancel()`

---

### 3.2 Fast Refresh full reload after session expiry

**증상**: 세션 만료 시 매 mount마다 redirect → full reload.

**원인**: `isAuthenticated` 변화마다 무조건 redirect.

**CORRECT**: `useRef`로 이전 auth 추적 — **true→false** 전환 때만 redirect.

---

## 4. 편집 후 (Post-edit / Recovery)

### 7.1 Write/write_file로 justfile 등 추적되지 않은 파일 덮어쓰기

> **범위**: 설정·justfile·비추적 파일 사고. **애플리케이션 소스**(`apps/`, `src/`, `packages/`)는 [§1.11](#111-원자-편집-단위--기존-파일-write-금지) — 기존 파일 `Write` 금지.

**증상**: `Write`/`write_file`로 파일을 쓰면 기존 내용이 완전히 사라짐.

**원인**: 쓰기 도구는 파일을 완전히 덮어씁니다. git에 추적되지 않은 파일(예: justfile)은 `git checkout`으로 복구할 수 없음.

```
❌ WRONG: Write로 justfile 수정
Write(path, "# 📝 Error patterns management\nerror-pattern-add:\n\t@echo ...")
# → 기존 1165줄이 모두 사라짐

✅ CORRECT: 부분 수정은 StrReplace
StrReplace(filePath="justfile", oldString="old content", newString="new content")

✅ CORRECT: Write 사용 시 반드시 먼저 Read로 전체 내용 확인
content = Read(path)  # → 전체 내용 확보
Write(path, content + "\n# new section")
```

### 7.2 git checkout으로 추적되지 않은 파일 복구 시도

**증상**: `git checkout -- justfile`이 "did not match any file(s) known to git" 에러.

**원인**: 파일이 git에 추적되지 않으면 `git checkout`으로 복구할 수 없음.

```
❌ WRONG: git checkout으로 복구 시도
git checkout -- justfile
# error: pathspec 'justfile' did not match any file(s) known to git

✅ CORRECT: git status로 먼저 확인
git status justfile  # → Untracked files인지 확인

✅ CORRECT: 백업이 없으면 수동 복구
# git stash, reflog, 또는 다른 저장소에서 내용 찾기
```

### 7.3 archive_plans.py — DISCUSS 종속 아카이브 시 plans-index broken reference

**증상**: `archive_plans.py archive` 실행 후 `just plans-index` 가 `"누락된 플랜 파일을 가리키는 참조"` 에러.

```
누락된 플랜 파일을 가리키는 참조:

  PLAN_tem_216_r1_layout_grid_preset.md  → 제안: docs/plans/archive/frontend/PLAN_tem_216_r1_layout_grid_preset.md
    - docs/discussions/archive/DISCUSS_tem_216_r1_layout_grid_preset.md
  PLAN_tem_216_r1_layout_server_sync.md
    - docs/discussions/archive/DISCUSS_tem_216_r1_layout_server_sync.md
```

**원인**: PLAN 아카이브 시 종속 DISCUSS 파일도 함께 archive 로 이동되는데, 그 DISCUSS 파일 본문에 plan 파일을 참조하는 텍스트가 있음.
- 참조가 `docs/plans/PLAN_xxx.md` 같은 절대 경로가 아닌 **단순 텍스트**(예: `` `PLAN_xxx.md` ``) 로 작성된 경우
- 해당 plan 파일이 이미 archive 에 있거나 존재하지 않는 경우

**방지법**:
1. `archive_plans.py archive` 실행 후 `just plans-index` 가 broken reference 를 보고하면 **pre-existing issue 인지 확인**
2. DISCUSS 파일 내 plan 참조가 단순 텍스트(`PLAN_xxx.md`) → 상대 링크(`[PLAN_xxx](../plans/archive/.../PLAN_xxx.md)`) 로 수정 필요
3. plan 파일이 아예 존재하지 않는 경우 → DISCUSS 참조 줄 삭제 또는 "미발행" 주석 추가
4. **이 오류는 아카이브 워크플로 자체의 실패가 아님** — archive 는 정상 완료됨

#### 7.3.1 복구 절차

1. `just plans-index` 실행 → broken reference 확인
2. DISCUSS 파일 grep → 단순 텍스트 참조 찾기: `rg 'PLAN_\w+\.md' docs/discussions/archive/`
3. 상대 링크로 변환 또는 삭제: `sed -i '' 's/`PLAN_\(.*?\)`/[PLAN_\1](../plans/archive\/...\/PLAN_\1)/g' <file>`
4. `just plans-index` 재실행 → PASS 확인

**2026-06-01 세션 기록**: `PLAN_tem_216_r1_layout_preset_entry.md` 아카이브 시 종속 DISCUSS 3 개도 이동. `DISCUSS_tem_216_r1_layout_grid_preset.md` 가 `` `PLAN_tem_216_r1_layout_grid_preset.md` `` 텍스트 참조 포함 — plan 파일은 root 에 존재하지만 링크 포맷이 상대 경로 아님. `just plans-index` 가 누락으로 오인.

---
