#!/usr/bin/env bash
# ==============================================================================
# Run Unit and Integration Test Suite (EC499)
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Dynamic Python Environment Detection (zero hardcoded paths)
if [ -n "$PYTHON_BIN" ] && [ -x "$PYTHON_BIN" ]; then
    : # Use user-specified PYTHON_BIN
elif [ -n "$VIRTUAL_ENV" ] && [ -x "$VIRTUAL_ENV/bin/python" ]; then
    PYTHON_BIN="$VIRTUAL_ENV/bin/python"
elif [ -n "$VENV_PATH" ] && [ -x "$VENV_PATH/bin/python" ]; then
    PYTHON_BIN="$VENV_PATH/bin/python"
elif [ -x "$SCRIPT_DIR/venv/bin/python" ]; then
    PYTHON_BIN="$SCRIPT_DIR/venv/bin/python"
elif [ -x "$SCRIPT_DIR/.venv/bin/python" ]; then
    PYTHON_BIN="$SCRIPT_DIR/.venv/bin/python"
elif [ -x "$HOME/ec499_env/bin/python" ]; then
    PYTHON_BIN="$HOME/ec499_env/bin/python"
elif [ -x "$HOME/.venv/bin/python" ]; then
    PYTHON_BIN="$HOME/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python3)"
else
    PYTHON_BIN="python"
fi

exec "$PYTHON_BIN" test_suite.py "$@"
