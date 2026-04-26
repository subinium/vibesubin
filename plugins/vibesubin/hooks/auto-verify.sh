#!/usr/bin/env bash
#
# vibesubin/hooks/auto-verify.sh
# PostToolUse(Edit|Write|MultiEdit) — opt-in symbol-diff after large or signature-changing edits.
#
# OPT-IN: defaults to OFF. Set VIBESUBIN_AUTO_VERIFY=1 to enable.
# Threshold: triggers only when MultiEdit has >= 5 edits OR the diff includes
#            export/def/class/pub fn/func lines (signature-changing).
# Output: stderr-only advisory ("run /vibesubin:refactor-verify"). PostToolUse cannot
#         block the tool call (exit 2 is ignored), so this is informational.
# Timeout-safe: 3-second cap on symbol-diff; bails on any failure.

set -euo pipefail

# Hard gate: opt-in only.
[ "${VIBESUBIN_AUTO_VERIFY:-0}" = "1" ] || exit 0

INPUT=$(cat)

PARSED=$(printf '%s' "$INPUT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    tool = d.get('tool_name', '')
    ti = d.get('tool_input', {}) if isinstance(d.get('tool_input'), dict) else {}
    file = ti.get('file_path', '')
    edits = len(ti.get('edits', [])) if tool == 'MultiEdit' else 1
    print(f'{tool}\t{file}\t{edits}')
except Exception:
    print('\t\t0')
" 2>/dev/null || printf '\t\t0')

TOOL=$(printf '%s' "$PARSED" | cut -f1)
FILE=$(printf '%s' "$PARSED" | cut -f2)
EDITS=$(printf '%s' "$PARSED" | cut -f3)
EDITS="${EDITS:-0}"  # Defensive: ensure numeric for the -lt comparison below.

# Need a file path to do anything useful.
[ -z "$FILE" ] && exit 0
[ -f "$FILE" ] || exit 0

# Only verify code files.
case "$FILE" in
    *.py|*.ts|*.tsx|*.js|*.jsx|*.mjs|*.cjs|*.rs|*.go|*.java|*.kt|*.swift) ;;
    *) exit 0 ;;
esac

# Threshold: skip small single edits unless they touch a signature line.
if [ "$EDITS" -lt 5 ]; then
    REPO_DIR=$(dirname "$FILE")
    if ! (cd "$REPO_DIR" && git rev-parse --is-inside-work-tree >/dev/null 2>&1); then
        exit 0
    fi
    # Check if recent diff contains signature-changing lines.
    if ! (cd "$REPO_DIR" && git diff --unified=0 HEAD -- "$FILE" 2>/dev/null \
          | grep -qE '^[-+](export |def |class |pub fn |func |fn |async function |interface |type )'); then
        exit 0
    fi
fi

# Advisory only — emit a stderr nudge to run /vibesubin:refactor-verify.
#
# Why we don't run symbol-diff inline:
#   symbol-diff.sh compares two git refs (e.g., HEAD~1 vs HEAD), which
#   requires a meaningful "before" snapshot. At PostToolUse time the edit
#   is in the working tree, not committed — there is no reliable ref to
#   diff against. /vibesubin:refactor-verify takes a proper snapshot at
#   the start of its session and runs the full 4-check verification then.
#   The hook's job is just to notice the pattern and remind.
{
    echo "vibesubin auto-verify: $TOOL on $(basename "$FILE") (edits=$EDITS)"
    echo "→ run /vibesubin:refactor-verify to verify nothing was dropped or moved"
} >&2

# PostToolUse: exit code is observability-only; always succeed.
exit 0
