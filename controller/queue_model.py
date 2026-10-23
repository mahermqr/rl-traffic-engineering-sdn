"""Finite-buffer queueing utilities shared by telemetry and benchmarks."""

from __future__ import annotations

import math
from typing import Dict


def mm1k_metrics(rho: float, queue_depth: int = 256, service_time_ms: float = 1.0,
                 max_queue_delay_ms: float = 1000.0) -> Dict[str, float]:
    """Return stable M/M/1/K blocking and delay estimates.

    ``rho`` is offered load divided by service capacity and may exceed one.  The
    finite buffer keeps the Markov chain stationary even in that case.  Delay is
    derived from Little's law using accepted arrivals, then bounded for display
    and numerical safety.
    """
    rho = max(0.0, float(rho))
    k = max(1, int(queue_depth))
    service_ms = max(1e-6, float(service_time_ms))

    if rho == 0.0:
        return {
            "blocking_probability": 0.0,
            "loss_pct": 0.0,
            "mean_system_size": 0.0,
            "queue_delay_ms": 0.0,
        }

    if math.isclose(rho, 1.0, rel_tol=1e-9, abs_tol=1e-12):
        p_block = 1.0 / (k + 1.0)
        mean_n = k / 2.0
    elif rho < 1.0:
        rho_k = rho ** k
        rho_k1 = rho_k * rho
        denom = 1.0 - rho_k1
        p_block = ((1.0 - rho) * rho_k) / max(1e-300, denom)
        mean_n = (
            rho * (1.0 - (k + 1.0) * rho_k + k * rho_k1)
            / max(1e-300, (1.0 - rho) * denom)
        )
    else:
        # Algebraically equivalent forms using negative powers avoid overflow.
        inv_rho_k = rho ** (-k)
        inv_rho_k1 = inv_rho_k / rho
        p_block = (rho - 1.0) / max(1e-300, rho - inv_rho_k)
        mean_n = (
            rho * (inv_rho_k1 - (k + 1.0) / rho + k)
            / max(1e-300, (1.0 - rho) * (inv_rho_k1 - 1.0))
        )

    p_block = min(1.0, max(0.0, float(p_block)))
    accepted_load = rho * (1.0 - p_block)
    system_time_units = mean_n / max(1e-12, accepted_load)
    queue_delay_ms = max(0.0, (system_time_units - 1.0) * service_ms)
    queue_delay_ms = min(float(max_queue_delay_ms), queue_delay_ms)

    return {
        "blocking_probability": p_block,
        "loss_pct": p_block * 100.0,
        "mean_system_size": max(0.0, float(mean_n)),
        "queue_delay_ms": float(queue_delay_ms),
    }

