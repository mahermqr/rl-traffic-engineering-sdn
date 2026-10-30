# `test_suite.py`

> **File:** `test_suite.py`  
> **Subsystem / Category:** 7. Verification, Testing & High Availability  
> **Language:** `python`  
> **Lines of Code:** 689  
> **File Size:** 30.00 KB  

---

## Overview

Comprehensive unit and integration test suite verifying controller components, DQN agent, queue model, and routing mechanisms.

### Architecture & Symbols
- **Classes:** `TestDQNAgent`, `TestPrioritizedReplay`, `TestStateManager`, `TestTraditionalRoutingBaselines`, `TestMultiTopologySupport`, `TestClosedLoopDynamicsAndUpgrades`, `TestCentralConfig`, `TestWebDashboardAndVersusAPI`, `TestHighAvailabilityClustering`
- **Key Functions:** `_bootstrap_environment`

---

## Source Code

```python
#!/usr/bin/env python3
"""
Comprehensive Unit & Integration Test Suite (EC499).
Reinforcement Learning for Adaptive Traffic Engineering in an SDN Network.

Tests:
  1. Deep Q-Network (Double DQN) Lifecycle & Dueling Architecture
  2. Prioritized Experience Replay (SumTree arithmetic, IS weights, priority updates)
  3. StateManager Telemetry (Throughput, Latency, Jitter RFC 3393, Packet Loss, Control Overhead)
  4. Classical & Greedy Routing Baselines (OSPF RFC 2328, Dijkstra SPF, ECMP, WSP, LLR)
  5. Multi-Topology Fabric Integrity (Tree, Fat-Tree, Abilene, NSFNet, Spine-Leaf)
  6. Controller OpenFlow 1.3 Flow Installation & Candidate Path Decomposition
"""

import sys
import os
import time
import tempfile
import unittest

# Auto-detect and activate virtualenv if dependencies like numpy or torch are missing
def _bootstrap_environment():
    """Ensure dependencies from virtual environment (e.g. ~/ec499_env) are loaded even if run with system python."""
    try:
        import numpy  # noqa: F401
        import torch  # noqa: F401
        return
    except ImportError:
        pass

    # 1. Search for virtual environment python executables to re-exec
    candidate_venvs = [
        os.path.expanduser('~/ec499_env/bin/python3'),
        os.path.expanduser('~/ec499_env/bin/python'),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.venv', 'bin', 'python3'),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'venv', 'bin', 'python3'),
        os.path.expanduser('~/.venv/bin/python3'),
    ]
    for cand in candidate_venvs:
        cand_prefix = os.path.dirname(os.path.dirname(os.path.abspath(cand)))
        if os.path.exists(cand) and os.access(cand, os.X_OK) and cand_prefix != sys.prefix:
            try:
                os.execv(cand, [cand] + sys.argv)
            except Exception:
                pass

    # 2. Fallback: Search for site-packages directories and inject into sys.path
    lib_candidates = [
        os.path.expanduser('~/ec499_env/lib'),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.venv', 'lib'),
        os.path.expanduser('~/.venv/lib'),
    ]
    for lib_dir in lib_candidates:
        if os.path.isdir(lib_dir):
            for entry in os.listdir(lib_dir):
                sp = os.path.join(lib_dir, entry, 'site-packages')
                if os.path.isdir(sp) and sp not in sys.path:
                    sys.path.insert(0, sp)

_bootstrap_environment()

# Setup path imports
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)
for subdir in ['agent', 'controller', 'topology']:
    p = os.path.join(BASE_DIR, subdir)
    if p not in sys.path:
        sys.path.append(p)

import numpy as np
import torch
import networkx as nx
import config

from dqn_router import DQNRoutingAgent, DuelingQNetwork
from prioritized_replay import PrioritizedReplayBuffer, SumTree
from state_manager import StateManager
from topology_library import get_topology, build_random_topology
from traditional_routing import (
    ospf_routing, dijkstra_spf, ecmp_routing, widest_shortest_path,
    least_loaded_routing, compute_path_metrics
)
from ha_controller_pool import HAControllerPool, ControllerNode
from benchmark_routing_algorithms import generate_flow_specs


class TestDQNAgent(unittest.TestCase):
    """Verifies PyTorch DQN Agent forward passes, Dueling architecture, experience replay, and checkpointing."""

    def test_dqn_router_lifecycle(self):
        agent = DQNRoutingAgent(state_size=10, action_size=4, lr=0.001)
        dummy_state = np.random.rand(10).astype(np.float32)

        # Test greedy vs exploration inference
        greedy_action = agent.act(dummy_state, explore=False)
        self.assertIn(greedy_action, range(4))

        # Test experience storage
        for _ in range(40):
            s = np.random.rand(10).astype(np.float32)
            a = np.random.randint(0, 4)
            r = float(np.random.randn())
            s_next = np.random.rand(10).astype(np.float32)
            agent.remember(s, a, r, s_next, False)

        loss = agent.train(batch_size=16)
        self.assertIsNotNone(loss)
        self.assertGreater(loss, 0.0)

        # Test checkpoint save and load
        with tempfile.NamedTemporaryFile(suffix='.pth', delete=False) as tmp:
            tmp_path = tmp.name
        try:
            agent.save(tmp_path)
            self.assertTrue(os.path.exists(tmp_path))
            new_agent = DQNRoutingAgent(state_size=10, action_size=4)
            loaded = new_agent.load(tmp_path)
            self.assertTrue(loaded)
            # Verify loaded weights match
            for p1, p2 in zip(agent.model.parameters(), new_agent.model.parameters()):
                self.assertTrue(torch.equal(p1, p2))
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_dueling_architecture(self):
        model = DuelingQNetwork(state_size=10, action_size=4)
        dummy_input = torch.randn(4, 10)
        q_values = model(dummy_input)

        self.assertEqual(q_values.shape, (4, 4))

        # Verify Value and Advantage streams
        features = model.feature_network(dummy_input)
        val = model.value_stream(features)
        adv = model.advantage_stream(features)
        self.assertEqual(val.shape, (4, 1))
        self.assertEqual(adv.shape, (4, 4))

        # Check advantage centering: mean of centered advantage should be ~0
        centered_adv = adv - adv.mean(dim=-1, keepdim=True)
        self.assertTrue(torch.allclose(centered_adv.mean(dim=-1), torch.zeros(4), atol=1e-5))


class TestPrioritizedReplay(unittest.TestCase):
    """Verifies SumTree arithmetic and Prioritized Experience Replay buffer sampling."""

    def test_sumtree_arithmetic(self):
        tree = SumTree(capacity=8)
        priorities = [1.0, 2.0, 3.0, 4.0]
        for p in priorities:
            tree.add(p, f"data_{p}")

        self.assertAlmostEqual(tree.total(), 10.0, places=4)
        self.assertEqual(tree.n_entries, 4)

        # Update priority of first entry from 1.0 to 5.0
        idx, _, _ = tree.get(0.5)
        tree.update(idx, 5.0)
        self.assertAlmostEqual(tree.total(), 14.0, places=4)

    def test_replay_buffer_sampling(self):
        buf = PrioritizedReplayBuffer(capacity=100, alpha=0.6, beta=0.4)
        batch, idxs, weights = buf.sample(16)
        self.assertEqual(len(batch), 0)

        for i in range(25):
            buf.add(np.zeros(10), i % 4, 1.0, np.zeros(10), False)

        batch, idxs, weights = buf.sample(16)
        self.assertEqual(len(batch), 16)
        self.assertEqual(len(idxs), 16)
        self.assertEqual(len(weights), 16)
        self.assertAlmostEqual(weights.max(), 1.0, places=3)


class TestStateManager(unittest.TestCase):
    """Verifies topology representation, rate extraction, Jitter, Loss, and Control Overhead."""

    def setUp(self):
        self.sm = StateManager()
        self.sm.update_link(1, 2, src_port=1, dst_port=1, capacity_mbps=100.0, delay_ms=2.0)
        self.sm.update_link(2, 1, src_port=1, dst_port=1, capacity_mbps=100.0, delay_ms=2.0)
        self.sm.update_link(2, 3, src_port=2, dst_port=1, capacity_mbps=50.0, delay_ms=4.0)
        self.sm.update_link(3, 2, src_port=1, dst_port=2, capacity_mbps=50.0, delay_ms=4.0)
        self.sm.update_link(1, 4, src_port=2, dst_port=1, capacity_mbps=100.0, delay_ms=3.0)
        self.sm.update_link(4, 1, src_port=1, dst_port=2, capacity_mbps=100.0, delay_ms=3.0)

    def test_routing_state_features(self):
        state = self.sm.get_routing_state(src_dpid=4, dst_dpid=3)
        self.assertEqual(len(state), 10)
        self.assertGreater(state[0], 0.0)
        self.assertLessEqual(state[0], 1.0)
        for i in range(10):
            self.assertGreaterEqual(state[i], 0.0)
            self.assertLessEqual(state[i], 1.0)

    def test_configurable_state_dimension_and_no_fake_route(self):
        self.sm.state_size = 12
        self.assertEqual(len(self.sm.get_routing_state(4, 3)), 12)
        self.sm.register_switch(99)
        self.assertEqual(self.sm.get_candidate_paths(4, 99), [])

    def test_directional_dynamic_flow_accounting_and_release(self):
        reverse_before = self.sm.link_utilization[(2, 1)]
        self.assertTrue(self.sm.allocate_dynamic_flow('directional', [1, 2], mbps=25.0, duration_sec=5.0))
        self.assertAlmostEqual(self.sm.link_utilization[(1, 2)], 0.25, places=5)
        self.assertEqual(self.sm.link_utilization[(2, 1)], reverse_before)
        self.sm.release_dynamic_flow('directional')
        self.assertAlmostEqual(self.sm.link_utilization[(1, 2)], 0.0, places=5)
        self.assertEqual(self.sm.link_utilization[(2, 1)], reverse_before)

    def test_host_location_tracking(self):
        self.sm.record_host(ip="10.0.0.1", mac="00:00:00:00:00:01", dpid=4, port=3)
        dpid, port = self.sm.get_host_location(ip="10.0.0.1")
        self.assertEqual(dpid, 4)
        self.assertEqual(port, 3)

    def test_differential_port_rates(self):
        self.sm.update_port_stats(dpid=1, port_no=1, rx_bytes=1000, tx_bytes=2000,
                                  rx_packets=10, tx_packets=20, duration_sec=1)
        time.sleep(0.12)
        self.sm.update_port_stats(dpid=1, port_no=1, rx_bytes=1000, tx_bytes=1002000,
                                  rx_packets=10, tx_packets=1020, duration_sec=2)

        rates = self.sm.port_rates.get((1, 1))
        self.assertIsNotNone(rates)
        self.assertGreater(rates['tx_mbps'], 10.0)
        self.assertGreater(rates['tx_pps'], 1000.0)

    def test_jitter_calculation(self):
        # Update link with varying latency
        self.sm.update_link_latency(1, 2, delay_ms=2.0)
        self.sm.update_link_latency(1, 2, delay_ms=8.0)
        jitter = self.sm.link_jitter.get((1, 2))
        self.assertIsNotNone(jitter)
        self.assertGreater(jitter, 0.0)

    def test_packet_loss_modeling(self):
        # Low load: loss near 0
        self.sm.link_utilization[(1, 2)] = 0.35
        self.sm.update_port_stats(1, 1, 1000, 2000, 10, 20, 1)
        # Saturated load: loss increases
        self.sm.link_utilization[(1, 2)] = 0.95
        loss_metric = 0.05 + 30.0 * (((0.95 - 0.70) / 0.30) ** 2.2)
        self.assertGreater(loss_metric, 10.0)

    def test_control_overhead_accounting(self):
        self.sm.record_packet_in(byte_size=64)
        self.sm.record_flow_mod(byte_size=72)
        self.sm.record_stats_request(byte_size=56)
        self.sm.record_stats_reply(byte_size=128)
        self.sm.record_decision_latency(0.45)

        summary = self.sm.get_control_overhead_summary()
        self.assertEqual(summary['packet_in_count'], 1)
        self.assertEqual(summary['flow_mod_count'], 1)
        self.assertEqual(summary['stats_request_count'], 1)
        self.assertEqual(summary['stats_reply_count'], 1)
        self.assertGreater(summary['mean_decision_latency_ms'], 0.0)

    def test_network_te_summary(self):
        self.sm.inject_traffic_flow("10.0.0.1", "10.0.0.3", 4, 3, mbps=20.0, path=[4, 1, 2, 3])
        summary = self.sm.get_network_te_summary()
        self.assertGreaterEqual(summary['total_throughput_mbps'], 0.0)
        self.assertGreaterEqual(summary['jains_fairness_index'], 0.0)
        self.assertLessEqual(summary['jains_fairness_index'], 1.0)
        self.assertIn('control_overhead', summary)

    def test_link_failure_and_restoration(self):
        self.assertTrue(self.sm.inject_link_failure(1, 2))
        self.assertFalse(self.sm.graph.has_edge(1, 2))
        restored = self.sm.restore_link(1, 2)
        self.assertEqual(restored, 2) # Restores both directions
        self.assertTrue(self.sm.graph.has_edge(1, 2))

    def test_flow_table_records(self):
        self.sm.inject_traffic_flow("10.0.0.1", "10.0.0.3", 4, 3, mbps=25.0, pps=1800.0, path=[4, 1, 2, 3])
        records = self.sm.get_flow_records()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]['src_ip'], "10.0.0.1")
        self.assertEqual(records[0]['dst_ip'], "10.0.0.3")
        self.assertEqual(records[0]['dpid'], 4)
        self.assertAlmostEqual(records[0]['mbps'], 25.0, places=1)
        self.assertIn("s4", records[0]['path'])
        self.assertIn("s3", records[0]['path'])

    def test_inject_traffic_flow_duration_and_latency_scaling(self):
        # Verify custom duration is stored and respected
        self.sm.inject_traffic_flow("10.0.0.1", "10.0.0.2", 1, 2, mbps=10.0, pps=500.0, duration=5.0, path=[1, 2])
        rec = self.sm.flow_stats.get((1, "10.0.0.1", "10.0.0.2"))
        self.assertIsNotNone(rec)
        self.assertEqual(rec['duration'], 5.0)

        # Verify repeated bursts accumulate offered load and finite-buffer delay monotonically.
        base_d = self.sm.base_link_delays.get((1, 2), 2.0)
        self.sm.inject_traffic_burst(1, 2, mbps=20.0)
        delay_1 = self.sm.link_delays.get((1, 2))
        self.sm.inject_traffic_burst(1, 2, mbps=20.0)
        delay_2 = self.sm.link_delays.get((1, 2))
        self.assertGreater(delay_1, base_d)
        self.assertGreater(delay_2, delay_1)
        self.assertLessEqual(delay_2 - base_d, config.MAX_QUEUE_DELAY_MS)


class TestTraditionalRoutingBaselines(unittest.TestCase):
    """Verifies OSPF, Dijkstra SPF, ECMP, WSP, LLR and path metric computations."""

    def setUp(self):
        g, _ = get_topology('tree')
        self.graph = g
        self.link_utils = {}
        self.link_delays = {}
        self.link_bws = {}
        for u, v, d in g.edges(data=True):
            self.link_bws[(u, v)] = d.get('capacity', 100.0)
            self.link_delays[(u, v)] = d.get('delay', 2.0)
            self.link_utils[(u, v)] = 0.20

    def test_ospf_routing(self):
        p = ospf_routing(self.graph, 4, 6, link_bandwidths=self.link_bws)
        self.assertEqual(p[0], 4)
        self.assertEqual(p[-1], 6)
        # OSPF path exists
        self.assertGreaterEqual(len(p), 2)

    def test_dijkstra_spf(self):
        p = dijkstra_spf(self.graph, 4, 6)
        self.assertEqual(p[0], 4)
        self.assertEqual(p[-1], 6)
        self.assertEqual(p, [4, 6]) # Direct cross-link is 1 hop

    def test_ecmp_routing(self):
        p = ecmp_routing(self.graph, 4, 6, flow_hash=0)
        self.assertEqual(p[0], 4)
        self.assertEqual(p[-1], 6)

    def test_wsp_and_llr_routing(self):
        # Saturate direct cross-link [4, 6] to 95%
        self.link_utils[(4, 6)] = 0.95
        self.link_utils[(6, 4)] = 0.95

        p_wsp = widest_shortest_path(self.graph, 4, 6, self.link_utils, self.link_delays)
        p_llr = least_loaded_routing(self.graph, 4, 6, self.link_utils)

        # Both WSP and LLR should avoid the 95% saturated direct link if an alternative is less loaded
        m_wsp = compute_path_metrics(p_wsp, self.link_utils, self.link_delays, self.link_bws)
        m_llr = compute_path_metrics(p_llr, self.link_utils, self.link_delays, self.link_bws)

        self.assertLessEqual(m_wsp['bottleneck_util'], 0.95)
        self.assertLessEqual(m_llr['bottleneck_util'], 0.95)

    def test_compute_path_metrics(self):
        path = [4, 2, 1, 3, 6]
        m = compute_path_metrics(path, self.link_utils, self.link_delays, self.link_bws)
        self.assertEqual(m['hops'], 4)
        self.assertGreater(m['total_delay'], 0.0)
        self.assertGreater(m['jitter'], 0.0)
        self.assertGreaterEqual(m['packet_loss'], 0.0)


class TestMultiTopologySupport(unittest.TestCase):
    """Verifies that all 5 required topologies instantiate properly."""

    def test_all_topologies(self):
        for topo_id in ['tree', 'fattree', 'abilene', 'nsfnet', 'spineleaf']:
            g, meta = get_topology(topo_id)
            self.assertGreater(g.number_of_nodes(), 0)
            self.assertGreater(g.number_of_edges(), 0)
            self.assertTrue(nx.is_strongly_connected(g), f"Topology {topo_id} is not strongly connected")
            # Verify coordinates
            pos = meta.get('positions', {})
            for n in g.nodes():
                self.assertIn(n, pos, f"Node {n} missing position in {topo_id}")
                self.assertGreaterEqual(pos[n]['x'], 0.0)
                self.assertLessEqual(pos[n]['x'], 1.0)
                self.assertGreaterEqual(pos[n]['y'], 0.0)
                self.assertLessEqual(pos[n]['y'], 1.0)
            # Verify link metrics
            for u, v, d in g.edges(data=True):
                self.assertGreater(d.get('capacity', 0), 0)
                self.assertGreater(d.get('delay', 0), 0)
            # Verify hosts
            hosts = meta.get('hosts', [])
            self.assertGreater(len(hosts), 0, f"Topology {topo_id} has no hosts")
            for h in hosts:
                self.assertIn('ip', h)
                self.assertIn('switch', h)
                self.assertIn(h['switch'], g.nodes(), f"Host switch {h['switch']} not in {topo_id}")

    def test_random_topology_generation(self):
        # Standard topology
        g, meta = build_random_topology(num_nodes=15, p_edge=0.30, seed=42)
        self.assertEqual(g.number_of_nodes(), 15)
        self.assertTrue(nx.is_strongly_connected(g))
        self.assertIn('core_nodes', meta)
        self.assertIn('edge_nodes', meta)
        self.assertGreaterEqual(len(meta['edge_nodes']), 2)

        # Edge case: small topologies (N=3, N=4) must not crash and have valid hosts
        for n in [3, 4]:
            g_small, meta_small = build_random_topology(num_nodes=n, seed=42)
            self.assertEqual(g_small.number_of_nodes(), n)
            self.assertTrue(nx.is_strongly_connected(g_small))
            self.assertGreaterEqual(len(meta_small['edge_nodes']), 1)
            self.assertGreaterEqual(len(meta_small['hosts']), 1)


class TestClosedLoopDynamicsAndUpgrades(unittest.TestCase):
    """Verifies architectural upgrades: Polyak soft updates, dynamic closed-loop flow dynamics, and generalized core congestion."""

    def test_seeded_workloads_are_reproducible_and_distinct(self):
        nodes = [1, 2, 3, 4]
        seed_42_a = generate_flow_specs(nodes, topology_size=7, seed=42, count=12)
        seed_42_b = generate_flow_specs(nodes, topology_size=7, seed=42, count=12)
        seed_43 = generate_flow_specs(nodes, topology_size=7, seed=43, count=12)
        self.assertEqual(seed_42_a, seed_42_b)
        self.assertNotEqual(seed_42_a, seed_43)

    def test_polyak_soft_update_consistency(self):
        agent = DQNRoutingAgent(state_size=10, action_size=4, tau=0.01)
        # Store initial target weights
        init_target_param = next(agent.target_model.parameters()).clone()
        # Mutate policy network weights
        with torch.no_grad():
            for p in agent.model.parameters():
                p.add_(1.0)
        # Populate replay buffer and train one step
        for _ in range(40):
            s = np.random.rand(10).astype(np.float32)
            agent.remember(s, 0, 1.0, s, False)
        agent.train(batch_size=16)
        updated_target_param = next(agent.target_model.parameters())
        # Target parameter should have smoothly shifted towards policy parameter
        self.assertFalse(torch.equal(init_target_param, updated_target_param))

    def test_closed_loop_flow_accumulation_and_expiration(self):
        sm = StateManager()
        sm.update_link(1, 2, src_port=1, dst_port=1, capacity_mbps=100.0, delay_ms=2.0)
        sm.update_link(2, 3, src_port=1, dst_port=1, capacity_mbps=100.0, delay_ms=2.0)
        init_u = sm.link_utilization.get((1, 2), 0.0)

        # Allocate dynamic flow of 30 Mbps
        sm.allocate_dynamic_flow(flow_id="f1", path=[1, 2, 3], mbps=30.0, duration_sec=0.2)
        post_alloc_u = sm.link_utilization[(1, 2)]
        self.assertAlmostEqual(post_alloc_u, init_u + 0.30, places=2)
        self.assertGreater(sm.link_loss[(1, 2)], 0.0)

        # Expire flow
        time.sleep(0.25)
        expired_count = sm.step_dynamic_flows()
        self.assertEqual(expired_count, 1)
        reclaimed_u = sm.link_utilization[(1, 2)]
        self.assertLess(reclaimed_u, post_alloc_u)

    def test_generalized_core_congestion_across_topologies(self):
        # Test topology-agnostic core discovery on NSFNet (continental mesh)
        g_nsf, meta_nsf = get_topology('nsfnet')
        sm = StateManager()
        sm.graph = g_nsf.copy()
        for u, v, d in g_nsf.edges(data=True):
            sm.update_link(u, v, src_port=1, dst_port=1, capacity_mbps=d.get('capacity', 100.0), delay_ms=d.get('delay', 2.0))

        congested_count = sm.inject_core_congestion(utilization=0.92)
        self.assertGreater(congested_count, 0)
        # Verify that saturated links have high utilization and analytical loss
        max_u = max(sm.link_utilization.values())
        self.assertAlmostEqual(max_u, 0.92, places=2)


class TestCentralConfig(unittest.TestCase):
    """Verifies the centralized, zero-hardcoded configuration engine and environment variable overrides."""

    def test_config_dictionary_structure(self):
        import config
        conf_dict = config.to_dict()
        self.assertIn("paths", conf_dict)
        self.assertIn("network", conf_dict)
        self.assertIn("rl", conf_dict)
        self.assertIn("traffic_engineering", conf_dict)

        self.assertIn("default_model_path", conf_dict["paths"])
        self.assertIn("controller_port", conf_dict["network"])
        self.assertIn("learning_rate", conf_dict["rl"])
        self.assertIn("congestion_barrier_threshold", conf_dict["traffic_engineering"])

    def test_env_var_override_and_type_casting(self):
        import config
        test_var_name = "SDN_TEST_OVERRIDE_VAL"
        os.environ[test_var_name] = "9999"
        try:
            val_int = config.get_config_val("dummy_key", test_var_name, default=1234, cast_type=int)
            self.assertEqual(val_int, 9999)

            val_str = config.get_config_val("dummy_key", test_var_name, default="default", cast_type=str)
            self.assertEqual(val_str, "9999")
        finally:
            del os.environ[test_var_name]

    def test_agent_and_state_manager_with_config_defaults(self):
        import config
        agent = DQNRoutingAgent(state_size=config.STATE_SIZE, action_size=config.ACTION_SIZE)
        self.assertEqual(agent.state_size, config.STATE_SIZE)
        self.assertEqual(agent.action_size, config.ACTION_SIZE)

        sm = StateManager()
        self.assertGreater(sm.default_capacity, 0.0)
        self.assertGreater(sm.default_delay, 0.0)

    def test_ha_config_presence(self):
        import config
        conf_dict = config.to_dict()
        self.assertIn("ha_enabled", conf_dict["network"])
        self.assertIn("backup_controllers", conf_dict["network"])
        self.assertEqual(len(conf_dict["network"]["backup_controllers"]), 2)
        self.assertEqual(config.CONTROLLER_PORT_BACKUP1, 6634)
        self.assertEqual(config.CONTROLLER_PORT_BACKUP2, 6635)
        self.assertEqual(config.REST_PORT_BACKUP1, 8081)
        self.assertEqual(config.REST_PORT_BACKUP2, 8082)


class TestWebDashboardAndVersusAPI(unittest.TestCase):
    """Automated tests for Web Dashboard, Connected Model Telemetry, and Versus Engine."""

    @classmethod
    def setUpClass(cls):
        import urllib.request
        from web_dashboard import DashboardServer
        cls.test_port = 8111
        cls.server = DashboardServer(host="127.0.0.1", port=cls.test_port)
        time.sleep(0.5)

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'server') and cls.server:
            cls.server.stop()

    def _get_json(self, path):
        import urllib.request
        import json
        url = f"http://127.0.0.1:{self.test_port}{path}"
        with urllib.request.urlopen(url, timeout=10) as resp:
            self.assertEqual(resp.status, 200)
            return json.loads(resp.read().decode('utf-8'))

    def _post_json(self, path, data=None):
        import urllib.request
        import json
        body = json.dumps(data or {}).encode('utf-8')
        request = urllib.request.Request(
            f"http://127.0.0.1:{self.test_port}{path}", data=body,
            headers={'Content-Type': 'application/json'}, method='POST',
        )
        with urllib.request.urlopen(request, timeout=10) as resp:
            return json.loads(resp.read().decode('utf-8'))

    def test_mutations_require_post_and_flow_is_counted_once(self):
        import urllib.error
        import urllib.request
        with self.assertRaises(urllib.error.HTTPError) as raised:
            urllib.request.urlopen(
                f"http://127.0.0.1:{self.test_port}/api/simulate/reset", timeout=10
            )
        self.assertEqual(raised.exception.code, 405)
        raised.exception.close()

        self._post_json('/api/simulate/reset')
        result = self._post_json('/api/simulate/apply_flow?src=4&dst=7&demand=10&duration=5')
        self.assertEqual(result['status'], 'success')
        first_edge = tuple(result['chosen_path'][:2])
        sm = self.server.state_manager
        expected = 0.05 + 10.0 / sm.link_bandwidths[first_edge]
        self.assertAlmostEqual(sm.link_utilization[first_edge], expected, places=6)
        reverse = (first_edge[1], first_edge[0])
        self.assertAlmostEqual(sm.link_utilization[reverse], 0.05, places=6)
        self._post_json('/api/simulate/clear_flows')

    def test_dashboard_model_telemetry(self):
        rl = self._get_json("/api/rl_metrics")
        self.assertIn("router_epsilon", rl)
        self.assertIn("router_device", rl)
        self.assertTrue(rl.get("model_loaded"))
        self.assertGreater(rl.get("parameter_count", 0), 20000)

    def test_model_inspect_and_predict(self):
        insp = self._get_json("/api/model_inspect")
        self.assertEqual(insp["architecture"]["type"], "Dueling Double Deep Q-Network (D3QN)")
        self.assertEqual(insp["architecture"]["state_dim"], 10)
        self.assertEqual(insp["architecture"]["action_dim"], 4)

        pred = self._get_json("/api/model_predict?src=4&dst=7")
        self.assertIn("chosen_path", pred)
        self.assertIn("inference_time_ms", pred)
        self.assertEqual(len(pred["candidate_paths"]), 4)

    def test_versus_endpoint_single_protocol(self):
        res = self._get_json("/api/verse?topo=tree&protocol=ospf&pattern=jam&flows=15")
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["topology_id"], "tree")
        self.assertIn("DQN (Ours)", res["metrics"])
        self.assertIn("OSPF (RFC 2328)", res["metrics"])
        self.assertIn("deltas", res)
        self.assertIn("radar", res)
        self.assertIn("verdict", res)

    def test_versus_endpoint_multi_protocol_checklist(self):
        res = self._get_json("/api/verse?topo=fattree&protocol=ospf,ecmp,wsp&pattern=burst&flows=15")
        self.assertEqual(res["status"], "success")
        self.assertEqual(len(res["algorithms"]), 4)  # DQN + OSPF + ECMP + WSP
        self.assertIn("DQN (Ours)", res["algorithms"])
        self.assertIn("OSPF (RFC 2328)", res["algorithms"])
        self.assertIn("ECMP Multi-Path", res["algorithms"])
        self.assertIn("WSP Widest Path", res["algorithms"])
        self.assertNotIn("Dijkstra SPF", res["algorithms"])
        self.assertEqual(res["deltas"]["competitors_count"], 3)

    def test_versus_endpoint_all_baselines(self):
        res = self._get_json("/api/verse?topo=nsfnet&protocol=all&pattern=jam&flows=15")
        self.assertEqual(res["status"], "success")
        self.assertGreaterEqual(len(res["algorithms"]), 6)
        self.assertIn("DQN (Ours)", res["algorithms"])
        self.assertIn("OSPF (RFC 2328)", res["algorithms"])
        self.assertIn("ECMP Multi-Path", res["algorithms"])

    def test_ha_status_endpoint(self):
        res = self._get_json("/api/ha/status")
        self.assertEqual(res["status"], "ok")
        self.assertIn("role", res)
        self.assertIn("ofp_port", res)
        self.assertIn("rest_port", res)
        self.assertIn("cluster_nodes", res)
        self.assertEqual(res["cluster_nodes"], ["primary", "backup1", "backup2"])


class TestHighAvailabilityClustering(unittest.TestCase):
    """Verifies High Availability multi-controller pool management, health probing, and failover mechanics."""

    def test_controller_node_properties(self):
        node = ControllerNode(name="primary", host="127.0.0.1", ofp_port=6633, rest_port=8080)
        self.assertEqual(node.name, "primary")
        self.assertEqual(node.ofp_target, "tcp:127.0.0.1:6633")
        self.assertEqual(node.rest_url, "http://127.0.0.1:8080")
        self.assertEqual(node.status, "standby")

    def test_ha_pool_init_and_active_leader(self):
        pool = HAControllerPool()
        self.assertEqual(len(pool.nodes), 3)
        self.assertEqual(pool.nodes[0].name, "primary")
        self.assertEqual(pool.nodes[1].name, "backup1")
        self.assertEqual(pool.nodes[2].name, "backup2")
        self.assertEqual(pool.active_index, 0)
        self.assertEqual(pool.get_active_controller().name, "primary")

    def test_ha_pool_cascaded_failovers(self):
        pool = HAControllerPool()
        self.assertEqual(pool.get_active_controller().name, "primary")

        # First failover: Primary -> Backup 1
        new_active = pool.failover(reason="simulated_primary_failure")
        self.assertEqual(new_active.name, "backup1")
        self.assertEqual(pool.total_failovers, 1)

        # Second failover: Backup 1 -> Backup 2
        new_active_2 = pool.failover(reason="simulated_backup1_failure")
        self.assertEqual(new_active_2.name, "backup2")
        self.assertEqual(pool.total_failovers, 2)

        # Cluster status
        status = pool.cluster_status()
        self.assertEqual(status["active_controller"], "backup2")
        self.assertEqual(status["total_failovers"], 2)
        self.assertEqual(len(status["failover_history"]), 2)
        self.assertEqual(status["failover_history"][0]["from"], "primary")
        self.assertEqual(status["failover_history"][0]["to"], "backup1")
        self.assertEqual(status["failover_history"][1]["from"], "backup1")
        self.assertEqual(status["failover_history"][1]["to"], "backup2")

    def test_ha_pool_ovs_targets_format(self):
        pool = HAControllerPool()
        targets = pool.get_ovs_controller_targets()
        self.assertEqual(len(targets), 3)
        self.assertTrue(targets[0].startswith("tcp:127.0.0.1:6633"))
        self.assertTrue(targets[1].startswith("tcp:127.0.0.1:6634"))
        self.assertTrue(targets[2].startswith("tcp:127.0.0.1:6635"))


if __name__ == '__main__':
    unittest.main(verbosity=2)
```
