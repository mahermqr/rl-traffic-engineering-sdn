#!/usr/bin/env bash
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -f "$SCRIPT_DIR/EC499tests/run_benchmarks.sh" ]; then
    exec "$SCRIPT_DIR/EC499tests/run_benchmarks.sh" "$@"
fi

if [ -f "$SCRIPT_DIR/scripts/resolve_python.sh" ]; then
    source "$SCRIPT_DIR/scripts/resolve_python.sh"
elif [ -f "$SCRIPT_DIR/../scripts/resolve_python.sh" ]; then
    source "$SCRIPT_DIR/../scripts/resolve_python.sh"
fi

exec "${PYTHON_BIN:-python3}" "$SCRIPT_DIR/benchmark_routing_algorithms.py" "$@"
