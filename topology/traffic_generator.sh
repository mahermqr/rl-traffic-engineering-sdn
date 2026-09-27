#!/usr/bin/env bash
# ==============================================================================
# SDN Mininet Network Traffic Generator (EC499)
# Generates realistic synthetic traffic patterns:
#  1. Continuous background unicast flows (Mice & Elephant flows)
#  2. Bursty Poisson traffic load surges
#  3. Asymmetric cross-pod elephant flows to test lateral link offload
# ==============================================================================

set -e

# Configurable Traffic Parameters (zero hardcoded values)
BASE_PORT="${TRAFFIC_BASE_PORT:-5000}"
MICE_RATE_1="${MICE_RATE_1:-5M}"
MICE_RATE_2="${MICE_RATE_2:-8M}"
ELEPHANT_RATE="${ELEPHANT_RATE:-45M}"
SURGE_RATE_1="${SURGE_RATE_1:-30M}"
SURGE_RATE_2="${SURGE_RATE_2:-25M}"

MICE_DURATION="${MICE_DURATION:-300}"
ELEPHANT_DURATION="${ELEPHANT_DURATION:-120}"
SURGE_DURATION="${SURGE_DURATION:-60}"

HOST_1="${TRAFFIC_HOST_1:-h1}"
HOST_2="${TRAFFIC_HOST_2:-h2}"
HOST_3="${TRAFFIC_HOST_3:-h3}"
HOST_4="${TRAFFIC_HOST_4:-h4}"
HOST_5="${TRAFFIC_HOST_5:-h5}"
HOST_6="${TRAFFIC_HOST_6:-h6}"
HOST_7="${TRAFFIC_HOST_7:-h7}"
HOST_8="${TRAFFIC_HOST_8:-h8}"

IP_1="${TRAFFIC_IP_1:-10.0.0.1}"
IP_5="${TRAFFIC_IP_5:-10.0.0.5}"
IP_6="${TRAFFIC_IP_6:-10.0.0.6}"
IP_7="${TRAFFIC_IP_7:-10.0.0.7}"
IP_8="${TRAFFIC_IP_8:-10.0.0.8}"

echo "======================================================================"
echo " Starting SDN Traffic Generator for Adaptive Traffic Engineering"
echo " Modes: Unicast Background, Bursty Surges, Elephant Flows"
echo " Elephant Rate: $ELEPHANT_RATE | Mice Rates: $MICE_RATE_1, $MICE_RATE_2"
echo "======================================================================"

check_mininet() {
    if ! pgrep -f "mininet:" >/dev/null 2>&1; then
        echo "[!] Error: No active Mininet host processes detected." >&2
        echo "    Please start the Mininet network first:" >&2
        echo "      sudo python3 topology/mininet_topo.py" >&2
        echo "    Or if running without Mininet, use the autonomous simulation driver:" >&2
        echo "      python3 simulate_live_traffic.py --mode auto" >&2
        exit 1
    fi
}

check_sudo() {
    if [ "$EUID" -ne 0 ]; then
        if ! sudo -n true 2>/dev/null; then
            if [ -t 0 ]; then
                echo "[*] Requesting sudo credentials for Mininet host namespace access..."
                sudo -v || { echo "[!] Sudo authorization failed."; exit 1; }
            else
                echo "[!] Error: Sudo privileges required to attach to Mininet host namespaces." >&2
                echo "    Please run with 'sudo' or authenticate sudo credentials first ('sudo -v')." >&2
                exit 1
            fi
        fi
    fi
}

if [ "$EUID" -ne 0 ]; then
    SUDO_CMD="sudo"
else
    SUDO_CMD=""
fi

mn_exec() {
    local host="$1"
    shift
    local pid
    pid=$(pgrep -f "mininet:${host}$" | head -n 1)
    if [ -z "$pid" ]; then
        pid=$(pgrep -f "mininet:${host}\b" | head -n 1)
    fi
    if [ -z "$pid" ]; then
        echo "[!] Error: Host '${host}' not found in active Mininet network." >&2
        return 1
    fi
    $SUDO_CMD mnexec -a "$pid" "$@"
}

clean_stale_iperf() {
    for host in "$HOST_1" "$HOST_2" "$HOST_3" "$HOST_4" "$HOST_5" "$HOST_6" "$HOST_7" "$HOST_8"; do
        local pid
        pid=$(pgrep -f "mininet:${host}$" | head -n 1)
        if [ -n "$pid" ]; then
            $SUDO_CMD mnexec -a "$pid" pkill -f iperf 2>/dev/null || true
        fi
    done
}

cleanup() {
    echo -e "\n[*] Stopping traffic generator and cleaning up background iperf processes..."
    clean_stale_iperf
    kill $(jobs -p) 2>/dev/null || true
    echo "[*] Cleanup complete."
}

generate_background() {
    local p1=$((BASE_PORT + 1))
    local p2=$((BASE_PORT + 2))
    local p3=$((BASE_PORT + 3))
    echo "[+] Launching continuous background traffic (Mice flows: web/RPC)..."
    mn_exec "$HOST_1" iperf -s -u -p "$p1" &
    mn_exec "$HOST_5" iperf -s -u -p "$p2" &
    mn_exec "$HOST_7" iperf -s -u -p "$p3" &
    sleep 1
    mn_exec "$HOST_2" iperf -c "$IP_1" -u -p "$p1" -b "$MICE_RATE_1" -t "$MICE_DURATION" &
    mn_exec "$HOST_3" iperf -c "$IP_5" -u -p "$p2" -b "$MICE_RATE_2" -t "$MICE_DURATION" &
    mn_exec "$HOST_6" iperf -c "$IP_7" -u -p "$p3" -b "$MICE_RATE_1" -t "$MICE_DURATION" &
    echo "[+] Background mice flows initiated."
}

generate_elephant_burst() {
    local p4=$((BASE_PORT + 4))
    echo "[+] Launching high-bandwidth elephant flow ($HOST_4 -> $HOST_8, $ELEPHANT_RATE)..."
    mn_exec "$HOST_8" iperf -s -u -p "$p4" &
    sleep 1
    mn_exec "$HOST_4" iperf -c "$IP_8" -u -p "$p4" -b "$ELEPHANT_RATE" -t "$ELEPHANT_DURATION" &
    echo "[+] Elephant flow active across core/lateral mesh."
}

generate_pod_surge() {
    local p5=$((BASE_PORT + 5))
    local p6=$((BASE_PORT + 6))
    echo "[+] Launching asymmetric pod surge (Pod 1 to Pod 2 cross-links)..."
    mn_exec "$HOST_1" iperf -s -u -p "$p5" &
    mn_exec "$HOST_6" iperf -s -u -p "$p6" &
    sleep 1
    mn_exec "$HOST_2" iperf -c "$IP_6" -u -p "$p6" -b "$SURGE_RATE_1" -t "$SURGE_DURATION" &
    mn_exec "$HOST_3" iperf -c "$IP_1" -u -p "$p5" -b "$SURGE_RATE_2" -t "$SURGE_DURATION" &
    echo "[+] Pod surge active."
}

check_mininet
check_sudo

trap cleanup EXIT INT TERM
clean_stale_iperf

case "$1" in
    background)
        generate_background
        ;;
    elephant)
        generate_elephant_burst
        ;;
    surge)
        generate_pod_surge
        ;;
    all|*)
        generate_background
        sleep 3
        generate_elephant_burst
        sleep 5
        generate_pod_surge
        ;;
esac

echo "[*] Traffic generation active. Press Ctrl+C to stop."
wait
