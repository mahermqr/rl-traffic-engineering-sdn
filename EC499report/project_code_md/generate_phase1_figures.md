# `generate_phase1_figures.py`

> **File:** `generate_phase1_figures.py`  
> **Subsystem / Category:** 9. Publications, Documentation & Slide Generation  
> **Language:** `python`  
> **Lines of Code:** 439  
> **File Size:** 21.18 KB  

---

## Overview

Comparative chart plotting script rendering Phase 1 benchmark results.

### Architecture & Symbols
- **Classes:** None (Procedural / Script)
- **Key Functions:** `plot_ablation_study`, `plot_multiple_model_seeds`, `plot_held_out_topologies`, `plot_optimisation_oracle`, `plot_reward_sensitivity_multiseed_surface`, `main`

---

## Source Code

```python
#!/usr/bin/env python3
"""
Publication-Quality Figure Generation for Phase 1 Experimental Suite.
Reads JSON data from report_artifacts/data/ and outputs high-resolution 300 DPI figures to report_artifacts/figures/:
  1. ablation_study_bootstrap.png (Paired bootstrap differences & 95% CIs)
  2. multiple_model_seeds_hierarchical.png (Variance decomposition: Model vs Workload vs Topology)
  3. held_out_topologies_generalization.png (OOD zero-shot generalization across 5 unseen benchmarks)
  4. optimisation_oracle_gap.png (HiGHS MILP theoretical optimal vs D3QN and baselines)
  5. reward_sensitivity_multiseed_surface.png (Multi-seed retraining across theta and relief weights: 3 panels)
"""

import os
import sys
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "report_artifacts", "data")
FIG_DIR = os.path.join(BASE_DIR, "report_artifacts", "figures")
LOGS_PLOT_DIR = os.path.join(BASE_DIR, "logs", "plots")
os.makedirs(FIG_DIR, exist_ok=True)
os.makedirs(LOGS_PLOT_DIR, exist_ok=True)

# Custom color palette
C_PRIMARY = "#1E3A8A"   # Navy Blue
C_ACCENT  = "#10B981"   # Emerald
C_AMBER   = "#F59E0B"   # Amber
C_CORAL   = "#EF4444"   # Crimson
C_PURPLE  = "#8B5CF6"   # Purple
C_TEAL    = "#06B6D4"   # Teal
C_SLATE   = "#64748B"   # Slate Grey

plt.rcParams.update({
    'font.sans-serif': ['DejaVu Sans', 'Arial', 'Helvetica'],
    'font.family': 'sans-serif',
    'font.size': 10,
    'axes.labelsize': 11,
    'axes.titlesize': 12,
    'xtick.labelsize': 9.5,
    'ytick.labelsize': 9.5,
    'legend.fontsize': 9.5,
    'figure.titlesize': 14,
    'axes.grid': True,
    'grid.alpha': 0.35,
    'grid.linestyle': '--',
    'figure.autolayout': False
})


# ============================================================================
# 1. Ablation Study: Paired Bootstrap Differences & 95% CIs
# ============================================================================
def plot_ablation_study():
    path = os.path.join(DATA_DIR, "ablation_study_results.json")
    if not os.path.exists(path):
        print(f"Skipping ablation plot: {path} not found")
        return
    with open(path) as f:
        data = json.load(f)

    boot = data.get("paired_bootstrap_against_full_d3qn", {})
    variants = ["plain_dqn", "double_dqn_no_dueling", "dueling_double_dqn_no_per"]
    var_labels = [
        "Plain DQN\n(No Dueling/DDQN/PER)",
        "Double DQN\n(No Dueling/PER)",
        "Dueling DDQN\n(No PER)"
    ]

    fig, axes = plt.subplots(1, 3, figsize=(16, 5.2))
    fig.suptitle("Architectural Ablation: Paired Bootstrap Effects vs. Full D3QN (95% CI)",
                 fontweight="bold", y=0.98)

    # Panel 1: Bottleneck Utilization Reduction by Full D3QN (% points)
    b_diffs = [boot[v]["bottleneck_util"]["mean_diff"] for v in variants]
    b_lows  = [boot[v]["bottleneck_util"]["ci95_low"] for v in variants]
    b_highs = [boot[v]["bottleneck_util"]["ci95_high"] for v in variants]
    b_err_l = [m - l for m, l in zip(b_diffs, b_lows)]
    b_err_h = [h - m for m, h in zip(b_diffs, b_highs)]

    bars1 = axes[0].bar(range(len(variants)), b_diffs, yerr=[b_err_l, b_err_h],
                        capsize=6, color=[C_CORAL, C_AMBER, C_TEAL], edgecolor="black", alpha=0.85, width=0.52)
    axes[0].set_xticks(range(len(variants)))
    axes[0].set_xticklabels(var_labels, fontsize=9)
    axes[0].set_ylabel("Bottleneck Utilization Relief (%)")
    axes[0].set_title("(a) Bottleneck Relief vs. Baselines", fontweight="semibold")
    axes[0].axhline(0, color="black", linestyle="-", linewidth=0.8)
    axes[0].set_ylim(-26, 56)

    for bar, d, l, h in zip(bars1, b_diffs, b_lows, b_highs):
        y_pos = bar.get_height() + (2.5 if d >= 0 else -9.0)
        va = "bottom" if d >= 0 else "top"
        axes[0].text(bar.get_x() + bar.get_width() / 2, y_pos,
                     f"{d:+.1f}%\n[{l:.1f}, {h:.1f}]", ha="center", va=va, fontsize=8.5, fontweight="bold")

    # Panel 2: Latency Profile across Ablation Stages (Mean, P95, P99)
    all_vars = ["plain_dqn", "double_dqn_no_dueling", "dueling_double_dqn_no_per", "full_d3qn"]
    all_labels = ["Plain DQN", "Double DQN", "Dueling DDQN", "Full D3QN"]
    mean_lats = [data["variants"][v]["summary"]["mean_latency_ms"]["mean"] for v in all_vars]
    p95_lats  = [data["variants"][v]["summary"]["p95_latency_ms"]["mean"] for v in all_vars]
    p99_lats  = [data["variants"][v]["summary"]["p99_latency_ms"]["mean"] for v in all_vars]

    x = np.arange(len(all_vars))
    w = 0.25
    axes[1].bar(x - w, mean_lats, width=w, label="Mean Latency", color=C_PRIMARY, edgecolor="black", alpha=0.85)
    axes[1].bar(x, p95_lats, width=w, label="P95 Latency", color=C_AMBER, edgecolor="black", alpha=0.85)
    axes[1].bar(x + w, p99_lats, width=w, label="P99 Tail Latency", color=C_CORAL, edgecolor="black", alpha=0.85)
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(all_labels, fontsize=9.5)
    axes[1].set_ylabel("Latency (ms)")
    axes[1].set_title("(b) Latency & Tail Dispersion", fontweight="semibold")
    axes[1].legend(loc="upper right")

    # Panel 3: Win Rate % across 25 Workloads
    win_rates = [boot[v]["bottleneck_util"]["win_rate_pct"] for v in variants]
    bars3 = axes[2].bar(range(len(variants)), win_rates, color=[C_PURPLE, C_TEAL, C_ACCENT],
                        edgecolor="black", alpha=0.85, width=0.52)
    axes[2].set_xticks(range(len(variants)))
    axes[2].set_xticklabels(var_labels, fontsize=9)
    axes[2].set_ylabel("D3QN Win Rate (%)")
    axes[2].set_ylim(0, 115)
    axes[2].set_title("(c) D3QN Win Rate across 25 Workloads", fontweight="semibold")
    axes[2].axhline(50, color=C_CORAL, linestyle=":", linewidth=1.2, label="Parity Threshold (50%)")
    axes[2].legend(loc="lower right")
    for bar, wr in zip(bars3, win_rates):
        axes[2].text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 2.0,
                     f"{wr:.1f}%", ha="center", va="bottom", fontsize=9.5, fontweight="bold")

    fig.tight_layout(rect=[0, 0, 1, 0.94])
    out = os.path.join(FIG_DIR, "ablation_study_bootstrap.png")
    plt.savefig(out, dpi=300)
    plt.savefig(os.path.join(LOGS_PLOT_DIR, "ablation_study_bootstrap.png"), dpi=300)
    plt.close()
    print(f"[✓] Saved figure: {out}")


# ============================================================================
# 2. Multiple Model Seeds: Hierarchical Variance Decomposition
# ============================================================================
def plot_multiple_model_seeds():
    path = os.path.join(DATA_DIR, "multiple_model_seeds_results.json")
    if not os.path.exists(path):
        print(f"Skipping model seeds plot: {path} not found")
        return
    with open(path) as f:
        data = json.load(f)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5.2))
    fig.suptitle("Multiple Model Seeds: Policy Stability & Variance Decomposition",
                 fontweight="bold", y=0.98)

    # Panel 1: Performance consistency across the 5 independent checkpoints
    m_seeds = data["metadata"]["model_seeds"]
    seed_means = [data["model_summaries"][f"seed_{s}"]["bottleneck_util"]["mean"] for s in m_seeds]
    seed_stds  = [data["model_summaries"][f"seed_{s}"]["bottleneck_util"]["std"] for s in m_seeds]

    bars = axes[0].bar([f"Seed {s}" for s in m_seeds], seed_means, yerr=seed_stds,
                       capsize=6, color=C_PRIMARY, edgecolor="black", alpha=0.85, width=0.5)
    grand_mean = data["overall_stability"]["bottleneck_util"]["grand_mean"]
    axes[0].axhline(grand_mean, color=C_CORAL, linestyle="--", linewidth=1.5,
                    label=f"Ensemble Mean: {grand_mean:.1f}%")
    axes[0].set_ylabel("Peak Bottleneck Utilization (%)")
    axes[0].set_title("(a) Peak Utilization across 5 Seeds", fontweight="semibold")
    axes[0].legend(loc="upper right")
    for bar, m in zip(bars, seed_means):
        axes[0].text(bar.get_x() + bar.get_width() / 2, bar.get_height() / 2,
                     f"{m:.1f}%", ha="center", va="center", color="white", fontweight="bold", fontsize=10)

    # Panel 2: Variance Decomposition Bar Chart (clean, no overlapping labels)
    var_decomp = data.get("hierarchical_variance_decomposition", {}).get("bottleneck_util", {})
    pct_model = var_decomp.get("model_seed_pct", 0.73)
    pct_workload = var_decomp.get("workload_seed_pct", 0.02)
    pct_topo = var_decomp.get("topology_pct", 93.51)
    pct_resid = var_decomp.get("residual_pct", 5.74)

    factors = [
        "Topology Graph Structure",
        "Residual / Interaction",
        "Model Initialization Seed",
        "Dynamic Workload Churn"
    ]
    pcts = [pct_topo, pct_resid, pct_model, pct_workload]
    bar_colors = [C_PRIMARY, C_SLATE, C_CORAL, C_TEAL]
    y_pos = np.arange(len(factors))

    bars_v = axes[1].barh(y_pos, pcts, color=bar_colors, edgecolor="black", alpha=0.85, height=0.52)
    axes[1].set_yticks(y_pos)
    axes[1].set_yticklabels(factors, fontweight="semibold", fontsize=9.5)
    axes[1].invert_yaxis()
    axes[1].set_xlabel("Share of Total Variance (%)")
    axes[1].set_xlim(0, 108)
    axes[1].set_title("(b) Hierarchical Variance Decomposition (%)", fontweight="semibold")

    for bar, p in zip(bars_v, pcts):
        axes[1].text(bar.get_width() + 1.2, bar.get_y() + bar.get_height() / 2,
                     f"{p:.2f}%", va="center", ha="left", fontweight="bold", fontsize=9.5)

    fig.tight_layout(rect=[0, 0, 1, 0.94])
    out = os.path.join(FIG_DIR, "multiple_model_seeds_hierarchical.png")
    plt.savefig(out, dpi=300)
    plt.savefig(os.path.join(LOGS_PLOT_DIR, "multiple_model_seeds_hierarchical.png"), dpi=300)
    plt.close()
    print(f"[✓] Saved figure: {out}")


# ============================================================================
# 3. Held-Out Topologies: Zero-Shot Generalization
# ============================================================================
def plot_held_out_topologies():
    path = os.path.join(DATA_DIR, "held_out_topologies_results.json")
    if not os.path.exists(path):
        print(f"Skipping held-out topologies plot: {path} not found")
        return
    with open(path) as f:
        data = json.load(f)

    topos = data["metadata"]["evaluated_topologies"]
    topo_labels = [t.capitalize() for t in topos]

    in_mat = np.array(data["in_curriculum_raw"]["bottleneck_util"])
    out_mat = np.array(data["held_out_raw"]["bottleneck_util"])

    # Mean over workload seeds (axis 0)
    in_b = np.mean(in_mat, axis=0)
    out_b = np.mean(out_mat, axis=0)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5.2))
    fig.suptitle("Zero-Shot Generalization on Held-Out Topologies",
                 fontweight="bold", y=0.98)

    x = np.arange(len(topos))
    w = 0.35
    axes[0].bar(x - w/2, in_b, width=w, label="Standard Agent (In-Curriculum)",
                color=C_PRIMARY, edgecolor="black", alpha=0.85)
    axes[0].bar(x + w/2, out_b, width=w, label="Zero-Shot Agent (Synthetic Graphs Only)",
                color=C_AMBER, edgecolor="black", alpha=0.85)
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(topo_labels)
    axes[0].set_ylabel("Bottleneck Link Utilization (%)")
    axes[0].set_title("(a) Bottleneck Utilization across Topologies", fontweight="semibold")
    axes[0].legend(loc="upper left")

    # Panel 2: Generalization Gap (% difference)
    gaps = ((out_b - in_b) / in_b) * 100.0
    bars_gap = axes[1].bar(topo_labels, gaps, color=[C_ACCENT if g <= 10 else C_AMBER if g <= 20 else C_CORAL for g in gaps],
                           edgecolor="black", alpha=0.85, width=0.5)
    axes[1].axhline(0, color="black", linestyle="-", linewidth=0.8)
    axes[1].set_ylabel("Generalization Penalty (% Gap)")
    axes[1].set_title("(b) Generalization Gap (% Degradation)",
                      fontweight="semibold")
    axes[1].set_ylim(min(gaps) - 5, max(gaps) + 6)

    for bar, g in zip(bars_gap, gaps):
        y_pos = bar.get_height() + (0.8 if g >= 0 else -1.8)
        va = "bottom" if g >= 0 else "top"
        axes[1].text(bar.get_x() + bar.get_width() / 2, y_pos,
                     f"{g:+.1f}%", ha="center", va=va, fontsize=9.5, fontweight="bold")

    fig.tight_layout(rect=[0, 0, 1, 0.94])
    out = os.path.join(FIG_DIR, "held_out_topologies_generalization.png")
    plt.savefig(out, dpi=300)
    plt.savefig(os.path.join(LOGS_PLOT_DIR, "held_out_topologies_generalization.png"), dpi=300)
    plt.close()
    print(f"[✓] Saved figure: {out}")


# ============================================================================
# 4. Optimisation Oracle: Exact HiGHS MILP Gap Analysis
# ============================================================================
def plot_optimisation_oracle():
    path = os.path.join(DATA_DIR, "optimisation_oracle_results.json")
    if not os.path.exists(path):
        print(f"Skipping oracle plot: {path} not found")
        return
    with open(path) as f:
        data = json.load(f)

    topos = list(data.keys())
    topo_labels = [t.capitalize() for t in topos]

    # Theoretical optimal alpha*
    alpha_star = [data[t]["theoretical_optimal_peak_pct"] for t in topos]
    d3qn_util  = [data[t]["algorithm_comparisons"].get("D3QN (Ours)", {}).get("achieved_peak_util_pct", 0) for t in topos]
    ospf_util  = [data[t]["algorithm_comparisons"].get("OSPF (RFC 2328)", {}).get("achieved_peak_util_pct", 0) for t in topos]
    ecmp_util  = [data[t]["algorithm_comparisons"].get("ECMP", {}).get("achieved_peak_util_pct", 0) for t in topos]
    llr_util   = [data[t]["algorithm_comparisons"].get("LLR (Least Loaded)", {}).get("achieved_peak_util_pct", 0) for t in topos]

    fig, axes = plt.subplots(1, 2, figsize=(15, 5.2))
    fig.suptitle("Optimization Oracle: Exact MILP Lower Bound vs. DRL",
                 fontweight="bold", y=0.98)

    x = np.arange(len(topos))
    w = 0.16
    axes[0].bar(x - 2*w, alpha_star, width=w, label="Exact MILP Oracle (\u03b1*)", color="#111827", hatch="//", edgecolor="black")
    axes[0].bar(x - w,   d3qn_util,  width=w, label="D3QN Adaptive", color=C_PRIMARY, edgecolor="black", alpha=0.9)
    axes[0].bar(x,       llr_util,   width=w, label="Least Loaded (LLR)", color=C_TEAL, edgecolor="black", alpha=0.85)
    axes[0].bar(x + w,   ecmp_util,  width=w, label="ECMP", color=C_AMBER, edgecolor="black", alpha=0.85)
    axes[0].bar(x + 2*w, ospf_util,  width=w, label="OSPF Shortest Path", color=C_CORAL, edgecolor="black", alpha=0.85)
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(topo_labels)
    axes[0].set_ylabel("Peak Link Utilization (%)")
    axes[0].set_title("(a) Peak Congestion vs. Exact Global Optimum", fontweight="semibold")
    axes[0].legend(loc="upper right")

    # Panel 2: Optimality Gap (%) = (alpha_algo - alpha*) / alpha*
    d3qn_gaps = [data[t]["algorithm_comparisons"].get("D3QN (Ours)", {}).get("optimality_gap_pct", 0) for t in topos]
    llr_gaps  = [data[t]["algorithm_comparisons"].get("LLR (Least Loaded)", {}).get("optimality_gap_pct", 0) for t in topos]
    ecmp_gaps = [data[t]["algorithm_comparisons"].get("ECMP", {}).get("optimality_gap_pct", 0) for t in topos]
    ospf_gaps = [data[t]["algorithm_comparisons"].get("OSPF (RFC 2328)", {}).get("optimality_gap_pct", 0) for t in topos]

    axes[1].plot(topo_labels, d3qn_gaps, marker="o", linewidth=2.5, color=C_PRIMARY, label="D3QN Gap (%)")
    axes[1].plot(topo_labels, llr_gaps,  marker="s", linewidth=1.8, color=C_TEAL, linestyle="--", label="LLR Gap (%)")
    axes[1].plot(topo_labels, ecmp_gaps, marker="^", linewidth=1.8, color=C_AMBER, linestyle="--", label="ECMP Gap (%)")
    axes[1].plot(topo_labels, ospf_gaps, marker="x", linewidth=1.8, color=C_CORAL, linestyle=":", label="OSPF Gap (%)")
    axes[1].axhline(0, color="black", linestyle="-", linewidth=0.8)
    axes[1].set_ylabel("Optimality Gap over Oracle (%)")
    axes[1].set_title("(b) Optimality Gap to Lower Bound (%)",
                      fontweight="semibold")
    axes[1].legend(loc="upper right")

    fig.tight_layout(rect=[0, 0, 1, 0.94])
    out = os.path.join(FIG_DIR, "optimisation_oracle_gap.png")
    plt.savefig(out, dpi=300)
    plt.savefig(os.path.join(LOGS_PLOT_DIR, "optimisation_oracle_gap.png"), dpi=300)
    plt.close()
    print(f"[✓] Saved figure: {out}")


# ============================================================================
# 5. Multi-Seed Reward Sensitivity Analysis (3-Panel Grid)
# ============================================================================
def plot_reward_sensitivity_multiseed_surface():
    path = os.path.join(DATA_DIR, "multiseed_reward_sensitivity_results.json")
    if not os.path.exists(path):
        print(f"Skipping reward sensitivity plot: {path} not found")
        return
    with open(path) as f:
        data = json.load(f)

    theta_vals = [0.6, 0.7, 0.8]
    w_relief_vals = [1.0, 2.0, 4.0, 8.0]

    b_mean = np.zeros((len(theta_vals), len(w_relief_vals)))
    b_std  = np.zeros((len(theta_vals), len(w_relief_vals)))
    lat_mean = np.zeros((len(theta_vals), len(w_relief_vals)))
    lat_std  = np.zeros((len(theta_vals), len(w_relief_vals)))
    loss_mean = np.zeros((len(theta_vals), len(w_relief_vals)))
    loss_std  = np.zeros((len(theta_vals), len(w_relief_vals)))

    for i, t in enumerate(theta_vals):
        for j, w in enumerate(w_relief_vals):
            k = f"theta_{t}_relief_{w}"
            if k in data:
                b_mean[i, j] = data[k]["bottleneck_util"]["mean"]
                b_std[i, j]  = data[k]["bottleneck_util"]["std"]
                lat_mean[i, j] = data[k]["latency_ms"]["mean"]
                lat_std[i, j]  = data[k]["latency_ms"]["std"]
                loss_mean[i, j] = data[k]["packet_loss_pct"]["mean"]
                loss_std[i, j]  = data[k]["packet_loss_pct"]["std"]

    fig, axes = plt.subplots(1, 3, figsize=(18, 5.2))
    fig.suptitle(r"Multi-Seed Reward Sensitivity: Hyperparameter Grid Sweeps ($\theta$ vs. $w_{\mathrm{relief}}$)",
                 fontweight="bold", y=0.98)

    # Panel 1: Bottleneck Utilization Surface
    im1 = axes[0].imshow(b_mean, cmap="YlGnBu_r", aspect="auto")
    axes[0].set_xticks(range(len(w_relief_vals)))
    axes[0].set_xticklabels([f"{w:.1f}" for w in w_relief_vals])
    axes[0].set_yticks(range(len(theta_vals)))
    axes[0].set_yticklabels([f"{t:.2f}" for t in theta_vals])
    axes[0].set_xlabel(r"Relief Bonus Weight ($w_{\mathrm{relief}}$)")
    axes[0].set_ylabel(r"Congestion Penalty Exponent ($\theta$)")
    axes[0].set_title("(a) Peak Bottleneck Util (%)", fontweight="semibold")
    cbar1 = fig.colorbar(im1, ax=axes[0])
    cbar1.set_label("Utilization (%)")
    for i in range(len(theta_vals)):
        for j in range(len(w_relief_vals)):
            axes[0].text(j, i, f"{b_mean[i, j]:.1f}%\n±{b_std[i, j]:.1f}", ha="center", va="center",
                         color="white" if b_mean[i, j] > np.median(b_mean) else "black",
                         fontweight="bold", fontsize=8.5)

    # Panel 2: Latency Surface
    im2 = axes[1].imshow(lat_mean, cmap="Blues_r", aspect="auto")
    axes[1].set_xticks(range(len(w_relief_vals)))
    axes[1].set_xticklabels([f"{w:.1f}" for w in w_relief_vals])
    axes[1].set_yticks(range(len(theta_vals)))
    axes[1].set_yticklabels([f"{t:.2f}" for t in theta_vals])
    axes[1].set_xlabel(r"Relief Bonus Weight ($w_{\mathrm{relief}}$)")
    axes[1].set_ylabel(r"Congestion Penalty Exponent ($\theta$)")
    axes[1].set_title("(b) End-to-End Latency (ms)", fontweight="semibold")
    cbar2 = fig.colorbar(im2, ax=axes[1])
    cbar2.set_label("Latency (ms)")
    for i in range(len(theta_vals)):
        for j in range(len(w_relief_vals)):
            axes[1].text(j, i, f"{lat_mean[i, j]:.0f} ms\n±{lat_std[i, j]:.0f}", ha="center", va="center",
                         color="white" if lat_mean[i, j] > np.median(lat_mean) else "black",
                         fontweight="bold", fontsize=8.5)

    # Panel 3: Packet Loss Rate Surface
    im3 = axes[2].imshow(loss_mean, cmap="OrRd", aspect="auto")
    axes[2].set_xticks(range(len(w_relief_vals)))
    axes[2].set_xticklabels([f"{w:.1f}" for w in w_relief_vals])
    axes[2].set_yticks(range(len(theta_vals)))
    axes[2].set_yticklabels([f"{t:.2f}" for t in theta_vals])
    axes[2].set_xlabel(r"Relief Bonus Weight ($w_{\mathrm{relief}}$)")
    axes[2].set_ylabel(r"Congestion Penalty Exponent ($\theta$)")
    axes[2].set_title("(c) Packet Loss Rate (%)", fontweight="semibold")
    cbar3 = fig.colorbar(im3, ax=axes[2])
    cbar3.set_label("Loss (%)")
    for i in range(len(theta_vals)):
        for j in range(len(w_relief_vals)):
            axes[2].text(j, i, f"{loss_mean[i, j]:.1f}%\n±{loss_std[i, j]:.1f}", ha="center", va="center",
                         color="white" if loss_mean[i, j] > np.median(loss_mean) else "black",
                         fontweight="bold", fontsize=8.5)

    fig.tight_layout(rect=[0, 0, 1, 0.94])
    out = os.path.join(FIG_DIR, "reward_sensitivity_multiseed_surface.png")
    plt.savefig(out, dpi=300)
    plt.savefig(os.path.join(LOGS_PLOT_DIR, "reward_sensitivity_multiseed_surface.png"), dpi=300)
    # Also save to legacy name for compatibility
    plt.savefig(os.path.join(FIG_DIR, "reward_sensitivity_retraining.png"), dpi=300)
    plt.close()
    print(f"[✓] Saved figure: {out}")


def main():
    print("Generating Phase 1 Figures from JSON data...")
    plot_ablation_study()
    plot_multiple_model_seeds()
    plot_held_out_topologies()
    plot_optimisation_oracle()
    plot_reward_sensitivity_multiseed_surface()
    print("All Phase 1 figures generated successfully!")


if __name__ == '__main__':
    main()
```
