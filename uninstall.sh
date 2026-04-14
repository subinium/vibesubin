#!/usr/bin/env bash
#
# vibesubin — uninstall symlinked skills.
# Removes only the symlinks this plugin's install.sh created.
# Leaves real files / directories with the same names alone.
#
# Usage:
#   bash uninstall.sh                 # default: Claude Code (~/.claude/skills)
#   bash uninstall.sh --to claude     # explicit Claude Code
#   bash uninstall.sh --to codex      # Codex CLI (~/.codex/skills)
#   bash uninstall.sh --to all        # every supported target

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_SRC="${REPO_ROOT}/plugins/vibesubin/skills"

TARGET="claude"

while [ $# -gt 0 ]; do
    case "$1" in
        --to)
            shift
            TARGET="${1:-}"
            if [ -z "${TARGET}" ]; then
                echo "❌ --to requires an argument: claude | codex | all" >&2
                exit 1
            fi
            ;;
        -h|--help)
            sed -n '3,12p' "$0" | sed 's/^# \{0,1\}//'
            exit 0
            ;;
        *) echo "unknown arg: $1" >&2; exit 1 ;;
    esac
    shift
done

uninstall_from() {
    local dst="$1"
    local label="$2"

    local removed=0 kept=0
    echo ""
    echo "← ${label}  (${dst})"

    for skill_dir in "${SKILLS_SRC}"/*/; do
        local name target current
        name="$(basename "${skill_dir}")"
        target="${dst}/${name}"

        if [ ! -e "${target}" ] && [ ! -L "${target}" ]; then
            continue
        fi

        if [ -L "${target}" ]; then
            current="$(readlink "${target}")"
            if [ "${current}" = "${skill_dir%/}" ]; then
                rm "${target}"
                echo "  removed  ${name}"
                removed=$((removed + 1))
            else
                echo "  keep     ${name} (links elsewhere: ${current})"
                kept=$((kept + 1))
            fi
        else
            echo "  keep     ${name} (real file/dir, not a symlink)"
            kept=$((kept + 1))
        fi
    done

    echo "  ─ ${removed} removed, ${kept} kept"
}

case "${TARGET}" in
    claude) uninstall_from "${HOME}/.claude/skills" "Claude Code" ;;
    codex)  uninstall_from "${HOME}/.codex/skills"  "Codex CLI" ;;
    all)
        uninstall_from "${HOME}/.claude/skills" "Claude Code"
        uninstall_from "${HOME}/.codex/skills"  "Codex CLI"
        ;;
    *)
        echo "❌ --to must be one of: claude, codex, all" >&2
        exit 1
        ;;
esac

echo ""
echo "Your local clone of this repo is untouched."
