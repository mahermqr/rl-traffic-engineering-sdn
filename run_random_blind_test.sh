#!/usr/bin/env bash
# ==============================================================================
# Autonomous Zero-Shot Random Blind Topologies Evaluation Runner (EC499)
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

echo "================================================================================"
echo " 🎲 RUNNING TRUE BLIND ZERO-SHOT TEST SUITE ON UNSEEN RANDOM TOPOLOGIES"
echo "================================================================================"

OUTPUT_JSON="${OUTPUT_JSON:-logs/random_blind_topologies_results.json}"
TEST_NODES="${TEST_NODES:-16 20 25 30}"

for NODES in $TEST_NODES; do
    echo ""
    echo ">>> Evaluating on Random Connected Mesh with N=$NODES nodes..."
    "$PYTHON_BIN" evaluate_random_blind_topology.py --nodes "$NODES" --output-json "$OUTPUT_JSON" "$@"
done

if [ -f "$OUTPUT_JSON" ]; then
    echo ""
    echo ">>> Rendering Figure 6 (random_blind_topologies_evaluation.png)..."
    "$PYTHON_BIN" -c "from generate_detailed_plots import plot_random_blind_evaluation; plot_random_blind_evaluation()" || true
fi

echo ""
echo "================================================================================"
echo " ✅ ALL RANDOM BLIND TOPOLOGY TESTS COMPLETED SUCCESSFULLY!"
echo "================================================================================"
