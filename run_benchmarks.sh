#!/usr/bin/env bash
# ==============================================================================
# Run All Routing Benchmarks and Stress Tests (EC499)
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

echo "======================================================================"
echo " 1. Running 5-Topology Head-to-Head Tournament Benchmark..."
echo "======================================================================"
"$PYTHON_BIN" benchmark_routing_algorithms.py "$@"

echo "======================================================================"
echo " 2. Running High-Intensity Load Balancer Stress Test..."
echo "======================================================================"
"$PYTHON_BIN" stress_test_load_balancer.py "$@"

echo "======================================================================"
echo " 3. Running Multi-Topology Blind Stress Benchmark..."
echo "======================================================================"
"$PYTHON_BIN" stress_test_blind_topologies.py "$@"

echo "======================================================================"
echo " All Benchmarks and Stress Tests Completed Successfully!"
echo " Results and plots saved to logs/ and logs/plots/"
echo "======================================================================"
