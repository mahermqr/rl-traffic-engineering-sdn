#!/usr/bin/env python3
"""
Comprehensive Routing Algorithms Tournament Benchmark (EC499).
Head-to-head evaluation of Deep Q-Network (DQN) Traffic Engineering against:
 1. OSPF (Open Shortest Path First - RFC 2328 Reference Bandwidth Metric)
 2. Dijkstra Shortest Path First (SPF - Hop Count Metric)
 3. Equal-Cost Multi-Path (ECMP)
 4. Widest Shortest Path (WSP / CSPF - Residual Bandwidth Priority)
 5. Greedy Least Loaded Routing (LLR - Minimum Peak & Average Utilization)

Evaluates all 5 Core Metrics specified in EC499 Proposal:
 - Metric 1: Total Network Throughput & Bottleneck Link Utilization (%)
 - Metric 2: Network Latency (ms)
 - Metric 3: Network Jitter (ms Delay Variation RFC 3393)
 - Metric 4: Packet Loss Rate (%)
 - Metric 5: OpenFlow Control Overhead (Decision Latency ms & Decisions/sec)
 - Plus: Jain's Fairness Index across links
"""

import os
import sys
import json
import time
import random

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
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Add directories to path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)
sys.path.append(os.path.join(BASE_DIR, 'agent'))
sys.path.append(os.path.join(BASE_DIR, 'controller'))
sys.path.append(os.path.join(BASE_DIR, 'topology'))

try:
    import config
except ImportError:
    config = None

from state_manager import StateManager
from dqn_router import DQNRoutingAgent
from policy_selector import select_dqn_path
from topology_library import get_topology
from traditional_routing import (
    ospf_routing, dijkstra_spf, ecmp_routing, widest_shortest_path, least_loaded_routing, compute_path_metrics
)

DEFAULT_PLOTS_DIR = getattr(config, 'PLOTS_DIR', os.path.join(BASE_DIR, 'logs', 'plots'))
DEFAULT_MODEL_PATH = getattr(config, 'DEFAULT_MODEL_PATH', os.path.join(BASE_DIR, 'models', 'dqn_router.pth'))
DEFAULT_JSON_PATH = getattr(config, 'TOURNAMENT_RESULTS_PATH', os.path.join(BASE_DIR, 'logs', 'routing_tournament_results.json'))

os.makedirs(DEFAULT_PLOTS_DIR, exist_ok=True)


def generate_flow_specs(edge_nodes, topology_size, seed=None, count=150):
    """Return a deterministic workload whose samples change with ``seed``."""
    edge_nodes = list(edge_nodes)
    if len(edge_nodes) < 2:
        raise ValueError("At least two edge nodes are required to generate flows")
    flow_rng = random.Random((42 if seed is None else int(seed)) + int(topology_size))
    flow_specs = []
    for _ in range(int(count)):
        src = flow_rng.choice(edge_nodes)
        dst = flow_rng.choice([node for node in edge_nodes if node != src])
        mbps = flow_rng.uniform(3.0, 7.0)
        duration = flow_rng.uniform(15.0, 30.0)
        flow_specs.append((src, dst, mbps, duration))
    return flow_specs


def run_routing_tournament(model_path=None, json_path=None, plots_dir=None, topologies=None,
                           seed=None, policy_mode=None, generate_plots=True):
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)

    plots_dir = plots_dir or os.environ.get("SDN_PLOTS_DIR", DEFAULT_PLOTS_DIR)
    os.makedirs(plots_dir, exist_ok=True)

    ckpt_path = model_path or os.environ.get("SDN_MODEL_PATH", DEFAULT_MODEL_PATH)
    out_json = json_path or os.environ.get("SDN_TOURNAMENT_RESULTS", DEFAULT_JSON_PATH)

    print("=" * 90)
    print(" 🏆 EC499 BENCHMARK TOURNAMENT: DQN ADAPTIVE ROUTING VS OSPF & GREEDY BASELINES")
    print(f" Model Checkpoint: {ckpt_path}")
    print(f" Results Output:   {out_json}")
    print(f" Plots Directory:  {plots_dir}")
    print("=" * 90)

    # 1. Initialize RL Agent
    router_agent = DQNRoutingAgent()
    if os.path.exists(ckpt_path):
        if router_agent.load(ckpt_path):
            print(f"[Init] Loaded pre-trained DQN checkpoint from {ckpt_path}")
        else:
            print(f"[Warning] Incompatible checkpoint at {ckpt_path}; using fresh policy.")
    else:
        print(f"[Init] Checkpoint not found at {ckpt_path}; agent initialized with fresh policy.")

    topologies_to_test = [
        ('tree', "Hierarchical Tree (7 Nodes)"),
        ('fattree', "Fat-Tree Clos Fabric (20 Nodes)"),
        ('abilene', "Abilene US Backbone (12 Nodes)"),
        ('nsfnet', "NSFNET Continental Mesh (14 Nodes)"),
        ('spineleaf', "Spine-Leaf Fabric (12 Nodes)")
    ]
    if topologies:
        requested = set(topologies)
        unknown = requested - {key for key, _ in topologies_to_test}
        if unknown:
            raise ValueError(f"Unknown topologies: {', '.join(sorted(unknown))}")
        topologies_to_test = [item for item in topologies_to_test if item[0] in requested]

    algorithms = ['OSPF (RFC 2328)', 'Dijkstra SPF', 'ECMP', 'WSP (Widest Path)', 'LLR (Least Loaded)', 'DQN (Ours)']

    selected_policy_mode = str(
        policy_mode or getattr(config, 'POLICY_MODE', 'pure')
    ).strip().lower()
    if selected_policy_mode not in {'pure', 'safety'}:
        raise ValueError(f"Unsupported DQN policy mode: {selected_policy_mode}")

    benchmark_data = {
        'metadata': {
            'seed': seed,
            'policy_mode': selected_policy_mode,
            'flows_per_topology': 150,
            'candidate_paths': 4,
            'model_path': os.path.abspath(ckpt_path),
        },
        'bottleneck_util': {algo: [] for algo in algorithms},
        'latency_ms': {algo: [] for algo in algorithms},
        'jitter_ms': {algo: [] for algo in algorithms},
        'packet_loss_pct': {algo: [] for algo in algorithms},
        'jains_fairness': {algo: [] for algo in algorithms},
        'offload_rate_pct': {algo: [] for algo in algorithms},
        'decision_time_ms': {algo: [] for algo in algorithms},
        'raw_samples': {
            'latency_ms': {algo: [] for algo in algorithms},
            'jitter_ms': {algo: [] for algo in algorithms},
        },
        'topologies': [name for _, name in topologies_to_test]
    }

    decision_timings = {algo: [] for algo in algorithms}

    for topo_key, topo_name in topologies_to_test:
        print(f"\n" + "-" * 90)
        print(f" 🌐 Fabric: {topo_name}")
        print("-" * 90)

        g, meta = get_topology(topo_key)
        edge_nodes = meta.get('edge_nodes', list(g.nodes()))
        core_nodes = meta.get('core_nodes', [list(g.nodes())[0]])

        flow_samples = 150
        algo_utils = {algo: [] for algo in algorithms}
        algo_lats = {algo: [] for algo in algorithms}
        algo_jits = {algo: [] for algo in algorithms}
        algo_losses = {algo: [] for algo in algorithms}
        algo_offloaded = {algo: 0 for algo in algorithms}

        # Generate deterministic synthetic flow sequence (identical across all algorithms)
        flow_specs = generate_flow_specs(edge_nodes, len(g), seed=seed, count=flow_samples)

        # Closed-Loop Dynamic Evaluation: each algorithm manages its own network state
        topology_decision_timings = {algo: [] for algo in algorithms}
        for algo in algorithms:
            sm_algo = StateManager()
            sm_algo.set_topology(topo_key, g, meta)

            # Apply topology-agnostic core saturation (85-95%)
            sm_algo.inject_core_congestion(utilization=0.90, core_nodes=core_nodes)

            # Route each flow dynamically
            for flow_idx, (src, dst, mbps, duration) in enumerate(flow_specs):
                cand_paths = sm_algo.get_candidate_paths(src, dst, k=4)
                if not cand_paths:
                    continue
                p_ospf_ref = cand_paths[0]

                t0 = time.perf_counter()
                if algo == 'OSPF (RFC 2328)':
                    p = ospf_routing(sm_algo.graph, src, dst, link_bandwidths=sm_algo.link_bandwidths)
                elif algo == 'Dijkstra SPF':
                    p = dijkstra_spf(sm_algo.graph, src, dst)
                elif algo == 'ECMP':
                    p = ecmp_routing(sm_algo.graph, src, dst, flow_hash=flow_idx)
                elif algo == 'WSP (Widest Path)':
                    p = widest_shortest_path(sm_algo.graph, src, dst, sm_algo.link_utilization, sm_algo.link_delays, candidate_paths=cand_paths)
                elif algo == 'LLR (Least Loaded)':
                    p = least_loaded_routing(sm_algo.graph, src, dst, sm_algo.link_utilization, candidate_paths=cand_paths)
                elif algo == 'DQN (Ours)':
                    decision = select_dqn_path(
                        router_agent, sm_algo, src, dst, candidate_paths=cand_paths,
                        demand_mbps=mbps, mode=selected_policy_mode
                    )
                    if decision['status'] != 'success':
                        continue
                    p = decision['path']
                else:
                    p = cand_paths[0]
                t_dec = (time.perf_counter() - t0) * 1000.0
                decision_timings[algo].append(t_dec)
                topology_decision_timings[algo].append(t_dec)

                # Compute performance metrics under active placement
                m = compute_path_metrics(p, sm_algo.link_utilization, sm_algo.link_delays, sm_algo.link_bandwidths)
                algo_utils[algo].append(m['bottleneck_util'])
                algo_lats[algo].append(m['total_delay'])
                algo_jits[algo].append(m['jitter'])
                algo_losses[algo].append(m['packet_loss'])

                # Allocate dynamic flow onto selected path links (closed-loop load accumulation)
                sm_algo.allocate_dynamic_flow(flow_id=f"{algo}_{flow_idx}", path=p, mbps=mbps, duration_sec=duration)

                if p != p_ospf_ref:
                    algo_offloaded[algo] += 1

                # Advance simulated time & expire past flows
                sm_algo.step_dynamic_flows(current_time=time.time() + (flow_idx * 0.4))

        for algo in algorithms:
            b_util = float(np.mean(algo_utils[algo]) * 100.0)
            lat = float(np.mean(algo_lats[algo]))
            jit = float(np.mean(algo_jits[algo]))
            loss = float(np.mean(algo_losses[algo]))
            off = float((algo_offloaded[algo] / flow_samples) * 100.0)

            # Jain's fairness across path bottlenecks
            u_arr = np.array(algo_utils[algo])
            jains = float((np.sum(u_arr) ** 2) / max(1e-6, len(u_arr) * np.sum(u_arr ** 2)))

            benchmark_data['bottleneck_util'][algo].append(round(b_util, 2))
            benchmark_data['latency_ms'][algo].append(round(lat, 2))
            benchmark_data['jitter_ms'][algo].append(round(jit, 3))
            benchmark_data['packet_loss_pct'][algo].append(round(loss, 3))
            benchmark_data['jains_fairness'][algo].append(round(jains, 4))
            benchmark_data['offload_rate_pct'][algo].append(round(off, 1))
            benchmark_data['decision_time_ms'][algo].append(
                round(float(np.mean(topology_decision_timings[algo])), 3)
            )
            benchmark_data['raw_samples']['latency_ms'][algo].extend(round(float(x), 6) for x in algo_lats[algo])
            benchmark_data['raw_samples']['jitter_ms'][algo].extend(round(float(x), 6) for x in algo_jits[algo])

            print(f"  • {algo:<18}: Bottleneck: {b_util:5.1f}% | Latency: {lat:5.2f}ms | Jitter: {jit:5.2f}ms | Loss: {loss:4.2f}% | Jain: {jains:.3f} | Offload: {off:4.1f}%")

    # Save quantitative results JSON
    out_parent = os.path.dirname(os.path.abspath(out_json))
    os.makedirs(out_parent, exist_ok=True)
    with open(out_json, 'w') as f:
        json.dump(benchmark_data, f, indent=2)
    print(f"\n[Saved] Detailed benchmark JSON saved to {out_json}")

    # Generate Publication-Grade 6-Panel Figure covering all Proposal Metrics
    if generate_plots:
        plot_proposal_tournament_figures(benchmark_data, decision_timings, plots_dir=plots_dir)
    return benchmark_data


def plot_proposal_tournament_figures(data, decision_timings, plots_dir=None):
    """Plots 6-panel comprehensive benchmark and radar comparison using publication styling."""
    try:
        from generate_detailed_plots import plot_tournament_benchmarks, plot_tournament_radar
        plot_tournament_benchmarks(data, output_dir=plots_dir)
        plot_tournament_radar(data, output_dir=plots_dir)
    except Exception as e:
        print(f"[Plot Warning] Could not import generate_detailed_plots: {e}")




if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="Routing Algorithms Tournament Benchmark (EC499)")
    parser.add_argument('--model-path', default=None, help="Path to pre-trained DQN checkpoint (.pth)")
    parser.add_argument('--output-json', default=None, help="Path to output JSON results")
    parser.add_argument('--plots-dir', default=None, help="Directory to save generated comparison plots")
    parser.add_argument('--topologies', nargs='+', default=None, help="Specific topologies to benchmark")
    parser.add_argument('--seed', type=int, default=None, help="Random seed for reproducibility")
    parser.add_argument('--policy-mode', choices=['pure', 'safety'], default=None,
                        help="Evaluate the pure learned policy or the labeled deployment safety policy")
    parser.add_argument('--no-plots', action='store_true', help="Skip plot generation")
    args = parser.parse_args()

    run_routing_tournament(
        model_path=args.model_path,
        json_path=args.output_json,
        plots_dir=args.plots_dir,
        topologies=args.topologies,
        seed=args.seed,
        policy_mode=args.policy_mode,
        generate_plots=not args.no_plots,
    )
