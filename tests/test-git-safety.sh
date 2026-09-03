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

printf '\n== result: %s passed, %s failed ==\n' "${PASS}" "${FAIL}"
[ "${FAIL}" = "0" ]
