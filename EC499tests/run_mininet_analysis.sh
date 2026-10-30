#!/usr/bin/env bash
# Analyze an existing measured Mininet run using a Python with Matplotlib.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ANALYSIS_PYTHON="${ANALYSIS_PYTHON:-$PROJECT_DIR/.venv/bin/python}"

if [[ ! -x "$ANALYSIS_PYTHON" ]] || ! "$ANALYSIS_PYTHON" -c 'import matplotlib, numpy' >/dev/null 2>&1; then
    echo "No Python interpreter with matplotlib and numpy was found: $ANALYSIS_PYTHON" >&2
    echo "Set ANALYSIS_PYTHON or install python3-matplotlib python3-numpy." >&2
    exit 2
fi

exec "$ANALYSIS_PYTHON" "$SCRIPT_DIR/analyze_mininet_measured_trials.py" "$@"
