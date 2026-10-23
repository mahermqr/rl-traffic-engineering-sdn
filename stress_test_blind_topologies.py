#!/usr/bin/env python3
"""
Multi-Topology High-Intensity Blind Stress & Generalization Testing Suite (EC499).
Evaluates trained Deep Q-Network Traffic Engineering agent ZERO-SHOT ("Going Blind") across:
  1. Hierarchical Tree (Baseline Training Fabric - 7 Switches)
  2. Fat-Tree k=4 (Multi-Stage Data Center Clos - 20 Switches)
  3. Abilene Network (Continental US WAN Backbone - 12 Nodes)
  4. NSFNet Mesh (National Science Foundation Core - 14 Nodes)
  5. Spine-Leaf Fabric (Cloud Data Center Interconnect - 12 Switches, 64 Directed Links)

Executes:
  - Scenario 1: Severe Core / Backbone Jamming (85% - 98% saturation)
  - Scenario 2: High-Concurrency Flow Avalanche (500 simultaneous flows)
  - Scenario 3: Asymmetric Regional Hotspot Surges
  - Scenario 4: Dynamic Latency Spikes (Core delay degraded 5x-10x)
  - Scenario 5: Network Jitter & Packet Loss Mitigation (RFC 3393)

Generates:
  - logs/blind_topologies_stress_results.json
  - logs/plots/blind_topologies_stress_benchmark.png
  - logs/plots/blind_topologies_radar.png
"""

import sys
import os
import time
import json
import random
import math
import itertools

# Auto-detect and activate virtualenv if running with system python
def _bootstrap_environment():
    try:
        import numpy  # noqa: F401
        import torch  # noqa: F401
        import matplotlib  # noqa: F401
        return
    except ImportError:
        pass
    candidates = [
        os.path.expanduser('~/ec499_env/bin/python3'),
        os.path.expanduser('~/ec499_env/bin/python'),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), '.venv', 'bin', 'python3'),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.venv', 'bin', 'python3'),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'venv', 'bin', 'python3'),
        os.path.expanduser('~/.venv/bin/python3'),
    ]
    for cand in candidates:
        cand_prefix = os.path.dirname(os.path.dirname(os.path.abspath(cand)))
        if os.path.exists(cand) and os.access(cand, os.X_OK) and cand_prefix != sys.prefix:
            try:
                os.execv(cand, [cand] + sys.argv)
            except Exception:
                pass

    lib_candidates = [
        os.path.expanduser('~/ec499_env/lib'),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.venv', 'lib'),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), '.venv', 'lib'),
        os.path.expanduser('~/.venv/lib'),
    ]
    for lib_dir in lib_candidates:
        if os.path.isdir(lib_dir):
            for entry in os.listdir(lib_dir):
                sp = os.path.join(lib_dir, entry, 'site-packages')
                if os.path.isdir(sp) and sp not in sys.path:
                    sys.path.insert(0, sp)

_bootstrap_environment()

import numpy as np
import networkx as nx
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)
sys.path.append(os.path.join(BASE_DIR, 'agent'))
sys.path.append(os.path.join(BASE_DIR, 'controller'))
sys.path.append(os.path.join(BASE_DIR, 'topology'))

try:
    import config
except ImportError:
    config = None

from dqn_router import DQNRoutingAgent
from state_manager import StateManager
from policy_selector import select_dqn_path
from topology_library import get_topology
from traditional_routing import compute_path_metrics

DEFAULT_PLOTS_DIR = getattr(config, 'PLOTS_DIR', os.path.join(BASE_DIR, 'logs', 'plots'))
DEFAULT_LOGS_DIR = getattr(config, 'LOGS_DIR', os.path.join(BASE_DIR, 'logs'))
DEFAULT_MODEL_PATH = getattr(config, 'DEFAULT_MODEL_PATH', os.path.join(BASE_DIR, 'models', 'dqn_router.pth'))
DEFAULT_JSON_PATH = getattr(config, 'BLIND_STRESS_RESULTS_PATH', os.path.join(DEFAULT_LOGS_DIR, 'blind_topologies_stress_results.json'))

os.makedirs(DEFAULT_PLOTS_DIR, exist_ok=True)
os.makedirs(DEFAULT_LOGS_DIR, exist_ok=True)

def jains_fairness_index(loads):
    """Computes Jain's Fairness Index in [1/n, 1.0]."""
    arr = np.array(loads, dtype=np.float64)
    if len(arr) == 0 or np.sum(arr**2) == 0:
        return 1.0
    return float((np.sum(arr)**2) / (len(arr) * np.sum(arr**2)))

def run_blind_topology_stress_tests(model_path=None, json_path=None, plots_dir=None, topologies=None, burst_flows=500, seed=None):
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)

    plots_dir = plots_dir or os.environ.get("SDN_PLOTS_DIR", DEFAULT_PLOTS_DIR)
    os.makedirs(plots_dir, exist_ok=True)

    ckpt_path = model_path or os.environ.get("SDN_MODEL_PATH", DEFAULT_MODEL_PATH)
    out_json = json_path or os.environ.get("SDN_BLIND_STRESS_RESULTS", DEFAULT_JSON_PATH)

    print("=" * 85)
    print(" 🚀 STARTING MULTI-TOPOLOGY BLIND STRESS & GENERALIZATION BENCHMARK SUITE (EC499)")
    print(" Evaluating Double DQN Traffic Engineering Zero-Shot Across 5 Fabrics")
    print(f" Model Checkpoint: {ckpt_path}")
    print(f" Output JSON:      {out_json}")
    print(f" Plots Directory:  {plots_dir}")
    print("=" * 85)

    # 1. Load trained agent checkpoint
    router_agent = DQNRoutingAgent()
    if not router_agent.load(ckpt_path):
        print(f"[Error] Failed to load router weights from {ckpt_path}")
        return
    print(f"[Init] Loaded trained Double DQN Router checkpoint from {ckpt_path}")

    results_summary = {}

    all_topos = ['tree', 'fattree', 'abilene', 'nsfnet', 'spineleaf']
    if topologies:
        topo_order = [t for t in all_topos if t in topologies]
    else:
        topo_order = all_topos

    topo_labels = {
        'tree': 'Hierarchical Tree',
        'fattree': 'Fat-Tree Clos (k=4)',
        'abilene': 'Abilene US Backbone',
        'nsfnet': 'NSFNet Continental',
        'spineleaf': 'Spine-Leaf Fabric'
    }

    for topo_id in topo_order:
        topo_name = topo_labels[topo_id]
        print("\n" + "=" * 85)
        print(f" 🌐 STRESS TESTING FABRIC: {topo_name.upper()}")
        print("=" * 85)

        g, meta = get_topology(topo_id)
        n_nodes = g.number_of_nodes()
        n_edges = g.number_of_edges()
        core_nodes = meta.get('core_nodes', [1])
        edge_nodes = meta.get('edge_nodes', list(g.nodes()))

        print(f" • Topology Characteristics: {n_nodes} Switches, {n_edges} Directed Links")
        print(f" • Core Nodes: {core_nodes} | Edge Nodes: {len(edge_nodes)} switches")

        sm = StateManager()
        sm.set_topology(topo_id, g, meta)

        def evaluate_flow(src, dst):
            candidate_paths = sm.get_candidate_paths(src, dst, k=4)
            if not candidate_paths:
                raise RuntimeError(f"No route between {src} and {dst}")
            spf_path = candidate_paths[0]
            decision = select_dqn_path(
                router_agent, sm, src, dst, candidate_paths=candidate_paths,
                mode=getattr(config, 'POLICY_MODE', 'pure')
            )
            chosen_path = decision['path']

            m_dqn = compute_path_metrics(chosen_path, sm.link_utilization, sm.link_delays, sm.link_bandwidths)
            m_spf = compute_path_metrics(spf_path, sm.link_utilization, sm.link_delays, sm.link_bandwidths)

            rerouted = (chosen_path != spf_path)
            return m_dqn['bottleneck_util'], m_spf['bottleneck_util'], m_dqn['total_delay'], m_spf['total_delay'], rerouted, chosen_path, spf_path, m_dqn['jitter'], m_spf['jitter'], m_dqn['packet_loss'], m_spf['packet_loss']

        # ---------------------------------------------------------------------
        # TEST 1: Severe Core / Backbone Jamming (85% - 98% Saturation)
        # ---------------------------------------------------------------------
        print(f"\n[Test 1/5] Core/Backbone Jamming (Core nodes: {core_nodes})")
        sm.inject_core_congestion(utilization=0.90, core_nodes=core_nodes, asymmetric_ratio=0.5)

        n_samples = 150
        t1_dqn_u, t1_spf_u, t1_dqn_lat, t1_spf_lat, t1_reroutes = [], [], [], [], 0

        for _ in range(n_samples):
            src = random.choice(edge_nodes)
            dst = random.choice([n for n in edge_nodes if n != src])
            du, su, dl, sl, rerouted, _, _, _, _, _, _ = evaluate_flow(src, dst)
            t1_dqn_u.append(du * 100.0)
            t1_spf_u.append(su * 100.0)
            t1_dqn_lat.append(dl)
            t1_spf_lat.append(sl)
            if rerouted:
                t1_reroutes += 1

        t1_offload_rate = (t1_reroutes / n_samples) * 100.0
        t1_relief = float(np.mean(t1_spf_u) - np.mean(t1_dqn_u))
        print(f" • Evaluated Flows:             {n_samples}")
        print(f" • Dijkstra SPF Bottleneck:     {np.mean(t1_spf_u):.2f}%")
        print(f" • Double DQN Bottleneck:       {np.mean(t1_dqn_u):.2f}%")
        sign_t1 = "+" if t1_relief >= 0 else ""
        print(f" • Congestion Reduction:        {sign_t1}{t1_relief:.2f}% {'relief' if t1_relief >= 0 else 'variance'}")
        print(f" • Autonomous Offload Rate:     {t1_offload_rate:.1f}% to alternate paths")
        print(f" • Mean Latency:                DQN: {np.mean(t1_dqn_lat):.2f} ms vs SPF: {np.mean(t1_spf_lat):.2f} ms")

        # ---------------------------------------------------------------------
        # TEST 2: High-Concurrency Flow Avalanche (500 Simultaneous Flows)
        # ---------------------------------------------------------------------
        print(f"\n[Test 2/5] High-Concurrency Flow Avalanche ({burst_flows} Concurrent Requests)")
        link_loads_dqn = {e: 0.05 for e in sm.graph.edges()}
        link_loads_spf = {e: 0.05 for e in sm.graph.edges()}

        n_burst = burst_flows
        k_paths = getattr(config, 'ACTION_SIZE', 4)
        t0 = time.time()
        for _ in range(n_burst):
            src = random.choice(edge_nodes)
            dst = random.choice([n for n in edge_nodes if n != src])
            cands = sm.get_candidate_paths(src, dst, k=k_paths)
            if not cands:
                continue
            for edge, count in link_loads_dqn.items():
                sm.link_utilization[edge] = max(0.0, count * 0.02)
            decision = select_dqn_path(
                router_agent, sm, src, dst, candidate_paths=cands,
                mode=getattr(config, 'POLICY_MODE', 'pure')
            )
            p_dqn = decision['path']
            p_spf = cands[0]
            for i in range(len(p_dqn)-1):
                e = (p_dqn[i], p_dqn[i+1])
                if e in link_loads_dqn:
                    link_loads_dqn[e] += 1.0
            for i in range(len(p_spf)-1):
                e = (p_spf[i], p_spf[i+1])
                if e in link_loads_spf:
                    link_loads_spf[e] += 1.0

        burst_duration = time.time() - t0
        decisions_sec = n_burst / max(0.001, burst_duration)
        jain_dqn = jains_fairness_index(list(link_loads_dqn.values()))
        jain_spf = jains_fairness_index(list(link_loads_spf.values()))

        print(f" • Execution Time:              {burst_duration*1000:.1f} ms for {n_burst} decisions")
        print(f" • Decision Throughput:         {decisions_sec:.1f} decisions/sec")
        print(f" • Jain's Fairness Index:       DQN: {jain_dqn:.4f} vs SPF: {jain_spf:.4f}")

        # ---------------------------------------------------------------------
        # TEST 3: Asymmetric Regional Hotspot Surges
        # ---------------------------------------------------------------------
        print(f"\n[Test 3/5] Asymmetric Regional Hotspot Surge (Sub-Cluster Congestion)")
        hotspot_nodes = edge_nodes[:max(2, len(edge_nodes)//3)]
        for u, v in sm.graph.edges():
            sm.link_utilization[(u, v)] = 0.15

        # Saturate primary default uplinks connecting the hotspot cluster
        for h in hotspot_nodes:
            for other in edge_nodes:
                if other not in hotspot_nodes:
                    try:
                        p = nx.shortest_path(sm.graph, h, other)
                        if len(p) >= 2:
                            sm.link_utilization[(p[0], p[1])] = 0.88
                            if (p[1], p[0]) in sm.link_utilization:
                                sm.link_utilization[(p[1], p[0])] = 0.88
                    except Exception:
                        pass
                    break

        t3_dqn_u, t3_spf_u, t3_diversions = [], [], 0
        for _ in range(100):
            src = random.choice(hotspot_nodes)
            dst = random.choice([n for n in edge_nodes if n not in hotspot_nodes])
            du, su, _, _, rerouted, _, _, _, _, _, _ = evaluate_flow(src, dst)
            t3_dqn_u.append(du * 100.0)
            t3_spf_u.append(su * 100.0)
            if rerouted:
                t3_diversions += 1

        t3_relief = float(np.mean(t3_spf_u) - np.mean(t3_dqn_u))
        sign_t3 = "+" if t3_relief >= 0 else ""
        print(f" • Hotspot Ingress Relief:      {sign_t3}{t3_relief:.2f}% load reduction")
        print(f" • Local Link Bypass Rate:      {t3_diversions}% rerouted")

        # ---------------------------------------------------------------------
        # TEST 4: Dynamic Delay Degradation
        # ---------------------------------------------------------------------
        print(f"\n[Test 4/5] Dynamic Delay Degradation (Core Link Delay 10x Inflated)")
        jammed_cores = set(core_nodes[:max(1, len(core_nodes)//2)]) if len(core_nodes) > 1 else set(core_nodes)
        for u, v in sm.graph.edges():
            if u in jammed_cores or v in jammed_cores:
                sm.link_delays[(u, v)] = 20.0
            else:
                sm.link_delays[(u, v)] = sm.base_link_delays.get((u, v), 2.0)

        t4_dqn_lats, t4_spf_lats = [], []
        for _ in range(100):
            src = random.choice(edge_nodes)
            dst = random.choice([n for n in edge_nodes if n != src])
            _, _, dl, sl, _, _, _, _, _, _, _ = evaluate_flow(src, dst)
            t4_dqn_lats.append(dl)
            t4_spf_lats.append(sl)

        t4_savings = float(np.mean(t4_spf_lats) - np.mean(t4_dqn_lats))
        print(f" • Double DQN Mean Latency:     {np.mean(t4_dqn_lats):.2f} ms")
        print(f" • Dijkstra SPF Mean Latency:   {np.mean(t4_spf_lats):.2f} ms")
        if t4_savings >= 0:
            print(f" • Latency Savings:             +{t4_savings:.2f} ms (Faster via low-delay bypass)")
        else:
            print(f" • Latency Difference:          {t4_savings:.2f} ms (Detour latency trade-off)")

        # ---------------------------------------------------------------------
        # TEST 5: Jitter & Packet Loss Mitigation (RFC 3393)
        # ---------------------------------------------------------------------
        print(f"\n[Test 5/5] Jitter & Packet Loss Suppression (RFC 3393 / RFC 3550)")
        t5_dqn_j, t5_spf_j = [], []
        t5_dqn_loss, t5_spf_loss = [], []
        for _ in range(100):
            src = random.choice(edge_nodes)
            dst = random.choice([n for n in edge_nodes if n != src])
            _, _, _, _, _, _, _, dj, sj, dloss, sloss = evaluate_flow(src, dst)
            t5_dqn_j.append(dj)
            t5_spf_j.append(sj)
            t5_dqn_loss.append(dloss)
            t5_spf_loss.append(sloss)

        mean_dj = float(np.mean(t5_dqn_j))
        mean_sj = float(np.mean(t5_spf_j))
        mean_dloss = float(np.mean(t5_dqn_loss))
        mean_sloss = float(np.mean(t5_spf_loss))
        jitter_suppression_pct = max(0.0, ((mean_sj - mean_dj) / max(0.01, mean_sj)) * 100.0)

        print(f" • DQN Jitter:                  {mean_dj:.2f} ms (vs SPF: {mean_sj:.2f} ms)")
        print(f" • Jitter Suppression:          {jitter_suppression_pct:.1f}%")
        print(f" • DQN Packet Loss:             {mean_dloss:.2f}% (vs SPF: {mean_sloss:.2f}%)")

        results_summary[topo_id] = {
            "name": topo_name,
            "switches": n_nodes,
            "edges": n_edges,
            "scenario_1_core_jamming": {
                "dijkstra_spf_bottleneck_pct": round(float(np.mean(t1_spf_u)), 2),
                "double_dqn_bottleneck_pct": round(float(np.mean(t1_dqn_u)), 2),
                "congestion_reduction_pct": round(t1_relief, 2),
                "autonomous_offload_rate_pct": round(t1_offload_rate, 1),
                "dqn_latency_ms": round(float(np.mean(t1_dqn_lat)), 2),
                "spf_latency_ms": round(float(np.mean(t1_spf_lat)), 2)
            },
            "scenario_2_concurrency_burst": {
                "decisions_per_sec": round(decisions_sec, 1),
                "jains_fairness_dqn": round(float(jain_dqn), 4),
                "jains_fairness_spf": round(float(jain_spf), 4)
            },
            "scenario_3_hotspot_surge": {
                "bottleneck_reduction_pct": round(t3_relief, 2),
                "diversion_rate_pct": round(float(t3_diversions), 1)
            },
            "scenario_4_latency_degradation": {
                "dqn_latency_ms": round(float(np.mean(t4_dqn_lats)), 2),
                "spf_latency_ms": round(float(np.mean(t4_spf_lats)), 2),
                "latency_savings_ms": round(t4_savings, 2)
            },
            "scenario_5_jitter_and_loss": {
                "dqn_jitter_ms": round(mean_dj, 2),
                "spf_jitter_ms": round(mean_sj, 2),
                "jitter_suppression_pct": round(jitter_suppression_pct, 1),
                "dqn_loss_pct": round(mean_dloss, 2),
                "spf_loss_pct": round(mean_sloss, 2)
            }
        }


    # Save summary JSON
    with open(out_json, 'w') as f:
        json.dump(results_summary, f, indent=2)
    print(f" • Saved Structured Results JSON to: {out_json}")

    # Generate 4-Panel Dashboard & Radar Chart
    bench_plot = plot_blind_stress_dashboard(results_summary, plots_dir, topo_order, topo_labels)
    radar_plot = plot_blind_radar(results_summary, plots_dir, topo_order, topo_labels)

    print("=" * 85)
    print(" ALL 5 TOPOLOGY BLIND STRESS BENCHMARKS COMPLETED SUCCESSFULLY!")
    print("=" * 85)


def plot_blind_stress_dashboard(results_summary, plots_dir, topo_order=None, topo_labels=None):
    """Generates 4-panel multi-topology stress test benchmark dashboard with zero label collision."""
    if topo_order is None:
        topo_order = ['tree', 'fattree', 'abilene', 'nsfnet', 'spineleaf']
    if topo_labels is None:
        topo_labels = {
            'tree': 'Hierarchical Tree',
            'fattree': 'Fat-Tree Clos (k=4)',
            'abilene': 'Abilene US Backbone',
            'nsfnet': 'NSFNet Continental',
            'spineleaf': 'Spine-Leaf Fabric'
        }

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 11), dpi=300)
    plt.subplots_adjust(top=0.91, bottom=0.08, left=0.08, right=0.96, hspace=0.32, wspace=0.22)
    short_names = {'tree': 'Tree', 'fattree': 'Fat-Tree', 'abilene': 'Abilene',
                   'nsfnet': 'NSFNet', 'spineleaf': 'Spine-Leaf'}
    topo_order = [topo for topo in topo_order if topo in results_summary]
    short_labels = [short_names.get(topo, topo) for topo in topo_order]
    x = np.arange(len(short_labels))
    width = 0.35

    # 1. Core Jamming
    spf_b = [results_summary[t]["scenario_1_core_jamming"]["dijkstra_spf_bottleneck_pct"] for t in topo_order]
    dqn_b = [results_summary[t]["scenario_1_core_jamming"]["double_dqn_bottleneck_pct"] for t in topo_order]
    b1 = ax1.bar(x - width/2, spf_b, width, label='Dijkstra SPF', color='#dc2626', alpha=0.88)
    b2 = ax1.bar(x + width/2, dqn_b, width, label='Double DQN (Ours)', color='#059669', alpha=0.88)
    for i in range(len(short_labels)):
        diff = abs(spf_b[i] - dqn_b[i])
        spf_y = spf_b[i] + (3.6 if diff < 5.0 else 1.2)
        dqn_y = dqn_b[i] + 1.2
        ax1.text(x[i] - width/2, spf_y, f"{spf_b[i]:.1f}%", ha='center', va='bottom', fontsize=8, fontweight='bold', color='#dc2626')
        ax1.text(x[i] + width/2, dqn_y, f"{dqn_b[i]:.1f}%", ha='center', va='bottom', fontsize=8, fontweight='bold', color='#059669')
    ax1.set_title('Scenario 1: Core Jamming Bottleneck Load (%) [Lower is Better]', fontsize=11, fontweight='bold', pad=8)
    ax1.set_ylabel('Bottleneck Utilization (%)', fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(short_labels, rotation=0, ha='center', fontweight='bold', fontsize=9.5)
    ax1.set_ylim(0, max(spf_b) * 1.22)
    ax1.legend(loc='upper left', fontsize=8.5)
    ax1.grid(True, linestyle='--', alpha=0.45)

    # 2. Decision Throughput
    dec_speeds = [results_summary[t]["scenario_2_concurrency_burst"]["decisions_per_sec"] for t in topo_order]
    bars2 = ax2.bar(x, dec_speeds, color='#0284c7', alpha=0.88, width=0.48)
    for b in bars2:
        h = b.get_height()
        ax2.text(b.get_x() + b.get_width()/2., h + max(dec_speeds)*0.02, f"{h:.0f}/s", ha='center', va='bottom', fontsize=8.5, fontweight='bold', color='#0284c7')
    ax2.set_title('Scenario 2: Decision Throughput (decisions/sec) [Higher is Better]', fontsize=11, fontweight='bold', pad=8)
    ax2.set_ylabel('Decisions / Second', fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(short_labels, rotation=0, ha='center', fontweight='bold', fontsize=9.5)
    ax2.set_ylim(0, max(dec_speeds) * 1.18)
    ax2.grid(True, linestyle='--', alpha=0.45)

    # 3. Hotspot Relief & Bypass Rate
    hotspot_relief = [results_summary[t]["scenario_3_hotspot_surge"]["bottleneck_reduction_pct"] for t in topo_order]
    hotspot_bypass = [results_summary[t]["scenario_3_hotspot_surge"]["diversion_rate_pct"] for t in topo_order]
    bars3 = ax3.bar(x, hotspot_relief, color='#7c3aed', alpha=0.88, width=0.48)
    ax3.set_title('Scenario 3: Asymmetric Hotspot Relief & Bypass [Higher is Better]', fontsize=11, fontweight='bold', pad=8)
    ax3.set_ylabel('Load Reduction (%)', fontweight='bold')
    ax3.set_ylim(0, max(85, max(hotspot_relief) * 1.30 if max(hotspot_relief) > 0 else 100))
    for i, b in enumerate(bars3):
        h = b.get_height()
        bp = hotspot_bypass[i]
        ax3.text(b.get_x() + b.get_width()/2., h + 1.5, f"+{h:.1f}%\n({bp:.0f}% bypass)", ha='center', va='bottom', fontsize=8, fontweight='bold', color='#6d28d9')
    ax3.set_xticks(x)
    ax3.set_xticklabels(short_labels, rotation=0, ha='center', fontweight='bold', fontsize=9.5)
    ax3.grid(True, linestyle='--', alpha=0.45)

    # 4. Latency
    spf_lats = [results_summary[t]["scenario_4_latency_degradation"]["spf_latency_ms"] for t in topo_order]
    dqn_lats = [results_summary[t]["scenario_4_latency_degradation"]["dqn_latency_ms"] for t in topo_order]
    ax4.bar(x - width/2, spf_lats, width, label='Dijkstra SPF', color='#dc2626', alpha=0.88)
    ax4.bar(x + width/2, dqn_lats, width, label='Double DQN (Ours)', color='#059669', alpha=0.88)
    for i in range(len(short_labels)):
        diff = abs(spf_lats[i] - dqn_lats[i])
        spf_y = spf_lats[i] + (2.2 if diff < 2.5 else 0.6)
        dqn_y = dqn_lats[i] + 0.6
        ax4.text(x[i] - width/2, spf_y, f"{spf_lats[i]:.1f} ms", ha='center', va='bottom', fontsize=8, fontweight='bold', color='#dc2626')
        ax4.text(x[i] + width/2, dqn_y, f"{dqn_lats[i]:.1f} ms", ha='center', va='bottom', fontsize=8, fontweight='bold', color='#059669')
    ax4.set_title('Scenario 4: Latency under Core Link Delay Degradation [Lower is Better]', fontsize=11, fontweight='bold', pad=8)
    ax4.set_ylabel('End-to-End Latency (ms)', fontweight='bold')
    ax4.set_xticks(x)
    ax4.set_xticklabels(short_labels, rotation=0, ha='center', fontweight='bold', fontsize=9.5)
    ax4.set_ylim(0, max(spf_lats) * 1.22)
    ax4.legend(loc='upper left', fontsize=8.5)
    ax4.grid(True, linestyle='--', alpha=0.45)

    plt.suptitle('Multi-Topology Stress Testing: DQN Traffic Engineering Benchmark\n(Evaluated on five built-in topology fixtures)', fontsize=13, fontweight='bold', y=0.975)
    bench_plot = os.path.join(plots_dir, 'blind_topologies_stress_benchmark.png')
    plt.savefig(bench_plot, dpi=300, bbox_inches='tight')
    plt.close()
    print(f" • Saved Benchmark Plot to: {bench_plot}")
    return bench_plot


def plot_blind_radar(results_summary, plots_dir, topo_order=None, topo_labels=None):
    """Generates the publication-grade multi-topology radar chart with non-overlapping labels."""
    if topo_order is None:
        topo_order = ['tree', 'fattree', 'abilene', 'nsfnet', 'spineleaf']
    if topo_labels is None:
        topo_labels = {
            'tree': 'Hierarchical Tree',
            'fattree': 'Fat-Tree Clos (k=4)',
            'abilene': 'Abilene US Backbone',
            'nsfnet': 'NSFNet Continental',
            'spineleaf': 'Spine-Leaf Fabric'
        }

    categories = ['Congestion Relief (%)', 'Offload Rate (%)', 'Fairness (x100)', 'Latency Avoidance (%)', 'Jitter Suppression (%)']
    N_cat = len(categories)
    angles = [n / float(N_cat) * 2 * math.pi for n in range(N_cat)]
    angles += angles[:1]

    fig_r, ax_r = plt.subplots(figsize=(9.0, 9.5), subplot_kw=dict(polar=True), dpi=300)
    plt.subplots_adjust(top=0.88, bottom=0.15)
    colors_radar = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']

    for idx, t in enumerate(topo_order):
        if t not in results_summary:
            continue
        s1 = results_summary[t].get("scenario_1_core_jamming", {})
        s2 = results_summary[t].get("scenario_2_concurrency_burst", {})
        s4 = results_summary[t].get("scenario_4_latency_degradation", {})
        s5 = results_summary[t].get("scenario_5_jitter_and_loss", {})

        spf_lat = max(1.0, s4.get('spf_latency_ms', 1.0))
        dqn_lat = s4.get('dqn_latency_ms', 1.0)
        lat_pct = max(0.0, ((spf_lat - dqn_lat) / spf_lat) * 100.0)
        values = [
            min(100.0, max(0.0, s1.get('congestion_reduction_pct', 0.0) * 2.0)),
            min(100.0, s1.get('autonomous_offload_rate_pct', 0.0)),
            min(100.0, s2.get('jains_fairness_dqn', 0.0) * 100.0),
            min(100.0, lat_pct),
            min(100.0, s5.get('jitter_suppression_pct', 0.0))
        ]
        values += values[:1]
        ax_r.plot(angles, values, lw=2.2, label=topo_labels.get(t, t), color=colors_radar[idx % len(colors_radar)])
        ax_r.fill(angles, values, color=colors_radar[idx % len(colors_radar)], alpha=0.10)

    ax_r.set_theta_offset(math.pi / 2)
    ax_r.set_theta_direction(-1)
    ax_r.set_rlabel_position(22)
    ax_r.tick_params(axis='x', pad=16)
    ax_r.set_xticks(angles[:-1])
    ax_r.set_xticklabels(categories, fontweight='bold', fontsize=10)
    for label, angle in zip(ax_r.get_xticklabels(), angles[:-1]):
        deg = math.degrees(angle) % 360
        if abs(deg - 0) < 5 or abs(deg - 360) < 5:
            label.set_horizontalalignment('center')
            label.set_verticalalignment('bottom')
        elif 0 < deg < 90:
            label.set_horizontalalignment('left')
            label.set_verticalalignment('center')
        elif 90 <= deg < 180:
            label.set_horizontalalignment('left')
            label.set_verticalalignment('top')
        elif 180 <= deg < 270:
            label.set_horizontalalignment('right')
            label.set_verticalalignment('top')
        else:
            label.set_horizontalalignment('right')
            label.set_verticalalignment('center')
    ax_r.set_ylim(0, 110)
    ax_r.set_yticks([20, 40, 60, 80, 100])
    ax_r.set_yticklabels(['20%', '40%', '60%', '80%', '100%'], fontsize=8, color='#64748b')
    ax_r.grid(True, linestyle='--', alpha=0.5)
    ax_r.set_title('Multi-Topology Resilience Radar\n(Evaluated across five built-in topology fixtures)', size=12, fontweight='bold', pad=26)
    ax_r.legend(loc='lower center', bbox_to_anchor=(0.50, -0.15), ncol=3, fontsize=9.5, frameon=True, facecolor='#ffffff', edgecolor='#cbd5e1')
    radar_plot = os.path.join(plots_dir, 'blind_topologies_radar.png')
    plt.savefig(radar_plot, dpi=300, bbox_inches='tight')
    plt.close()
    print(f" • Saved Radar Plot to: {radar_plot}")
    return radar_plot


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="Multi-Topology Blind Stress & Generalization Benchmark (EC499)")
    parser.add_argument('--model-path', default=None, help="Path to pre-trained DQN checkpoint (.pth)")
    parser.add_argument('--output-json', default=None, help="Path to output JSON results")
    parser.add_argument('--plots-dir', default=None, help="Directory to save generated comparison plots")
    parser.add_argument('--topologies', nargs='+', default=None, help="Specific topologies to test")
    parser.add_argument('--burst-flows', type=int, default=500, help="Number of concurrent burst flows in Test 2 (default: 500)")
    parser.add_argument('--seed', type=int, default=None, help="Random seed for reproducibility")
    parser.add_argument('--replot-only', action='store_true', help="Regenerate radar plot and stress dashboard from existing JSON results without re-running tests")
    args = parser.parse_args()

    plots_dir = args.plots_dir or os.path.join(BASE_DIR, 'logs', 'plots')
    os.makedirs(plots_dir, exist_ok=True)
    json_path = args.output_json or os.path.join(BASE_DIR, 'logs', 'blind_topologies_stress_results.json')

    if args.replot_only:
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            plot_blind_stress_dashboard(data, plots_dir)
            plot_blind_radar(data, plots_dir)
            print("Done replotting stress dashboard and radar chart.")
        else:
            print(f"Error: {json_path} not found for replotting.")
    else:
        run_blind_topology_stress_tests(
            model_path=args.model_path,
            json_path=json_path,
            plots_dir=plots_dir,
            topologies=args.topologies,
            burst_flows=args.burst_flows,
            seed=args.seed
        )
