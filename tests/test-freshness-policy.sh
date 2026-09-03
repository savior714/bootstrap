#!/bin/sh
# test-freshness-policy.sh — regression lock for the Concurrent Development &
# Publication Freshness Policy (contract-first vertical slice).
#
# Covers R1–R5 + second-advance circuit breaker with the minimal combination:
# canonical DEVELOPMENT.md contract greps plus focused file://-remote helper
# fixtures. R5 reuses the existing identity proof in test-git-safety.sh
# (no duplicate fixture here — only presence assertions on that proof).
#
# Run: sh tests/test-freshness-policy.sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd -P)
ENTRY="${ROOT}/scripts/git-safety"
CANON="${ROOT}/scripts/lib/git-safety-canonical.sh"
SCAFFOLD_CANON="${ROOT}/scaffold/scripts/lib/git-safety-canonical.sh"
DEV="${ROOT}/scaffold/docs/operations/DEVELOPMENT.md"
PRIOR_SUITE="${ROOT}/tests/test-git-safety.sh"

PASS=0
FAIL=0

export GIT_CONFIG_NOSYSTEM=1
export GIT_CONFIG_GLOBAL=/dev/null
export GIT_AUTHOR_NAME="freshness-test"
export GIT_AUTHOR_EMAIL="test@example.invalid"
export GIT_COMMITTER_NAME="freshness-test"
export GIT_COMMITTER_EMAIL="test@example.invalid"
export GIT_CONFIG_COUNT=1
export GIT_CONFIG_KEY_0="init.defaultBranch"
export GIT_CONFIG_VALUE_0="main"

TMPBASE=$(mktemp -d "${TMPDIR:-/tmp}/freshness-proof.XXXXXX")
trap 'rm -rf "${TMPBASE}"' EXIT INT TERM

pass() { PASS=$((PASS + 1)); printf 'PASS: %s\n' "${1}"; }
fail() { FAIL=$((FAIL + 1)); printf 'FAIL: %s\n' "${1}"; printf '      %s\n' "${2:-}"; }

assert_contains() {
	if grep -q -F -- "${3}" "${2}"; then pass "${1}"; else fail "${1}" "missing [${3}] in ${2}"; fi
}

assert_not_contains() {
	if grep -q -F -- "${3}" "${2}"; then fail "${1}" "forbidden [${3}] found in ${2}"; else pass "${1}"; fi
}

assert_exit() {
	if [ "${2}" = "${3}" ]; then pass "${1}"; else fail "${1}" "expected exit ${2} got ${3}"; fi
}

assert_eq() {
	if [ "${2}" = "${3}" ]; then pass "${1}"; else fail "${1}" "expected [${2}] got [${3}]"; fi
}

run_entry() {
	_out=$1
	shift
	[ "${1:-}" = "--" ] && shift
	set +e
	sh "${ENTRY}" "$@" >"${_out}" 2>&1
	_code=$?
	set -e
	printf '%s' "${_code}"
}

make_origin_with_clone() {
	_name=$1
	_bare="${TMPBASE}/${_name}.git"
	_seed="${TMPBASE}/${_name}-seed"
	git init -q --bare -b main "${_bare}"
	git --git-dir="${_bare}" symbolic-ref HEAD refs/heads/main
	git clone -q "file://${_bare}" "${_seed}" 2>/dev/null
	git -C "${_seed}" commit -q --allow-empty -m seed
	git -C "${_seed}" push -q origin main
	_clone="${TMPBASE}/${_name}-clone"
	git clone -q "file://${_bare}" "${_clone}" 2>/dev/null
	printf '%s %s' "${_bare}" "${_clone}"
}

field() {
	grep -F -- "${2}: " "${1}" | head -n 1 | sed -e "s/^${2}: //"
}

printf '== Freshness Policy proof ==\nROOT=%s\nTMP=%s\n' "${ROOT}" "${TMPBASE}"

# --- 0. parity + contract version ----------------------------------------------
if cmp -s "${CANON}" "${SCAFFOLD_CANON}"; then
	pass "root/scaffold canonical helper byte-identical"
else
	fail "root/scaffold canonical helper byte-identical" "diff scripts/ vs scaffold/scripts/"
fi
if grep -q -F 'GIT_SAFETY_CONTRACT_VERSION="1"' "${CANON}"; then
	pass "contract remains bootstrap-git-safety/1"
else
	fail "contract remains bootstrap-git-safety/1" "version changed"
fi
if grep -q -F 'EXPECTED_BASE' "${CANON}"; then
	fail "no EXPECTED_BASE string-comparison authority in helper" "found EXPECTED_BASE"
else
	pass "no EXPECTED_BASE string-comparison authority in helper"
fi
if grep -q -F 'merge-base --is-ancestor' "${CANON}"; then
	pass "helper judges topology by direct containment evidence"
else
	fail "helper judges topology by direct containment evidence" "no merge-base containment"
fi

# --- 1. canonical contract: freshness semantics discoverable --------------------
assert_contains "contract: SEMANTIC_READY vs PUBLISHABLE" "${DEV}" 'SEMANTIC_READY != PUBLISHABLE'
assert_contains "contract: SEMANTIC_READY defined" "${DEV}" 'SEMANTIC_READY'
assert_contains "contract: PUBLISHABLE defined" "${DEV}" 'PUBLISHABLE'
assert_contains "contract: JIT publication binding" "${DEV}" 'JIT topology binding'
assert_contains "contract: JIT flow binding step" "${DEV}" 'final JIT topology binding'
assert_contains "contract: topology-only preservation" "${DEV}" 'preserve semantic work'
assert_contains "contract: existing proof reuse" "${DEV}" 'reuse existing proof'
assert_contains "contract: semantic-owner READMIT" "${DEV}" 'READMIT'
assert_contains "contract: blind salvage forbidden" "${DEV}" 'Never blind-salvage'
assert_contains "contract: proof-owner targeted recheck" "${DEV}" 'affected targeted proof'
assert_contains "contract: uncertainty nearest proof" "${DEV}" 'nearest relevant targeted proof'
assert_contains "contract: UNKNOWN->FULL_REBUILD forbidden" "${DEV}" 'UNKNOWN -> FULL_REBUILD'
assert_contains "contract: Recover-or-Preserve" "${DEV}" 'Recover-or-Preserve'
assert_contains "contract: read-only reconstruction first" "${DEV}" 'read-only reconstruction'
assert_contains "contract: insufficient-reconstruction continuable" "${DEV}" 'CONTINUABLE'
assert_contains "contract: second-advance circuit breaker" "${DEV}" 'circuit breaker'
assert_contains "contract: no same-attempt rebind loop" "${DEV}" 'same attempt'
assert_contains "contract: WATCH_SURFACES DIRECT_PATHS" "${DEV}" 'DIRECT_PATHS'
assert_contains "contract: WATCH_SURFACES SEMANTIC_OWNERS" "${DEV}" 'SEMANTIC_OWNERS'
assert_contains "contract: WATCH_SURFACES PROOF_OWNERS" "${DEV}" 'PROOF_OWNERS'
assert_contains "contract: WATCH_SURFACES transient" "${DEV}" 'transient handoff/execution evidence'
assert_contains "contract: no durable dependency graph" "${DEV}" 'not a durable project-wide dependency graph'
assert_contains "contract: Git Safety owns objective facts" "${DEV}" 'only objective Git/repository facts'
assert_contains "contract: REMOTE_ADVANCED never commands rebuild" "${DEV}" 'never commands a rebuild'
assert_contains "contract: proof runtime owns PASS/FAIL" "${DEV}" 'owns actual PASS/FAIL'
assert_contains "contract: remote owns truth + read-back" "${DEV}" 'owns final publication truth'
assert_contains "contract: beweging is not invalidation" "${DEV}" 'is not semantic invalidation'
assert_contains "contract: forbidden TOPOLOGY_STALE->PROOF_STALE" "${DEV}" 'TOPOLOGY_STALE -> PROOF_STALE'
assert_contains "contract: forbidden MISSING_METADATA->READMIT" "${DEV}" 'MISSING_METADATA -> READMIT'
assert_contains "contract: concurrent semantic work permitted" "${DEV}" 'Concurrent semantic development'
assert_contains "contract: no global queue" "${DEV}" 'never serialized into a global queue'
assert_contains "contract: keeps serialization-boundary wording" "${DEV}" 'serialize that mutation/materialization boundary'
assert_contains "contract: keeps no-helper-mutex wording" "${DEV}" 'not a helper-enforced mutex'

# --- fixture A: R1 topology-only advance ----------------------------------------
# shellcheck disable=SC2046
set -- $(make_origin_with_clone freshA)
BARE_A=$1
CLONE_A=$2
BASE_A=$(git -C "${CLONE_A}" rev-parse origin/main)
printf 'fixture A: bare=%s clone=%s base=%s\n' "${BARE_A}" "${CLONE_A}" "${BASE_A}"

OUT_A_CREATE="${TMPBASE}/a-create.out"
CODE=$(run_entry "${OUT_A_CREATE}" -- --repo "${CLONE_A}" create r1task)
assert_exit "R1: create r1task exit 0" "0" "${CODE}"
WT_A=$(field "${OUT_A_CREATE}" 'WORKTREE')
echo "semantic-payload-v1" >"${WT_A}/feature.txt"
git -C "${WT_A}" add feature.txt
git -C "${WT_A}" commit -q -m "r1 semantic work"
printf 'PASS r1task proof-criterion\n' >"${WT_A}/proof-evidence.log"
H1_A=$(git -C "${WT_A}" rev-parse HEAD)
EVIDENCE_SUM_BEFORE=$(cksum <"${WT_A}/proof-evidence.log")

OTHER_A="${TMPBASE}/other-a"
git clone -q "file://${BARE_A}" "${OTHER_A}" 2>/dev/null
git -C "${OTHER_A}" commit -q --allow-empty -m "unrelated-trunk-advance"
git -C "${OTHER_A}" push -q origin main
CUR_A=$(git -C "${CLONE_A}" ls-remote "file://${BARE_A}" refs/heads/main | awk '{print $1}')

OUT_A_PRE="${TMPBASE}/a-pre.out"
CODE=$(run_entry "${OUT_A_PRE}" -- --repo "${CLONE_A}" pre-publish r1task)
assert_exit "R1: topology-only advance stays BLOCKED exit 3" "3" "${CODE}"
assert_contains "R1: reason is topology-only REMOTE_ADVANCED" "${OUT_A_PRE}" "REASON: REMOTE_ADVANCED"
assert_contains "R1: stays topology verdict" "${OUT_A_PRE}" "topology-only verdict"
assert_eq "R1: candidate HEAD preserved (no redo)" "${H1_A}" "$(git -C "${WT_A}" rev-parse HEAD)"
assert_eq "R1: proof evidence bytes preserved" "${EVIDENCE_SUM_BEFORE}" "$(cksum <"${WT_A}/proof-evidence.log")"
assert_eq "R1: admitted base untouched" "${BASE_A}" "$(field "${OUT_A_PRE}" 'ADMITTED_BASE')"
assert_eq "R1: current base is the unrelated advance" "${CUR_A}" "$(field "${OUT_A_PRE}" 'CURRENT_BASE')"
assert_not_contains "R1: no semantic-invalidation claim" "${OUT_A_PRE}" "SEMANTIC_INVALID"
assert_not_contains "R1: no blind re-derivation prescription" "${OUT_A_PRE}" "re-apply the semantic delta"
assert_not_contains "R1: no proof-invalidation claim" "${OUT_A_PRE}" "proof invalid"

# R1 JIT binding: fresh admission at CURRENT + same semantic delta, no redo.
OUT_A_BIND="${TMPBASE}/a-bind-create.out"
CODE=$(run_entry "${OUT_A_BIND}" -- --repo "${CLONE_A}" create r1bind)
assert_exit "R1: JIT-bind admission at fresh base exit 0" "0" "${CODE}"
assert_eq "R1: JIT bind tracks moved remote" "${CUR_A}" "$(field "${OUT_A_BIND}" 'BASE')"
WT_BIND=$(field "${OUT_A_BIND}" 'WORKTREE')
echo "semantic-payload-v1" >"${WT_BIND}/feature.txt"
git -C "${WT_BIND}" add feature.txt
git -C "${WT_BIND}" commit -q -m "r1 semantic delta bound onto fresh trunk (single binding cost)"
H_BIND=$(git -C "${WT_BIND}" rev-parse HEAD)
OUT_A_BIND_PRE="${TMPBASE}/a-bind-pre.out"
CODE=$(run_entry "${OUT_A_BIND_PRE}" -- --repo "${CLONE_A}" pre-publish r1bind)
assert_exit "R1: JIT-bound candidate is PUBLISHABLE_FF" "0" "${CODE}"
assert_contains "R1: JIT-bound publishable" "${OUT_A_BIND_PRE}" "GIT_SAFETY: PUBLISHABLE_FF"
assert_eq "R1: JIT-bound candidate HEAD" "${H_BIND}" "$(field "${OUT_A_BIND_PRE}" 'CANDIDATE_HEAD')"

# R1 FF-contained: old candidate already containing CURRENT is not stale.
git -C "${WT_A}" fetch -q origin 2>/dev/null || true
git -C "${WT_A}" reset -q --hard "${CUR_A}"
echo "semantic-payload-v1" >"${WT_A}/feature.txt"
git -C "${WT_A}" add feature.txt proof-evidence.log
git -C "${WT_A}" commit -q -m "r1 delta as child of current trunk"
H1_A2=$(git -C "${WT_A}" rev-parse HEAD)
if git -C "${WT_A}" merge-base --is-ancestor "${CUR_A}" "${H1_A2}" 2>/dev/null; then
	pass "R1: rebound HEAD contains current base (containment evidence)"
else
	fail "R1: rebound HEAD contains current base (containment evidence)" "H=${H1_A2} C=${CUR_A}"
fi
OUT_A_FF="${TMPBASE}/a-ff.out"
CODE=$(run_entry "${OUT_A_FF}" -- --repo "${CLONE_A}" pre-publish r1task)
assert_exit "R1: FF-contained candidate is PUBLISHABLE_FF, not stale" "0" "${CODE}"
assert_contains "R1: FF-contained publishable" "${OUT_A_FF}" "GIT_SAFETY: PUBLISHABLE_FF"
if grep -q -F "REASON: REMOTE_ADVANCED" "${OUT_A_FF}"; then
	fail "R1: FF-contained candidate never reports REMOTE_ADVANCED" "stale leak"
else
	pass "R1: FF-contained candidate never reports REMOTE_ADVANCED"
fi

# --- R2/R3: helper stays silent on semantic/proof impact -------------------------
assert_not_contains "R2: helper never prescribes READMIT" "${OUT_A_PRE}" "READMIT"
assert_not_contains "R2: helper never claims semantic overlap" "${OUT_A_PRE}" "semantic overlap"
assert_not_contains "R3: helper never demands broad re-proof" "${OUT_A_PRE}" "re-run broad"
assert_contains "R2/R3: helper defers classification to contract" "${OUT_A_PRE}" "governing repository/runtime contract"

# --- R4: missing legacy metadata -> Recover-or-Preserve ---------------------------
OUT_R4_CREATE="${TMPBASE}/r4-create.out"
CODE=$(run_entry "${OUT_R4_CREATE}" -- --repo "${CLONE_A}" create r4task)
assert_exit "R4: create r4task exit 0" "0" "${CODE}"
WT_R4=$(field "${OUT_R4_CREATE}" 'WORKTREE')
R4_RDIR="${CLONE_A}/.git/git-safety/tasks/r4task"
if [ -f "${R4_RDIR}/BASE" ] && [ -f "${R4_RDIR}/WORKTREE" ]; then
	pass "R4: admission record is thin (BASE/WORKTREE only)"
else
	fail "R4: admission record is thin (BASE/WORKTREE only)" "${R4_RDIR}"
fi
# Legacy shape: drop the optional ADMITTED_AT timestamp; classification must
# still work from repository evidence alone (no metadata -> rebuild demand).
rm -f "${R4_RDIR}/ADMITTED_AT"
OUT_R4_CHECK="${TMPBASE}/r4-check.out"
CODE=$(run_entry "${OUT_R4_CHECK}" -- --repo "${CLONE_A}" check r4task)
assert_exit "R4: thin-metadata check still classifies exit 0" "0" "${CODE}"
assert_contains "R4: thin-metadata check OK" "${OUT_R4_CHECK}" "GIT_SAFETY: OK"
OUT_R4_PRE="${TMPBASE}/r4-pre.out"
CODE=$(run_entry "${OUT_R4_PRE}" -- --repo "${CLONE_A}" pre-publish r4task)
assert_exit "R4: thin-metadata pre-publish at fresh base classifies exit 0" "0" "${CODE}"
assert_contains "R4: thin-metadata publishable (no rebuild demand)" "${OUT_R4_PRE}" "GIT_SAFETY: PUBLISHABLE_FF"
assert_eq "R4: worktree preserved, nothing rematerialized" "$(git -C "${WT_R4}" rev-parse HEAD)" "$(field "${OUT_R4_PRE}" 'CANDIDATE_HEAD')"
# Legacy old-base thin record whose candidate already contains CURRENT:
# still FF-publishable — missing metadata never forces rematerialization.
printf '%s\n' "${BASE_A}" >"${R4_RDIR}/BASE"
OUT_R4_LEGACY="${TMPBASE}/r4-legacy.out"
CODE=$(run_entry "${OUT_R4_LEGACY}" -- --repo "${CLONE_A}" pre-publish r4task)
assert_exit "R4: legacy old-base contained candidate publishable" "0" "${CODE}"
assert_contains "R4: legacy contained publishable" "${OUT_R4_LEGACY}" "GIT_SAFETY: PUBLISHABLE_FF"
if grep -q -F "REASON: REMOTE_ADVANCED" "${OUT_R4_LEGACY}"; then
	fail "R4: legacy contained candidate never stale" "stale leak"
else
	pass "R4: legacy contained candidate never stale"
fi
# Legacy stale thin record (HEAD at old base, remote advanced): topology-only
# BLOCKED, candidate preserved, publication alone continuable — no rebuild.
git -C "${CLONE_A}" worktree add --detach -- "${TMPBASE}/r4legacy-wt" "${BASE_A}" 2>/dev/null
WT_R4LEG_PHYS=$(CDPATH= cd -- "${TMPBASE}/r4legacy-wt" && pwd -P)
R4LEG_RDIR="${CLONE_A}/.git/git-safety/tasks/r4legacy"
mkdir -p "${R4LEG_RDIR}"
printf '%s\n' "${BASE_A}" >"${R4LEG_RDIR}/BASE"
printf 'origin/main\n' >"${R4LEG_RDIR}/BASE_REF"
git -C "${CLONE_A}" config --get remote.origin.url >"${R4LEG_RDIR}/REMOTE_URL"
printf '%s\n' "${WT_R4LEG_PHYS}" >"${R4LEG_RDIR}/WORKTREE"
H_R4LEG=$(git -C "${WT_R4LEG_PHYS}" rev-parse HEAD)
OUT_R4_STALE="${TMPBASE}/r4-stale.out"
CODE=$(run_entry "${OUT_R4_STALE}" -- --repo "${CLONE_A}" pre-publish r4legacy)
assert_exit "R4: legacy stale candidate topology-BLOCKED exit 3" "3" "${CODE}"
assert_contains "R4: legacy stale verdict is topology-only" "${OUT_R4_STALE}" "topology-only verdict"
assert_eq "R4: legacy stale candidate preserved" "${H_R4LEG}" "$(git -C "${WT_R4LEG_PHYS}" rev-parse HEAD)"
if grep -q -F "SEMANTIC_OWNERS" "${CANON}" || grep -q -F "DIRECT_PATHS" "${CANON}"; then
	fail "R4: helper requires no WATCH_SURFACES metadata" "watch-surface gating in helper"
else
	pass "R4: helper requires no WATCH_SURFACES metadata"
fi

# --- R5: wrong invocation context (reuse existing identity proof) ------------------
assert_contains "R5: prior suite proves TASK_ID_REQUIRED" "${PRIOR_SUITE}" "TASK_ID_REQUIRED"
assert_contains "R5: prior suite proves AMBIGUOUS_TASK" "${PRIOR_SUITE}" "AMBIGUOUS_TASK"
assert_contains "R5: prior suite forbids implicit selection" "${PRIOR_SUITE}" "never implicitly selects"
assert_contains "R5: prior suite forbids REMOTE_ADVANCED leak (lone)" "${PRIOR_SUITE}" "must not report REMOTE_ADVANCED"
assert_contains "R5: prior suite forbids PUBLISHABLE leak (multi)" "${PRIOR_SUITE}" "must not report PUBLISHABLE"
assert_contains "R5: contract names TASK_ID_REQUIRED" "${DEV}" "TASK_ID_REQUIRED"
assert_contains "R5: contract forbids unrelated REMOTE_ADVANCED" "${DEV}" "never reports that unrelated admission"

# --- SECOND_ADVANCE: lose the race once, keep state, no loop ----------------------
# shellcheck disable=SC2046
set -- $(make_origin_with_clone freshS)
BARE_S=$1
CLONE_S=$2
OUT_S_CREATE="${TMPBASE}/s-create.out"
CODE=$(run_entry "${OUT_S_CREATE}" -- --repo "${CLONE_S}" create satask)
assert_exit "SA: create satask exit 0" "0" "${CODE}"
WT_S=$(field "${OUT_S_CREATE}" 'WORKTREE')
echo "sa-payload" >"${WT_S}/sa.txt"
git -C "${WT_S}" add sa.txt
git -C "${WT_S}" commit -q -m "sa semantic work"
H_S=$(git -C "${WT_S}" rev-parse HEAD)
OTHER_S1="${TMPBASE}/other-s1"
git clone -q "file://${BARE_S}" "${OTHER_S1}" 2>/dev/null
git -C "${OTHER_S1}" commit -q --allow-empty -m "first-advance"
git -C "${OTHER_S1}" push -q origin main
CUR_S1=$(git -C "${CLONE_S}" ls-remote "file://${BARE_S}" refs/heads/main | awk '{print $1}')
OUT_S_BIND="${TMPBASE}/s-bind-create.out"
CODE=$(run_entry "${OUT_S_BIND}" -- --repo "${CLONE_S}" create sabind)
assert_exit "SA: JIT-bind admission at first advance exit 0" "0" "${CODE}"
WT_SBIND=$(field "${OUT_S_BIND}" 'WORKTREE')
echo "sa-payload" >"${WT_SBIND}/sa.txt"
git -C "${WT_SBIND}" add sa.txt
git -C "${WT_SBIND}" commit -q -m "sa JIT-bound child of first advance"
H_SBIND=$(git -C "${WT_SBIND}" rev-parse HEAD)
LOG_SBIND_BEFORE=$(git -C "${WT_SBIND}" rev-list --count HEAD)
# Second writer advances BEFORE the bound candidate publishes.
OTHER_S2="${TMPBASE}/other-s2"
git clone -q "file://${BARE_S}" "${OTHER_S2}" 2>/dev/null
git -C "${OTHER_S2}" commit -q --allow-empty -m "second-advance"
git -C "${OTHER_S2}" push -q origin main
CUR_S2=$(git -C "${CLONE_S}" ls-remote "file://${BARE_S}" refs/heads/main | awk '{print $1}')
if [ "${CUR_S1}" != "${CUR_S2}" ]; then
	pass "SA: second advance proven (C1 != C2)"
else
	fail "SA: second advance proven (C1 != C2)" "no movement"
fi
OUT_S_PRE="${TMPBASE}/s-pre.out"
CODE=$(run_entry "${OUT_S_PRE}" -- --repo "${CLONE_S}" pre-publish sabind)
assert_exit "SA: second advance ends the attempt BLOCKED exit 3" "3" "${CODE}"
assert_contains "SA: second-advance reason stays REMOTE_ADVANCED" "${OUT_S_PRE}" "REASON: REMOTE_ADVANCED"
assert_contains "SA: second advance is not task failure wording" "${OUT_S_PRE}" "topology-only verdict"
assert_eq "SA: bound HEAD preserved (no same-attempt rebind)" "${H_SBIND}" "$(git -C "${WT_SBIND}" rev-parse HEAD)"
assert_eq "SA: bound log untouched (no re-proof loop commits)" "${LOG_SBIND_BEFORE}" "$(git -C "${WT_SBIND}" rev-list --count HEAD)"
assert_eq "SA: original semantic HEAD preserved" "${H_S}" "$(git -C "${WT_S}" rev-parse HEAD)"
if [ "$(grep -c -F "REASON:" "${OUT_S_PRE}")" = "1" ]; then
	pass "SA: single verdict per attempt (no loop)"
else
	fail "SA: single verdict per attempt (no loop)" "REASON count $(grep -c -F "REASON:" "${OUT_S_PRE}")"
fi

printf '\n== result: %s passed, %s failed ==\n' "${PASS}" "${FAIL}"
[ "${FAIL}" = "0" ]
