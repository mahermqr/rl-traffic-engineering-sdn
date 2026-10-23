"""Canonical D3QN path selection used by live routing and every benchmark."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

import numpy as np

try:
    from traditional_routing import compute_path_metrics
except ImportError:  # package import
    from controller.traditional_routing import compute_path_metrics


def select_dqn_path(agent: Any, state_manager: Any, src: int, dst: int,
                    candidate_paths: Optional[Sequence[Sequence[int]]] = None,
                    demand_mbps: Optional[float] = None,
                    mode: str = "pure") -> Dict[str, Any]:
    """Select a valid candidate with a single, reusable policy definition.

    ``pure`` measures the learned D3QN policy without post-processing.
    ``safety`` applies an explicitly labelled deterministic capacity guard.  The
    latter is useful in deployment but must not be reported as a pure D3QN result.
    """
    paths = [list(p) for p in (candidate_paths or state_manager.get_candidate_paths(src, dst))]
    paths = [p for p in paths if len(p) > 1 and all(state_manager.graph.has_edge(u, v) for u, v in zip(p, p[1:]))]
    if not paths:
        return {
            "status": "no_route", "path": None, "action": None,
            "q_values": [], "scores": [], "mode": mode,
        }

    state = state_manager.get_routing_state(src, dst)
    q_values = list(agent.get_q_values(state))
    selectable = min(len(paths), len(q_values))
    if selectable <= 0:
        return {
            "status": "no_action", "path": None, "action": None,
            "q_values": q_values, "scores": [], "mode": mode,
        }

    mode = str(mode or "pure").strip().lower()
    if mode not in {"pure", "safety"}:
        raise ValueError(f"Unsupported DQN policy mode: {mode}")

    if mode == "pure":
        scores = [float(v) for v in q_values[:selectable]]
    else:
        q_arr = np.asarray(q_values[:selectable], dtype=np.float64)
        q_span = max(1e-6, float(np.ptp(q_arr)))
        q_norm = (q_arr - float(np.min(q_arr))) / q_span
        demand = max(0.0, float(demand_mbps or getattr(state_manager, "traffic_flow_rate_mbps", 0.0)))
        scores = []
        for idx, path in enumerate(paths[:selectable]):
            metrics = compute_path_metrics(
                path, state_manager.link_utilization, state_manager.link_delays,
                state_manager.link_bandwidths,
                queue_depth=getattr(state_manager, "switch_queue_depth", 256),
            )
            projected = 0.0
            for u, v in zip(path, path[1:]):
                capacity = max(1.0, float(state_manager.link_bandwidths.get((u, v), 100.0)))
                projected = max(projected, state_manager.get_effective_utilization((u, v)) + demand / capacity)
            barrier = 40.0 * max(0.0, projected - 0.70) ** 2
            cost = (
                barrier
                + 0.35 * metrics["total_delay"]
                + 2.5 * metrics["packet_loss"]
                + 0.5 * max(0, metrics["hops"] - 1)
            )
            scores.append(float(q_norm[idx]) - cost)

    action = int(np.argmax(np.asarray(scores, dtype=np.float64)))
    return {
        "status": "success",
        "path": paths[action],
        "action": action,
        "q_values": [float(v) for v in q_values],
        "scores": scores,
        "state": state,
        "mode": mode,
    }

