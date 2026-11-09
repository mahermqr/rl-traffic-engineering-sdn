#!/usr/bin/env bash
# ==============================================================================
# Run 4-Tier Opaque-Box E2E Validation Runner (EC499)
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ -f "$SCRIPT_DIR/scripts/resolve_python.sh" ]; then
    source "$SCRIPT_DIR/scripts/resolve_python.sh"
elif [ -f "$SCRIPT_DIR/../scripts/resolve_python.sh" ]; then
    source "$SCRIPT_DIR/../scripts/resolve_python.sh"
elif [ -x "$SCRIPT_DIR/../../.venv/bin/python" ]; then
    PYTHON_BIN="$SCRIPT_DIR/../../.venv/bin/python"
elif [ -x "$SCRIPT_DIR/../.venv/bin/python" ]; then
    PYTHON_BIN="$SCRIPT_DIR/../.venv/bin/python"
fi

exec "${PYTHON_BIN:-python3}" test_e2e_opaque_box.py "$@"
