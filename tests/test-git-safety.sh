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
