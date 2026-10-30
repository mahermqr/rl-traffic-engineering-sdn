#!/usr/bin/env python3
"""Typed orchestration entry point for all benchmark suites."""

import argparse

from benchmark_routing_algorithms import run_routing_tournament
from stress_test_load_balancer import run_stress_tests
from stress_test_blind_topologies import run_blind_topology_stress_tests


def main():
    parser = argparse.ArgumentParser(description="Run the EC499 benchmark and stress suites")
    parser.add_argument('--model-path')
    parser.add_argument('--plots-dir')
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--topologies', nargs='+')
    parser.add_argument('--tournament-json')
    parser.add_argument('--stress-json')
    parser.add_argument('--blind-json')
    parser.add_argument('--samples', type=int, default=100)
    parser.add_argument('--burst-flows', type=int, default=500)
    args = parser.parse_args()

    run_routing_tournament(
        model_path=args.model_path, json_path=args.tournament_json,
        plots_dir=args.plots_dir, topologies=args.topologies, seed=args.seed,
    )
    run_stress_tests(
        model_path=args.model_path, json_path=args.stress_json,
        plots_dir=args.plots_dir, n_samples=args.samples,
        n_burst=args.burst_flows, seed=args.seed,
    )
    run_blind_topology_stress_tests(
        model_path=args.model_path, json_path=args.blind_json,
        plots_dir=args.plots_dir, topologies=args.topologies,
        burst_flows=args.burst_flows, seed=args.seed,
    )


if __name__ == '__main__':
    main()
