#!/usr/bin/env bash
# ==============================================================================
# Run All Routing Benchmarks and Stress Tests (EC499)
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ -f "$SCRIPT_DIR/scripts/resolve_python.sh" ]; then
    source "$SCRIPT_DIR/scripts/resolve_python.sh"
elif [ -f "$SCRIPT_DIR/../scripts/resolve_python.sh" ]; then
    source "$SCRIPT_DIR/../scripts/resolve_python.sh"
fi

echo "======================================================================"
echo " Running tournament and stress suites with validated shared arguments..."
echo "======================================================================"
"$PYTHON_BIN" run_benchmarks.py "$@"

echo "======================================================================"
echo " All Benchmarks and Stress Tests Completed Successfully!"
echo " Results and plots saved to logs/ and logs/plots/"
echo "======================================================================"
