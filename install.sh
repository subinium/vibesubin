#!/usr/bin/env bash
#
# vibesubin — manual fallback installer.
#
# Preferred install paths:
#   Claude Code plugin:  /plugin marketplace add subinium/vibesubin
#                        /plugin install vibesubin@vibesubin
#   skills.sh:           npx skills add subinium/vibesubin
#   Codex CLI (manual):  bash install.sh --to codex
#
# This script symlinks the plugin's skill directories into a target agent's
# skills folder. Editing files in this repo is then reflected live in your
# sessions (no re-install after a pull).
#
# Usage:
#   bash install.sh                 # default: install to Claude Code
#   bash install.sh --to claude     # explicit Claude Code (~/.claude/skills)
#   bash install.sh --to codex      # Codex CLI (~/.codex/skills)
#   bash install.sh --to all        # every supported target
#   bash install.sh --dry-run       # show what would happen without doing it
#   bash install.sh --force         # overwrite existing entries with the same name

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_SRC="${REPO_ROOT}/plugins/vibesubin/skills"

DRY_RUN=0
FORCE=0
TARGET="claude"

while [ $# -gt 0 ]; do
    case "$1" in
        --dry-run) DRY_RUN=1 ;;
        --force)   FORCE=1 ;;
        --to)
            shift
            TARGET="${1:-}"
            if [ -z "${TARGET}" ]; then
                echo "❌ --to requires an argument: claude | codex | all" >&2
                exit 1
            fi
            ;;
        -h|--help)
            sed -n '3,22p' "$0" | sed 's/^# \{0,1\}//'
            exit 0
            ;;
        *) echo "unknown arg: $1" >&2; exit 1 ;;
    esac
    shift
done

if [ ! -d "${SKILLS_SRC}" ]; then
    echo "❌ ${SKILLS_SRC} does not exist. Are you running from the repo root?"
    exit 1
fi

install_to() {
    local dst="$1"
    local label="$2"

    mkdir -p "${dst}"

    local installed=0 skipped=0 replaced=0
    echo ""
    echo "→ ${label}  (${dst})"

    for skill_dir in "${SKILLS_SRC}"/*/; do
        local name target current
        name="$(basename "${skill_dir}")"
        target="${dst}/${name}"

        if [ -L "${target}" ]; then
            current="$(readlink "${target}")"
            if [ "${current}" = "${skill_dir%/}" ]; then
                echo "  skip     ${name} (already linked)"
                skipped=$((skipped + 1))
                continue
            fi
            if [ ${FORCE} -eq 1 ]; then
                [ ${DRY_RUN} -eq 0 ] && rm "${target}"
                echo "  replace  ${name} (was → ${current})"
                replaced=$((replaced + 1))
            else
                echo "  ⚠ exists ${name} (linked elsewhere: ${current}) — use --force to replace"
                skipped=$((skipped + 1))
                continue
            fi
        elif [ -e "${target}" ]; then
            if [ ${FORCE} -eq 1 ]; then
                [ ${DRY_RUN} -eq 0 ] && rm -rf "${target}"
                echo "  replace  ${name} (was a real directory)"
                replaced=$((replaced + 1))
            else
                echo "  ⚠ exists ${name} (real file/dir present) — use --force to replace"
                skipped=$((skipped + 1))
                continue
            fi
        fi

        if [ ${DRY_RUN} -eq 0 ]; then
            ln -s "${skill_dir%/}" "${target}"
        fi
        echo "  install  ${name}"
        installed=$((installed + 1))
    done

    echo "  ─ ${installed} installed, ${replaced} replaced, ${skipped} skipped"
}

case "${TARGET}" in
    claude)
        install_to "${HOME}/.claude/skills" "Claude Code"
        ;;
    codex)
        install_to "${HOME}/.codex/skills" "Codex CLI"
        ;;
    all)
        install_to "${HOME}/.claude/skills" "Claude Code"
        install_to "${HOME}/.codex/skills" "Codex CLI"
        ;;
    *)
        echo "❌ --to must be one of: claude, codex, all" >&2
        exit 1
        ;;
esac

echo ""
if [ ${DRY_RUN} -eq 1 ]; then
    echo "(dry run — no changes made)"
else
    echo "Done. Start a new session and type / to see the skills."
    echo "To uninstall: bash uninstall.sh [--to claude|codex|all]"
fi
