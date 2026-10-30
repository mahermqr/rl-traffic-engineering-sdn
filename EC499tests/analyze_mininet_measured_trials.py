#!/usr/bin/env python3
"""Analyze measured Mininet trials without manufacturing missing observations."""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np


_curr = Path(__file__).resolve().parent
BASE_DIR = _curr if (_curr / "agent").exists() else _curr.parent
METRICS = {
    "throughput_mbps": True,
    "loss_pct": False,
    "packet_loss_pct": False,
    "jitter_ms": False,
    "rtt_avg_ms": False,
    "controller_decision_mean_ms": False,
}


def percentile_interval(samples: np.ndarray) -> list[float]:
    low, high = np.percentile(samples, [2.5, 97.5])
    return [float(low), float(high)]


def bootstrap_mean(values: list[float], rng: np.random.Generator, iterations: int) -> list[float] | None:
    array = np.asarray(values, dtype=float)
    if array.size < 2:
        return None
    indices = rng.integers(0, array.size, size=(iterations, array.size))
    return percentile_interval(array[indices].mean(axis=1))


def bootstrap_paired(values: list[float], rng: np.random.Generator, iterations: int) -> list[float] | None:
    return bootstrap_mean(values, rng, iterations)


def load_trials(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    trials = [row for row in payload.get("trials", []) if row.get("status") == "success"]
    if not trials:
        raise SystemExit("No successful measured trials are present; analysis was not generated.")
    return payload.get("environment", {}), trials


def summarize(
    trials: list[dict[str, Any]], seed: int, iterations: int
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rng = np.random.default_rng(seed)
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in trials:
        grouped[(row["topology"], row["protocol"], row["policy"])].append(row)

    summaries: list[dict[str, Any]] = []
    for (topology, protocol, policy), rows in sorted(grouped.items()):
        summary: dict[str, Any] = {
            "topology": topology,
            "protocol": protocol,
            "policy": policy,
            "n": len(rows),
        }
        for metric in METRICS:
            values = [float(row[metric]) for row in rows if row.get(metric) is not None]
            summary[metric] = {
                "n": len(values),
                "mean": float(np.mean(values)) if values else None,
                "sd": float(np.std(values, ddof=1)) if len(values) > 1 else None,
                "bootstrap_95_ci": bootstrap_mean(values, rng, iterations),
            }
        summaries.append(summary)

    indexed = {
        (int(row["replicate"]), row["topology"], row["protocol"], row["policy"]): row
        for row in trials
    }
    comparisons: list[dict[str, Any]] = []
    cells = sorted({(row["topology"], row["protocol"]) for row in trials})
    for topology, protocol in cells:
        for baseline in ("llr", "spf"):
            comparison: dict[str, Any] = {
                "topology": topology,
                "protocol": protocol,
                "comparison": f"d3qn_vs_{baseline}",
            }
            for metric, higher_is_better in METRICS.items():
                differences: list[float] = []
                replicate_ids = sorted({int(row["replicate"]) for row in trials})
                for replicate in replicate_ids:
                    learned = indexed.get((replicate, topology, protocol, "d3qn"))
                    reference = indexed.get((replicate, topology, protocol, baseline))
                    if not learned or not reference:
                        continue
                    if learned.get(metric) is None or reference.get(metric) is None:
                        continue
                    raw = float(learned[metric]) - float(reference[metric])
                    differences.append(raw if higher_is_better else -raw)
                comparison[metric] = {
                    "n_pairs": len(differences),
                    "mean_improvement": float(np.mean(differences)) if differences else None,
                    "bootstrap_95_ci": bootstrap_paired(differences, rng, iterations),
                }
            comparisons.append(comparison)
    return summaries, comparisons


def write_figure(summaries: list[dict[str, Any]], path: Path) -> None:
    policies = ["spf", "llr", "d3qn"]
    cells = sorted({(row["topology"], row["protocol"]) for row in summaries})
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), constrained_layout=True)
    colors = {"spf": "#777777", "llr": "#2f78b7", "d3qn": "#d97706"}
    for axis, metric, label in zip(
        axes,
        ("throughput_mbps", "loss_pct"),
        ("Throughput (Mbit/s)", "UDP loss (%)"),
    ):
        width = 0.24
        x = np.arange(len(cells))
        for offset, policy in enumerate(policies):
            values = []
            for topology, protocol in cells:
                row = next(
                    (item for item in summaries if item["topology"] == topology
                     and item["protocol"] == protocol and item["policy"] == policy),
                    None,
                )
                values.append(row[metric]["mean"] if row and row[metric]["mean"] is not None else np.nan)
            axis.bar(x + (offset - 1) * width, values, width, label=policy.upper(), color=colors[policy])
        axis.set_xticks(x, [f"{topology}\n{protocol.upper()}" for topology, protocol in cells])
        axis.set_ylabel(label)
        axis.grid(axis="y", alpha=0.25)
    axes[0].legend(frameon=False, ncol=3)
    fig.suptitle("Measured Mininet/OVS Trial Summary")
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=300)
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=BASE_DIR / "EC499report" / "report_artifacts" / "data" / "mininet_measured_trials.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=BASE_DIR / "EC499report" / "report_artifacts" / "data" / "mininet_measured_analysis.json",
    )
    parser.add_argument(
        "--figure",
        type=Path,
        default=BASE_DIR / "EC499report" / "report_artifacts" / "figures" / "mininet_measured_trials.png",
    )
    parser.add_argument("--bootstrap-iterations", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=2026)
    args = parser.parse_args()
    environment, trials = load_trials(args.input)
    summaries, comparisons = summarize(trials, args.seed, args.bootstrap_iterations)
    payload = {
        "schema_version": 1,
        "source_run_id": environment.get("run_id"),
        "successful_trials": len(trials),
        "bootstrap_iterations": args.bootstrap_iterations,
        "bootstrap_seed": args.seed,
        "summaries": summaries,
        "paired_comparisons": comparisons,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_figure(summaries, args.figure)
    print(f"Analysis: {args.output}")
    print(f"Figure:   {args.figure}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
