#!/bin/sh
# test-git-safety.sh — bounded proof for the Git Safety Baseline.
#
# Self-contained POSIX sh harness (no framework dependency: this repository
# owns no test architecture). Uses file:// bare remotes in temp dirs, so no
# network or GitHub dependency exists.
#
# Run: sh tests/test-git-safety.sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd -P)
ENTRY="${ROOT}/scripts/git-safety"
CANON="${ROOT}/scripts/lib/git-safety-canonical.sh"

PASS=0
FAIL=0

# Isolate git from ambient user/system config; identity is fixture-scoped.
export GIT_CONFIG_NOSYSTEM=1
export GIT_CONFIG_GLOBAL=/dev/null
export GIT_AUTHOR_NAME="git-safety-test"
export GIT_AUTHOR_EMAIL="test@example.invalid"
export GIT_COMMITTER_NAME="git-safety-test"
export GIT_COMMITTER_EMAIL="test@example.invalid"
export GIT_CONFIG_COUNT=1
export GIT_CONFIG_KEY_0="init.defaultBranch"
export GIT_CONFIG_VALUE_0="main"

TMPBASE=$(mktemp -d "${TMPDIR:-/tmp}/git-safety-proof.XXXXXX")
trap 'rm -rf "${TMPBASE}"' EXIT INT TERM

pass() { PASS=$((PASS + 1)); printf 'PASS: %s\n' "${1}"; }
fail() { FAIL=$((FAIL + 1)); printf 'FAIL: %s\n' "${1}"; printf '      %s\n' "${2:-}"; }

assert_eq() {
	# assert_eq NAME expected actual
	if [ "${2}" = "${3}" ]; then pass "${1}"; else fail "${1}" "expected [${2}] got [${3}]"; fi
}

assert_contains() {
	# assert_contains NAME haystack-file needle-fixed
	if grep -q -F -- "${3}" "${2}"; then pass "${1}"; else fail "${1}" "missing [${3}] in ${2}"; fi
}

assert_exit() {
	# assert_exit NAME expected actual
	if [ "${2}" = "${3}" ]; then pass "${1}"; else fail "${1}" "expected exit ${2} got ${3}"; fi
}

run_entry() {
	# run_entry outfile -- args...  (inherits current environment; callers
	# export GIT_SAFETY_* overrides beforehand — space-safe, no eval).
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
	# make_origin_with_clone NAME -> prints "<bare> <clone>"
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
	# field FILE KEY -> value after "KEY: "
	grep -F -- "${2}: " "${1}" | head -n 1 | sed -e "s/^${2}: //"
}

printf '== Git Safety Baseline proof ==\nROOT=%s\nTMP=%s\n' "${ROOT}" "${TMPBASE}"

# --- 1. contract/discovery ------------------------------------------------------
if [ -x "${ENTRY}" ]; then pass "entrypoint exists and is executable"; else fail "entrypoint exists and is executable" "${ENTRY}"; fi
if [ -x "${ROOT}/scaffold/scripts/git-safety" ]; then pass "scaffold entrypoint exists"; else fail "scaffold entrypoint exists"; fi
if cmp -s "${ENTRY}" "${ROOT}/scaffold/scripts/git-safety" && cmp -s "${CANON}" "${ROOT}/scaffold/scripts/lib/git-safety-canonical.sh"; then
	pass "root materialization identical to scaffold template (no drift)"
else
	fail "root materialization identical to scaffold template (no drift)" "diff root scripts/ vs scaffold/scripts/"
fi
if grep -q -F './scripts/git-safety create' "${ROOT}/scaffold/docs/operations/DEVELOPMENT.md"; then
	pass "development contract discovers the entrypoint"
else
	fail "development contract discovers the entrypoint" "DEVELOPMENT.md"
fi
if grep -q -F 'do not bypass' "${ROOT}/scaffold/docs/operations/DEVELOPMENT.md" && grep -q -F 'pre-publish' "${ROOT}/scaffold/docs/operations/DEVELOPMENT.md"; then
	pass "development contract states non-bypass + pre-publish"
else
	fail "development contract states non-bypass + pre-publish" "DEVELOPMENT.md"
fi
# No convenience-alias UX exists in this repository (no just/Makefile/npm
# scripts), so alias-delegation is vacuously satisfied; delegation itself is
# proven by the GIT_SAFETY_CANONICAL override test below.
if [ ! -e "${ROOT}/justfile" ] && [ ! -e "${ROOT}/Justfile" ] && [ ! -e "${ROOT}/Makefile" ] && [ ! -e "${ROOT}/package.json" ]; then
	pass "no alias UX present (nothing to delegate incorrectly)"
else
	fail "no alias UX present (nothing to delegate incorrectly)" "unexpected alias surface"
fi

# --- fixture --------------------------------------------------------------------
# shellcheck disable=SC2046
set -- $(make_origin_with_clone reposhared)
BARE=$1
CLONE=$2
FRESH_BASE=$(git -C "${CLONE}" rev-parse origin/main)
printf 'fixture: bare=%s clone=%s base=%s\n' "${BARE}" "${CLONE}" "${FRESH_BASE}"

# --- 2. happy path ----------------------------------------------------------------
OUT="${TMPBASE}/t-create.out"
CODE=$(run_entry "${OUT}" -- --repo "${CLONE}" create task1)
assert_exit "create exit 0" "0" "${CODE}"
assert_contains "create admitted" "${OUT}" "GIT_SAFETY: ADMITTED"
assert_eq "admitted base is fresh remote base" "${FRESH_BASE}" "$(field "${OUT}" 'BASE')"
WT1=$(field "${OUT}" 'WORKTREE')
if [ -d "${WT1}" ] && [ "$(git -C "${WT1}" rev-parse HEAD)" = "${FRESH_BASE}" ]; then
	pass "task-owned linked worktree at admitted base"
else
	fail "task-owned linked worktree at admitted base" "WT1=${WT1}"
fi
if [ -z "$(git -C "${WT1}" status --porcelain)" ]; then pass "fresh worktree is clean"; else fail "fresh worktree is clean"; fi
if [ -f "${CLONE}/.git/git-safety/tasks/task1/BASE" ] && [ "$(cat "${CLONE}/.git/git-safety/tasks/task1/BASE")" = "${FRESH_BASE}" ]; then
	pass "admission base recorded immutably"
else
	fail "admission base recorded immutably" "record dir"
fi

# --- 3. canonical/shared dirty state is not inherited ------------------------------
echo "canonical-dirty" >"${CLONE}/tracked.txt"
git -C "${CLONE}" add tracked.txt 2>/dev/null || true
echo "untracked-noise" >"${CLONE}/untracked-noise.txt"
OUT2="${TMPBASE}/t-create2.out"
CODE=$(run_entry "${OUT2}" -- --repo "${CLONE}" create task2)
assert_exit "create with dirty canonical exit 0" "0" "${CODE}"
WT2=$(field "${OUT2}" 'WORKTREE')
if [ -z "$(git -C "${WT2}" status --porcelain)" ] && [ ! -e "${WT2}/untracked-noise.txt" ] && [ ! -e "${WT2}/tracked.txt" ]; then
	pass "dirty canonical state not inherited by worktree"
else
	fail "dirty canonical state not inherited by worktree" "WT2=${WT2}"
fi
if [ -n "$(git -C "${CLONE}" status --porcelain)" ]; then
	pass "helper did not stash/reset/clean the canonical checkout"
else
	fail "helper did not stash/reset/clean the canonical checkout" "canonical dirt was touched"
fi
# restore canonical cleanliness for later steps (explicit test-side cleanup,
# never helper-side)
rm -f "${CLONE}/tracked.txt" "${CLONE}/untracked-noise.txt"
git -C "${CLONE}" reset -q 2>/dev/null || true

# --- 4. check validates admission ---------------------------------------------------
OUT3="${TMPBASE}/t-check.out"
CODE=$(run_entry "${OUT3}" -- --repo "${CLONE}" check task2)
assert_exit "check exit 0" "0" "${CODE}"
assert_contains "check ok" "${OUT3}" "GIT_SAFETY: OK"
assert_eq "check reports admitted base" "${FRESH_BASE}" "$(field "${OUT3}" 'ADMITTED_BASE')"
echo "wip" >"${WT2}/wip.txt"
OUT3B="${TMPBASE}/t-check-dirty.out"
CODE=$(run_entry "${OUT3B}" -- --repo "${CLONE}" check task2)
assert_exit "check with work-in-progress dirt still exit 0" "0" "${CODE}"
assert_contains "check reports dirty state as info" "${OUT3B}" "WORKTREE_STATE: DIRTY"
rm -f "${WT2}/wip.txt"

# --- 5. fail-closed -----------------------------------------------------------------
OUTM="${TMPBASE}/t-missing.out"
export GIT_SAFETY_CANONICAL="${TMPBASE}/does-not-exist.sh"
CODE=$(run_entry "${OUTM}" -- --repo "${CLONE}" create nope1)
assert_exit "missing helper exit 3" "3" "${CODE}"
assert_contains "missing helper blocked" "${OUTM}" "GIT_SAFETY: BLOCKED"
assert_contains "missing helper reason" "${OUTM}" "REASON: CANONICAL_MISSING"
assert_contains "missing helper required" "${OUTM}" "REQUIRED_CONTRACT: bootstrap-git-safety/1"
assert_contains "missing helper observed none" "${OUTM}" "OBSERVED_CONTRACT: NONE"
assert_contains "missing helper remediation" "${OUTM}" "REMEDIATION:"
unset GIT_SAFETY_CANONICAL
if [ ! -e "${CLONE}/.git/git-safety/tasks/nope1" ] && ! git -C "${CLONE}" worktree list --porcelain | grep -q -F "nope1"; then
	pass "missing helper performs no raw-git fallback"
else
	fail "missing helper performs no raw-git fallback" "state was created"
fi

BADVER="${TMPBASE}/badver.sh"
sed -e 's/^GIT_SAFETY_CONTRACT_VERSION="1"$/GIT_SAFETY_CONTRACT_VERSION="2"/' "${CANON}" >"${BADVER}"
OUTV="${TMPBASE}/t-badver.out"
export GIT_SAFETY_CANONICAL="${BADVER}"
CODE=$(run_entry "${OUTV}" -- --repo "${CLONE}" create nope2)
assert_exit "incompatible version exit 3" "3" "${CODE}"
assert_contains "incompatible version blocked" "${OUTV}" "REASON: CONTRACT_MISMATCH"
assert_contains "incompatible version observed" "${OUTV}" "OBSERVED_CONTRACT: bootstrap-git-safety/2"
unset GIT_SAFETY_CANONICAL
if [ ! -e "${CLONE}/.git/git-safety/tasks/nope2" ]; then pass "incompatible version performs no fallback"; else fail "incompatible version performs no fallback"; fi

BADID="${TMPBASE}/badid.sh"
grep -v -E '^GIT_SAFETY_CONTRACT_(ID|VERSION)=' "${CANON}" >"${BADID}"
OUTI="${TMPBASE}/t-badid.out"
export GIT_SAFETY_CANONICAL="${BADID}"
CODE=$(run_entry "${OUTI}" -- --repo "${CLONE}" create nope3)
assert_exit "unverifiable identity exit 3" "3" "${CODE}"
assert_contains "unverifiable identity blocked" "${OUTI}" "REASON: IDENTITY_UNVERIFIABLE"
assert_contains "unverifiable identity observed" "${OUTI}" "OBSERVED_CONTRACT: UNKNOWN"
unset GIT_SAFETY_CANONICAL
if [ ! -e "${CLONE}/.git/git-safety/tasks/nope3" ]; then pass "unverifiable helper performs no fallback"; else fail "unverifiable helper performs no fallback"; fi

BADCORRUPT="${TMPBASE}/badcorrupt.sh"
cp "${CANON}" "${BADCORRUPT}"
printf '\nif [\n' >>"${BADCORRUPT}"
OUTC="${TMPBASE}/t-badcorrupt.out"
export GIT_SAFETY_CANONICAL="${BADCORRUPT}"
CODE=$(run_entry "${OUTC}" -- --repo "${CLONE}" create nope4)
assert_exit "corrupted helper exit 3" "3" "${CODE}"
assert_contains "corrupted helper blocked" "${OUTC}" "REASON: CANONICAL_UNUSABLE"
unset GIT_SAFETY_CANONICAL

OUTID="${TMPBASE}/t-invalid.out"
CODE=$(run_entry "${OUTID}" -- --repo "${CLONE}" create "../evil")
assert_exit "invalid task-id exit 3" "3" "${CODE}"
assert_contains "invalid task-id blocked" "${OUTID}" "REASON: INVALID_TASK_ID"
if [ ! -e "${TMPBASE}/evil" ] && [ ! -e "${CLONE}/.git/git-safety/tasks/..evil" ]; then
	pass "invalid task-id escapes nothing"
else
	fail "invalid task-id escapes nothing" "path escape"
fi

# delegation proof: override points at an intact copy elsewhere
ALTDIR="${TMPBASE}/alt layout"
mkdir -p "${ALTDIR}"
cp "${CANON}" "${ALTDIR}/git-safety-canonical.sh"
OUTD="${TMPBASE}/t-delegate.out"
export GIT_SAFETY_CANONICAL="${ALTDIR}/git-safety-canonical.sh"
CODE=$(run_entry "${OUTD}" -- --repo "${CLONE}" check task1)
assert_exit "canonical override delegates" "0" "${CODE}"
assert_contains "delegation ok" "${OUTD}" "GIT_SAFETY: OK"
unset GIT_SAFETY_CANONICAL

# --- 6. divergence --------------------------------------------------------------------
# Advance the remote AFTER admission (second actor), then pre-publish.
OTHER="${TMPBASE}/other-clone"
git clone -q "file://${BARE}" "${OTHER}" 2>/dev/null
git -C "${OTHER}" commit -q --allow-empty -m "other-actor-advance"
git -C "${OTHER}" push -q origin main
NEW_BASE=$(git -C "${CLONE}" ls-remote "file://${BARE}" refs/heads/main | awk '{print $1}')
WT2_HEAD_BEFORE=$(git -C "${WT2}" rev-parse HEAD)
WT2_FILE_SUM_BEFORE=$(find "${WT2}" -type f -not -path '*/.git/*' | sort | xargs cat 2>/dev/null | cksum)
LOG_COUNT_BEFORE=$(git -C "${WT2}" rev-list --count HEAD)

OUTP="${TMPBASE}/t-prepublish.out"
CODE=$(run_entry "${OUTP}" -- --repo "${CLONE}" pre-publish task2)
assert_exit "pre-publish on advanced remote exit 3" "3" "${CODE}"
assert_contains "remote advance detected" "${OUTP}" "REASON: REMOTE_ADVANCED"
assert_contains "no auto reconciliation claim" "${OUTP}" "AUTO_RECONCILIATION: none"
assert_eq "current base differs from admitted" "${NEW_BASE}" "$(field "${OUTP}" 'CURRENT_BASE')"
assert_contains "preserved candidate head" "${OUTP}" "CANDIDATE_HEAD: ${WT2_HEAD_BEFORE}"
if ! grep -q -F -e "merge" -e "rebase" -e "cherry-pick" -e "force" "${OUTP}" 2>/dev/null || grep -q -F "refused by baseline scope" "${OUTP}"; then
	pass "no reconciliation attempted in output"
else
	fail "no reconciliation attempted in output" "${OUTP}"
fi
assert_eq "worktree head preserved" "${WT2_HEAD_BEFORE}" "$(git -C "${WT2}" rev-parse HEAD)"
assert_eq "worktree log untouched (no merge/rebase)" "${LOG_COUNT_BEFORE}" "$(git -C "${WT2}" rev-list --count HEAD)"
WT2_FILE_SUM_AFTER=$(find "${WT2}" -type f -not -path '*/.git/*' | sort | xargs cat 2>/dev/null | cksum)
assert_eq "worktree files preserved" "${WT2_FILE_SUM_BEFORE}" "${WT2_FILE_SUM_AFTER}"
if [ -z "$(git -C "${WT2}" stash list 2>/dev/null)" ] && [ ! -e "${WT2}/.git/MERGE_HEAD" ] && [ ! -e "${CLONE}/.git/MERGE_HEAD" ]; then
	pass "no stash/merge residue from helper"
else
	fail "no stash/merge residue from helper" "residue found"
fi

# --- 6b. REMOTE_ADVANCED is a topology-only verdict ----------------------------------
# Regression for the candidate-rematerialization loop: remote movement by itself
# must not be reported as semantic invalidation and must not blindly prescribe
# semantic re-derivation/re-proof. Classification belongs to the governing
# repository/runtime contract (DEVELOPMENT.md publication closure).
assert_contains "blocked verdict preserved" "${OUTP}" "GIT_SAFETY: BLOCKED"
assert_contains "remote advanced stays a topology verdict" "${OUTP}" "topology-only verdict"
assert_contains "remote base difference explicit" "${OUTP}" "current remote base differs from admitted base"
assert_contains "not fast-forward eligible" "${OUTP}" "not currently fast-forward eligible"
assert_contains "remote movement is not semantic invalidation" "${OUTP}" "is not semantic invalidation"
assert_contains "candidate/worktree preservation explicit" "${OUTP}" "nothing was removed, overwritten, or reconciled"
assert_contains "required field TASK" "${OUTP}" "TASK: task2"
assert_contains "required field REMOTE_REF" "${OUTP}" "REMOTE_REF: origin/main"
assert_contains "required field WORKTREE" "${OUTP}" "WORKTREE: "
assert_contains "remediation hands classification to governing contract" "${OUTP}" "governing repository/runtime contract"
assert_contains "remediation requires classification first" "${OUTP}" "classify intervening movement"
assert_contains "remediation defers transition choice" "${OUTP}" "next bounded transition"
assert_contains "remediation scopes re-check to overlapping movement" "${OUTP}" "only overlapping semantic movement requires"
assert_contains "remediation forbids bypass" "${OUTP}" "do not bypass git-safety"
assert_contains "remediation forbids reconciliation" "${OUTP}" "do not merge/rebase/cherry-pick/force-push"
assert_eq "admitted base still original B" "${FRESH_BASE}" "$(field "${OUTP}" 'ADMITTED_BASE')"
if [ "$(field "${OUTP}" 'ADMITTED_BASE')" != "$(field "${OUTP}" 'CURRENT_BASE')" ]; then
	pass "CURRENT_BASE differs from ADMITTED_BASE as expected"
else
	fail "CURRENT_BASE differs from ADMITTED_BASE as expected" "both are $(field "${OUTP}" 'CURRENT_BASE')"
fi
if grep -q -F "SEMANTIC_INVALID" "${OUTP}"; then
	fail "no SEMANTIC_INVALID claim on topology-only movement" "found SEMANTIC_INVALID in ${OUTP}"
else
	pass "no SEMANTIC_INVALID claim on topology-only movement"
fi
if grep -q -F "semantic overlap" "${OUTP}"; then
	fail "no presumed semantic overlap in output" "found [semantic overlap] in ${OUTP}"
else
	pass "no presumed semantic overlap in output"
fi
if grep -q -F "proof is invalid" "${OUTP}" || grep -q -F "proof invalid" "${OUTP}"; then
	fail "no presumed proof invalidation in output" "found proof-invalid claim in ${OUTP}"
else
	pass "no presumed proof invalidation in output"
fi
if grep -q -F "re-apply the semantic delta" "${OUTP}"; then
	fail "no blind semantic reapplication in output" "found unconditional [re-apply the semantic delta] in ${OUTP}"
else
	pass "no blind semantic reapplication in output"
fi
if grep -q -F "carry the semantic delta" "${OUTP}"; then
	fail "no presumed semantic carryover in output" "found [carry the semantic delta] in ${OUTP}"
else
	pass "no presumed semantic carryover in output"
fi
if grep -q -F "create <next-task-id>" "${OUTP}"; then
	fail "no blind follow-up task prescription in output" "found [create <next-task-id>] in ${OUTP}"
else
	pass "no blind follow-up task prescription in output"
fi
if grep -q -F "follow-up task" "${OUTP}"; then
	fail "no presumed follow-up task in output" "found [follow-up task] in ${OUTP}"
else
	pass "no presumed follow-up task in output"
fi
if grep -q -F "re-apply the semantic delta" "${CANON}"; then
	fail "canonical helper has no unconditional re-apply remediation" "old wording still in ${CANON}"
else
	pass "canonical helper has no unconditional re-apply remediation"
fi
if grep -q -F "carry the semantic delta" "${CANON}"; then
	fail "canonical helper has no presumed carryover wording" "old wording still in ${CANON}"
else
	pass "canonical helper has no presumed carryover wording"
fi
if grep -q -F "create <next-task-id>" "${CANON}"; then
	fail "canonical helper has no blind follow-up task prescription" "old wording still in ${CANON}"
else
	pass "canonical helper has no blind follow-up task prescription"
fi
if grep -q -F 'GIT_SAFETY_CONTRACT_VERSION="1"' "${CANON}"; then
	pass "contract remains bootstrap-git-safety/1"
else
	fail "contract remains bootstrap-git-safety/1" "version changed"
fi
if cmp -s "${CANON}" "${ROOT}/scaffold/scripts/lib/git-safety-canonical.sh"; then
	pass "root/scaffold canonical helper remain byte-identical after correction"
else
	fail "root/scaffold canonical helper remain byte-identical after correction" "diff root vs scaffold canonical"
fi
if grep -q -F "Unrelated upstream movement is information, not invalidation" "${ROOT}/scaffold/docs/operations/DEVELOPMENT.md" && grep -q -F "is not semantic invalidation" "${OUTP}"; then
	pass "cold-read consistency: unrelated movement is not semantic invalidation in both contracts"
else
	fail "cold-read consistency: unrelated movement is not semantic invalidation in both contracts" "DEVELOPMENT.md vs REMOTE_ADVANCED disagree"
fi
if grep -q -F "not an independent mutation topology" "${ROOT}/scaffold/docs/operations/DEVELOPMENT.md" && grep -q -F "Remote topology movement alone does not reopen semantic work" "${ROOT}/scaffold/docs/operations/DEVELOPMENT.md"; then
	pass "development contract states same-branch mutation serialization rule"
else
	fail "development contract states same-branch mutation serialization rule" "DEVELOPMENT.md §7"
fi
if grep -q -F "do not pre-materialize" "${ROOT}/scaffold/docs/operations/DEVELOPMENT.md" && grep -q -F "serialize that mutation/materialization boundary" "${ROOT}/scaffold/docs/operations/DEVELOPMENT.md"; then
	pass "development contract serializes same-branch materialization by default"
else
	fail "development contract serializes same-branch materialization by default" "DEVELOPMENT.md §7"
fi
if grep -q -F "not a helper-enforced mutex" "${ROOT}/scaffold/docs/operations/DEVELOPMENT.md" && grep -q -F "independent repositories / independent publication destinations" "${ROOT}/scaffold/docs/operations/DEVELOPMENT.md" && grep -q -F "Read-only investigation remains parallel" "${ROOT}/scaffold/docs/operations/DEVELOPMENT.md"; then
	pass "development contract keeps parallelism for read-only and independent destinations without helper mutex"
else
	fail "development contract keeps parallelism for read-only and independent destinations without helper mutex" "DEVELOPMENT.md §7"
fi

# --- 6c. two-writer topology contention proof --------------------------------------
# Minimal B/T1/T2 model for the rematerialization loop:
#   B --- T1            (both T1=task1 and T2=task2 admitted from B=FRESH_BASE)
#    \--- T2
# After T1-equivalent publication (OTHER) advances origin/main B -> NEW_BASE:
#   B --- T1 (=NEW_BASE) <- origin/main
#    \--- T2 (old head, still at/below B)
# Old T2 is no longer a direct fast-forward publication candidate. This is
# topology staleness irrespective of whether T1/T2 touched semantically
# unrelated surfaces; no semantic-overlap inference is encoded here.
T1_BASE=$(cat "${CLONE}/.git/git-safety/tasks/task1/BASE")
T2_BASE=$(cat "${CLONE}/.git/git-safety/tasks/task2/BASE")
assert_eq "T1 originates from B" "${FRESH_BASE}" "${T1_BASE}"
assert_eq "T2 originates from B" "${FRESH_BASE}" "${T2_BASE}"
assert_eq "T2 admitted base in output is B" "${FRESH_BASE}" "$(field "${OUTP}" 'ADMITTED_BASE')"
assert_eq "origin moved B -> NEW_BASE" "${NEW_BASE}" "$(field "${OUTP}" 'CURRENT_BASE')"
if [ "${FRESH_BASE}" != "${NEW_BASE}" ]; then
	pass "origin movement proven (B != NEW_BASE)"
else
	fail "origin movement proven (B != NEW_BASE)" "no movement"
fi
# Sibling staleness: the other candidate from B is stale too once one publishes.
OUTP_T1="${TMPBASE}/t-prepublish-t1.out"
CODE=$(run_entry "${OUTP_T1}" -- --repo "${CLONE}" pre-publish task1)
assert_exit "sibling T1 also blocked after origin advance exit 3" "3" "${CODE}"
assert_contains "sibling T1 reason still REMOTE_ADVANCED" "${OUTP_T1}" "REASON: REMOTE_ADVANCED"
assert_eq "sibling T1 sees same moved base" "${NEW_BASE}" "$(field "${OUTP_T1}" 'CURRENT_BASE')"
# Unrelated surfaces still stale: T2 commits on surface-t2 while the T1-equivalent
# advance never touched that path, yet pre-publish stays topology-blocked.
echo "t2-unrelated-surface" >"${WT2}/surface-t2.txt"
git -C "${WT2}" add surface-t2.txt
git -C "${WT2}" commit -q -m "t2 unrelated surface"
T2_NEW_HEAD=$(git -C "${WT2}" rev-parse HEAD)
if git -C "${WT2}" merge-base --is-ancestor "${FRESH_BASE}" "${T2_NEW_HEAD}" 2>/dev/null; then
	pass "T2 descends from B (was valid before T1 published)"
else
	fail "T2 descends from B (was valid before T1 published)" "T2_NEW_HEAD=${T2_NEW_HEAD}"
fi
if git -C "${CLONE}" merge-base --is-ancestor "${NEW_BASE}" "${T2_NEW_HEAD}" 2>/dev/null; then
	fail "old T2 is not a fast-forward descendant of current main" "unexpectedly FF-publishable"
else
	pass "old T2 is not a fast-forward descendant of current main"
fi
if git -C "${CLONE}" show --name-only --format= "${NEW_BASE}" 2>/dev/null | grep -q -F "surface-t2.txt"; then
	fail "T1/T2 surfaces are disjoint in this proof" "overlap found"
else
	pass "T1/T2 surfaces are disjoint in this proof (staleness is topology, not semantics)"
fi
OUTP_T2B="${TMPBASE}/t-prepublish-t2b.out"
CODE=$(run_entry "${OUTP_T2B}" -- --repo "${CLONE}" pre-publish task2)
assert_exit "T2 with unrelated delta still topology-blocked exit 3" "3" "${CODE}"
assert_contains "T2 unrelated delta reason still REMOTE_ADVANCED" "${OUTP_T2B}" "REASON: REMOTE_ADVANCED"
assert_contains "T2 unrelated delta stays topology-only" "${OUTP_T2B}" "topology-only verdict"

# fresh task after advance is publishable (FF still possible at new base)
OUTN="${TMPBASE}/t-new.out"
CODE=$(run_entry "${OUTN}" -- --repo "${CLONE}" create task3)
assert_exit "create after advance exit 0" "0" "${CODE}"
assert_eq "new admission tracks moved remote" "${NEW_BASE}" "$(field "${OUTN}" 'BASE')"
OUTP2="${TMPBASE}/t-prepublish2.out"
CODE=$(run_entry "${OUTP2}" -- --repo "${CLONE}" pre-publish task3)
assert_exit "pre-publish without advance exit 0" "0" "${CODE}"
assert_contains "publishable ff" "${OUTP2}" "GIT_SAFETY: PUBLISHABLE_FF"

# --- 7. non-applicable repo --------------------------------------------------------------
LOCALONLY="${TMPBASE}/localonly"
git init -q -b main "${LOCALONLY}"
git -C "${LOCALONLY}" commit -q --allow-empty -m init
OUTN2="${TMPBASE}/t-na.out"
CODE=$(run_entry "${OUTN2}" -- --repo "${LOCALONLY}" create solt)
assert_exit "local-only repo exit 0 (not forced)" "0" "${CODE}"
assert_contains "local-only not applicable" "${OUTN2}" "GIT_SAFETY: NOT_APPLICABLE"
if [ ! -e "${LOCALONLY}/.git/git-safety" ]; then
	pass "no coupling state written to non-applicable repo"
else
	fail "no coupling state written to non-applicable repo" "state dir created"
fi

# --- 8. paths with spaces ------------------------------------------------------------------
SPACED="${TMPBASE}/dir with space/spaced-clone"
mkdir -p "${TMPBASE}/dir with space"
git clone -q "file://${BARE}" "${SPACED}" 2>/dev/null
OUTS="${TMPBASE}/t-spaced.out"
CODE=$(run_entry "${OUTS}" -- --repo "${SPACED}" create "spaced.task-1")
assert_exit "spaced path create exit 0" "0" "${CODE}"
assert_contains "spaced path admitted" "${OUTS}" "GIT_SAFETY: ADMITTED"
WTS=$(field "${OUTS}" 'WORKTREE')
OUTS2="${TMPBASE}/t-spaced-check.out"
CODE=$(run_entry "${OUTS2}" -- --repo "${SPACED}" check "spaced.task-1")
assert_exit "spaced path check exit 0" "0" "${CODE}"
assert_contains "spaced path check ok" "${OUTS2}" "GIT_SAFETY: OK"
if [ -d "${WTS}" ]; then pass "spaced worktree path intact"; else fail "spaced worktree path intact" "WTS=${WTS}"; fi

# --- 9. publication-identity: stale singleton is not proof for another candidate ---
# Regression for the e2a6bbe publication ambiguity: `pre-publish` without an
# explicit task-id implicitly selects the sole stored admission and reports that
# task's worktree HEAD as CANDIDATE_HEAD. That verdict is scoped to the admitted
# task candidate only and must never be mistaken for proof about a different
# invoking-checkout/main HEAD, even when that other HEAD is fast-forward-safe.
# Publication-intended checks must carry the same <task-id> from create through
# pre-publish; a BLOCKED result never authorizes raw-git publication of any
# candidate.
# shellcheck disable=SC2046
set -- $(make_origin_with_clone repoidentity)
ID_BARE=$1
ID_CLONE=$2
ID_BASE=$(git -C "${ID_CLONE}" rev-parse origin/main)
OUT_ID_CREATE="${TMPBASE}/t-identity-create.out"
CODE=$(run_entry "${OUT_ID_CREATE}" -- --repo "${ID_CLONE}" create oldtask)
assert_exit "identity: create oldtask exit 0" "0" "${CODE}"
WT_OLD=$(field "${OUT_ID_CREATE}" 'WORKTREE')
HEAD_OLD=$(git -C "${WT_OLD}" rev-parse HEAD)
assert_eq "identity: worktree starts at admitted base" "${ID_BASE}" "${HEAD_OLD}"
ID_OTHER="${TMPBASE}/identity-other"
git clone -q "file://${ID_BARE}" "${ID_OTHER}" 2>/dev/null
git -C "${ID_OTHER}" commit -q --allow-empty -m "identity-advance"
git -C "${ID_OTHER}" push -q origin main
ID_NEW_BASE=$(git -C "${ID_CLONE}" ls-remote "file://${ID_BARE}" refs/heads/main | awk '{print $1}')
git -C "${ID_CLONE}" fetch -q origin
git -C "${ID_CLONE}" checkout -q main
git -C "${ID_CLONE}" reset -q --hard origin/main
git -C "${ID_CLONE}" commit -q --allow-empty -m "identity-main-candidate"
MAIN_HEAD=$(git -C "${ID_CLONE}" rev-parse HEAD)
if [ "${MAIN_HEAD}" != "${HEAD_OLD}" ]; then
	pass "identity: main HEAD differs from admitted worktree HEAD"
else
	fail "identity: main HEAD differs from admitted worktree HEAD" "both ${MAIN_HEAD}"
fi
if git -C "${ID_CLONE}" merge-base --is-ancestor "${ID_NEW_BASE}" "${MAIN_HEAD}" 2>/dev/null; then
	pass "identity: main candidate descends from current remote base (FF-safe shape)"
else
	fail "identity: main candidate descends from current remote base (FF-safe shape)" "MAIN_HEAD=${MAIN_HEAD} NEW_BASE=${ID_NEW_BASE}"
fi
OUT_ID_IMP="${TMPBASE}/t-identity-implicit.out"
CODE=$(run_entry "${OUT_ID_IMP}" -- --repo "${ID_CLONE}" pre-publish)
assert_exit "identity: bare pre-publish from unrelated checkout stays BLOCKED exit 3" "3" "${CODE}"
assert_contains "identity: unrelated bare verdict is BLOCKED" "${OUT_ID_IMP}" "GIT_SAFETY: BLOCKED"
assert_contains "identity: unrelated bare requires explicit task-id" "${OUT_ID_IMP}" "REASON: TASK_ID_REQUIRED"
assert_contains "identity: unrelated bare carries invocation repo" "${OUT_ID_IMP}" "INVOCATION_REPO:"
assert_contains "identity: unrelated bare never implicitly selects" "${OUT_ID_IMP}" "never implicitly selects an unrelated admission"
assert_contains "identity: unrelated bare remediation offers explicit or worktree" "${OUT_ID_IMP}" "explicit task-id"
if grep -q -F "REASON: REMOTE_ADVANCED" "${OUT_ID_IMP}"; then
	fail "identity: stale sole admission from unrelated checkout must not report REMOTE_ADVANCED" "found REMOTE_ADVANCED in ${OUT_ID_IMP}"
else
	pass "identity: stale sole admission from unrelated checkout must not report REMOTE_ADVANCED"
fi
if [ -f "${ID_CLONE}/.git/git-safety/tasks/oldtask/BASE" ]; then
	pass "identity: fail-closed bare pre-publish preserves admission record"
else
	fail "identity: fail-closed bare pre-publish preserves admission record" "record missing"
fi
OUT_ID_WT="${TMPBASE}/t-identity-worktree-implicit.out"
CODE=$(run_entry "${OUT_ID_WT}" -- --repo "${WT_OLD}" pre-publish)
assert_exit "identity: bare pre-publish from admitted worktree stays BLOCKED exit 3" "3" "${CODE}"
assert_contains "identity: worktree implicit verdict is BLOCKED" "${OUT_ID_WT}" "GIT_SAFETY: BLOCKED"
assert_contains "identity: worktree implicit reason REMOTE_ADVANCED" "${OUT_ID_WT}" "REASON: REMOTE_ADVANCED"
assert_contains "identity: worktree implicit reports stored TASK" "${OUT_ID_WT}" "TASK: oldtask"
assert_contains "identity: worktree implicit selection is visible" "${OUT_ID_WT}" "TASK_SELECTION: implicit-singleton"
assert_contains "identity: candidate scope is worktree-only" "${OUT_ID_WT}" "CANDIDATE_SCOPE:"
assert_contains "identity: scope excludes invoking checkout" "${OUT_ID_WT}" "not the invoking checkout/main HEAD"
assert_eq "identity: worktree implicit CANDIDATE_HEAD is worktree HEAD, not main HEAD" "${HEAD_OLD}" "$(field "${OUT_ID_WT}" 'CANDIDATE_HEAD')"
if [ "$(field "${OUT_ID_WT}" 'CANDIDATE_HEAD')" != "${MAIN_HEAD}" ]; then
	pass "identity: BLOCKED CANDIDATE_HEAD is not the main HEAD"
else
	fail "identity: BLOCKED CANDIDATE_HEAD is not the main HEAD" "confused with main ${MAIN_HEAD}"
fi
assert_contains "identity: BLOCKED is not proof about other candidates" "${OUT_ID_WT}" "not proof about any other"
assert_contains "identity: BLOCKED never authorizes any candidate" "${OUT_ID_WT}" "never authorizes"
OUT_ID_EXP="${TMPBASE}/t-identity-explicit.out"
CODE=$(run_entry "${OUT_ID_EXP}" -- --repo "${ID_CLONE}" pre-publish oldtask)
assert_exit "identity: explicit pre-publish stays BLOCKED exit 3" "3" "${CODE}"
assert_contains "identity: explicit selection is visible" "${OUT_ID_EXP}" "TASK_SELECTION: explicit"
assert_contains "identity: explicit reports stored TASK" "${OUT_ID_EXP}" "TASK: oldtask"
assert_contains "identity: explicit stale stays topology-only" "${OUT_ID_EXP}" "topology-only verdict"
assert_eq "identity: explicit CANDIDATE_HEAD matches worktree implicit" "$(field "${OUT_ID_WT}" 'CANDIDATE_HEAD')" "$(field "${OUT_ID_EXP}" 'CANDIDATE_HEAD')"
OUT_ID_CHECK="${TMPBASE}/t-identity-check.out"
CODE=$(run_entry "${OUT_ID_CHECK}" -- --repo "${ID_CLONE}" check oldtask)
assert_exit "identity: explicit check exit 0" "0" "${CODE}"
assert_contains "identity: check carries TASK_SELECTION" "${OUT_ID_CHECK}" "TASK_SELECTION: explicit"
assert_contains "identity: check candidate scope worktree-only" "${OUT_ID_CHECK}" "not the invoking checkout/main HEAD"
if grep -q -F './scripts/git-safety pre-publish <task-id>' "${ROOT}/scaffold/docs/operations/DEVELOPMENT.md"; then
	pass "identity: docs require explicit pre-publish <task-id>"
else
	fail "identity: docs require explicit pre-publish <task-id>" "DEVELOPMENT.md §8"
fi
if grep -q -F 'do not rely on singleton auto-selection' "${ROOT}/scaffold/docs/operations/DEVELOPMENT.md"; then
	pass "identity: docs forbid relying on singleton auto-selection for publication"
else
	fail "identity: docs forbid relying on singleton auto-selection for publication" "DEVELOPMENT.md §8"
fi
if grep -q -F 'never the invoking checkout/main HEAD' "${ROOT}/scaffold/docs/operations/DEVELOPMENT.md"; then
	pass "identity: docs scope CANDIDATE_HEAD to task worktree only"
else
	fail "identity: docs scope CANDIDATE_HEAD to task worktree only" "DEVELOPMENT.md §8"
fi
if grep -q -F 'never authorizes' "${ROOT}/scaffold/docs/operations/DEVELOPMENT.md" && grep -q -F '§8 still owns Git publication safety' "${ROOT}/scaffold/docs/operations/DEVELOPMENT.md"; then
	pass "identity: docs state BLOCKED never authorizes bypass (§6 does not override §8)"
else
	fail "identity: docs state BLOCKED never authorizes bypass (§6 does not override §8)" "DEVELOPMENT.md §6/§8"
fi
if grep -q -F 'an omitted `<task-id>` is inferred only when the invocation repository' "${ROOT}/scaffold/docs/operations/DEVELOPMENT.md"; then
	pass "identity: docs state context-bound omitted-id inference only"
else
	fail "identity: docs state context-bound omitted-id inference only" "DEVELOPMENT.md §8"
fi
if grep -q -F 'TASK_ID_REQUIRED' "${ROOT}/scaffold/docs/operations/DEVELOPMENT.md"; then
	pass "identity: docs name TASK_ID_REQUIRED for lone unrelated admission"
else
	fail "identity: docs name TASK_ID_REQUIRED for lone unrelated admission" "DEVELOPMENT.md §8"
fi
if grep -q -F 'never reports that unrelated admission' "${ROOT}/scaffold/docs/operations/DEVELOPMENT.md"; then
	pass "identity: docs forbid unrelated REMOTE_ADVANCED on bare pre-publish"
else
	fail "identity: docs forbid unrelated REMOTE_ADVANCED on bare pre-publish" "DEVELOPMENT.md §8"
fi
if grep -q -F 'CANDIDATE_SCOPE:' "${CANON}"; then
	pass "identity: canonical helper emits CANDIDATE_SCOPE"
else
	fail "identity: canonical helper emits CANDIDATE_SCOPE" "${CANON}"
fi
if grep -q -F 'TASK_SELECTION:' "${CANON}"; then
	pass "identity: canonical helper emits TASK_SELECTION"
else
	fail "identity: canonical helper emits TASK_SELECTION" "${CANON}"
fi
if grep -q -F 'TASK_ID_REQUIRED' "${CANON}"; then
	pass "identity: canonical helper emits TASK_ID_REQUIRED"
else
	fail "identity: canonical helper emits TASK_ID_REQUIRED" "${CANON}"
fi
if grep -q -F 'implicit-worktree' "${CANON}"; then
	pass "identity: canonical helper emits implicit-worktree for multi-task worktree inference"
else
	fail "identity: canonical helper emits implicit-worktree for multi-task worktree inference" "${CANON}"
fi
if grep -q -F 'GIT_SAFETY_CONTRACT_VERSION="1"' "${CANON}"; then
	pass "identity: contract remains bootstrap-git-safety/1"
else
	fail "identity: contract remains bootstrap-git-safety/1" "version changed"
fi
OUT_ID_NEW="${TMPBASE}/t-identity-new.out"
CODE=$(run_entry "${OUT_ID_NEW}" -- --repo "${ID_CLONE}" create newtask)
assert_exit "identity: create newtask at moved base exit 0" "0" "${CODE}"
WT_NEW=$(field "${OUT_ID_NEW}" 'WORKTREE')
echo "identity-payload" >"${WT_NEW}/identity.txt"
git -C "${WT_NEW}" add identity.txt
git -C "${WT_NEW}" commit -q -m "identity correct-flow change"
NEW_HEAD=$(git -C "${WT_NEW}" rev-parse HEAD)
OUT_ID_PRE="${TMPBASE}/t-identity-new-pre.out"
CODE=$(run_entry "${OUT_ID_PRE}" -- --repo "${ID_CLONE}" pre-publish newtask)
assert_exit "identity: correct-flow pre-publish exit 0" "0" "${CODE}"
assert_contains "identity: correct-flow publishable" "${OUT_ID_PRE}" "GIT_SAFETY: PUBLISHABLE_FF"
assert_contains "identity: correct-flow selection explicit" "${OUT_ID_PRE}" "TASK_SELECTION: explicit"
assert_eq "identity: correct-flow candidate is worktree HEAD" "${NEW_HEAD}" "$(field "${OUT_ID_PRE}" 'CANDIDATE_HEAD')"
git -C "${WT_NEW}" push -q origin "HEAD:main"
ID_READBACK=$(git -C "${ID_CLONE}" ls-remote "file://${ID_BARE}" refs/heads/main | awk '{print $1}')
assert_eq "identity: remote read-back matches published candidate" "${NEW_HEAD}" "${ID_READBACK}"
OUT_ID_STALE="${TMPBASE}/t-identity-stale.out"
CODE=$(run_entry "${OUT_ID_STALE}" -- --repo "${ID_CLONE}" pre-publish oldtask)
assert_exit "identity: stale task still BLOCKED after advance exit 3" "3" "${CODE}"
assert_contains "identity: stale reason still REMOTE_ADVANCED" "${OUT_ID_STALE}" "REASON: REMOTE_ADVANCED"
assert_contains "identity: stale explicit keeps BLOCKED verdict" "${OUT_ID_STALE}" "GIT_SAFETY: BLOCKED"
assert_contains "identity: stale explicit keeps topology-only" "${OUT_ID_STALE}" "topology-only verdict"
assert_contains "identity: stale explicit selects requested task" "${OUT_ID_STALE}" "TASK: oldtask"
assert_contains "identity: stale explicit selection visible" "${OUT_ID_STALE}" "TASK_SELECTION: explicit"
OUT_ID_AMB="${TMPBASE}/t-identity-ambiguous.out"
CODE=$(run_entry "${OUT_ID_AMB}" -- --repo "${ID_CLONE}" pre-publish)
assert_exit "identity: implicit with two tasks is AMBIGUOUS exit 3" "3" "${CODE}"
assert_contains "identity: ambiguous requires explicit" "${OUT_ID_AMB}" "REASON: AMBIGUOUS_TASK"
if grep -q -F "REASON: REMOTE_ADVANCED" "${OUT_ID_AMB}"; then
	fail "identity: multi-task unrelated bare must not report REMOTE_ADVANCED" "found REMOTE_ADVANCED in ${OUT_ID_AMB}"
else
	pass "identity: multi-task unrelated bare must not report REMOTE_ADVANCED"
fi
if grep -q -F "PUBLISHABLE_FF" "${OUT_ID_AMB}"; then
	fail "identity: multi-task unrelated bare must not report PUBLISHABLE" "found PUBLISHABLE in ${OUT_ID_AMB}"
else
	pass "identity: multi-task unrelated bare must not report PUBLISHABLE"
fi

# --- 10. task-identity selection proof (A-E) --------------------------------------
# A. explicit task identity with several admissions selects exactly that task.
assert_contains "proof-A: explicit oldtask selects oldtask" "${OUT_ID_STALE}" "TASK: oldtask"
assert_contains "proof-A: explicit newtask flow selects newtask" "${OUT_ID_PRE}" "TASK: newtask"
if [ "$(field "${OUT_ID_STALE}" 'TASK')" != "oldtask" ]; then
	fail "proof-A: explicit oldtask TASK field exact" "$(field "${OUT_ID_STALE}" 'TASK')"
else
	pass "proof-A: explicit oldtask TASK field exact"
fi
# B. current admitted worktree + omitted id keeps the convenience safely.
# After publication WT_NEW is itself stale (its admitted BASE predates its own
# push), so prove PUBLISHABLE inference on a fresh admission at current base.
OUT_B_FRESH="${TMPBASE}/t-proof-b-fresh.out"
CODE=$(run_entry "${OUT_B_FRESH}" -- --repo "${ID_CLONE}" create proofb)
assert_exit "proof-B: create fresh task at current base exit 0" "0" "${CODE}"
WT_B=$(field "${OUT_B_FRESH}" 'WORKTREE')
HEAD_B=$(git -C "${WT_B}" rev-parse HEAD)
OUT_B_WT="${TMPBASE}/t-proof-b-worktree.out"
CODE=$(run_entry "${OUT_B_WT}" -- --repo "${WT_B}" pre-publish)
assert_exit "proof-B: bare pre-publish from admitted worktree exit 0" "0" "${CODE}"
assert_contains "proof-B: worktree inference publishable" "${OUT_B_WT}" "GIT_SAFETY: PUBLISHABLE_FF"
assert_contains "proof-B: worktree inference selects proofb" "${OUT_B_WT}" "TASK: proofb"
assert_contains "proof-B: multi-task worktree selection visible" "${OUT_B_WT}" "TASK_SELECTION: implicit-worktree"
assert_eq "proof-B: worktree candidate is its own HEAD" "${HEAD_B}" "$(field "${OUT_B_WT}" 'CANDIDATE_HEAD')"
OUT_B_CHECK="${TMPBASE}/t-proof-b-check.out"
CODE=$(run_entry "${OUT_B_CHECK}" -- --repo "${WT_B}" check)
assert_exit "proof-B: bare check from admitted worktree exit 0" "0" "${CODE}"
assert_contains "proof-B: bare check selects worktree task" "${OUT_B_CHECK}" "TASK: proofb"
# WT_NEW already published its own HEAD (CURRENT == HEAD, direct containment
# evidence), so it is FF-eligible despite its older admitted BASE — string
# inequality alone never marks a contained candidate stale (§6/§8 freshness
# policy). Identity inference safety still holds on this path.
OUT_B_STALE_WT="${TMPBASE}/t-proof-b-stale-wt.out"
CODE=$(run_entry "${OUT_B_STALE_WT}" -- --repo "${WT_NEW}" pre-publish)
assert_exit "proof-B: bare pre-publish from published worktree is PUBLISHABLE exit 0" "0" "${CODE}"
assert_contains "proof-B: published worktree inference publishable" "${OUT_B_STALE_WT}" "GIT_SAFETY: PUBLISHABLE_FF"
assert_contains "proof-B: stale worktree inference selects newtask" "${OUT_B_STALE_WT}" "TASK: newtask"
# C. stale sole admission from unrelated checkout is already proven above via
# OUT_ID_IMP (TASK_ID_REQUIRED, no REMOTE_ADVANCED, record preserved).
# Re-assert the fixture shape here for cold readers.
if [ "$(cat "${ID_CLONE}/.git/git-safety/tasks/oldtask/BASE")" = "${ID_BASE}" ]; then
	pass "proof-C: stale fixture admitted base is still original B"
else
	fail "proof-C: stale fixture admitted base is still original B" "record changed"
fi
# D. multiple admissions with no safe connection never guess (covered by AMB).
if [ -f "${ID_CLONE}/.git/git-safety/tasks/oldtask/BASE" ] && [ -f "${ID_CLONE}/.git/git-safety/tasks/newtask/BASE" ]; then
	pass "proof-D: ambiguous fail-closed preserves both admission records"
else
	fail "proof-D: ambiguous fail-closed preserves both admission records" "record missing"
fi
# E. existing topology semantics preserved on the explicit stale path.
assert_contains "proof-E: explicit stale keeps exit-3 BLOCKED shape" "${OUT_ID_STALE}" "GIT_SAFETY: BLOCKED"
if grep -q -F "SEMANTIC_INVALID" "${OUT_ID_STALE}"; then
	fail "proof-E: explicit stale stays topology-only" "found SEMANTIC_INVALID"
else
	pass "proof-E: explicit stale stays topology-only"
fi

printf '\n== result: %s passed, %s failed ==\n' "${PASS}" "${FAIL}"
[ "${FAIL}" = "0" ]
