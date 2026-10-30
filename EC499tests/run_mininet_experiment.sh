#!/usr/bin/env bash
# Run auditable packet-level Mininet/OVS trials.  Requires Linux root privileges.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd -P)"
cd "$SCRIPT_DIR"

# Mininet is commonly installed through the operating system package manager,
# so it is unavailable inside a project virtual environment. Select an
# interpreter by capability, not merely by the active virtual environment.
MININET_SITE_PACKAGES="${MININET_SITE_PACKAGES:-/usr/lib/python3/dist-packages}"
if [[ -n "${PYTHONPATH:-}" ]]; then
    MININET_PYTHONPATH="$MININET_SITE_PACKAGES:$PYTHONPATH"
else
    MININET_PYTHONPATH="$MININET_SITE_PACKAGES"
fi

if [[ -n "${MININET_PYTHON:-}" ]]; then
    RUNNER_PYTHON="$MININET_PYTHON"
else
    RUNNER_PYTHON=""
    for candidate in "$PROJECT_DIR/.venv/bin/python" /usr/bin/python3 "$(command -v python3 2>/dev/null || true)"; do
        if [[ -n "$candidate" && -x "$candidate" ]] && PYTHONPATH="$MININET_PYTHONPATH" "$candidate" -c 'import mininet, networkx, numpy' >/dev/null 2>&1; then
            RUNNER_PYTHON="$candidate"
            break
        fi
    done
fi
if [[ -z "$RUNNER_PYTHON" ]] || ! PYTHONPATH="$MININET_PYTHONPATH" "$RUNNER_PYTHON" -c 'import mininet, networkx, numpy' >/dev/null 2>&1; then
    echo "No Python interpreter with Mininet, NumPy, and NetworkX was found." >&2
    echo "Set MININET_PYTHON and MININET_SITE_PACKAGES, or install the missing packages." >&2
    exit 2
fi

CONTROLLER_PYTHON="${CONTROLLER_PYTHON:-$PROJECT_DIR/.venv-controller/bin/python}"
if [[ ! -x "$CONTROLLER_PYTHON" ]]; then
    echo "Controller interpreter not found: $CONTROLLER_PYTHON" >&2
    echo "Set CONTROLLER_PYTHON to an interpreter with Ryu installed." >&2
    exit 2
fi
if ! "$CONTROLLER_PYTHON" -c 'import eventlet, ryu' >/dev/null 2>&1; then
    echo "Controller interpreter cannot import eventlet and ryu: $CONTROLLER_PYTHON" >&2
    echo "Use: CONTROLLER_PYTHON=$PROJECT_DIR/.venv-controller/bin/python $0 ..." >&2
    exit 2
fi

echo "Experiment Python: $RUNNER_PYTHON"
echo "Controller Python: $CONTROLLER_PYTHON"

exec env PYTHONPATH="$MININET_PYTHONPATH" "$RUNNER_PYTHON" reproduce_mininet_packet_experiment.py \
    --controller-command "$CONTROLLER_PYTHON" "$@"
