#!/usr/bin/env python3
"""Repeated-seed statistical evaluation for the EC499 routing tournament.

This runner evaluates independent workload seeds, retains topology-level paired
observations, bootstraps 95% confidence intervals, and separates the pure D3QN
policy from the explicitly hybrid deployment-safety policy.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import tempfile
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from benchmark_routing_algorithms import run_routing_tournament


METRICS = {
    "bottleneck_util": ("Bottleneck utilization", "%", "lower"),
    "latency_ms": ("End-to-end latency", "ms", "lower"),
    "jitter_ms": ("Jitter", "ms", "lower"),
    "packet_loss_pct": ("Modeled packet loss", "%", "lower"),
    "jains_fairness": ("Jain fairness", "index", "higher"),
    "decision_time_ms": ("Decision time", "ms", "lower"),
}


def bootstrap_mean_ci(values, rng, iterations=10000):
    """Two-way cluster bootstrap over workload seeds and topologies."""
    values = np.asarray(values, dtype=np.float64)
    if values.size == 0:
        return 0.0, 0.0, 0.0
    if values.ndim != 2:
        raise ValueError("bootstrap input must be a seed-by-topology matrix")
    seed_idx = rng.integers(0, values.shape[0], size=(iterations, values.shape[0]))
    topology_idx = rng.integers(0, values.shape[1], size=(iterations, values.shape[1]))
    draws = values[seed_idx[:, :, None], topology_idx[:, None, :]].mean(axis=(1, 2))
    return (
        float(values.mean()),
        float(np.percentile(draws, 2.5)),
        float(np.percentile(draws, 97.5)),
    )


def flatten_runs(runs, metric, algorithm):
    return np.asarray(
        [value for run in runs for value in run[metric][algorithm]],
        dtype=np.float64,
    )


def matrix_runs(runs, metric, algorithm):
    return np.asarray([run[metric][algorithm] for run in runs], dtype=np.float64)


def compact_run(data):
    return {
        "metadata": data["metadata"],
        "topologies": data["topologies"],
        **{
            metric: data[metric]
            for metric in METRICS
        },
    }


def summarize(mode_runs, seeds, bootstrap_iterations=10000, bootstrap_seed=2026):
    rng = np.random.default_rng(bootstrap_seed)
    algorithms = list(mode_runs["pure"][0]["bottleneck_util"])
    summary = {
        "methodology": {
            "workload_seeds": seeds,
            "seed_count": len(seeds),
            "topologies_per_seed": len(mode_runs["pure"][0]["topologies"]),
            "paired_topology_seed_observations": len(seeds) * len(mode_runs["pure"][0]["topologies"]),
            "flows_per_topology_algorithm": mode_runs["pure"][0]["metadata"]["flows_per_topology"],
            "bootstrap_iterations": bootstrap_iterations,
            "bootstrap_seed": bootstrap_seed,
            "confidence_level_pct": 95,
            "unit_of_analysis": "balanced seed-by-topology matrix",
            "bootstrap_method": "two-way cluster bootstrap resampling workload seeds and topologies independently",
            "policy_note": "pure is learned-only; safety is a labeled deterministic guard applied after Q inference",
        },
        "topologies": mode_runs["pure"][0]["topologies"],
        "algorithm_summary": {},
        "pure_dqn_paired_effects": {},
        "policy_mode_ablation": {},
        "runs": {
            mode: [compact_run(run) for run in runs]
            for mode, runs in mode_runs.items()
        },
    }

    for mode, runs in mode_runs.items():
        summary["algorithm_summary"][mode] = {}
        for metric, (_, unit, direction) in METRICS.items():
            summary["algorithm_summary"][mode][metric] = {}
            for algorithm in algorithms:
                matrix = matrix_runs(runs, metric, algorithm)
                values = matrix.ravel()
                mean, low, high = bootstrap_mean_ci(matrix, rng, bootstrap_iterations)
                summary["algorithm_summary"][mode][metric][algorithm] = {
                    "mean": round(mean, 6),
                    "sample_sd": round(float(values.std(ddof=1)), 6),
                    "ci95_low": round(low, 6),
                    "ci95_high": round(high, 6),
                    "n": int(values.size),
                    "unit": unit,
                    "direction": direction,
                }

    dqn = "DQN (Ours)"
    baselines = [a for a in algorithms if a != dqn]
    pure_runs = mode_runs["pure"]
    for baseline in baselines:
        summary["pure_dqn_paired_effects"][baseline] = {}
        for metric, (_, unit, direction) in METRICS.items():
            dqn_matrix = matrix_runs(pure_runs, metric, dqn)
            base_matrix = matrix_runs(pure_runs, metric, baseline)
            improvement_matrix = base_matrix - dqn_matrix if direction == "lower" else dqn_matrix - base_matrix
            improvement = improvement_matrix.ravel()
            mean, low, high = bootstrap_mean_ci(improvement_matrix, rng, bootstrap_iterations)
            base_values = base_matrix.ravel()
            base_mean = float(base_values.mean())
            relative = (100.0 * mean / abs(base_mean)) if abs(base_mean) > 1e-12 else 0.0
            summary["pure_dqn_paired_effects"][baseline][metric] = {
                "mean_improvement": round(mean, 6),
                "ci95_low": round(low, 6),
                "ci95_high": round(high, 6),
                "relative_improvement_pct": round(relative, 3),
                "win_rate_pct": round(float(np.mean(improvement > 0.0) * 100.0), 2),
                "tie_rate_pct": round(float(np.mean(np.isclose(improvement, 0.0)) * 100.0), 2),
                "n": int(improvement.size),
                "unit": unit,
                "positive_means_dqn_better": True,
            }

    for metric, (_, unit, direction) in METRICS.items():
        pure_matrix = matrix_runs(mode_runs["pure"], metric, dqn)
        safety_matrix = matrix_runs(mode_runs["safety"], metric, dqn)
        pure_values = pure_matrix.ravel()
        safety_values = safety_matrix.ravel()
        improvement_matrix = pure_matrix - safety_matrix if direction == "lower" else safety_matrix - pure_matrix
        improvement = improvement_matrix.ravel()
        mean, low, high = bootstrap_mean_ci(improvement_matrix, rng, bootstrap_iterations)
        summary["policy_mode_ablation"][metric] = {
            "pure_mean": round(float(pure_values.mean()), 6),
            "safety_mean": round(float(safety_values.mean()), 6),
            "safety_improvement": round(mean, 6),
            "ci95_low": round(low, 6),
            "ci95_high": round(high, 6),
            "safety_win_rate_pct": round(float(np.mean(improvement > 0.0) * 100.0), 2),
            "n": int(improvement.size),
            "unit": unit,
            "positive_means_safety_better": True,
        }
    return summary


def plot_paired_effects(summary, output_path):
    metrics = ["bottleneck_util", "latency_ms", "jitter_ms", "packet_loss_pct"]
    baselines = list(summary["pure_dqn_paired_effects"])
    short = {
        "OSPF (RFC 2328)": "OSPF",
        "Dijkstra SPF": "Dijkstra",
        "ECMP": "ECMP",
        "WSP (Widest Path)": "WSP",
        "LLR (Least Loaded)": "LLR",
    }
    fig, axes = plt.subplots(2, 2, figsize=(13.5, 9.0), dpi=250)
    for ax, metric in zip(axes.flat, metrics):
        label, unit, _ = METRICS[metric]
        rows = [summary["pure_dqn_paired_effects"][b][metric] for b in baselines]
        means = np.array([r["mean_improvement"] for r in rows])
        lows = np.array([r["ci95_low"] for r in rows])
        highs = np.array([r["ci95_high"] for r in rows])
        y = np.arange(len(baselines))
        colors = ["#059669" if lo > 0 else ("#dc2626" if hi < 0 else "#d97706") for lo, hi in zip(lows, highs)]
        ax.errorbar(means, y, xerr=[means - lows, highs - means], fmt="none", ecolor="#475569", capsize=4, lw=1.5)
        ax.scatter(means, y, c=colors, s=55, zorder=3)
        ax.axvline(0.0, color="#0f172a", linestyle="--", linewidth=1)
        ax.set_yticks(y)
        ax.set_yticklabels([short[b] for b in baselines])
        ax.invert_yaxis()
        ax.set_xlabel(f"Paired improvement ({unit}); positive favors pure D3QN")
        ax.set_title(label, fontweight="bold")
        ax.grid(axis="x", linestyle=":", alpha=0.45)
    fig.suptitle(
        "Pure D3QN Paired Effects Across 5 Workload Seeds and 5 Topologies\n"
        "Points are mean differences; bars are two-way bootstrap 95% confidence intervals (5 seeds x 5 topologies)",
        fontsize=13, fontweight="bold",
    )
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)


def plot_policy_ablation(summary, output_path):
    metrics = ["bottleneck_util", "latency_ms", "jitter_ms", "packet_loss_pct", "jains_fairness"]
    labels = ["Bottleneck (%)", "Latency (ms)", "Jitter (ms)", "Loss (%)", "Jain fairness"]
    fig, axes = plt.subplots(1, len(metrics), figsize=(16, 4.4), dpi=250)
    for ax, metric, label in zip(axes, metrics, labels):
        row = summary["policy_mode_ablation"][metric]
        values = [row["pure_mean"], row["safety_mean"]]
        bars = ax.bar([0, 1], values, width=0.64, color=["#0284c7", "#059669"])
        ax.bar_label(bars, fmt="%.2f", fontsize=8, padding=2)
        ax.set_xticks([0, 1], ["Pure", "Safety"])
        ax.set_title(label, fontweight="bold", fontsize=10)
        ax.grid(axis="y", linestyle=":", alpha=0.45)
        # Each metric gets its own native scale so small-valued loss and
        # fairness results remain visible beside millisecond-valued delay.
        upper = max(values) * 1.22 if max(values) > 0 else 1.0
        ax.set_ylim(0, upper)
    fig.suptitle(
        "Policy-Mode Ablation Across 25 Paired Topology--Seed Observations",
        fontsize=13,
        fontweight="bold",
    )
    fig.text(0.5, 0.01, "Safety = D3QN with the labeled deployment-safety guard", ha="center", fontsize=9)
    fig.tight_layout(rect=[0, 0.04, 1, 0.92])
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description="Repeated-seed EC499 routing evaluation")
    parser.add_argument("--seeds", nargs="+", type=int, default=[42, 43, 44, 45, 46])
    parser.add_argument("--model-path", default=None)
    parser.add_argument("--output-json", default="gptreport/data/multiseed_statistical_results.json")
    parser.add_argument("--plots-dir", default="gptreport/figures")
    parser.add_argument("--bootstrap-iterations", type=int, default=10000)
    args = parser.parse_args()

    mode_runs = {"pure": [], "safety": []}
    with tempfile.TemporaryDirectory(prefix="ec499_multiseed_") as temp_dir:
        for mode in mode_runs:
            for seed in args.seeds:
                capture = io.StringIO()
                with contextlib.redirect_stdout(capture):
                    data = run_routing_tournament(
                        model_path=args.model_path,
                        json_path=os.path.join(temp_dir, f"{mode}_{seed}.json"),
                        plots_dir=temp_dir,
                        seed=seed,
                        policy_mode=mode,
                        generate_plots=False,
                    )
                mode_runs[mode].append(data)
                print(f"[complete] mode={mode:<6} seed={seed}")

    summary = summarize(mode_runs, args.seeds, args.bootstrap_iterations)
    out_json = Path(args.output_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    plots_dir = Path(args.plots_dir)
    plot_paired_effects(summary, plots_dir / "multiseed_paired_effects.png")
    plot_policy_ablation(summary, plots_dir / "policy_mode_ablation.png")
    print(f"[saved] {out_json}")
    print(f"[saved] {plots_dir / 'multiseed_paired_effects.png'}")
    print(f"[saved] {plots_dir / 'policy_mode_ablation.png'}")


if __name__ == "__main__":
    main()
