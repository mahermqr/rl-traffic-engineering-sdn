#!/usr/bin/env python3
"""
SDN High Availability (HA) Cluster & Controller Status Viewer (EC499).
Queries the active controller endpoint without requiring 'curl' or 'jq'.
"""

import sys
import json
import urllib.request
import urllib.error

PORT = 8080
for arg in sys.argv[1:]:
    if arg.isdigit():
        PORT = int(arg)

URL = f"http://127.0.0.1:{PORT}/api/ha/status"

BOLD = "\033[1m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
RESET = "\033[0m"

try:
    req = urllib.request.Request(URL, headers={"User-Agent": "SDN-Status-CLI"})
    with urllib.request.urlopen(req, timeout=2.0) as resp:
        data = json.loads(resp.read().decode("utf-8"))
except urllib.error.URLError as e:
    print(f"\n{RED}[Error] Could not connect to controller at {URL}: {e.reason}{RESET}")
    print(f"Make sure './run_system.sh' is currently running.\n")
    sys.exit(1)
except Exception as e:
    print(f"\n{RED}[Error] {e}{RESET}\n")
    sys.exit(1)

active_leader = data.get("active_leader", "unknown").upper()
cluster_mode = data.get("cluster_mode", "NOMINAL")
cluster_status = data.get("cluster_status", "NOMINAL")
ofp_port = data.get("ofp_port", 6633)
rest_port = data.get("rest_port", PORT)

leader_color = GREEN if active_leader == "PRIMARY" else YELLOW
if cluster_status != "NOMINAL":
    status_color = YELLOW
else:
    status_color = GREEN

print(f"\n{BOLD}{'=' * 68}{RESET}")
print(f" {BOLD}🛡️  SDN HIGH AVAILABILITY (HA) CLUSTER STATUS REPORT (EC499){RESET}")
print(f"{BOLD}{'=' * 68}{RESET}")
print(f" • Active Cluster Leader:    {leader_color}{BOLD}{active_leader}{RESET} (OFP Port: {ofp_port}, REST: {rest_port})")
print(f" • Cluster Mode:             {status_color}{cluster_mode}{RESET}")
print(f" • Data Plane Mode:          {GREEN}{data.get('data_plane_mode', 'OPENFLOW_ACTIVE')}{RESET}")
print(f" • Active Flows / Uptime:    {data.get('active_flows', 0)} flows | {data.get('uptime_sec', 0.0):.1f}s")
print(f"\n {BOLD}Cluster Nodes Health & Roles:{RESET}")
print(f" ------------------------------------------------------------------")

for n in data.get("nodes_detail", []):
    nid = n.get("id", "")
    name = n.get("name", nid)
    is_curr = n.get("is_current", False)
    is_live = n.get("is_live", False)
    state = n.get("state", "")
    port = n.get("ofp_port", "")

    if is_curr:
        marker = f"{GREEN}▶ [ACTIVE LEADER]{RESET}"
    elif is_live:
        marker = f"{CYAN}  [STANDBY READY]{RESET}"
    else:
        marker = f"{RED}  [OFFLINE / DOWN]{RESET}"

    print(f"  {marker} {BOLD}{name:<28}{RESET} OFP: {port} | State: {state}")

bench = data.get("benchmarks", {})
hist = bench.get("failover_history", [])
if hist:
    print(f"\n {BOLD}Failover History (Most Recent Transitions):{RESET}")
    print(f" ------------------------------------------------------------------")
    for ev in hist[-4:]:
        ts = ev.get("timestamp", "")
        failed = ev.get("failed_node", "")
        promoted = ev.get("promoted_leader", "").upper()
        lat = ev.get("failover_latency_ms", 0.0)
        p = ev.get("ofp_port", "")
        print(f"  • {ts} | {RED}{failed}{RESET} failed ➔ Promoted {GREEN}{BOLD}{promoted}{RESET} (:{p}) in {lat:.3f} ms")

print(f"{BOLD}{'=' * 68}{RESET}\n")
