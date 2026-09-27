#!/usr/bin/env bash
# ==============================================================================
# Adaptive SDN Traffic Engineering & Multi-Agent Reinforcement Learning Launcher
# ==============================================================================

set -e

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Configuration with environment variable overrides
DASHBOARD_PORT="${SDN_REST_PORT:-8080}"
DASHBOARD_HOST="${SDN_REST_HOST:-0.0.0.0}"
CONTROLLER_PORT="${SDN_CONTROLLER_PORT:-6633}"
TOPOLOGY_NAME="${SDN_DEFAULT_TOPOLOGY:-tree}"

echo "======================================================================"
echo " Starting Adaptive SDN Traffic Engineering Platform (EC499)"
echo " Ryu OpenFlow 1.3 Controller + Deep Q-Network (DQN) Routing Engine"
echo " Web Dashboard: http://localhost:${DASHBOARD_PORT}"
echo " Controller Port: ${CONTROLLER_PORT} | Default Topology: ${TOPOLOGY_NAME}"
echo "======================================================================"

# Dynamic Environment Detection (zero hardcoded paths)
if [ -n "$PYTHON_EXEC" ] && [ -x "$PYTHON_EXEC" ]; then
    echo "[1/3] Using configured PYTHON_EXEC ($PYTHON_EXEC)..."
    RYU_EXEC="${RYU_EXEC:-$(dirname "$PYTHON_EXEC")/ryu-manager}"
elif [ -n "$VIRTUAL_ENV" ] && [ -x "$VIRTUAL_ENV/bin/python" ]; then
    echo "[1/3] Using active virtual environment ($VIRTUAL_ENV)..."
    PYTHON_EXEC="$VIRTUAL_ENV/bin/python"
    RYU_EXEC="$VIRTUAL_ENV/bin/ryu-manager"
elif [ -n "$VENV_PATH" ] && [ -d "$VENV_PATH" ]; then
    echo "[1/3] Activating virtual environment ($VENV_PATH)..."
    PYTHON_EXEC="$VENV_PATH/bin/python"
    RYU_EXEC="$VENV_PATH/bin/ryu-manager"
elif [ -d "$BASE_DIR/venv" ]; then
    echo "[1/3] Activating local virtual environment ($BASE_DIR/venv)..."
    PYTHON_EXEC="$BASE_DIR/venv/bin/python"
    RYU_EXEC="$BASE_DIR/venv/bin/ryu-manager"
elif [ -d "$BASE_DIR/.venv" ]; then
    echo "[1/3] Activating local virtual environment ($BASE_DIR/.venv)..."
    PYTHON_EXEC="$BASE_DIR/.venv/bin/python"
    RYU_EXEC="$BASE_DIR/.venv/bin/ryu-manager"
elif [ -d "$HOME/ec499_env" ]; then
    echo "[1/3] Activating user virtual environment ($HOME/ec499_env)..."
    PYTHON_EXEC="$HOME/ec499_env/bin/python"
    RYU_EXEC="$HOME/ec499_env/bin/ryu-manager"
elif [ -d "$HOME/.venv" ]; then
    echo "[1/3] Activating user virtual environment ($HOME/.venv)..."
    PYTHON_EXEC="$HOME/.venv/bin/python"
    RYU_EXEC="$HOME/.venv/bin/ryu-manager"
else
    echo "[1/3] Using system PATH for python and ryu-manager..."
    PYTHON_EXEC="$(command -v python3 || echo python)"
    RYU_EXEC="$(command -v ryu-manager || echo ryu-manager)"
fi

# Clean up stale mininet and ovs ports if sudo is available
if sudo -n true 2>/dev/null; then
    echo "[2/3] Cleaning stale Mininet and OpenFlow state..."
    sudo mn -c 2>/dev/null || true
else
    echo "[2/3] Skipping stale Mininet cleanup (passwordless sudo not active)."
fi

mkdir -p "$BASE_DIR/logs"

echo "[3/3] Starting Ryu OpenFlow 1.3 Controller in background..."
cd "$BASE_DIR/controller"
PYTHONPATH="$BASE_DIR:$BASE_DIR/agent:$BASE_DIR/controller" SDN_REST_PORT="$DASHBOARD_PORT" SDN_REST_HOST="$DASHBOARD_HOST" "$RYU_EXEC" main_controller.py --observe-links --ofp-tcp-listen-port "$CONTROLLER_PORT" > "$BASE_DIR/logs/ryu_controller.log" 2>&1 &
RYU_PID=$!
echo "Ryu Controller started (PID: $RYU_PID). Waiting 3s for initialization..."
sleep 3

# Trap exit to kill Ryu upon script termination
cleanup() {
    echo -e "\nShutting down controller and network..."
    kill $RYU_PID 2>/dev/null || true
    if sudo -n true 2>/dev/null; then
        sudo mn -c 2>/dev/null || true
    fi
    echo "Done."
}
trap cleanup EXIT INT TERM

echo ""
echo "======================================================================"
echo " Web Dashboard is live at: http://localhost:${DASHBOARD_PORT}"
echo "======================================================================"

# Check if Mininet can run with sudo
if sudo -n true 2>/dev/null; then
    echo "Starting Mininet Unified Topology & Traffic Simulator (Root Mode)..."
    cd "$BASE_DIR/topology"
    sudo "$PYTHON_EXEC" mininet_topo.py --topo "$TOPOLOGY_NAME" --controller-port "$CONTROLLER_PORT" "$@"
else
    echo "Interactive sudo requires authentication for Mininet."
    echo "Starting Autonomous SDN Simulation Driver & Web Telemetry Stream..."
    cd "$BASE_DIR"
    "$PYTHON_EXEC" simulate_live_traffic.py --mode auto --interval 4.0 --controller-url "http://localhost:${DASHBOARD_PORT}" "$@"
fi
