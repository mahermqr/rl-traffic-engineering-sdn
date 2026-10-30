# `controller/state_manager.py`

> **File:** `controller/state_manager.py`  
> **Subsystem / Category:** 2. SDN Controller Architecture & Modules  
> **Language:** `python`  
> **Lines of Code:** 1,036  
> **File Size:** 48.09 KB  

---

## Overview

Real-time network telemetry engine collecting switch statistics, calculating link latency, jitter, loss, and maintaining the active topology graph.

### Architecture & Symbols
- **Classes:** `StateManager`
- **Key Functions:** None (Module level / Declarative)

---

## Source Code

```python
import numpy as np
import networkx as nx
import time
import collections
import os
import sys
import threading

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BASE_DIR not in sys.path:
    sys.path.insert(0, _BASE_DIR)

try:
    import config
except ImportError:
    config = None
try:
    from .queue_model import mm1k_metrics
except ImportError:
    from queue_model import mm1k_metrics

class StateManager:
    """
    Centralized State and Telemetry Repository for Adaptive SDN Traffic Engineering (EC499).
    Maintains network topology, link metrics, port/flow differential rates,
    host locations, network jitter (RFC 3393), packet loss modeling, and OpenFlow control overhead.
    """
    def __init__(self):
        self._lock = threading.RLock()
        # Topology graph: nodes are switch DPIDs, edges have 'port', 'bandwidth', 'delay', 'loss'
        self.graph = nx.DiGraph()

        # Configurable defaults
        self.default_capacity = getattr(config, 'DEFAULT_LINK_CAPACITY', 100.0)
        self.default_delay = getattr(config, 'DEFAULT_LINK_DELAY', 2.0)
        self.default_jitter = getattr(config, 'DEFAULT_LINK_JITTER', 0.25)
        self.core_trunk_ratio = 1.0
        self.base_loss_pct = 0.0
        self.default_k = min(getattr(config, 'K_CANDIDATE_PATHS', 4), getattr(config, 'ACTION_SIZE', 4))
        self.state_size = int(getattr(config, 'STATE_SIZE', 10))
        if self.state_size < 2:
            raise ValueError("STATE_SIZE must be at least 2")

        # Link metric dictionaries: keyed by (src_dpid, dst_dpid)
        self.link_bandwidths = {}   # Capacity in Mbps
        self.link_utilization = {}  # Current utilization [0.0 - 1.0]
        self.base_link_delays = {}  # Static physical base latency in ms (uncongested)
        self.link_delays = {}       # Real-time queuing latency in ms
        self.link_jitter = {}       # Network Jitter / Delay Variation in ms (RFC 3393)
        self.link_loss = {}         # Packet loss rate percentage [0.0 - 100.0%]
        self._prev_delays = {}      # Previous delay sample for jitter calculation
        self.active_dynamic_flows = {} # flow_id -> {'path', 'mbps', 'expires_at'}

        # Host tracking tables: enables dynamic ARP/L2/L3 resolution
        self.host_ip_to_mac = {}    # ip -> mac
        self.host_locations = {}    # mac -> (dpid, port)
        self.ip_to_location = {}    # ip -> (dpid, port)
        self.mac_to_port = {}       # (dpid, mac) -> port

        # Telemetry history for rate calculation
        self.raw_port_stats = {}    # (dpid, port) -> {'rx_bytes', 'tx_bytes', 'rx_pkts', 'tx_pkts', 'timestamp'}
        self.port_rates = {}        # (dpid, port) -> {'rx_mbps', 'tx_mbps', 'rx_pps', 'tx_pps'}

        self.raw_flow_stats = {}    # (dpid, src_ip, dst_ip) -> {'bytes', 'packets', 'duration', 'timestamp'}
        self.flow_stats = {}        # (dpid, src_ip, dst_ip) -> {'mbps', 'pps', 'packets', 'bytes', 'duration'}
        self.flow_paths = {}        # (dpid, src_ip, dst_ip) -> [hop1, hop2, ...]

        # OpenFlow Control Overhead Accounting (Proposal Objective 5)
        self.packet_in_count = 0
        self.flow_mod_count = 0
        self.stats_request_count = 0
        self.stats_reply_count = 0
        self.control_overhead_bytes = 0
        self.controller_decision_times = collections.deque(maxlen=1000) # latencies in ms
        self.decision_count = 0
        self.switch_rtt_ms = {}
        self.control_overhead_start_time = time.time()

        # Link failure & degradation recovery tracking: (u, v) -> edge_attributes
        self.failed_links = {}
        self.degraded_links = {}

        # D3QN Multi-Objective reward weights
        self.w_hops = getattr(config, 'W_HOPS', 0.35)
        self.w_delay = getattr(config, 'W_DELAY', 0.06)
        self.w_congestion = getattr(config, 'W_CONGESTION', 1.0)
        self.w_jitter = getattr(config, 'W_JITTER', 0.25)
        self.w_loss = getattr(config, 'W_LOSS', 0.50)
        self.congestion_barrier_pct = getattr(config, 'CONGESTION_BARRIER_THRESHOLD', 0.70) * 100.0

        # Traffic Generation & Matrix defaults
        self.traffic_pattern = getattr(config, 'DEFAULT_TRAFFIC_PATTERN', 'uniform')
        self.traffic_flow_rate_mbps = getattr(config, 'DEFAULT_FLOW_RATE_MBPS', 15.0)
        self.diffserv_dscp = getattr(config, 'DEFAULT_DSCP', 'BE')
        self.flow_duration_model = getattr(config, 'DEFAULT_FLOW_DURATION_MODEL', 'closed_loop')

        # OpenFlow 1.3 Control Plane defaults
        self.switch_queue_depth = getattr(config, 'SWITCH_QUEUE_DEPTH', 256)
        self.switch_mtu = getattr(config, 'SWITCH_MTU', 1500)
        self.flow_timeout_sec = getattr(config, 'FLOW_IDLE_TIMEOUT', 30)
        self.max_flow_rules = getattr(config, 'MAX_FLOW_RULES', 1000)
        self.poll_interval_sec = getattr(config, 'STATS_POLL_INTERVAL', 2.5)
        self.k_candidate_paths = getattr(config, 'K_CANDIDATE_PATHS', 4)
        self.lldp_interval_sec = getattr(config, 'LLDP_INTERVAL_SEC', 2.0)
        self.multipart_stats_mode = getattr(config, 'MULTIPART_STATS_MODE', 'port')
        self.control_channel_mode = getattr(config, 'CONTROL_CHANNEL_MODE', 'oob')

        # Rolling time-series telemetry history (up to 60 data points for live web charts)
        self.telemetry_history = collections.deque(maxlen=60)
        self.active_simulation_mode = None

        # Routing candidate path cache: (src_dpid, dst_dpid) -> list of candidate paths
        self._routing_path_cache = {}

        # Closed-loop shadow reservation tracking to eliminate micro-herd pileups during telemetry polling interval:
        self.shadow_reservations = collections.defaultdict(float)
        self.shadow_last_update = collections.defaultdict(float)
        self.shadow_decay_half_life = float(getattr(config, 'SHADOW_DECAY_HALF_LIFE', 1.5))

        # Active topology metadata tracking
        default_topo = getattr(config, 'DEFAULT_TOPOLOGY_ID', 'tree')
        self.current_topology_id = default_topo
        self.current_topology_meta = {'name': f'Default Topology ({default_topo})', 'id': default_topo}

    def record_flow_reservation(self, path, estimated_rate_mbps=None):
        """
        Records an immediate shadow reservation along the routed path to damp
        micro-herd pileup between OpenFlow port statistics polling intervals.
        """
        if not path or len(path) <= 1:
            return
        if estimated_rate_mbps is None:
            estimated_rate_mbps = float(getattr(self, 'traffic_flow_rate_mbps', 15.0))

        now = time.time()
        for i in range(len(path) - 1):
            edge = (path[i], path[i+1])
            cap = max(1.0, self.link_bandwidths.get(edge, self.default_capacity))
            add_ratio = float(estimated_rate_mbps) / cap
            self.shadow_reservations[edge] += add_ratio
            self.shadow_last_update[edge] = now

    def get_effective_utilization(self, edge):
        """
        Returns effective link utilization combining physical OpenFlow polled byte counters
        with decaying shadow reservations to eradicate micro-burst herding.
        """
        polled_u = float(self.link_utilization.get(edge, 0.0))
        shadow_u = self.shadow_reservations.get(edge, 0.0)
        if shadow_u > 0.0:
            last_t = self.shadow_last_update.get(edge, 0.0)
            elapsed = max(0.0, time.time() - last_t)
            decayed_shadow = shadow_u * (0.5 ** (elapsed / max(0.5, self.shadow_decay_half_life)))
            self.shadow_reservations[edge] = decayed_shadow
            return max(0.0, polled_u + decayed_shadow)
        return max(0.0, polled_u)

    def clear_shadow_reservations(self):
        """Clears shadow reservations upon global topology reset or manual flush."""
        self.shadow_reservations.clear()
        self.shadow_last_update.clear()

    def set_topology(self, topo_id, graph, meta):
        """Sets active topology and initializes links, attributes, and routing cache."""
        with self._lock:
            self.current_topology_id = topo_id
            self.current_topology_meta = meta or {'name': topo_id, 'id': topo_id}
            self.active_core_nodes = list((meta or {}).get('core_nodes', []))
            self.active_edge_nodes = list((meta or {}).get('edge_nodes', []))
            self.graph = nx.DiGraph()
            self.graph.add_nodes_from(graph.nodes(data=True))
            for store in (
                self.link_bandwidths, self.base_link_delays, self.link_delays,
                self.link_jitter, self.link_loss, self.link_utilization,
                self._prev_delays, self.failed_links, self.degraded_links,
                self.raw_port_stats, self.port_rates, self.raw_flow_stats,
                self.flow_stats, self.flow_paths, self.active_dynamic_flows,
                self.switch_rtt_ms,
            ):
                store.clear()
            self.clear_hosts()
            self.clear_shadow_reservations()
            self._routing_path_cache.clear()
            self.active_simulation_mode = None

            host_port_max = collections.defaultdict(int)
            for host in (meta or {}).get('hosts', []):
                host_port_max[host.get('switch')] = max(host_port_max[host.get('switch')], int(host.get('port', 0)))
            next_port = {node: host_port_max[node] + 1 for node in graph.nodes()}
            port_map = {}
            for u in sorted(graph.nodes(), key=str):
                succs = graph.successors(u) if hasattr(graph, 'is_directed') and graph.is_directed() else graph.neighbors(u)
                for v in sorted(succs, key=str):
                    port_map[(u, v)] = next_port[u]
                    next_port[u] += 1

            for u, v, d in graph.edges(data=True):
                self.update_link(
                    u, v, src_port=port_map[(u, v)], dst_port=port_map.get((v, u)),
                    capacity_mbps=d.get('capacity', self.default_capacity),
                    delay_ms=d.get('delay', self.default_delay), loss=d.get('loss', 0.0),
                )

    # --------------------------------------------------------------------------
    # Topology & Host Management
    # --------------------------------------------------------------------------

    def register_switch(self, dpid):
        """Registers a switch datapath node in the topology graph."""
        if not self.graph.has_node(dpid):
            self.graph.add_node(dpid)

    def unregister_switch(self, dpid):
        """Removes a switch datapath node from the topology graph."""
        if self.graph.has_node(dpid):
            self.graph.remove_node(dpid)
            self._routing_path_cache.clear()
        edge_stores = (self.link_bandwidths, self.base_link_delays, self.link_delays,
                       self.link_jitter, self.link_loss, self.link_utilization,
                       self._prev_delays, self.failed_links, self.degraded_links,
                       self.shadow_reservations, self.shadow_last_update)
        for store in edge_stores:
            for key in [key for key in store if dpid in key]:
                store.pop(key, None)
        for key in [key for key in self.raw_port_stats if key[0] == dpid]:
            self.raw_port_stats.pop(key, None)
            self.port_rates.pop(key, None)
        for ip, location in list(self.ip_to_location.items()):
            if location[0] == dpid:
                self.ip_to_location.pop(ip, None)
                self.host_ip_to_mac.pop(ip, None)
        for mac, location in list(self.host_locations.items()):
            if location[0] == dpid:
                self.host_locations.pop(mac, None)
        for key in [key for key in self.mac_to_port if key[0] == dpid]:
            self.mac_to_port.pop(key, None)

    def update_link(self, src_dpid, dst_dpid, src_port, dst_port=None, capacity_mbps=None, delay_ms=None, loss=0.0):
        """Adds or updates an inter-switch directional link."""
        if capacity_mbps is None:
            capacity_mbps = self.default_capacity
        if delay_ms is None:
            delay_ms = self.default_delay

        self.register_switch(src_dpid)
        self.register_switch(dst_dpid)

        self.graph.add_edge(src_dpid, dst_dpid, port=src_port, peer_port=dst_port,
                            capacity=float(capacity_mbps), delay=float(delay_ms), loss=float(loss))
        self._routing_path_cache.clear()
        self.link_bandwidths[(src_dpid, dst_dpid)] = float(capacity_mbps)
        self.base_link_delays[(src_dpid, dst_dpid)] = float(delay_ms)
        if (src_dpid, dst_dpid) not in self.link_delays:
            self.link_delays[(src_dpid, dst_dpid)] = float(delay_ms)
        if (src_dpid, dst_dpid) not in self.link_jitter:
            self.link_jitter[(src_dpid, dst_dpid)] = float(self.default_jitter) # Nominal base jitter ms
        if (src_dpid, dst_dpid) not in self.link_loss:
            self.link_loss[(src_dpid, dst_dpid)] = float(loss)
        if (src_dpid, dst_dpid) not in self.link_utilization:
            self.link_utilization[(src_dpid, dst_dpid)] = 0.0

    def update_network_parameters(self, default_capacity=None, default_delay=None, default_jitter=None, loss_rate=None, core_capacity_ratio=None):
        """Configures global link capacities, propagation delays, and loss rates across the active fabric."""
        if default_capacity is not None:
            self.default_capacity = float(default_capacity)
        if default_delay is not None:
            self.default_delay = float(default_delay)
        if default_jitter is not None:
            self.default_jitter = float(default_jitter)
        if loss_rate is not None:
            self.base_loss_pct = float(loss_rate)
        if core_capacity_ratio is not None:
            self.core_trunk_ratio = float(core_capacity_ratio)
        core_ratio = getattr(self, 'core_trunk_ratio', 1.0)

        for (u, v) in list(self.link_bandwidths.keys()):
            cap = float(self.default_capacity)
            is_core = u in getattr(self, 'active_core_nodes', []) or v in getattr(self, 'active_core_nodes', [])
            if is_core and core_ratio > 1.0:
                cap *= core_ratio

            self.link_bandwidths[(u, v)] = cap
            self.base_link_delays[(u, v)] = float(self.default_delay)
            self.link_delays[(u, v)] = float(self.default_delay)
            if loss_rate is not None:
                self.link_loss[(u, v)] = float(loss_rate)
            if default_jitter is not None:
                self.link_jitter[(u, v)] = float(default_jitter)

        self._routing_path_cache.clear()

    def record_host(self, ip, mac, dpid, port):
        """Records host location and mapping for dynamic packet routing."""
        # Never record a host on an inter-switch trunk port
        if self.graph.has_node(dpid):
            for _, _, data in self.graph.out_edges(dpid, data=True):
                if data.get('port') == port:
                    return  # Packet arrived on a trunk port connecting two switches, ignore

        if ip:
            self.host_ip_to_mac[ip] = mac
            self.ip_to_location[ip] = (dpid, port)
        if mac:
            self.host_locations[mac] = (dpid, port)
            self.mac_to_port[(dpid, mac)] = port

    def clear_hosts(self):
        """Clears learned host locations."""
        self.host_ip_to_mac.clear()
        self.host_locations.clear()
        self.ip_to_location.clear()
        self.mac_to_port.clear()

    def get_host_location(self, ip=None, mac=None):
        """Returns (dpid, port) for a given IP or MAC address."""
        if ip and ip in self.ip_to_location:
            return self.ip_to_location[ip]
        if mac and mac in self.host_locations:
            return self.host_locations[mac]
        if ip and ip in self.host_ip_to_mac:
            m = self.host_ip_to_mac[ip]
            return self.host_locations.get(m, (None, None))
        return (None, None)

    # --------------------------------------------------------------------------
    # Telemetry & Differential Statistics
    # --------------------------------------------------------------------------

    def update_port_stats(self, dpid, port_no, rx_bytes, tx_bytes, rx_packets, tx_packets, duration_sec):
        """Updates port stats and computes differential Mbps, PPS, link utilization, jitter, and loss."""
        now = time.time()
        key = (dpid, port_no)

        if key in self.raw_port_stats:
            prev = self.raw_port_stats[key]
            dt = max(0.1, now - prev['timestamp'])

            delta_rx_bytes = max(0, rx_bytes - prev['rx_bytes'])
            delta_tx_bytes = max(0, tx_bytes - prev['tx_bytes'])
            delta_rx_pkts = max(0, rx_packets - prev['rx_pkts'])
            delta_tx_pkts = max(0, tx_packets - prev['tx_pkts'])

            # Rate in Mbps: (bytes * 8) / (1e6 * dt)
            rx_mbps = (delta_rx_bytes * 8.0) / (1e6 * dt)
            tx_mbps = (delta_tx_bytes * 8.0) / (1e6 * dt)
            rx_pps = delta_rx_pkts / dt
            tx_pps = delta_tx_pkts / dt

            self.port_rates[key] = {
                'rx_mbps': rx_mbps,
                'tx_mbps': tx_mbps,
                'rx_pps': rx_pps,
                'tx_pps': tx_pps
            }

            # Update link utilization if this port connects to an adjacent switch
            for neighbor in self.graph.successors(dpid):
                edge_data = self.graph.get_edge_data(dpid, neighbor)
                if edge_data and edge_data.get('port') == port_no:
                    capacity = self.link_bandwidths.get((dpid, neighbor), 100.0)
                    util = max(0.0, tx_mbps / max(1.0, capacity))
                    self.link_utilization[(dpid, neighbor)] = util
                    self._recalculate_link_metrics((dpid, neighbor))

        self.raw_port_stats[key] = {
            'rx_bytes': rx_bytes,
            'tx_bytes': tx_bytes,
            'rx_pkts': rx_packets,
            'tx_pkts': tx_packets,
            'duration': duration_sec,
            'timestamp': now
        }

    def update_flow_stats(self, dpid, src_ip, dst_ip, packets, bytes_count, duration_sec):
        """Updates flow counters and calculates throughput rates."""
        now = time.time()
        key = (dpid, src_ip, dst_ip)

        delta_packets = packets
        delta_bytes = bytes_count

        if key in self.raw_flow_stats:
            prev = self.raw_flow_stats[key]
            dt = max(0.1, now - prev['timestamp'])
            delta_packets = max(0, packets - prev['packets'])
            delta_bytes = max(0, bytes_count - prev['bytes'])

            mbps = (delta_bytes * 8.0) / (1e6 * dt)
            pps = delta_packets / dt
        else:
            mbps = (bytes_count * 8.0) / (1e6 * max(0.1, duration_sec)) if duration_sec > 0 else 0.0
            pps = delta_packets / max(0.1, duration_sec) if duration_sec > 0 else 0.0

        self.raw_flow_stats[key] = {
            'packets': packets,
            'bytes': bytes_count,
            'duration': duration_sec,
            'timestamp': now
        }

        self.flow_stats[key] = {
            'mbps': mbps,
            'pps': pps,
            'packets': packets,
            'bytes': bytes_count,
            'duration': duration_sec
        }

    def record_flow_path(self, dpid, src_ip, dst_ip, path):
        """Records the installed or simulated routing path decision for a flow."""
        if not hasattr(self, 'flow_paths'):
            self.flow_paths = {}
        self.flow_paths[(dpid, src_ip, dst_ip)] = list(path)

    def get_flow_records(self):
        """Returns structured flow table telemetry for REST and dashboard display."""
        records = []
        flow_paths = getattr(self, 'flow_paths', {})
        for (dpid, src_ip, dst_ip), stats in self.flow_stats.items():
            path = flow_paths.get((dpid, src_ip, dst_ip), [])
            path_str = " \u2192 ".join(f"s{n}" for n in path) if path else f"s{dpid}"
            records.append({
                'dpid': dpid,
                'src_ip': src_ip,
                'dst_ip': dst_ip,
                'packets': stats.get('packets', 0),
                'bytes': stats.get('bytes', 0),
                'mbps': round(stats.get('mbps', 0.0), 2),
                'pps': round(stats.get('pps', 0.0), 1),
                'path': path_str
            })
        return records

    def update_link_latency(self, src_dpid, dst_dpid, delay_ms):
        """
        Updates measured link latency and calculates RFC 3393 / RFC 3550 Delay Variation (Jitter).
        Exponential moving average: J_k = J_{k-1} + (|D_k - D_{k-1}| - J_{k-1}) / 16
        """
        link = (src_dpid, dst_dpid)
        d_new = max(0.1, float(delay_ms))
        d_prev = self._prev_delays.get(link, d_new)
        self._prev_delays[link] = d_new
        self.link_delays[link] = d_new

        # Instantaneous delay variation
        d_diff = abs(d_new - d_prev)
        j_prev = self.link_jitter.get(link, 0.25)

        # Account for queue congestion variance target (RFC 3393 / RFC 3550)
        util = self.link_utilization.get(link, 0.0)
        congestion_jitter = 0.0
        if util > 0.60:
            congestion_boost = (util ** 2) / max(0.05, 1.0 - min(0.95, util))
            congestion_jitter = min(12.0, 0.15 * d_new * min(3.0, congestion_boost))

        # Target instant jitter includes physical variation plus load-induced queue variance
        target_jitter = max(0.20, d_diff + congestion_jitter)
        # RFC 3550 Jitter filter: smooth convergence without runaway accumulation
        j_new = j_prev + (target_jitter - j_prev) / 16.0
        j_bounded = min(15.0, max(0.05, float(j_new)))

        self.link_jitter[link] = j_bounded

    # --------------------------------------------------------------------------
    # Control Overhead Accounting (Proposal Objective 5)
    # --------------------------------------------------------------------------

    def record_packet_in(self, byte_size=64):
        """Records an incoming OpenFlow OFPPacketIn message."""
        self.packet_in_count += 1
        self.control_overhead_bytes += byte_size

    def record_flow_mod(self, byte_size=72):
        """Records an outgoing OpenFlow OFPFlowMod rule installation."""
        self.flow_mod_count += 1
        self.control_overhead_bytes += byte_size

    def record_stats_request(self, byte_size=56):
        """Records a stats query message."""
        self.stats_request_count += 1
        self.control_overhead_bytes += byte_size

    def record_stats_reply(self, byte_size=128):
        """Records a stats reply message."""
        self.stats_reply_count += 1
        self.control_overhead_bytes += byte_size

    def record_decision_latency(self, latency_ms):
        """Records the time taken by the controller / RL agent to infer an optimal path."""
        self.controller_decision_times.append(float(latency_ms))
        self.decision_count += 1

    def record_switch_rtt(self, dpid, latency_ms):
        """Records controller-to-switch echo RTT without mislabelling it as link delay."""
        self.switch_rtt_ms[int(dpid)] = max(0.0, float(latency_ms))

    def get_control_overhead_summary(self):
        """
        Computes detailed quantitative OpenFlow control plane metrics.
        Returns:
          - packet_in_count: total PacketIn messages
          - flow_mod_count: total FlowMod installations
          - total_control_messages: PacketIn + FlowMod + Stats
          - mean_decision_latency_ms: average decision execution time
          - p95_decision_latency_ms: 95th percentile decision latency
          - decision_throughput_dps: decisions processed per second
          - total_control_overhead_kb: total control channel bytes in KB
        """
        dt = max(0.5, time.time() - self.control_overhead_start_time)
        times = list(self.controller_decision_times)
        mean_time = float(np.mean(times)) if times else 0.45
        p95_time = float(np.percentile(times, 95)) if times else 0.85
        total_msgs = self.packet_in_count + self.flow_mod_count + self.stats_request_count + self.stats_reply_count
        dps = (self.decision_count / dt) if dt > 0 else 0.0

        return {
            'packet_in_count': int(self.packet_in_count),
            'flow_mod_count': int(self.flow_mod_count),
            'stats_request_count': int(self.stats_request_count),
            'stats_reply_count': int(self.stats_reply_count),
            'total_control_messages': int(total_msgs),
            'control_message_rate_mps': round(float(total_msgs / dt), 2),
            'mean_decision_latency_ms': round(mean_time, 3),
            'p95_decision_latency_ms': round(p95_time, 3),
            'decision_throughput_dps': round(float(dps), 1),
            'flow_mod_rate_mps': round(float(self.flow_mod_count / dt), 2),
            'switch_rtt_ms': {str(k): round(v, 3) for k, v in self.switch_rtt_ms.items()},
            'total_control_overhead_kb': round(float(self.control_overhead_bytes / 1024.0), 2)
        }

    # --------------------------------------------------------------------------
    # Aggregate Network Telemetry Summary (Proposal Objectives 3, 4, 5)
    # --------------------------------------------------------------------------

    def get_network_te_summary(self):
        """
        Calculates all key metrics defined in the EC499 Proposal:
          - Total Network Throughput (Mbps)
          - Bottleneck Link Utilization (%)
          - Mean Link Utilization (%)
          - Jain's Fairness Index across links
          - Mean Latency (ms)
          - Mean Jitter (ms)
          - Aggregate Packet Loss Rate (%)
          - Active Flows Count
          - Control Overhead Summary
        """
        # End-to-end offered throughput counts each active flow once, not once per hop.
        total_mbps = sum(float(f.get('mbps', 0.0)) for f in self.active_dynamic_flows.values())
        if total_mbps == 0.0 and self.flow_stats:
            unique_flows = {}
            for (_dpid, src_ip, dst_ip), stats in self.flow_stats.items():
                key = (src_ip, dst_ip)
                unique_flows[key] = max(unique_flows.get(key, 0.0), float(stats.get('mbps', 0.0)))
            total_mbps = sum(unique_flows.values())
        aggregate_link_tx = sum(p.get('tx_mbps', 0.0) for p in self.port_rates.values())

        utils = list(self.link_utilization.values()) or [0.0]
        path_delays = []
        for path in self.flow_paths.values():
            if len(path) > 1:
                path_delays.append(sum(self.link_delays.get((u, v), self.default_delay) for u, v in zip(path, path[1:])))
        delays = path_delays or list(self.link_delays.values()) or [self.default_delay]
        jitters = list(self.link_jitter.values()) or [0.25]
        losses = list(self.link_loss.values()) or [0.0]

        max_u = float(np.max(utils))
        mean_u = float(np.mean(utils))

        # Jain's Fairness Index: (sum(u))^2 / (n * sum(u^2))
        u_arr = np.array(utils, dtype=np.float64)
        sum_u = np.sum(u_arr)
        sum_sq_u = np.sum(u_arr ** 2)
        n = len(u_arr)
        jains_index = float((sum_u ** 2) / max(1e-6, n * sum_sq_u)) if sum_sq_u > 0 else 1.0
        jains_index = min(1.0, max(0.0, jains_index))

        summary = {
            'total_throughput_mbps': round(float(total_mbps), 2),
            'aggregate_link_tx_mbps': round(float(aggregate_link_tx), 2),
            'bottleneck_utilization_pct': round(float(max_u * 100.0), 2),
            'peak_bottleneck_util_pct': round(float(max_u * 100.0), 2),
            'mean_utilization_pct': round(float(mean_u * 100.0), 2),
            'jains_fairness_index': round(float(jains_index), 4),
            'mean_latency_ms': round(float(np.mean(delays)), 2),
            'mean_jitter_ms': round(float(np.mean(jitters)), 3),
            'mean_packet_loss_pct': round(float(np.mean(losses)), 3),
            'active_flows_count': len(self.active_dynamic_flows) if self.active_dynamic_flows else len({(k[1], k[2]) for k in self.flow_stats}),
            'control_overhead': self.get_control_overhead_summary(),
            'current_topology': getattr(self, 'current_topology_id', 'tree'),
            'topology_name': getattr(self, 'current_topology_meta', {}).get('name', 'Hierarchical Tree (Baseline)')
        }
        return summary

    def get_traffic_engineering_summary(self):
        """Alias for get_network_te_summary."""
        return self.get_network_te_summary()

    # --------------------------------------------------------------------------
    # Feature Extractors for DQN Adaptive Routing
    # --------------------------------------------------------------------------

    def get_candidate_paths(self, src_dpid, dst_dpid, k=None):
        """
        Discovers up to k diversity-aware candidate paths between source and destination:
        - Path 0: Dijkstra Shortest Path (hop count / OSPF base)
        - Path 1: 2nd Shortest Simple Path
        - Path 2: Diverse / Low-Overlap Bypass Path (routes around primary path edges)
        - Path 3: Widest Path (minimizes peak link utilization)
        """
        k = max(1, int(k or self.default_k))
        if not self.graph.has_node(src_dpid) or not self.graph.has_node(dst_dpid):
            return []
        if src_dpid == dst_dpid:
            return [[src_dpid]]

        cache_key = (src_dpid, dst_dpid)
        with self._lock:
            simple_paths = self._routing_path_cache.get(cache_key)
            if simple_paths is None:
                try:
                    import itertools
                    simple_paths = list(itertools.islice(
                        nx.shortest_simple_paths(self.graph, src_dpid, dst_dpid), 16
                    ))
                except (nx.NetworkXNoPath, nx.NodeNotFound):
                    simple_paths = []
                self._routing_path_cache[cache_key] = simple_paths
        if not simple_paths:
            return []

        primary = simple_paths[0]
        selected = [primary]
        if len(simple_paths) > 1:
            selected.append(simple_paths[1])

        primary_edges = set(zip(primary, primary[1:]))
        remaining = [p for p in simple_paths if p not in selected]
        if remaining:
            diverse = min(remaining, key=lambda p: (len(set(zip(p, p[1:])) & primary_edges), len(p)))
            selected.append(diverse)

        # The load-aware candidate is recomputed on every call; only topology paths are cached.
        try:
            def dynamic_cost(u, v, data):
                util = self.get_effective_utilization((u, v))
                delay = float(self.link_delays.get((u, v), data.get('delay', self.default_delay)))
                return delay * (1.0 + 25.0 * max(0.0, util - 0.55) ** 2)
            load_aware = nx.dijkstra_path(self.graph, src_dpid, dst_dpid, weight=dynamic_cost)
            if load_aware not in selected:
                selected.append(load_aware)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            pass

        for path in simple_paths:
            if len(selected) >= k:
                break
            if path not in selected:
                selected.append(path)
        return selected[:k]

    def get_routing_state(self, src_dpid, dst_dpid):
        """
        Builds a normalized 10-dimensional state vector for DQN Traffic Engineering Agent:
        [0]: Normalized shortest path length (hops / 10.0) in (0, 1]
        [1-4]: Bottleneck link utilization of Candidate Paths 0, 1, 2, 3 [0.0 - 1.0] (effective utilization)
        [5-8]: Normalized end-to-end latency of Candidate Paths 0, 1, 2, 3 [0.0 - 1.0] (delay / 50.0)
        [9]: Network-wide peak link utilization [0.0 - 1.0] (effective utilization)
        """
        state = np.zeros(self.state_size, dtype=np.float32)
        if not self.graph.has_node(src_dpid) or not self.graph.has_node(dst_dpid):
            return state
        feature_k = max(0, min(self.default_k, (self.state_size - 2) // 2))
        candidate_paths = self.get_candidate_paths(src_dpid, dst_dpid, k=feature_k)

        # 0: Shortest path hops normalized
        if candidate_paths and len(candidate_paths[0]) > 1:
            hops = len(candidate_paths[0]) - 1
            state[0] = min(1.0, max(0.1, hops / 10.0))
        else:
            state[0] = 0.1

        # 1-4: Effective bottleneck link utilization on each candidate path
        # 5-8: Normalized delay on each candidate path
        for i in range(feature_k):
            if i < len(candidate_paths):
                p = candidate_paths[i]
                if len(p) > 1:
                    utils = [self.get_effective_utilization((p[j], p[j+1])) for j in range(len(p)-1)]
                    delays = [self.link_delays.get((p[j], p[j+1]), self.default_delay) for j in range(len(p)-1)]
                    state[1 + i] = min(1.0, max(0.0, float(max(utils) if utils else 0.0)))
                    state[1 + feature_k + i] = min(1.0, max(0.0, float(sum(delays) / 50.0)))
                else:
                    state[1 + i] = 0.0
                    state[1 + feature_k + i] = 0.04
            else:
                state[1 + i] = 1.0
                state[1 + feature_k + i] = 1.0

        # 9: Peak effective network utilization across all active links
        all_utils = [self.get_effective_utilization(edge) for edge in self.link_bandwidths.keys()]
        if self.state_size > 1:
            state[-1] = min(1.0, max(0.0, float(max(all_utils)))) if all_utils else 0.0

        return state

    # --------------------------------------------------------------------------
    # Interactive Simulation & Telemetry Injection
    # --------------------------------------------------------------------------

    def _recalculate_link_metrics(self, edge):
        """Recomputes finite-buffer loss, queue delay, and synthetic port rate."""
        if edge not in self.link_bandwidths:
            return
        util = max(0.0, float(self.link_utilization.get(edge, 0.0)))
        base_delay = max(0.01, float(self.base_link_delays.get(edge, self.default_delay)))
        queue = mm1k_metrics(
            util,
            queue_depth=self.switch_queue_depth,
            service_time_ms=base_delay,
            max_queue_delay_ms=getattr(config, 'MAX_QUEUE_DELAY_MS', 1000.0),
        )
        self.link_loss[edge] = queue['loss_pct']
        self.update_link_latency(edge[0], edge[1], base_delay + queue['queue_delay_ms'])
        if self.graph.has_edge(*edge):
            port = self.graph[edge[0]][edge[1]].get('port')
            if port is not None:
                mbps = util * self.link_bandwidths[edge]
                previous = self.port_rates.get((edge[0], port), {})
                self.port_rates[(edge[0], port)] = {
                    'rx_mbps': mbps, 'tx_mbps': mbps,
                    'rx_pps': previous.get('rx_pps', 0.0),
                    'tx_pps': previous.get('tx_pps', 0.0),
                }

    def inject_traffic_flow(self, src_ip, dst_ip, src_dpid, dst_dpid, mbps=15.0, pps=1200.0, duration=10.0, path=None):
        """Injects a simulated flow and updates link utilization, jitter, and loss along the chosen path."""
        flow_duration = float(duration) if duration else 10.0
        bytes_count = int((mbps * 1e6 * flow_duration) / 8.0)
        packets = int(pps * flow_duration)
        self.update_flow_stats(src_dpid, src_ip, dst_ip, packets, bytes_count, flow_duration)
        key = (src_dpid, src_ip, dst_ip)
        self.flow_stats[key]['mbps'] = float(mbps)
        self.flow_stats[key]['pps'] = float(pps)
        if path:
            self.record_flow_path(src_dpid, src_ip, dst_ip, path)

        if path and len(path) > 1:
            for i in range(len(path) - 1):
                u, v = path[i], path[i+1]
                cap = self.link_bandwidths.get((u, v), 100.0)
                add_util = mbps / max(1.0, cap)
                new_u = max(0.0, self.link_utilization.get((u, v), 0.0) + add_util)
                self.link_utilization[(u, v)] = new_u
                self._recalculate_link_metrics((u, v))

    # --------------------------------------------------------------------------
    # Closed-Loop Dynamic Flow Allocation (Proposal Objective 4)
    # --------------------------------------------------------------------------

    def allocate_dynamic_flow(self, flow_id, path, mbps=5.0, duration_sec=10.0,
                              src_ip=None, dst_ip=None, src_dpid=None, pps=0.0):
        """
        Allocates an active unicast flow along a designated multi-hop path.
        Simulates dynamic closed-loop bandwidth consumption on link queues.
        """
        now = time.time()
        if not hasattr(self, 'active_dynamic_flows'):
            self.active_dynamic_flows = {}

        if not path or len(path) < 2 or any(not self.graph.has_edge(u, v) for u, v in zip(path, path[1:])):
            return False
        with self._lock:
            if flow_id in self.active_dynamic_flows:
                self.release_dynamic_flow(flow_id)
            flow = {
                'path': list(path), 'mbps': float(mbps),
                'expires_at': now + max(0.0, float(duration_sec)),
            }
            if src_ip and dst_ip:
                origin = int(src_dpid if src_dpid is not None else path[0])
                duration = max(0.1, float(duration_sec))
                bytes_count = int(float(mbps) * 1e6 * duration / 8.0)
                packets = int(float(pps) * duration)
                self.update_flow_stats(origin, src_ip, dst_ip, packets, bytes_count, duration)
                key = (origin, src_ip, dst_ip)
                self.flow_stats[key]['mbps'] = float(mbps)
                self.flow_stats[key]['pps'] = float(pps)
                self.record_flow_path(origin, src_ip, dst_ip, path)
                flow['flow_key'] = key
            self.active_dynamic_flows[flow_id] = flow
            for u, v in zip(path, path[1:]):
                edge = (u, v)
                cap = self.link_bandwidths.get(edge, self.default_capacity)
                self.link_utilization[edge] = max(0.0, self.link_utilization.get(edge, 0.0) + float(mbps) / max(1.0, cap))
                self._recalculate_link_metrics(edge)
        return True

    def release_dynamic_flow(self, flow_id):
        """Reclaims link bandwidth and relieves queue congestion upon flow completion."""
        if not hasattr(self, 'active_dynamic_flows'):
            self.active_dynamic_flows = {}
            return
        flow = self.active_dynamic_flows.pop(flow_id, None)
        if not flow:
            return
        path = flow['path']
        mbps = flow['mbps']
        with self._lock:
            for u, v in zip(path, path[1:]):
                edge = (u, v)
                cap = self.link_bandwidths.get(edge, self.default_capacity)
                self.link_utilization[edge] = max(0.0, self.link_utilization.get(edge, 0.0) - mbps / max(1.0, cap))
                self._recalculate_link_metrics(edge)
            key = flow.get('flow_key')
            if key:
                self.flow_stats.pop(key, None)
                self.raw_flow_stats.pop(key, None)
                self.flow_paths.pop(key, None)

    def clear_dynamic_flows(self):
        """Releases all simulated allocations through the same accounting path."""
        for flow_id in list(self.active_dynamic_flows):
            self.release_dynamic_flow(flow_id)

    def step_dynamic_flows(self, current_time=None):
        """Expires finished flows whose lifespan has ended."""
        if not hasattr(self, 'active_dynamic_flows'):
            self.active_dynamic_flows = {}
            return 0
        now = current_time or time.time()
        expired = [fid for fid, f in self.active_dynamic_flows.items() if now >= f['expires_at']]
        for fid in expired:
            self.release_dynamic_flow(fid)
        return len(expired)

    def inject_core_congestion(self, utilization=0.95, core_nodes=None, asymmetric_ratio=0.5):
        """
        Saturates core switch links to test lateral cross-link rerouting.
        Topology-Agnostic: dynamically identifies core / transit bottlenecks via
        metadata or networkx edge betweenness centrality.
        When multiple core nodes exist, saturates the primary subset (asymmetric_ratio)
        to simulate realistic elephant-flow hotspot bottlenecks rather than total gridlock.
        """
        target_edges = []
        c_nodes = core_nodes or (self.active_core_nodes if hasattr(self, 'active_core_nodes') and self.active_core_nodes else None)
        if c_nodes:
            if len(c_nodes) > 1 and asymmetric_ratio is not None and asymmetric_ratio < 1.0:
                subset_count = max(1, int(round(len(c_nodes) * asymmetric_ratio)))
                jammed_cores = set(c_nodes[:subset_count])
            else:
                jammed_cores = set(c_nodes)
            for u, v in self.graph.edges():
                if u in jammed_cores or v in jammed_cores:
                    target_edges.append((u, v))
        else:
            # Fallback: Automatic discovery via Edge Betweenness Centrality on arbitrary graph
            if self.graph.number_of_edges() > 0:
                centrality = nx.edge_betweenness_centrality(self.graph)
                sorted_edges = sorted(centrality.items(), key=lambda x: x[1], reverse=True)
                top_k = max(2, int(len(sorted_edges) * 0.25))
                target_edges = [edge for edge, _ in sorted_edges[:top_k]]
                for u, v in list(target_edges):
                    if self.graph.has_edge(v, u) and (v, u) not in target_edges:
                        target_edges.append((v, u))

        # Apply high congestion to discovered core edges
        target_set = set(target_edges)
        for u, v in self.graph.edges():
            if (u, v) in target_set:
                self.link_utilization[(u, v)] = float(utilization)
                self._recalculate_link_metrics((u, v))
            else:
                # Keep lateral / perimeter edges uncongested
                self.link_utilization[(u, v)] = 0.15
                self._recalculate_link_metrics((u, v))

        self.active_simulation_mode = "core_jamming"
        return len(target_edges)

    def reset_simulation(self, restore_faults=False):
        """Resets link utilization and clears simulated telemetry."""
        self.clear_dynamic_flows()
        self.clear_shadow_reservations()
        for k in self.link_utilization:
            self.link_utilization[k] = 0.05
            self.link_loss[k] = getattr(self, 'base_loss_pct', 0.0)
            self.link_jitter[k] = getattr(self, 'default_jitter', 0.25)
        for k in self.link_delays:
            self.link_delays[k] = self.base_link_delays.get(k, getattr(self, 'default_delay', 2.0))
        self._prev_delays.clear()
        self.port_rates.clear()
        self.flow_stats.clear()
        self.flow_paths.clear()
        self.raw_flow_stats.clear()
        self.raw_port_stats.clear()
        self.active_simulation_mode = None
        if restore_faults:
            self.restore_link()
            if hasattr(self, 'restore_degraded_links'):
                self.restore_degraded_links()
            self.active_simulation_mode = None

    def inject_link_failure(self, u, v):
        """Simulates physical fiber cut or port down between switch u and v."""
        try:
            u, v = int(u), int(v)
        except (ValueError, TypeError):
            return False
        if not self.graph.has_edge(u, v) and not self.graph.has_edge(v, u):
            return False
        data_fwd = dict(self.graph[u][v]) if self.graph.has_edge(u, v) else {}
        data_rev = dict(self.graph[v][u]) if self.graph.has_edge(v, u) else data_fwd
        if not data_fwd and data_rev:
            data_fwd = data_rev
        self.failed_links[(u, v)] = data_fwd
        self.failed_links[(v, u)] = data_rev
        if self.graph.has_edge(u, v):
            self.graph.remove_edge(u, v)
        if self.graph.has_edge(v, u):
            self.graph.remove_edge(v, u)
        self._routing_path_cache.clear()
        self.active_simulation_mode = f"link_failure_{u}_{v}"
        return True

    def restore_link(self, u=None, v=None):
        """Restores specific or all previously severed links."""
        restored = 0
        if u is not None and v is not None:
            try:
                u, v = int(u), int(v)
                pairs = [(u, v), (v, u)]
            except (ValueError, TypeError):
                pairs = list(self.failed_links.keys())
        else:
            pairs = list(self.failed_links.keys())

        for edge in pairs:
            if edge in self.failed_links:
                data = self.failed_links.pop(edge)
                src, dst = edge
                self.graph.add_edge(src, dst, **data)
                restored += 1

        if restored > 0:
            self._routing_path_cache.clear()
            if not self.failed_links:
                self.active_simulation_mode = None
        return restored

    def inject_link_degradation(self, u, v, throttle_pct=0.10, delay_mult=5.0):
        """Simulates physical fiber degradation (e.g. dirty optics, high bit error rate)."""
        try:
            u, v = int(u), int(v)
            throttle_pct, delay_mult = float(throttle_pct), float(delay_mult)
        except (TypeError, ValueError):
            return False
        if not (0.0 < throttle_pct <= 1.0 and delay_mult >= 1.0):
            return False
        if not self.graph.has_edge(u, v):
            return False
        pairs = [(u, v)]
        if self.graph.has_edge(v, u):
            pairs.append((v, u))
        for src, dst in pairs:
            orig_cap = self.link_bandwidths.get((src, dst), self.default_capacity)
            orig_delay = self.base_link_delays.get((src, dst), self.default_delay)
            orig_loss = self.link_loss.get((src, dst), 0.0)
            self.degraded_links[(src, dst)] = {
                'bandwidth': orig_cap,
                'delay': orig_delay,
                'loss': orig_loss
            }
            self.link_bandwidths[(src, dst)] = max(1.0, orig_cap * throttle_pct)
            self.base_link_delays[(src, dst)] = orig_delay * delay_mult
            self.link_delays[(src, dst)] = orig_delay * delay_mult
            self.link_loss[(src, dst)] = 12.5  # High physical bit error rate
        self._routing_path_cache.clear()
        self.active_simulation_mode = f"degraded_{u}_{v}"
        return True

    def restore_degraded_links(self, u=None, v=None):
        """Restores degraded links back to nominal capacity, delay, and zero base loss."""
        restored = 0
        if u is not None and v is not None:
            pairs = [(u, v), (v, u)]
        else:
            pairs = list(self.degraded_links.keys())
        for edge in pairs:
            if edge in self.degraded_links:
                data = self.degraded_links.pop(edge)
                self.link_bandwidths[edge] = data['bandwidth']
                self.base_link_delays[edge] = data['delay']
                self.link_delays[edge] = data['delay']
                self.link_loss[edge] = data['loss']
                restored += 1
        if restored > 0:
            self._routing_path_cache.clear()
            if not self.degraded_links and not self.failed_links:
                self.active_simulation_mode = None
        return restored

    def inject_traffic_burst(self, u, v=None, mbps=50.0):
        """Injects a sudden congestion spike / flash traffic surge to stress test D3QN rerouting."""
        burst_edges = []
        if v is not None and self.graph.has_edge(u, v):
            burst_edges.append((u, v))
        else:
            for neighbor in self.graph.neighbors(u):
                burst_edges.append((u, neighbor))
        for src, dst in burst_edges:
            cap = self.link_bandwidths.get((src, dst), self.default_capacity)
            add_util = float(mbps) / max(1.0, cap)
            self.link_utilization[(src, dst)] = max(0.0, self.link_utilization.get((src, dst), 0.0) + add_util)
            self._recalculate_link_metrics((src, dst))
        return len(burst_edges)

    def sample_telemetry_history(self):
        """Periodic telemetry history sampler."""
        now = time.time()
        te_summary = self.get_network_te_summary()
        self.telemetry_history.append({
            'timestamp': time.strftime("%H:%M:%S", time.localtime(now)),
            'throughput_mbps': te_summary['total_throughput_mbps'],
            'bottleneck_utilization_pct': te_summary['bottleneck_utilization_pct'],
            'mean_utilization_pct': te_summary['mean_utilization_pct'],
            'avg_latency_ms': te_summary['mean_latency_ms'],
            'avg_jitter_ms': te_summary['mean_jitter_ms'],
            'packet_loss_pct': te_summary['mean_packet_loss_pct'],
            'active_flows': te_summary['active_flows_count'],
            'flow_mods': te_summary['control_overhead']['flow_mod_count']
        })

    def update_security_window(self):
        """Alias for backward compatibility."""
        self.sample_telemetry_history()
```
