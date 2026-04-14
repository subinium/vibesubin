#!/usr/bin/env bash
#
# symbol-diff.sh — compare the exported symbol set between two git refs.
#
# The "exported symbol set" is every top-level function / class / constant
# that a refactor should preserve unless explicitly deleted. This script
# is intentionally conservative — it uses ripgrep patterns for common
# language syntax, not real ASTs. It's a coarse first-pass check; pair it
# with the language's own tooling for anything it misses.
#
# Usage:
#   scripts/symbol-diff.sh <ref-before> <ref-after>
#
# Examples:
#   scripts/symbol-diff.sh HEAD~1 HEAD
#   scripts/symbol-diff.sh "$SNAP" HEAD
#
# Exit code:
#   0 — symbol sets identical, or only additions (refactor added API)
#   1 — symbols were dropped (refactor lost API) — investigate immediately
#   2 — bad args or missing tool

set -euo pipefail

if [ $# -ne 2 ]; then
    echo "usage: $0 <ref-before> <ref-after>" >&2
    exit 2
fi

BEFORE="$1"
AFTER="$2"

if ! command -v rg >/dev/null 2>&1; then
    echo "error: ripgrep (rg) is required" >&2
    echo "install: brew install ripgrep | apt install ripgrep | cargo install ripgrep" >&2
    exit 2
fi

workdir=$(mktemp -d)
trap 'rm -rf "$workdir"' EXIT

extract() {
    local ref="$1"
    local outfile="$2"
    # Create a temporary checkout of the ref into a worktree
    local wt="$workdir/wt-$(echo "$ref" | tr '/' '-')"
    git worktree add --quiet --detach "$wt" "$ref" 2>/dev/null
    (
        cd "$wt"
        # Patterns for common languages. Each outputs "file:symbol".
        # Python
        rg -t py --no-heading --line-number \
            '^(def|async def|class) ([A-Za-z_][A-Za-z0-9_]*)' \
            -r '$2' 2>/dev/null || true
        rg -t py --no-heading \
            '^([A-Z][A-Z0-9_]*)\s*=' \
            -r '$1' 2>/dev/null || true
        # JavaScript / TypeScript
        rg -t js -t ts --no-heading \
            '^export\s+(?:async\s+)?(?:function|class|const|let|var|interface|type|enum)\s+([A-Za-z_$][A-Za-z0-9_$]*)' \
            -r '$1' 2>/dev/null || true
        rg -t js -t ts --no-heading \
            '^export\s*\{\s*([A-Za-z_$][A-Za-z0-9_$,\s]*)\s*\}' \
            -r '$1' 2>/dev/null || true
        # Rust
        rg -t rust --no-heading \
            '^pub\s+(?:async\s+)?(?:fn|struct|enum|trait|const|static|type)\s+([A-Za-z_][A-Za-z0-9_]*)' \
            -r '$1' 2>/dev/null || true
        # Go
        rg -t go --no-heading \
            '^func\s+(?:\([^)]*\)\s+)?([A-Z][A-Za-z0-9_]*)' \
            -r '$1' 2>/dev/null || true
        rg -t go --no-heading \
            '^(?:type|var|const)\s+([A-Z][A-Za-z0-9_]*)' \
            -r '$1' 2>/dev/null || true
    ) | sort -u > "$outfile"
    git worktree remove --force "$wt" 2>/dev/null || true
}

before_file="$workdir/before.txt"
after_file="$workdir/after.txt"

extract "$BEFORE" "$before_file"
extract "$AFTER"  "$after_file"

before_count=$(wc -l < "$before_file" | tr -d ' ')
after_count=$(wc -l < "$after_file" | tr -d ' ')

echo "Symbols extracted:"
echo "  $BEFORE: $before_count"
echo "  $AFTER:  $after_count"
echo

# Dropped symbols: present before, absent after.
dropped=$(comm -23 "$before_file" "$after_file")
added=$(comm -13 "$before_file" "$after_file")

if [ -n "$added" ]; then
    echo "Added (present only in $AFTER):"
    echo "$added" | sed 's/^/  + /'
    echo
fi

if [ -n "$dropped" ]; then
    echo "Dropped (present only in $BEFORE):"
    echo "$dropped" | sed 's/^/  - /'
    echo
    echo "FAIL — some exported symbols disappeared. Investigate every entry above."
    echo "If the drop is intentional, the operator should confirm each one."
    exit 1
fi

echo "OK — no symbols were dropped between $BEFORE and $AFTER"
exit 0
