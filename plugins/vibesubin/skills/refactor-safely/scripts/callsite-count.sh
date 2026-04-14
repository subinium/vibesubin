#!/usr/bin/env bash
#
# callsite-count.sh — count references to a symbol and compare before/after.
#
# The #1 LLM refactoring failure is "updated the definition, missed the call
# sites." This script gives you a concrete count from two git refs so you
# can prove every reference moved.
#
# Usage:
#   scripts/callsite-count.sh <ref-before> <ref-after> <before-symbol>
#   scripts/callsite-count.sh <ref-before> <ref-after> <before-symbol> <after-symbol>
#
# Examples:
#   scripts/callsite-count.sh HEAD~1 HEAD fetch_user
#   scripts/callsite-count.sh "$SNAP" HEAD fetch_user get_user     # renamed
#   scripts/callsite-count.sh "$SNAP" HEAD 'oldA|oldB' 'newA|newB'
#
# The symbol arguments are ripgrep regexes. For a rename, pass the old pattern
# first and the new pattern second. The script proves:
#   1. old-count(before) == new-count(after)
#   2. old-count(after) == 0
#
# Exit code:
#   0 — counts match and stale old-name references are gone
#   1 — counts disagree — callsites were missed
#   2 — bad args or missing tool

set -euo pipefail

if [ $# -lt 3 ] || [ $# -gt 4 ]; then
    echo "usage: $0 <ref-before> <ref-after> <before-symbol-regex> [after-symbol-regex]" >&2
    exit 2
fi

BEFORE="$1"
AFTER="$2"
BEFORE_SYMBOL="$3"
AFTER_SYMBOL="${4:-$3}"

if ! command -v rg >/dev/null 2>&1; then
    echo "error: ripgrep (rg) is required" >&2
    exit 2
fi

workdir=$(mktemp -d)
trap 'rm -rf "$workdir"' EXIT

count_in_ref() {
    local ref="$1"
    local pattern="$2"
    local wt="$workdir/wt-$(echo "$ref" | tr '/' '-')"
    git worktree add --quiet --detach "$wt" "$ref" 2>/dev/null
    local n
    # Word-boundary match to avoid partial-name hits.
    n=$(cd "$wt" && rg --count-matches --word-regexp "$pattern" 2>/dev/null | awk -F: '{sum+=$NF} END {print sum+0}')
    git worktree remove --force "$wt" 2>/dev/null || true
    echo "$n"
}

list_sites_in_ref() {
    local ref="$1"
    local pattern="$2"
    local wt="$workdir/list-$(echo "$ref" | tr '/' '-')"
    git worktree add --quiet --detach "$wt" "$ref" 2>/dev/null
    (cd "$wt" && rg --line-number --word-regexp "$pattern" 2>/dev/null || true)
    git worktree remove --force "$wt" 2>/dev/null || true
}

before_count=$(count_in_ref "$BEFORE" "$BEFORE_SYMBOL")
after_count=$(count_in_ref "$AFTER" "$AFTER_SYMBOL")
stale_old_after_count=$(count_in_ref "$AFTER" "$BEFORE_SYMBOL")

echo "Before pattern: $BEFORE_SYMBOL"
echo "After pattern:  $AFTER_SYMBOL"
echo "  $BEFORE: $before_count references"
echo "  $AFTER:  $after_count references"
if [ "$BEFORE_SYMBOL" != "$AFTER_SYMBOL" ]; then
    echo "  stale old-name refs in $AFTER: $stale_old_after_count"
fi
echo

if [ "$after_count" -lt "$before_count" ]; then
    echo "FAIL — $((before_count - after_count)) references disappeared"
    echo "Sites in $BEFORE matching '$BEFORE_SYMBOL':"
    list_sites_in_ref "$BEFORE" "$BEFORE_SYMBOL" | sed 's/^/  /'
    echo
    echo "Sites in $AFTER matching '$AFTER_SYMBOL':"
    list_sites_in_ref "$AFTER" "$AFTER_SYMBOL" | sed 's/^/  /'
    exit 1
fi

if [ "$BEFORE_SYMBOL" != "$AFTER_SYMBOL" ] && [ "$stale_old_after_count" -ne 0 ]; then
    echo "FAIL — old-name references are still present after the rename"
    echo "Stale sites in $AFTER matching '$BEFORE_SYMBOL':"
    list_sites_in_ref "$AFTER" "$BEFORE_SYMBOL" | sed 's/^/  /'
    exit 1
fi

if [ "$before_count" -eq "$after_count" ]; then
    echo "OK — reference counts match"
    exit 0
fi

if [ "$after_count" -gt "$before_count" ]; then
    echo "NOTE — $AFTER has more references ($((after_count - before_count)) new)."
    echo "This can be intentional (wrapper, adapter, alias), but confirm with the operator."
    exit 0
fi
