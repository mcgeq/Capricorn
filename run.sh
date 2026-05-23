#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
TEMPLATE_HELPER="$SCRIPT_DIR/tools/rename_template.py"
DOCTOR_HELPER="$SCRIPT_DIR/tools/doctor.py"
FIX_HELPER="$SCRIPT_DIR/tools/fix.py"
HOOKS_HELPER="$SCRIPT_DIR/tools/install_git_hooks.py"
TARGET_HELPER="$TEMPLATE_HELPER"

if [ "${1-}" = "--doctor" ]; then
    shift
    TARGET_HELPER="$DOCTOR_HELPER"
elif [ "${1-}" = "--fix" ]; then
    shift
    TARGET_HELPER="$FIX_HELPER"
elif [ "${1-}" = "--install-hooks" ]; then
    shift
    TARGET_HELPER="$HOOKS_HELPER"
fi

if command -v python3 >/dev/null 2>&1; then
    exec python3 "$TARGET_HELPER" "$@"
fi

if command -v python >/dev/null 2>&1; then
    exec python "$TARGET_HELPER" "$@"
fi

printf '%s\n' "error: Python 3 interpreter not found. Install Python and retry." >&2
exit 1
