#!/usr/bin/env python3
"""Docs DRY linter — cross-layer Jaccard duplicate detection (baseline incremental).

Usage:
  python3 scripts/verify/docs_dry_linter.py --check
  python3 scripts/verify/docs_dry_linter.py --update-baseline
  python3 scripts/verify/docs_dry_linter.py --check-touched
  python3 scripts/verify/docs_dry_linter.py --threshold 0.72
"""

from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import sys
from dataclasses import dataclass
from enum import Enum
from fnmatch import fnmatch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_SCRIPTS_VERIFY = Path(__file__).resolve().parent
if str(_SCRIPTS_VERIFY) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_VERIFY))

from baseline_gate import filter_new_entries, load_baseline, write_baseline

BASELINE_PATH = ROOT / "scripts" / "verify" / "docs_dry_baseline.txt"
DEFAULT_THRESHOLD = 0.72
MIN_PARAGRAPH_LEN = 80

INCLUDE_PATTERNS = (
    "docs/knowledge/guide/**/*.md",
    "docs/knowledge/GUIDE_*.md",
    "docs/knowledge/RES_*.md",
    "docs/specs/**/*.md",
    "docs/knowledge/**/RES_*.md",
    "docs/knowledge/integration/*.md",
)

EXCLUDE_PREFIXES = (
    "docs/plans/",
    "docs/discussions/",
    "docs/agent-context/",
    "docs/reports/",
    "docs/templates/",
    "scripts/bootstrap/",
    "agents/",
)

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_LANG_MARKER_RE = re.compile(r"^<!--\s*Language:\s*[^>]+-->\s*\n?", re.IGNORECASE)
_CODE_BLOCK_RE = re.compile(r"```[\s\S]*?```", re.MULTILINE)
_TRACK_HEADING_RE = re.compile(r"^#{1,4}\s*Track\s+[ABC]\b", re.MULTILINE | re.IGNORECASE)
_SECTION_BOILER_RE = re.compile(r"^##\s*§[01]\b", re.MULTILINE)
_SSOT_BANNER_RE = re.compile(r"\bSSOT\b", re.IGNORECASE)
_ENV_VAR_LINE_RE = re.compile(r"^[A-Z][A-Z0-9_]*=", re.MULTILINE)
_URL_LINE_RE = re.compile(r"^https?://\S+$", re.MULTILINE)


class DocLayer(Enum):
    RUNBOOK = "runbook"
    SPEC = "spec"
    RES = "res"
    SKIP = "skip"


@dataclass(frozen=True)
class ParsedDoc:
    path: Path
    rel_path: str
    layer: DocLayer
    paragraphs: tuple[str, ...]


@dataclass(frozen=True)
class Violation:
    path_a: str
    path_b: str
    paragraph_hash: str
    jaccard: float
    snippet: str


# ---------------------------------------------------------------------------
# doc_parser
# ---------------------------------------------------------------------------


def _strip_lang_marker(text: str) -> str:
    return _LANG_MARKER_RE.sub("", text, count=1)


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    text = _strip_lang_marker(text)
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return {}, text
    raw_fm = match.group(1)
    body = text[match.end() :]
    frontmatter: dict[str, str] = {}
    for line in raw_fm.splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        frontmatter[key.strip()] = value.strip()
    return frontmatter, body


def _is_allowlisted_paragraph(paragraph: str) -> bool:
    stripped = paragraph.strip()
    if not stripped:
        return True
    if _TRACK_HEADING_RE.search(stripped):
        return True
    if _SECTION_BOILER_RE.search(stripped):
        return True
    if _SSOT_BANNER_RE.search(stripped) and len(stripped) < 120:
        return True
    lines = [ln.strip() for ln in stripped.splitlines() if ln.strip()]
    if len(lines) == 1:
        if _ENV_VAR_LINE_RE.match(lines[0]) or _URL_LINE_RE.match(lines[0]):
            return True
    if all(ln.startswith("|") for ln in lines) and len(lines) <= 6:
        return True
    return False


def extract_paragraphs(text: str) -> list[str]:
    _, body = parse_frontmatter(text)
    body = _CODE_BLOCK_RE.sub("\n", body)
    chunks = re.split(r"\n\s*\n", body)
    paragraphs: list[str] = []
    for chunk in chunks:
        prose = " ".join(line.strip() for line in chunk.splitlines() if line.strip())
        prose = prose.strip()
        if len(prose) < MIN_PARAGRAPH_LEN:
            continue
        if _is_allowlisted_paragraph(prose):
            continue
        paragraphs.append(prose)
    return paragraphs


def detect_layer(rel_path: str, frontmatter: dict[str, str]) -> DocLayer:
    if frontmatter.get("lint_scope") == "human-first":
        return DocLayer.SKIP
    name = Path(rel_path).name
    if name.startswith("RES_"):
        return DocLayer.RES
    if rel_path.startswith("docs/specs/") and frontmatter.get("type") == "SPEC":
        return DocLayer.SPEC
    if frontmatter.get("guide_type") == "runbook":
        return DocLayer.RUNBOOK
    if name.lower().startswith("guide_") or name.startswith("GUIDE_"):
        return DocLayer.RUNBOOK
    return DocLayer.SKIP


def parse_document(path: Path, repo_root: Path) -> ParsedDoc | None:
    rel = path.relative_to(repo_root).as_posix()
    if not _is_included(rel):
        return None
    text = path.read_text(encoding="utf-8")
    frontmatter, _ = parse_frontmatter(text)
    layer = detect_layer(rel, frontmatter)
    if layer is DocLayer.SKIP:
        return None
    paragraphs = tuple(extract_paragraphs(text))
    return ParsedDoc(path=path, rel_path=rel, layer=layer, paragraphs=paragraphs)


def _is_included(rel_path: str) -> bool:
    if any(rel_path.startswith(prefix) for prefix in EXCLUDE_PREFIXES):
        return False
    return any(fnmatch(rel_path, pattern) for pattern in INCLUDE_PATTERNS)


def discover_documents(repo_root: Path) -> list[ParsedDoc]:
    docs: list[ParsedDoc] = []
    for pattern in INCLUDE_PATTERNS:
        for path in sorted(repo_root.glob(pattern)):
            if not path.is_file():
                continue
            parsed = parse_document(path, repo_root)
            if parsed is not None:
                docs.append(parsed)
    seen: set[str] = set()
    unique: list[ParsedDoc] = []
    for doc in docs:
        if doc.rel_path in seen:
            continue
        seen.add(doc.rel_path)
        unique.append(doc)
    return unique


# ---------------------------------------------------------------------------
# similarity (jaccard)
# ---------------------------------------------------------------------------


def tokenize(text: str) -> set[str]:
    return {token for token in text.split() if token}


def jaccard_similarity(a: str, b: str) -> float:
    tokens_a = tokenize(a)
    tokens_b = tokenize(b)
    if not tokens_a or not tokens_b:
        return 0.0
    union = tokens_a | tokens_b
    if not union:
        return 0.0
    return len(tokens_a & tokens_b) / len(union)


def paragraph_hash(text: str) -> str:
    normalized = " ".join(text.split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


# ---------------------------------------------------------------------------
# layer_rules
# ---------------------------------------------------------------------------


def spec_domain_prefix(rel_path: str) -> str | None:
    parts = rel_path.split("/")
    try:
        idx = parts.index("specs")
    except ValueError:
        return None
    if idx + 1 < len(parts) - 1:
        return parts[idx + 1]
    return None


def integration_neighbor_key(rel_path: str) -> str | None:
    if "/integration/" in rel_path or rel_path.endswith("/integration"):
        return "integration"
    return spec_domain_prefix(rel_path)


def knowledge_neighbor_key(rel_path: str) -> str | None:
    """Cluster key for intra-layer RES↔RES and RUNBOOK↔RUNBOOK comparison."""
    name = Path(rel_path).name
    lower_name = name.lower()

    if "/integration/" in rel_path or name.startswith("RES_INT_"):
        return "integration"

    if "/certification/" in rel_path or name.startswith("RES_CERT_"):
        return "certification"

    if "billing_edi" in lower_name or name.startswith("RES_billing_edi"):
        return "billing_edi"
    if name.startswith("guide_RES_billing_edi"):
        return "billing_edi"

    if name.startswith("RES_medical_standard"):
        return "medical_standard"

    if "/debug/" in rel_path:
        if "consultation_grid" in lower_name:
            return "debug/consultation_grid"
        if "prescription" in lower_name:
            return "debug/prescription"
        if "session" in lower_name:
            return "debug/session"
        if "valkey" in lower_name:
            return "debug/valkey"
        return None

    return None


def allowed_pair(doc_a: ParsedDoc, doc_b: ParsedDoc) -> bool:
    layer_a, layer_b = doc_a.layer, doc_b.layer
    if layer_a == layer_b:
        if layer_a is DocLayer.SPEC:
            domain_a = spec_domain_prefix(doc_a.rel_path)
            domain_b = spec_domain_prefix(doc_b.rel_path)
            return domain_a is not None and domain_a == domain_b
        if layer_a in {DocLayer.RES, DocLayer.RUNBOOK}:
            key_a = knowledge_neighbor_key(doc_a.rel_path)
            key_b = knowledge_neighbor_key(doc_b.rel_path)
            return key_a is not None and key_a == key_b
        return False
    pair = {layer_a, layer_b}
    if pair == {DocLayer.RUNBOOK, DocLayer.SPEC}:
        return True
    if pair == {DocLayer.RUNBOOK, DocLayer.RES}:
        return True
    return False


def is_neighbor(doc_a: ParsedDoc, doc_b: ParsedDoc) -> bool:
    key_a = knowledge_neighbor_key(doc_a.rel_path) or integration_neighbor_key(doc_a.rel_path)
    key_b = knowledge_neighbor_key(doc_b.rel_path) or integration_neighbor_key(doc_b.rel_path)
    return key_a is not None and key_a == key_b


# ---------------------------------------------------------------------------
# compare / scan
# ---------------------------------------------------------------------------


def compare_pair(
    doc_a: ParsedDoc, doc_b: ParsedDoc, *, threshold: float = DEFAULT_THRESHOLD
) -> list[Violation]:
    if not allowed_pair(doc_a, doc_b):
        return []
    violations: list[Violation] = []
    for para_a in doc_a.paragraphs:
        for para_b in doc_b.paragraphs:
            score = jaccard_similarity(para_a, para_b)
            if score < threshold:
                continue
            para_hash = paragraph_hash(para_a)
            violations.append(
                Violation(
                    path_a=doc_a.rel_path,
                    path_b=doc_b.rel_path,
                    paragraph_hash=para_hash,
                    jaccard=score,
                    snippet=para_a[:80],
                )
            )
    return violations


def violation_fingerprint(violation: Violation) -> str:
    return f"{violation.path_a}|{violation.path_b}|{violation.paragraph_hash}"


def compare_documents(
    path_a: Path,
    path_b: Path,
    *,
    repo_root: Path | None = None,
    threshold: float = DEFAULT_THRESHOLD,
) -> list[str]:
    root = repo_root or ROOT
    doc_a = parse_document(path_a.resolve(), root)
    doc_b = parse_document(path_b.resolve(), root)
    if doc_a is None or doc_b is None:
        return []
    return [violation_fingerprint(v) for v in compare_pair(doc_a, doc_b, threshold=threshold)]


def scan_docs(
    repo_root: Path,
    *,
    threshold: float = DEFAULT_THRESHOLD,
    touched_only: bool = False,
) -> list[str]:
    docs = discover_documents(repo_root)
    if touched_only:
        touched = _git_touched_rel_paths(repo_root)
        docs = _filter_touched_scope(docs, touched)
    fingerprints: set[str] = set()
    for i, doc_a in enumerate(docs):
        for doc_b in docs[i + 1 :]:
            for violation in compare_pair(doc_a, doc_b, threshold=threshold):
                fingerprints.add(violation_fingerprint(violation))
    return sorted(fingerprints)


def _git_touched_rel_paths(repo_root: Path) -> set[str]:
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return set()
    if result.returncode != 0:
        return set()
    return {line.strip() for line in result.stdout.splitlines() if line.strip().endswith(".md")}


def _filter_touched_scope(docs: list[ParsedDoc], touched: set[str]) -> list[ParsedDoc]:
    if not touched:
        return []
    scope: set[str] = set(touched)
    for doc in docs:
        if doc.rel_path in touched:
            for other in docs:
                if other.rel_path == doc.rel_path:
                    continue
                if is_neighbor(doc, other) and other.layer in {DocLayer.SPEC, DocLayer.RES}:
                    scope.add(other.rel_path)
    return [doc for doc in docs if doc.rel_path in scope]


# ---------------------------------------------------------------------------
# baseline CLI
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description="Docs cross-layer DRY linter")
    parser.add_argument("--check", action="store_true", help="Fail on new violations vs baseline")
    parser.add_argument("--update-baseline", action="store_true", help="Rewrite baseline file")
    parser.add_argument(
        "--check-touched",
        action="store_true",
        help="Scan git-touched docs and integration neighbors only",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=DEFAULT_THRESHOLD,
        help=f"Jaccard threshold (default {DEFAULT_THRESHOLD})",
    )
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    args = parser.parse_args()

    if not args.check and not args.update_baseline and not args.check_touched:
        parser.print_help()
        return 0

    current = set(
        scan_docs(
            args.repo_root,
            threshold=args.threshold,
            touched_only=args.check_touched,
        )
    )
    loaded = load_baseline(BASELINE_PATH)

    if args.update_baseline:
        write_baseline(BASELINE_PATH, current)
        print(f"[docs-dry] Baseline updated: {len(current)} entries → {BASELINE_PATH}")
        return 0

    new_entries = filter_new_entries(current, loaded)
    mode = "touched" if args.check_touched else "full"
    print(
        f"[docs-dry] mode={mode} violations: current={len(current)}, "
        f"baseline={len(loaded)}, new={len(new_entries)}"
    )

    if args.check and new_entries:
        print("[docs-dry] FAIL — new cross-layer duplicate violations:")
        for entry in new_entries[:25]:
            print(f"  - {entry}")
        if len(new_entries) > 25:
            print(f"  ... and {len(new_entries) - 25} more")
        return 1

    if args.check or args.check_touched:
        print("[docs-dry] PASS — no new cross-layer duplicate violations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
