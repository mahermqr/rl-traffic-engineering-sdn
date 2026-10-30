# `run_random_blind_test.sh`

> **File:** `run_random_blind_test.sh`  
> **Subsystem / Category:** 8. Operational Automation & Shell Scripts  
> **Language:** `bash`  
> **Lines of Code:** 35  
> **File Size:** 1.50 KB  

---

## Overview

Zero-shot blind topology transfer evaluation automation script.

---

## Source Code

```bash
#!/usr/bin/env bash
# ==============================================================================
# Autonomous Zero-Shot Random Blind Topologies Evaluation Runner (EC499)
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# shellcheck source=scripts/resolve_python.sh
source "$SCRIPT_DIR/scripts/resolve_python.sh"

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
```
