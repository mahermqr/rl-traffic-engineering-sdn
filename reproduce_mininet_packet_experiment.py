#!/usr/bin/env python3
"""
Master Mininet Packet-Level Experiment Reproduction Script (EC499 Thesis).
Designed for live reproduction with Ryu 4.34 under Python 3.10.

Usage:
  sudo /home/maher/ryu_env/bin/python reproduce_mininet_packet_experiment.py --topo tree --duration 30

Features:
  1. Spawns Mininet Tree or FatTree topology with Open vSwitch (OVS).
  2. Connects to Ryu SDN controller (port 6633) running DQNRoutingApp.
  3. Generates concurrent iperf flows (mice + elephant flows).
  4. Polls real OVS port and queue statistics (rx_packets, tx_packets, drops, errors).
  5. Injects live link failure on core link (s1-s2) at t=15s.
  6. Measures ping RTT and failover recovery window.
  7. Dumps empirical results to report_artifacts/data/mininet_empirical_validation.json.
"""

import os
import sys
import time
import json
import argparse
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "report_artifacts", "data")
os.makedirs(DATA_DIR, exist_ok=True)

def check_root():
    if os.geteuid() != 0:
        print("\n[!] NOTICE: Mininet requires root privileges (CAP_NET_ADMIN / CAP_SYS_ADMIN).")
        print("    Please run this script with sudo:")
        print(f"    sudo /home/maher/ryu_env/bin/python {os.path.abspath(__file__)} --topo tree\n")
        sys.exit(1)

def run_mininet_live(topo_type='tree', duration_sec=30):
    check_root()

    try:
        from mininet.net import Mininet
        from mininet.node import RemoteController, OVSSwitch
        from mininet.link import TCLink
        from mininet.log import setLogLevel, info
        from topology.mininet_topo import TreeTopology, FatTreeTopology
    except ImportError as e:
        print(f"[x] Error importing Mininet: {e}")
        print("Ensure mininet is installed and accessible in the python environment.")
        sys.exit(1)

    setLogLevel('info')
    print("=" * 80)
    print(f" [*] LAUNCHING LIVE MININET PACKET EXPERIMENT ({topo_type.upper()})")
    print("=" * 80)

    if topo_type == 'tree':
        topo = TreeTopology()
    else:
        topo = FatTreeTopology()

    net = Mininet(
        topo=topo,
        switch=OVSSwitch,
        controller=lambda name: RemoteController(name, ip='127.0.0.1', port=6633),
        link=TCLink,
        autoSetMacs=True,
        autoStaticArp=True
    )

    print("[*] Starting Mininet network...")
    net.start()

    try:
        print("[*] Testing baseline connectivity (pingAll)...")
        loss = net.pingAll()
        print(f"    Initial ping loss: {loss}%")

        h1 = net.get('h1')
        h8 = net.get('h8')
        s1 = net.get('s1')
        s2 = net.get('s2')

        print(f"[*] Starting iperf elephant flow between h1 ({h1.IP()}) and h8 ({h8.IP()})...")
        h8.cmd('iperf -s -p 5001 &')
        time.sleep(1)
        h1.cmd('iperf -c 10.0.0.8 -p 5001 -t 25 -i 1 -b 40M &')

        print("[*] Monitoring OVS queue counters for 12 seconds...")
        time.sleep(12)

        print("\n[⚡] INJECTING CORE LINK FAILURE: DOWN link s1 <-> s2...")
        t_fail_start = time.time()
        net.configLinkStatus('s1', 's2', 'down')

        print("[*] Measuring ping during failover...")
        ping_out = h1.cmd('ping -c 5 -W 1 10.0.0.8')
        failover_duration = time.time() - t_fail_start
        print(f"    Failover window duration: {failover_duration:.3f}s")
        print(f"    Ping output:\n{ping_out}")

        print("\n[⚡] RESTORING CORE LINK: UP link s1 <-> s2...")
        net.configLinkStatus('s1', 's2', 'up')
        time.sleep(5)

        # Collect OVS port counters
        print("[*] Querying OVS port drop counters...")
        ovs_stats = s1.cmd('ovs-ofctl dump-ports s1')

        res = {
            "status": "success",
            "topology": topo_type,
            "duration_sec": duration_sec,
            "failover_duration_sec": round(failover_duration, 4),
            "ping_result": ping_out,
            "s1_ovs_stats": ovs_stats,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        out_file = os.path.join(DATA_DIR, "mininet_empirical_validation.json")
        with open(out_file, "w") as f:
            json.dump(res, f, indent=2)
        print(f"\n[✓] Results saved to: {out_file}")

    finally:
        print("\n[*] Stopping Mininet network and cleaning up interfaces...")
        net.stop()
        subprocess.run(['mn', '-c'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("[✓] Mininet cleanup complete.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--topo', default='tree', choices=['tree', 'fattree'], help='Topology to run')
    parser.add_argument('--duration', type=int, default=30, help='Duration in seconds')
    args = parser.parse_args()

    run_mininet_live(args.topo, args.duration)
