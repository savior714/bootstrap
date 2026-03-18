/**
 * types-extractor.ts
 * 목적: ts-morph를 사용하여 TypeScript 소스에서 타입 정의(선언부)만 추출
 *       → LLM에 전달할 최소 컨텍스트(Definition-Only) 생성
 *
 * 전략: docs/TS_TYPE_VALIDATION.md §7 (Symbol Reference) / §8 (Type Flatten)
 *
 * 사용법:
 *   npx ts-node scripts/types-extractor.ts --name UserService
 *   npx ts-node scripts/types-extractor.ts --name UserRole --flat
 *   npx ts-node scripts/types-extractor.ts --barrel src/domain/index.ts
 *
 * 설치 필요: npm install -D ts-morph ts-node
 */

import { Project, InterfaceDeclaration, TypeAliasDeclaration, SourceFile } from 'ts-morph';

// ── CLI 인자 파싱 ──────────────────────────────────────────────────────────────
const args = process.argv.slice(2);
const nameIdx = args.indexOf('--name');
const barrelIdx = args.indexOf('--barrel');
const isFlat = args.includes('--flat');

const targetName = nameIdx !== -1 ? args[nameIdx + 1] : null;
const barrelPath = barrelIdx !== -1 ? args[barrelIdx + 1] : null;

if (!targetName && !barrelPath) {
  console.error('Usage: ts-node types-extractor.ts --name <TypeName> [--flat]');
  console.error('       ts-node types-extractor.ts --barrel <path/to/index.ts>');
  process.exit(1);
}

// ── Project 초기화 ─────────────────────────────────────────────────────────────
const project = new Project({
  tsConfigFilePath: 'tsconfig.json',
  skipAddingFilesFromTsConfig: false,
});

// ── 헬퍼: 인터페이스 선언부만 추출 ────────────────────────────────────────────
function extractInterface(node: InterfaceDeclaration): string {
  // 구현부 없음 → getText()는 선언 전체이지만 interface는 구현체가 없으므로 그대로 반환
  return node.getText().trim();
}

// ── 헬퍼: 타입 별칭 추출 (Flatten 옵션 적용) ──────────────────────────────────
function extractTypeAlias(node: TypeAliasDeclaration, flatten: boolean): string {
  if (!flatten) {
    return node.getText().trim();
  }
  // Flatten 모드: 타입 텍스트에서 중첩 조건부 타입을 단계 분리하여 주석 추가
  const text = node.getText().trim();
  const hasConditional = /\bextends\b.+\?/.test(text);
  if (hasConditional) {
    return `// ⚠️ Conditional Type 감지 — 평탄화 권장 (docs/TS_TYPE_VALIDATION.md §8)\n${text}`;
  }
  return text;
}

// ── 헬퍼: 소스 파일에서 타입/인터페이스 검색 ──────────────────────────────────
function findDefinition(name: string): string | null {
  const sourceFiles = project.getSourceFiles();

  for (const sf of sourceFiles) {
    // 인터페이스 탐색
    const iface = sf.getInterface(name);
    if (iface) {
      return `// 📄 ${sf.getFilePath()}\n${extractInterface(iface)}`;
    }
    // 타입 별칭 탐색
    const typeAlias = sf.getTypeAlias(name);
    if (typeAlias) {
      return `// 📄 ${sf.getFilePath()}\n${extractTypeAlias(typeAlias, isFlat)}`;
    }
    // Enum 탐색
    const enumDecl = sf.getEnum(name);
    if (enumDecl) {
      return `// 📄 ${sf.getFilePath()}\n${enumDecl.getText().trim()}`;
    }
  }
  return null;
}

// ── 헬퍼: Barrel Export 파일에서 모든 타입 추출 ───────────────────────────────
function extractBarrel(barrelFilePath: string): string[] {
  const sf: SourceFile | undefined = project.getSourceFile(barrelFilePath);
  if (!sf) {
    console.error(`❌ Barrel 파일을 찾을 수 없습니다: ${barrelFilePath}`);
    process.exit(1);
  }

  const results: string[] = [];
  // re-export 선언에서 타입명 수집
  for (const exportDecl of sf.getExportDeclarations()) {
    const namedExports = exportDecl.getNamedExports();
    for (const ne of namedExports) {
      const name = ne.getName();
      const def = findDefinition(name);
      if (def) {
        results.push(def);
      }
    }
  }
  return results;
}

// ── 메인 실행 ─────────────────────────────────────────────────────────────────
console.log('');
console.log('── Type Definition Extractor (LLM Minimal Context) ──────────────');

if (targetName) {
  // 단일 심볼 추출
  const result = findDefinition(targetName);
  if (result) {
    console.log(`\n✅ 추출 성공: ${targetName}\n`);
    console.log(result);
  } else {
    console.error(`\n❌ "${targetName}" 정의를 찾을 수 없습니다.`);
    console.error('   확인: tsconfig.json의 include 범위, 파일명, export 여부');
    process.exit(1);
  }
} else if (barrelPath) {
  // Barrel Export 전체 추출
  const results = extractBarrel(barrelPath);
  if (results.length === 0) {
    console.log('⚠️  Barrel 파일에서 추출할 타입 정의가 없습니다.');
  } else {
    console.log(`\n✅ ${results.length}개 타입 추출 완료 (${barrelPath})\n`);
    console.log('── LLM에 전달할 최소 컨텍스트 ──────────────────────────────────');
    results.forEach((r, i) => {
      console.log(`\n// [${i + 1}/${results.length}]`);
      console.log(r);
    });
  }
}

console.log('\n── 사용 가이드 ───────────────────────────────────────────────────');
console.log('  이 출력을 tsc 에러 ±5줄과 함께 LLM에 전달하세요.');
console.log('  전략: docs/TS_TYPE_VALIDATION.md §6~§8\n');
