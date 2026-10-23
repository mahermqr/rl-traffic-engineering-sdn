#!/usr/bin/env python3
"""
Comprehensive Multi-Seed Ablation & Multi-Seed Reward Sensitivity Runner (EC499).
Fulfills Senior External Examiner Requirement 5:
  1. Train each ablation variant across 5 independent training seeds (4 x 5 = 20 models).
  2. Bootstrap over training seed as well as workload and topology (3-way cluster bootstrap).
  3. Re-evaluate Dueling vs. Double and PER vs. Dueling paired differences with cross-seed intervals.
  4. Train reward sensitivity grid (3 theta x 4 w_relief = 12 cells) across 3 seeds per cell (36 models).
  5. Compute mean +/- SD across training seeds for every cell in the reward grid.
"""

import os
import sys
import time
import json
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "report_artifacts", "data")
os.makedirs(DATA_DIR, exist_ok=True)

sys.path.extend([os.path.join(BASE_DIR, 'controller'), os.path.join(BASE_DIR, 'topology'), BASE_DIR])

from experiment_phase1_suite import (
    train_specialized_agent,
    evaluate_agent_on_matrix,
    WORKLOAD_SEEDS,
    TOPOLOGY_KEYS
)

TRAIN_SEEDS = [42, 101, 102, 103, 104]

VARIANTS = {
    "plain_dqn": {"dueling": False, "double_dqn": False, "use_per": False, "desc": "Plain DQN"},
    "double_dqn": {"dueling": False, "double_dqn": True, "use_per": False, "desc": "Double DQN (no dueling)"},
    "dueling_ddqn": {"dueling": True, "double_dqn": True, "use_per": False, "desc": "Dueling DDQN (no PER)"},
    "full_d3qn": {"dueling": True, "double_dqn": True, "use_per": True, "desc": "Full D3QN (with PER)"}
}

METRIC_NAMES = [
    "bottleneck_util",
    "mean_latency_ms",
    "p95_latency_ms",
    "p99_latency_ms",
    "mean_jitter_ms",
    "packet_loss_pct",
    "worst_link_loss_pct",
    "jains_fairness",
    "decision_time_ms"
]

def bootstrap_3way_difference(matrix_a, matrix_b, rng, iterations=10000, higher_is_better=False):
    """
    3-Way cluster bootstrap over:
      - Training seeds (axis 0: 5 seeds)
      - Workload seeds (axis 1: 5 seeds)
      - Topologies (axis 2: 5 topologies)
    """
    diff_tensor = (matrix_a - matrix_b) if not higher_is_better else (matrix_b - matrix_a)
    n_train, n_work, n_topo = diff_tensor.shape

    # Vectorized hierarchical resampling
    train_idx = rng.integers(0, n_train, size=(iterations, n_train))
    work_idx = rng.integers(0, n_work, size=(iterations, n_work))
    topo_idx = rng.integers(0, n_topo, size=(iterations, n_topo))

    draws = diff_tensor[
        train_idx[:, :, None, None],
        work_idx[:, None, :, None],
        topo_idx[:, None, None, :]
    ].mean(axis=(1, 2, 3))

    point_est = float(diff_tensor.mean())
    ci_low = float(np.percentile(draws, 2.5))
    ci_high = float(np.percentile(draws, 97.5))
    win_rate = float(np.mean(draws > 0) * 100.0)

    return {
        "point_estimate": round(point_est, 4),
        "ci95_low": round(ci_low, 4),
        "ci95_high": round(ci_high, 4),
        "win_rate_pct": round(win_rate, 2)
    }

def run_multiseed_ablation():
    print("=" * 80)
    print(" [*] COMMENCING MULTI-SEED ARCHITECTURAL ABLATION (20 MODELS: 4 VARIANTS x 5 SEEDS)")
    print("=" * 80)
    rng = np.random.default_rng(2026)

    # Dictionary: variant -> 3D numpy array [n_train_seeds, n_work_seeds, n_topos]
    variant_tensors = {
        v: {m: np.zeros((len(TRAIN_SEEDS), len(WORKLOAD_SEEDS), len(TOPOLOGY_KEYS))) for m in METRIC_NAMES}
        for v in VARIANTS
    }

    t0_all = time.time()
    for v_key, v_cfg in VARIANTS.items():
        print(f"\n--- Variant: {v_key} ({v_cfg['desc']}) ---")
        for s_idx, t_seed in enumerate(TRAIN_SEEDS):
            t_start = time.time()
            agent = train_specialized_agent(
                dueling=v_cfg["dueling"],
                double_dqn=v_cfg["double_dqn"],
                use_per=v_cfg["use_per"],
                episodes=350,
                seed=t_seed
            )
            eval_mat = evaluate_agent_on_matrix(agent, WORKLOAD_SEEDS, TOPOLOGY_KEYS, flow_count=150)
            dur = time.time() - t_start
            for m in METRIC_NAMES:
                variant_tensors[v_key][m][s_idx, :, :] = eval_mat[m]
            print(f"  [+] Seed {t_seed} ({s_idx+1}/5) completed in {dur:.2f}s | Mean Bottleneck: {eval_mat['bottleneck_util'].mean():.2f}% | Latency: {eval_mat['mean_latency_ms'].mean():.2f} ms")

    # Compute summary statistics
    variant_summaries = {}
    for v_key in VARIANTS:
        v_sum = {}
        for m in METRIC_NAMES:
            flat = variant_tensors[v_key][m].flatten()
            seed_means = variant_tensors[v_key][m].mean(axis=(1, 2))
            v_sum[m] = {
                "grand_mean": round(float(np.mean(flat)), 2),
                "grand_std": round(float(np.std(flat)), 2),
                "inter_seed_mean": round(float(np.mean(seed_means)), 2),
                "inter_seed_std": round(float(np.std(seed_means)), 2),
                "p95": round(float(np.percentile(flat, 95)), 2),
                "p99": round(float(np.percentile(flat, 99)), 2)
            }
        variant_summaries[v_key] = v_sum

    # Paired 3-way cluster bootstraps
    # Reference: Full D3QN
    full_t = variant_tensors["full_d3qn"]
    bootstrap_results = {}

    comparisons = [
        ("full_d3qn_vs_plain_dqn", "full_d3qn", "plain_dqn"),
        ("full_d3qn_vs_double_dqn", "full_d3qn", "double_dqn"),
        ("dueling_ddqn_vs_double_dqn", "dueling_ddqn", "double_dqn"),
        ("full_d3qn_vs_dueling_ddqn", "full_d3qn", "dueling_ddqn")
    ]

    for comp_name, var_a, var_b in comparisons:
        bootstrap_results[comp_name] = {}
        for m in ["bottleneck_util", "mean_latency_ms", "packet_loss_pct", "jains_fairness"]:
            higher = (m == "jains_fairness")
            # Note: for lower-is-better metrics (util, latency, loss), improvement is var_b - var_a (positive = D3QN/Dueling better)
            res = bootstrap_3way_difference(variant_tensors[var_b][m], variant_tensors[var_a][m], rng, iterations=10000, higher_is_better=higher)
            bootstrap_results[comp_name][m] = res

    ablation_out = {
        "metadata": {
            "training_seeds": TRAIN_SEEDS,
            "workload_seeds": WORKLOAD_SEEDS,
            "topologies": TOPOLOGY_KEYS,
            "total_evaluations_per_variant": len(TRAIN_SEEDS) * len(WORKLOAD_SEEDS) * len(TOPOLOGY_KEYS),
            "episodes_per_training": 350,
            "bootstrap_method": "3-way hierarchical cluster bootstrap resampling (training_seed, workload_seed, topology)",
            "iterations": 10000
        },
        "variant_summaries": variant_summaries,
        "three_way_bootstrap_paired_effects": bootstrap_results
    }

    out_file = os.path.join(DATA_DIR, "multiseed_ablation_study_results.json")
    with open(out_file, "w") as f:
        json.dump(ablation_out, f, indent=2)

    total_time = time.time() - t0_all
    print(f"\n[✓] Multi-Seed Ablation Complete in {total_time:.1f}s. Saved to: {out_file}")
    return ablation_out

def run_multiseed_reward_sensitivity():
    print("\n" + "=" * 80)
    print(" [*] COMMENCING MULTI-SEED REWARD SENSITIVITY GRID (12 CELLS x 3 SEEDS = 36 MODELS)")
    print("=" * 80)
    t0_all = time.time()

    theta_vals = [0.6, 0.7, 0.8]
    w_relief_vals = [1.0, 2.0, 4.0, 8.0]
    seeds_per_cell = [42, 101, 102]

    grid_results = {}

    for theta in theta_vals:
        for w_rel in w_relief_vals:
            cell_key = f"theta_{theta}_relief_{w_rel}"
            cell_bottlenecks = []
            cell_latencies = []
            cell_losses = []
            cell_fairness = []

            print(f"\n[*] Evaluating Cell: theta={theta}, w_relief={w_rel} across 3 seeds...")
            for s in seeds_per_cell:
                agent = train_specialized_agent(
                    dueling=True, double_dqn=True, use_per=True,
                    episodes=350, seed=s,
                    reward_params={"w_congestion": theta, "w_relief": w_rel}
                )
                res = evaluate_agent_on_matrix(agent, WORKLOAD_SEEDS, TOPOLOGY_KEYS, flow_count=150)
                cell_bottlenecks.append(float(np.mean(res["bottleneck_util"])))
                cell_latencies.append(float(np.mean(res["mean_latency_ms"])))
                cell_losses.append(float(np.mean(res["packet_loss_pct"])))
                cell_fairness.append(float(np.mean(res["jains_fairness"])))

            grid_results[cell_key] = {
                "theta_congestion": theta,
                "w_relief": w_rel,
                "seeds_evaluated": seeds_per_cell,
                "bottleneck_util": {
                    "mean": round(float(np.mean(cell_bottlenecks)), 2),
                    "std": round(float(np.std(cell_bottlenecks)), 2)
                },
                "latency_ms": {
                    "mean": round(float(np.mean(cell_latencies)), 2),
                    "std": round(float(np.std(cell_latencies)), 2)
                },
                "packet_loss_pct": {
                    "mean": round(float(np.mean(cell_losses)), 4),
                    "std": round(float(np.std(cell_losses)), 4)
                },
                "jains_fairness": {
                    "mean": round(float(np.mean(cell_fairness)), 4),
                    "std": round(float(np.std(cell_fairness)), 4)
                }
            }
            print(f"  --> Result: Bottleneck={grid_results[cell_key]['bottleneck_util']['mean']:.2f} +/- {grid_results[cell_key]['bottleneck_util']['std']:.2f}% | Latency={grid_results[cell_key]['latency_ms']['mean']:.2f} +/- {grid_results[cell_key]['latency_ms']['std']:.2f} ms")

    out_file = os.path.join(DATA_DIR, "multiseed_reward_sensitivity_results.json")
    with open(out_file, "w") as f:
        json.dump(grid_results, f, indent=2)

    total_time = time.time() - t0_all
    print(f"\n[✓] Multi-Seed Reward Grid Complete in {total_time:.1f}s. Saved to: {out_file}")
    return grid_results

if __name__ == '__main__':
    run_multiseed_ablation()
    run_multiseed_reward_sensitivity()
