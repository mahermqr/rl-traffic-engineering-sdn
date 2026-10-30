#!/usr/bin/env python3
"""
Routing Objective Hyperparameter Sensitivity Analysis.
Evaluates six SLA weight regimes over reproducible flows on project topologies.
This is an objective-policy sensitivity test, not a D3QN retraining experiment.
"""

import os
import sys
import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

_curr = Path(__file__).resolve().parent
BASE_DIR = _curr if (_curr / 'agent').exists() else _curr.parent
sys.path.extend([
    str(BASE_DIR / 'agent'),
    str(BASE_DIR / 'controller'),
    str(BASE_DIR / 'topology'),
    str(BASE_DIR)
])
from state_manager import StateManager
from topology_library import get_topology
from traditional_routing import compute_path_metrics

LOGS_DIR = BASE_DIR / "logs"
PLOTS_DIR = LOGS_DIR / "plots"
OUTPUT_JSON = LOGS_DIR / "pareto_sensitivity_ablation.json"
OUTPUT_PLOT = PLOTS_DIR / "pareto_weight_sensitivity.png"

# Configurations to ablate
CONFIGS = [
    {
        "id": "proposed_balanced",
        "name": "Proposed (Balanced SLA)",
        "w_util": 4.0, "w_lat": 0.5, "w_jit": 0.8, "w_loss": 10.0, "barrier_theta": 0.70,
        "description": "Standard telecom carrier profile with exponential barrier at 70% load."
    },
    {
        "id": "loss_averse",
        "name": "Loss-Averse (High Reliability)",
        "w_util": 2.0, "w_lat": 0.2, "w_jit": 0.5, "w_loss": 20.0, "barrier_theta": 0.65,
        "description": "Heavy packet loss penalty with aggressive barrier at 65% load."
    },
    {
        "id": "latency_prioritized",
        "name": "Latency-Prioritized (HFT)",
        "w_util": 1.0, "w_lat": 2.0, "w_jit": 1.5, "w_loss": 5.0, "barrier_theta": 0.80,
        "description": "Minimizes propagation delay, accepting higher core utilization up to 80%."
    },
    {
        "id": "utilization_only",
        "name": "Utilization-Biased",
        "w_util": 8.0, "w_lat": 0.1, "w_jit": 0.1, "w_loss": 2.0, "barrier_theta": 0.70,
        "description": "Greedily offloads core trunks without regard for detour propagation delay."
    },
    {
        "id": "no_barrier_ablation",
        "name": "Ablation: No Barrier (Theta=None)",
        "w_util": 4.0, "w_lat": 0.5, "w_jit": 0.8, "w_loss": 10.0, "barrier_theta": 1.00,
        "description": "Linear penalty only; demonstrates failure without exponential congestion barrier."
    },
    {
        "id": "equal_weights",
        "name": "Equal Unit Weights",
        "w_util": 1.0, "w_lat": 1.0, "w_jit": 1.0, "w_loss": 1.0, "barrier_theta": 0.70,
        "description": "Uncalibrated unit weights across all QoS dimensions."
    }
]

def simulate_regime(cfg, episodes=50):
    """Evaluate the configured objective on real project graphs and queue metrics."""
    rng = np.random.default_rng(42)
    w_u = cfg["w_util"]
    w_d = cfg["w_lat"]
    w_j = cfg["w_jit"]
    w_l = cfg["w_loss"]
    theta = cfg["barrier_theta"]

    bottlenecks = []
    latencies = []
    losses = []
    jitters = []

    topology_ids = ('tree', 'abilene', 'spineleaf')
    for ep in range(episodes):
        topology_id = topology_ids[ep % len(topology_ids)]
        graph, meta = get_topology(topology_id)
        sm = StateManager()
        sm.set_topology(topology_id, graph, meta)
        for edge in sm.link_utilization:
            sm.link_utilization[edge] = float(rng.uniform(0.20, 0.92))
            sm._recalculate_link_metrics(edge)

        endpoints = meta.get('edge_nodes', list(graph.nodes()))
        src = endpoints[int(rng.integers(0, len(endpoints)))]
        dst_options = [node for node in endpoints if node != src]
        dst = dst_options[int(rng.integers(0, len(dst_options)))]
        demand = float(rng.uniform(5.0, 25.0))
        candidates = sm.get_candidate_paths(src, dst, k=4)
        if not candidates:
            continue

        scored = []
        for path in candidates:
            projected = dict(sm.link_utilization)
            for u, v in zip(path, path[1:]):
                projected[(u, v)] = projected.get((u, v), 0.0) + demand / max(1.0, sm.link_bandwidths[(u, v)])
            metrics = compute_path_metrics(
                path, projected, sm.base_link_delays, sm.link_bandwidths,
                queue_depth=sm.switch_queue_depth, observed_delays=False,
            )
            barrier = 0.0 if theta >= 1.0 else 10.0 * w_u * max(0.0, metrics['bottleneck_util'] - theta) ** 2
            cost = (
                w_u * metrics['bottleneck_util'] ** 2
                + w_d * metrics['total_delay']
                + w_j * metrics['jitter']
                + w_l * metrics['packet_loss']
                + barrier
            )
            scored.append((cost, path))
        _, chosen = min(scored, key=lambda item: item[0])
        sm.allocate_dynamic_flow(f"ablation_{ep}", chosen, mbps=demand, duration_sec=1.0)
        observed = compute_path_metrics(
            chosen, sm.link_utilization, sm.base_link_delays, sm.link_bandwidths,
            queue_depth=sm.switch_queue_depth, observed_delays=False,
        )
        bottlenecks.append(observed['bottleneck_util'] * 100.0)
        latencies.append(observed['total_delay'])
        losses.append(observed['packet_loss'])
        jitters.append(observed['jitter'])

    mean_b = float(np.mean(bottlenecks))
    mean_lat = float(np.mean(latencies))
    mean_loss = float(np.mean(losses))
    mean_jit = float(np.mean(jitters))

    # A reporting score only; routing choices above use each ablated objective.
    score = (mean_b / 100.0) * 0.4 + (mean_lat / 50.0) * 0.25 + (mean_jit / 20.0) * 0.15 + (mean_loss / 100.0) * 0.20

    return {
        "mean_bottleneck_pct": round(mean_b, 2),
        "mean_latency_ms": round(mean_lat, 2),
        "mean_loss_pct": round(mean_loss, 3),
        "mean_jitter_ms": round(mean_jit, 2),
        "pareto_rank_score": round(float(score), 3),
        "samples": len(bottlenecks),
        "method": "deterministic multi-topology routing-objective sensitivity; no retraining"
    }

def main():
    print("[*] Running reproducible routing-objective sensitivity analysis across 6 configurations...")
    results = {}
    for cfg in CONFIGS:
        cid = cfg["id"]
        res = simulate_regime(cfg)
        results[cid] = {
            "config": cfg,
            "metrics": res
        }
        print(f"  [+] {cfg['name']}: Bottleneck={res['mean_bottleneck_pct']}% | Latency={res['mean_latency_ms']}ms | Loss={res['mean_loss_pct']}% | Score={res['pareto_rank_score']}")

    with open(OUTPUT_JSON, "w") as f:
        json.dump(results, f, indent=2)
    print(f"[+] Saved ablation records to: {OUTPUT_JSON}")

    # Generate publication-grade Pareto frontier sensitivity chart
    names = [cfg["name"] for cfg in CONFIGS]
    b_loads = [results[cfg["id"]]["metrics"]["mean_bottleneck_pct"] for cfg in CONFIGS]
    latencies = [results[cfg["id"]]["metrics"]["mean_latency_ms"] for cfg in CONFIGS]
    losses = [results[cfg["id"]]["metrics"]["mean_loss_pct"] for cfg in CONFIGS]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))
    fig.patch.set_facecolor('#ffffff')

    # Plot 1: Bottleneck Load vs End-to-End Latency Trade-Off
    colors = ['#6d28d9', '#059669', '#0284c7', '#d97706', '#e11d48', '#64748b']
    for i, cfg in enumerate(CONFIGS):
        cid = cfg["id"]
        m = results[cid]["metrics"]
        size = 180 if cid == "proposed_balanced" else 100
        ax1.scatter(m["mean_bottleneck_pct"], m["mean_latency_ms"], color=colors[i], s=size, zorder=5, label=cfg["name"])
        ax1.annotate(cfg["name"].split('(')[0].strip(), (m["mean_bottleneck_pct"] + 0.8, m["mean_latency_ms"] + 0.2), fontsize=8.5, fontweight='bold', color=colors[i])

    ax1.axvline(70.0, color='#e11d48', linestyle='--', alpha=0.6, label='Congestion Barrier (Theta=70%)')
    ax1.set_xlabel("Peak Bottleneck Utilization (%)", fontsize=11, fontweight='bold')
    ax1.set_ylabel("End-to-End Latency (ms)", fontsize=11, fontweight='bold')
    ax1.set_title("Pareto Trade-Off: Bottleneck Relief vs Latency", fontsize=12, fontweight='bold', pad=10)
    ax1.grid(True, linestyle=':', alpha=0.6)
    ax1.set_facecolor('#f8fafc')

    # Plot 2: Bar comparison of Loss and Jitter
    x = np.arange(len(names))
    width = 0.38
    ax2.bar(x - width/2, losses, width, label='Packet Loss Rate (%)', color='#e11d48', alpha=0.85)
    ax2.bar(x + width/2, [results[cfg["id"]]["metrics"]["mean_jitter_ms"] for cfg in CONFIGS], width, label='Jitter (ms)', color='#0284c7', alpha=0.85)
    ax2.set_xticks(x)
    ax2.set_xticklabels([n.split('(')[0].strip() for n in names], rotation=25, ha='right', fontsize=8.5)
    ax2.set_ylabel("Metric Value (% Loss / ms Jitter)", fontsize=11, fontweight='bold')
    ax2.set_title("Reliability Metrics Across Hyperparameter Regimes", fontsize=12, fontweight='bold', pad=10)
    ax2.legend(fontsize=9)
    ax2.grid(True, linestyle=':', alpha=0.6)
    ax2.set_facecolor('#f8fafc')

    plt.tight_layout()
    plt.savefig(OUTPUT_PLOT, dpi=300)
    plt.close()
    print(f"[+] Saved publication plot to: {OUTPUT_PLOT}")

if __name__ == "__main__":
    main()
