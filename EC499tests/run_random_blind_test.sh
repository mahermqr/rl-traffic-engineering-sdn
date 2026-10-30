#!/usr/bin/env bash
# ==============================================================================
# Autonomous Zero-Shot Random Blind Topologies Evaluation Runner (EC499)
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ -f "$SCRIPT_DIR/scripts/resolve_python.sh" ]; then
    source "$SCRIPT_DIR/scripts/resolve_python.sh"
elif [ -f "$SCRIPT_DIR/../scripts/resolve_python.sh" ]; then
    source "$SCRIPT_DIR/../scripts/resolve_python.sh"
fi

export PYTHONPATH="$SCRIPT_DIR/..:$SCRIPT_DIR/../EC499report:$PYTHONPATH"

echo "================================================================================"
echo " 🎲 RUNNING TRUE BLIND ZERO-SHOT TEST SUITE ON UNSEEN RANDOM TOPOLOGIES"
echo "================================================================================"

OUTPUT_JSON="${OUTPUT_JSON:-$SCRIPT_DIR/../logs/random_blind_topologies_results.json}"
TEST_NODES="${TEST_NODES:-16 20 25 30}"

for NODES in $TEST_NODES; do
    echo ""
    echo ">>> Evaluating on Random Connected Mesh with N=$NODES nodes..."
    "$PYTHON_BIN" evaluate_random_blind_topology.py --nodes "$NODES" --output-json "$OUTPUT_JSON" "$@"
done

if [ -f "$OUTPUT_JSON" ]; then
    echo ""
    echo ">>> Rendering Figure 6 (random_blind_topologies_evaluation.png)..."
    "$PYTHON_BIN" -c "import sys; sys.path.insert(0, '$SCRIPT_DIR/../EC499report'); from generate_detailed_plots import plot_random_blind_evaluation; plot_random_blind_evaluation()" || true
fi

echo ""
echo "================================================================================"
echo " ✅ ALL RANDOM BLIND TOPOLOGY TESTS COMPLETED SUCCESSFULLY!"
echo "================================================================================"
