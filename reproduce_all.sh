#!/usr/bin/env bash
# Rebuild the report and run regression tests.  --rerun also executes model benchmarks.
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(cd "$PROJECT_DIR/.." && pwd)"
MODE="${1:-}"

case "$MODE" in
  ""|--test-only|--rerun) ;;
  *) echo "Usage: $0 [--test-only|--rerun]" >&2; exit 2 ;;
esac

"$WORKSPACE_DIR/run_tests.sh"
if [[ "$MODE" == "--rerun" ]]; then
  "$WORKSPACE_DIR/run_benchmarks.sh"
fi
if [[ "$MODE" != "--test-only" ]]; then
  (cd "$WORKSPACE_DIR" && python3 report_builder/build_report.py)
fi

echo "Reproducibility workflow completed. Packet-level Mininet trials are opt-in:"
echo "  cd $PROJECT_DIR/EC499tests && sudo ./run_mininet_experiment.sh --matrix --replicates 10"
