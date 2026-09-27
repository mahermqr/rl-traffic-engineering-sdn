#!/usr/bin/env python3
"""
Unified SDN Topology & Traffic Evaluation Suite for Reinforcement Learning (EC499).
Features:
  - Multi-Topology Support:
      1. Hierarchical Tree Topology (7 switches, 8 hosts, redundant mesh links)
      2. Fat-Tree Topology (k=4: 4 Core, 8 Aggregation, 8 Edge switches, 16 hosts)
  - Adaptive background unicast traffic generator (iperf mice flows)
  - Bursty elephant flows to stress-test core link utilization and adaptive rerouting
  - Fully configurable controller IP, ports, bandwidths, delays, and traffic rates
"""

import sys
import os
import time
import threading
import argparse

# Dynamic import of central config
_PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_DIR not in sys.path:
    sys.path.insert(0, _PROJECT_DIR)

try:
    import config
    DEFAULT_CTRL_IP = config.CONTROLLER_IP
    DEFAULT_CTRL_PORT = config.CONTROLLER_PORT
    DEFAULT_CORE_BW = config.DEFAULT_LINK_CAPACITY
    DEFAULT_CORE_DELAY = f"{config.DEFAULT_LINK_DELAY}ms"
except ImportError:
    DEFAULT_CTRL_IP = os.environ.get("SDN_CONTROLLER_IP", "127.0.0.1")
    DEFAULT_CTRL_PORT = int(os.environ.get("SDN_CONTROLLER_PORT", 6633))
    DEFAULT_CORE_BW = float(os.environ.get("SDN_DEFAULT_CAPACITY", 100.0))
    DEFAULT_CORE_DELAY = f"{os.environ.get('SDN_DEFAULT_DELAY', '2.0')}ms"

from mininet.net import Mininet
from mininet.topo import Topo
from mininet.node import RemoteController, OVSSwitch
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.log import setLogLevel, info


class TreeTopology(Topo):
    """
    Hierarchical Tree Topology:
      - 1 Core switch (s1)
      - 2 Aggregation switches (s2, s3)
      - 4 Edge switches (s4, s5, s6, s7)
      - 8 End hosts (h1 - h8)
    """
    def build(self, core_bw=100, core_delay='2ms', agg_bw=50, agg_delay='3ms', mesh_bw=30, mesh_delay='8ms'):
        info("*** Creating Core, Aggregation, and Edge Switches\n")
        s1 = self.addSwitch('s1', dpid='0000000000000001')
        s2 = self.addSwitch('s2', dpid='0000000000000002')
        s3 = self.addSwitch('s3', dpid='0000000000000003')
        s4 = self.addSwitch('s4', dpid='0000000000000004')
        s5 = self.addSwitch('s5', dpid='0000000000000005')
        s6 = self.addSwitch('s6', dpid='0000000000000006')
        s7 = self.addSwitch('s7', dpid='0000000000000007')

        # Inter-switch links with configurable bandwidth and delay attributes
        info("*** Creating Inter-switch Links\n")
        self.addLink(s1, s2, bw=core_bw, delay=core_delay)
        self.addLink(s1, s3, bw=core_bw, delay=core_delay)
        self.addLink(s2, s4, bw=agg_bw, delay=agg_delay)
        self.addLink(s2, s5, bw=agg_bw, delay=agg_delay)
        self.addLink(s3, s6, bw=agg_bw, delay=agg_delay)
        self.addLink(s3, s7, bw=agg_bw, delay=agg_delay)

        # Redundant mesh cross-links to provide alternate routing paths for DQN Unicast
        self.addLink(s4, s6, bw=mesh_bw, delay=mesh_delay)
        self.addLink(s5, s7, bw=mesh_bw, delay=mesh_delay)

        # Hosts attached to edge switches (2 hosts per edge switch)
        info("*** Creating Hosts and Host Links\n")
        h1 = self.addHost('h1', ip='10.0.0.1/24', mac='00:00:00:00:00:01')
        h2 = self.addHost('h2', ip='10.0.0.2/24', mac='00:00:00:00:00:02')
        h3 = self.addHost('h3', ip='10.0.0.3/24', mac='00:00:00:00:00:03')
        h4 = self.addHost('h4', ip='10.0.0.4/24', mac='00:00:00:00:00:04')
        h5 = self.addHost('h5', ip='10.0.0.5/24', mac='00:00:00:00:00:05')
        h6 = self.addHost('h6', ip='10.0.0.6/24', mac='00:00:00:00:00:06')
        h7 = self.addHost('h7', ip='10.0.0.7/24', mac='00:00:00:00:00:07')
        h8 = self.addHost('h8', ip='10.0.0.8/24', mac='00:00:00:00:00:08')

        self.addLink(h1, s4, bw=core_bw, delay='1ms')
        self.addLink(h2, s4, bw=core_bw, delay='1ms')
        self.addLink(h3, s5, bw=core_bw, delay='1ms')
        self.addLink(h4, s5, bw=core_bw, delay='1ms')
        self.addLink(h5, s6, bw=core_bw, delay='1ms')
        self.addLink(h6, s6, bw=core_bw, delay='1ms')
        self.addLink(h7, s7, bw=core_bw, delay='1ms')
        self.addLink(h8, s7, bw=core_bw, delay='1ms')


class FatTreeTopology(Topo):
    """
    Standard Fat-Tree Topology (k=4):
    - 4 Core Switches (c1..c4)
    - 4 Pods, each with 2 Aggregation (a1..a8) and 2 Edge (e1..e8) switches
    - 16 End Hosts (h1..h16)
    """
    def build(self, k=4, core_bw=100, core_delay='2ms', edge_bw=50, edge_delay='2ms'):
        num_cores = (k // 2) ** 2
        num_pods = k
        num_aggr_per_pod = k // 2
        num_edge_per_pod = k // 2
        num_hosts_per_edge = k // 2

        core_switches = []
        for i in range(1, num_cores + 1):
            dpid = f"{i:016x}"
            sw = self.addSwitch(f'c{i}', dpid=dpid)
            core_switches.append(sw)

        host_id = 1
        dpid_counter = 100
        for pod in range(num_pods):
            aggr_switches = []
            edge_switches = []

            for a in range(num_aggr_per_pod):
                dpid_counter += 1
                sw = self.addSwitch(f'a{pod}_{a}', dpid=f"{dpid_counter:016x}")
                aggr_switches.append(sw)

            for e in range(num_edge_per_pod):
                dpid_counter += 1
                sw = self.addSwitch(f'e{pod}_{e}', dpid=f"{dpid_counter:016x}")
                edge_switches.append(sw)

            for e_idx, e_sw in enumerate(edge_switches):
                for a_sw in aggr_switches:
                    self.addLink(e_sw, a_sw, bw=edge_bw, delay=edge_delay)

                for h in range(num_hosts_per_edge):
                    host_ip = f"10.{pod}.{e_idx}.{h+2}/24"
                    host_mac = f"00:00:00:{pod:02x}:{e_idx:02x}:{h+2:02x}"
                    host = self.addHost(f'h{host_id}', ip=host_ip, mac=host_mac)
                    self.addLink(host, e_sw, bw=core_bw, delay='1ms')
                    host_id += 1

            for a_idx, a_sw in enumerate(aggr_switches):
                for c in range(k // 2):
                    core_idx = a_idx * (k // 2) + c
                    self.addLink(a_sw, core_switches[core_idx], bw=core_bw, delay=core_delay)


def start_unicast_traffic(net, mice_rate_1="15M", mice_rate_2="10M", mice_duration=45):
    """Generates continuous background unicast mice flows (HTTP/RPC traffic)."""
    info("\n[Traffic] Starting Background Mice Flows (Web/RPC lightweight streams)...\n")
    try:
        h1 = net.get('h1')
        h2 = net.get('h2')
        h3 = net.get('h3')
        h5 = net.get('h5')
        h6 = net.get('h6')

        h1.cmd('iperf -s -u -p 5001 &')
        h5.cmd('iperf -s -u -p 5002 &')

        h2.cmd(f'iperf -c {h1.IP()} -u -p 5001 -b {mice_rate_1} -t {mice_duration} &')
        h3.cmd(f'iperf -c {h5.IP()} -u -p 5002 -b {mice_rate_2} -t {mice_duration} &')
        h6.cmd(f'iperf -c {h1.IP()} -u -p 5001 -b 8M -t {mice_duration} &')
        info("[Traffic] Background mice flows active.\n")
    except Exception as e:
        info(f"[Traffic] Background traffic error: {e}\n")


def start_elephant_flows(net, rate="45M", duration=35, src_host='h4', dst_host='h8', port=5004):
    """Generates high-bandwidth bursty elephant flows to induce core link congestion."""
    info(f"\n[Traffic] Starting Bursty Elephant Flows ({src_host} -> {dst_host} @ {rate})...\n")
    try:
        src = net.get(src_host)
        dst = net.get(dst_host)

        dst.cmd(f'iperf -s -u -p {port} &')
        time.sleep(1)
        # High-rate burst to saturate primary core link and trigger DQN rerouting
        src.cmd(f'iperf -c {dst.IP()} -u -p {port} -b {rate} -t {duration} &')
        info(f"[Traffic] Elephant flow active ({src_host} -> {dst_host} @ {rate}).\n")
    except Exception as e:
        info(f"[Traffic] Elephant flow error: {e}\n")


def run_network(topo_choice='tree', controller_ip=DEFAULT_CTRL_IP, controller_port=DEFAULT_CTRL_PORT,
                core_bw=DEFAULT_CORE_BW, core_delay=DEFAULT_CORE_DELAY,
                elephant_rate="45M", auto_traffic=True):
    setLogLevel('info')

    if topo_choice == 'fattree':
        info("*** Selected Topology: FatTree (k=4: 20 switches, 16 hosts)\n")
        topo = FatTreeTopology(k=4, core_bw=int(core_bw), core_delay=core_delay)
    else:
        info("*** Selected Topology: Hierarchical Tree (7 switches, 8 hosts, redundant mesh)\n")
        topo = TreeTopology(core_bw=int(core_bw), core_delay=core_delay)

    info(f"*** Initializing Mininet Network with Remote Ryu Controller on {controller_ip}:{controller_port}\n")
    net = Mininet(
        topo=topo,
        switch=OVSSwitch,
        controller=RemoteController('c0', ip=controller_ip, port=int(controller_port)),
        link=TCLink,
        autoSetMacs=True,
        autoStaticArp=True
    )

    net.start()
    info("\n*** Network Started successfully! Waiting 5s for LLDP discovery...\n")
    time.sleep(5)

    info("*** Performing Initial Host Ping Test...\n")
    try:
        net.ping([net.get('h1'), net.get('h2')])
    except Exception:
        pass

    # Launch Synthetic Traffic Scenarios in background threads if enabled
    if auto_traffic:
        t1 = threading.Thread(target=start_unicast_traffic, args=(net,))
        t2 = threading.Thread(target=start_elephant_flows, args=(net, elephant_rate))

        t1.start()
        time.sleep(3)
        t2.start()

    info("\n*** Dropping into interactive Mininet CLI. Type 'exit' to stop.\n")
    CLI(net)

    info("*** Stopping Network\n")
    net.stop()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Adaptive SDN Traffic Engineering Mininet Runner (EC499)")
    parser.add_argument('--topo', choices=['tree', 'fattree'], default='tree',
                        help='Topology selection (tree or fattree)')
    parser.add_argument('--controller-ip', default=DEFAULT_CTRL_IP,
                        help=f'OpenFlow controller IP address (default: {DEFAULT_CTRL_IP})')
    parser.add_argument('--controller-port', type=int, default=DEFAULT_CTRL_PORT,
                        help=f'OpenFlow controller port (default: {DEFAULT_CTRL_PORT})')
    parser.add_argument('--core-bw', type=float, default=DEFAULT_CORE_BW,
                        help=f'Core link bandwidth in Mbps (default: {DEFAULT_CORE_BW})')
    parser.add_argument('--core-delay', default=DEFAULT_CORE_DELAY,
                        help=f'Core link propagation delay (default: {DEFAULT_CORE_DELAY})')
    parser.add_argument('--elephant-rate', default="45M",
                        help='Bandwidth rate for elephant burst flow (default: 45M)')
    parser.add_argument('--no-traffic', action='store_true',
                        help='Disable automatic synthetic traffic generation')
    args = parser.parse_args()

    run_network(
        topo_choice=args.topo,
        controller_ip=args.controller_ip,
        controller_port=args.controller_port,
        core_bw=args.core_bw,
        core_delay=args.core_delay,
        elephant_rate=args.elephant_rate,
        auto_traffic=not args.no_traffic
    )
