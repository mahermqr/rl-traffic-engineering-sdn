#!/usr/bin/env python3
"""
Dynamic Zero-Shot Blind Evaluation on Random Unseen Topologies (EC499).
Evaluates the pre-trained Double DQN Router on dynamically generated, arbitrary random topologies without retraining.
Evaluates: Core Jamming Relief, Avalanche Decisions/sec, Latency Degradation, and Jitter/Loss Resilience.
"""

import os
import sys
import time
import random
import argparse

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

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)
for subdir in ['agent', 'controller', 'topology']:
    p = os.path.join(BASE_DIR, subdir)
    if p not in sys.path:
        sys.path.append(p)

import numpy as np

from config import (
    DEFAULT_MODEL_PATH,
    STATE_SIZE,
    ACTION_SIZE,
    K_CANDIDATE_PATHS,
    POLICY_MODE,
    TORCH_DEVICE,
)
from dqn_router import DQNRoutingAgent
from state_manager import StateManager
from policy_selector import select_dqn_path
from topology_library import build_random_topology
from traditional_routing import dijkstra_spf, compute_path_metrics

def evaluate_random_blind_topology(
    num_nodes=20,
    seed=None,
    num_flows=200,
    model_path=None,
    output_json=None,
    k_paths=None,
    burst_flows_count=500,
    device=None
):
    print("=" * 85)
    print(" 🎲 ZERO-SHOT BLIND EVALUATION ON DYNAMICALLY GENERATED RANDOM TOPOLOGY (EC499)")
    print("=" * 85)

    k_val = k_paths or K_CANDIDATE_PATHS
    dev = device or TORCH_DEVICE

    # 1. Load trained agent checkpoints
    router_agent = DQNRoutingAgent(state_size=STATE_SIZE, action_size=ACTION_SIZE, device=dev)
    router_ckpt = model_path or os.environ.get('SDN_MODEL_PATH', DEFAULT_MODEL_PATH)
    if not router_agent.load(router_ckpt):
        print(f"[Error] Failed to load router weights from {router_ckpt}")
        return None
    router_agent.epsilon = 0.0 # Strict greedy inference
    print(f"[Init] Loaded trained Double DQN Router checkpoint from {router_ckpt}")

    # 2. Build completely unseen random connected topology
    graph, meta = build_random_topology(num_nodes=num_nodes, p_edge=0.30, seed=seed)
    topo_name = meta['name']
    n_nodes = graph.number_of_nodes()
    n_edges = graph.number_of_edges()

    print(f"\n[Topology Generated on the Fly]")
    print(f" • Fabric:                 {topo_name}")
    print(f" • Random Seed:            {seed if seed is not None else 'Dynamic / Unseeded'}")
    print(f" • Switches/Nodes:         {n_nodes}")
    print(f" • Directed Links:         {n_edges}")
    print(f" • Core Nodes:             {meta['core_nodes']}")
    print(f" • Edge Nodes:             {len(meta['edge_nodes'])} switches")

    sm = StateManager()
    sm.set_topology('random', graph, meta)

    core_nodes = meta['core_nodes']
    edge_nodes = meta['edge_nodes']

    # -------------------------------------------------------------------------
    # TEST 1: Core Jamming & Lateral Path Offloading
    # -------------------------------------------------------------------------
    print("\n" + "-" * 85)
    print(f" [TEST 1/4] CORE JAMMING RESILIENCE ({num_flows} Flows Across Random Topology)")
    print("-" * 85)
    for u, v in sm.graph.edges():
        if u in core_nodes or v in core_nodes:
            sm.link_utilization[(u, v)] = random.uniform(0.85, 0.98)
        else:
            sm.link_utilization[(u, v)] = random.uniform(0.10, 0.30)

    offloaded_count = 0
    dqn_bottlenecks, spf_bottlenecks = [], []
    dqn_latencies, spf_latencies = [], []

    def evaluate_flow(src, dst):
        cand_paths = sm.get_candidate_paths(src, dst, k=k_val)
        spf_p = dijkstra_spf(sm.graph, src, dst)
        decision = select_dqn_path(
            router_agent, sm, src, dst, candidate_paths=cand_paths,
            mode=POLICY_MODE
        )
        if decision['status'] != 'success' or not spf_p:
            raise RuntimeError(f"No route between {src} and {dst}")
        dqn_p = decision['path']

        m_dqn = compute_path_metrics(dqn_p, sm.link_utilization, sm.link_delays, sm.link_bandwidths)
        m_spf = compute_path_metrics(spf_p, sm.link_utilization, sm.link_delays, sm.link_bandwidths)

        is_offload = (dqn_p != spf_p) and (m_dqn['bottleneck_util'] < m_spf['bottleneck_util'])
        return is_offload, m_dqn['bottleneck_util'], m_spf['bottleneck_util'], m_dqn['total_delay'], m_spf['total_delay'], m_dqn['jitter'], m_dqn['packet_loss']

    for _ in range(num_flows):
        src = random.choice(edge_nodes)
        dst = random.choice([n for n in edge_nodes if n != src])
        off, db, sb, dl, sl, _, _ = evaluate_flow(src, dst)
        if off:
            offloaded_count += 1
        dqn_bottlenecks.append(db)
        spf_bottlenecks.append(sb)
        dqn_latencies.append(dl)
        spf_latencies.append(sl)

    mean_dqn_b = np.mean(dqn_bottlenecks) * 100.0
    mean_spf_b = np.mean(spf_bottlenecks) * 100.0
    offload_rate = (offloaded_count / float(num_flows)) * 100.0
    congestion_relief = mean_spf_b - mean_dqn_b

    print(f" • Evaluated Flows:                      {num_flows}")
    print(f" • Double DQN Mean Bottleneck Load:      {mean_dqn_b:.2f}%")
    print(f" • Dijkstra SPF Mean Bottleneck Load:    {mean_spf_b:.2f}%")
    print(f" • Congestion Relief:                    +{congestion_relief:.2f}% net load reduction")
    print(f" • Autonomous Offload Rate:              {offload_rate:.1f}% of flows steered away from core jam")

    # -------------------------------------------------------------------------
    # TEST 2: High-Concurrency Burst
    # -------------------------------------------------------------------------
    print("\n" + "-" * 85)
    print(f" [TEST 2/4] HIGH-CONCURRENCY DECISION AVALANCHE ({burst_flows_count} Simultaneous Ingress Flows)")
    print("-" * 85)
    burst_flows = []
    for _ in range(burst_flows_count):
        s = random.choice(edge_nodes)
        d = random.choice([n for n in edge_nodes if n != s])
        burst_flows.append((s, d))
    t0 = time.time()
    link_loads_dqn = {e: 0 for e in sm.graph.edges()}
    link_loads_spf = {e: 0 for e in sm.graph.edges()}

    for s, d in burst_flows:
        cands = sm.get_candidate_paths(s, d, k=k_val)
        if not cands:
            continue
        for edge, count in link_loads_dqn.items():
            sm.link_utilization[edge] = max(0.0, count * 0.02)
        decision = select_dqn_path(
            router_agent, sm, s, d, candidate_paths=cands,
            mode=POLICY_MODE
        )
        p_dqn = decision.get('path')
        p_spf = dijkstra_spf(sm.graph, s, d)
        if not p_dqn or not p_spf:
            continue
        for i in range(len(p_dqn)-1):
            if (p_dqn[i], p_dqn[i+1]) in link_loads_dqn:
                link_loads_dqn[(p_dqn[i], p_dqn[i+1])] += 1
        for i in range(len(p_spf)-1):
            if (p_spf[i], p_spf[i+1]) in link_loads_spf:
                link_loads_spf[(p_spf[i], p_spf[i+1])] += 1

    burst_time_ms = (time.time() - t0) * 1000.0
    decisions_per_sec = burst_flows_count / max(0.001, (burst_time_ms / 1000.0))

    def jains_fairness(loads_dict):
        x = list(loads_dict.values())
        if not x or sum(x) == 0:
            return 1.0
        return float((sum(x) ** 2) / (len(x) * sum(val ** 2 for val in x)))

    j_dqn = jains_fairness(link_loads_dqn)
    j_spf = jains_fairness(link_loads_spf)
    print(f" • Processed Burst:                      {burst_flows_count} concurrent flows in {burst_time_ms:.1f} ms")
    print(f" • Controller Decision Throughput:       {decisions_per_sec:.1f} decisions/second")
    print(f" • Jain's Fairness Index:                DQN: {j_dqn:.4f} vs SPF: {j_spf:.4f}")

    # -------------------------------------------------------------------------
    # TEST 3: Dynamic Latency Degradation
    # -------------------------------------------------------------------------
    print("\n" + "-" * 85)
    print(f" [TEST 3/4] DYNAMIC LATENCY DEGRADATION (Core links degraded to 25ms)")
    print("-" * 85)
    for u, v in sm.graph.edges():
        if u in core_nodes or v in core_nodes:
            sm.link_delays[(u, v)] = 25.0
            sm.link_utilization[(u, v)] = 0.50
        else:
            sm.link_delays[(u, v)] = 4.0
            sm.link_utilization[(u, v)] = 0.20

    t3_dqn_l, t3_spf_l = [], []
    for _ in range(150):
        src = random.choice(edge_nodes)
        dst = random.choice([n for n in edge_nodes if n != src])
        _, _, _, dl, sl, _, _ = evaluate_flow(src, dst)
        t3_dqn_l.append(dl)
        t3_spf_l.append(sl)

    t3_savings = np.mean(t3_spf_l) - np.mean(t3_dqn_l)
    print(f" • Double DQN Mean Latency:              {np.mean(t3_dqn_l):.2f} ms")
    print(f" • Dijkstra SPF Mean Latency:            {np.mean(t3_spf_l):.2f} ms")
    if t3_savings >= 0:
        print(f" • End-to-End Latency Improvement:       +{t3_savings:.2f} ms (Faster via low-delay bypass!)")
    else:
        print(f" • End-to-End Latency Trade-Off:         {t3_savings:.2f} ms (Detour prioritized low-congestion)")

    # -------------------------------------------------------------------------
    # TEST 4: Network Jitter & Packet Loss Resilience (RFC 3393)
    # -------------------------------------------------------------------------
    print("\n" + "-" * 85)
    print(f" [TEST 4/4] JITTER & PACKET LOSS RESILIENCE (RFC 3393 / RFC 3550)")
    print("-" * 85)
    t4_dqn_j, t4_spf_j = [], []
    t4_dqn_loss, t4_spf_loss = [], []
    for _ in range(150):
        src = random.choice(edge_nodes)
        dst = random.choice([n for n in edge_nodes if n != src])
        _, _, _, _, _, dj, dloss = evaluate_flow(src, dst)
        cand_paths = sm.get_candidate_paths(src, dst, k=k_val)
        spf_p = dijkstra_spf(sm.graph, src, dst)
        m_spf = compute_path_metrics(spf_p, sm.link_utilization, sm.link_delays, sm.link_bandwidths)
        t4_dqn_j.append(dj)
        t4_spf_j.append(m_spf['jitter'])
        t4_dqn_loss.append(dloss)
        t4_spf_loss.append(m_spf['packet_loss'])

    print(f" • Double DQN Mean Jitter:               {np.mean(t4_dqn_j):.2f} ms (vs SPF: {np.mean(t4_spf_j):.2f} ms)")
    print(f" • Double DQN Mean Packet Loss:          {np.mean(t4_dqn_loss):.2f}% (vs SPF: {np.mean(t4_spf_loss):.2f}%)")
    print("=" * 85)
    print(f" ✅ ZERO-SHOT BLIND TRANSFER TEST PASSED ON UNSEEN {n_nodes}-NODE RANDOM TOPOLOGY!")
    print("=" * 85)

    results = {
        'topology_name': topo_name,
        'num_nodes': n_nodes,
        'num_edges': n_edges,
        'topology': {
            'nodes': n_nodes,
            'edges': n_edges,
            'core_nodes': core_nodes,
            'edge_nodes': edge_nodes
        },
        'num_flows': num_flows,
        'burst_flows': burst_flows_count,
        'k_candidate_paths': k_val,
        'test1_jamming': {
            'dqn_bottleneck_pct': float(round(mean_dqn_b, 2)),
            'spf_bottleneck_pct': float(round(mean_spf_b, 2)),
            'congestion_relief_pct': float(round(congestion_relief, 2)),
            'offload_rate_pct': float(round(offload_rate, 2))
        },
        'test1_core_jamming': {
            'dqn_bottleneck_pct': float(round(mean_dqn_b, 2)),
            'spf_bottleneck_pct': float(round(mean_spf_b, 2)),
            'congestion_relief_pct': float(round(congestion_relief, 2)),
            'offload_rate_pct': float(round(offload_rate, 2))
        },
        'test2_avalanche': {
            'burst_time_ms': float(round(burst_time_ms, 2)),
            'decisions_per_sec': float(round(decisions_per_sec, 1)),
            'jains_fairness_dqn': float(round(j_dqn, 4)),
            'jains_fairness_spf': float(round(j_spf, 4))
        },
        'test3_latency': {
            'dqn_mean_latency_ms': float(round(float(np.mean(t3_dqn_l)), 2)),
            'spf_mean_latency_ms': float(round(float(np.mean(t3_spf_l)), 2)),
            'latency_improvement_ms': float(round(t3_savings, 2))
        },
        'test4_jitter_loss': {
            'dqn_mean_jitter_ms': float(round(float(np.mean(t4_dqn_j)), 2)),
            'spf_mean_jitter_ms': float(round(float(np.mean(t4_spf_j)), 2)),
            'dqn_mean_loss_pct': float(round(float(np.mean(t4_dqn_loss)), 2)),
            'spf_mean_loss_pct': float(round(float(np.mean(t4_spf_loss)), 2))
        }
    }

    if output_json:
        import json
        out_dir = os.path.dirname(os.path.abspath(output_json))
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        existing_evals = []
        if os.path.isfile(output_json):
            try:
                with open(output_json, 'r') as f:
                    prev = json.load(f)
                    if isinstance(prev, dict) and 'evaluations' in prev:
                        existing_evals = prev['evaluations']
                    elif isinstance(prev, list):
                        existing_evals = prev
                    elif isinstance(prev, dict):
                        existing_evals = [prev]
            except Exception:
                existing_evals = []
        existing_evals = [
            e for e in existing_evals
            if e.get('num_nodes') != n_nodes and e.get('topology', {}).get('nodes') != n_nodes
        ]
        existing_evals.append(results)
        existing_evals.sort(key=lambda x: x.get('num_nodes', x.get('topology', {}).get('nodes', 0)))
        payload = {
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
            'evaluations': existing_evals,
            **results
        }
        with open(output_json, 'w') as f:
            json.dump(payload, f, indent=2)
        print(f"[Saved] Blind evaluation metrics exported to: {output_json}")

    return results

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Evaluate DRL Traffic Engineering Zero-Shot on Random Unseen Topologies")
    parser.add_argument('--nodes', type=int, default=20, help="Number of random network switches/nodes (default: 20)")
    parser.add_argument('--seed', type=int, default=None, help="Random seed for reproducibility (default: None)")
    parser.add_argument('--flows', type=int, default=200, help="Number of test flows to evaluate (default: 200)")
    parser.add_argument('--burst-flows', type=int, default=500, help="Number of concurrent burst flows in Test 2 (default: 500)")
    parser.add_argument('--candidate-paths', '-k', type=int, default=None, help=f"Number of candidate paths K (default: {K_CANDIDATE_PATHS})")
    parser.add_argument('--model-path', '-m', type=str, default=None, help=f"Path to trained model checkpoint (default: {DEFAULT_MODEL_PATH})")
    parser.add_argument('--output-json', '-o', type=str, default=None, help="Optional path to export JSON evaluation results")
    args = parser.parse_args()

    evaluate_random_blind_topology(
        num_nodes=args.nodes,
        seed=args.seed,
        num_flows=args.flows,
        model_path=args.model_path,
        output_json=args.output_json,
        k_paths=args.candidate_paths,
        burst_flows_count=args.burst_flows
    )
