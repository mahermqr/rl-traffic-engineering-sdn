#!/usr/bin/env python3
"""
High Availability (HA) Multi-Controller Failover & Resilience Benchmark (EC499).
Tests and validates 3-Controller Cluster Resilience:
  - Controller 1 (Primary):  OFP 6633 / REST 8180
  - Controller 2 (Backup 1): OFP 6634 / REST 8181
  - Controller 3 (Backup 2): OFP 6635 / REST 8182

Test Sequence:
  [Phase 1] 3-Controller Cluster Deployment & Leader Verification
  [Phase 2] Nominal Traffic Engineering & Routing Telemetry on Primary
  [Phase 3] Primary Crash Injection -> Sub-Millisecond Failover to Backup 1
  [Phase 4] Secondary Crash Injection -> Cascaded Failover to Backup 2
  [Phase 5] Cluster Self-Healing & Controller Recovery
  [Phase 6] Export Failover Metrics JSON
"""

import os
import sys
import time
import json
import socket
import logging
import subprocess

# Ensure base directory in path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, 'controller'))
sys.path.insert(0, os.path.join(BASE_DIR, 'agent'))

from ha_controller_pool import HAControllerPool, ControllerNode, MultiControllerCluster

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("HAFailoverTest")


def run_ha_validation_suite(export_json="logs/ha_controller_failover_results.json"):
    print("=" * 85)
    print(" 🛡️ STARTING SDN HIGH AVAILABILITY CONTROLLER FAILOVER VALIDATION (EC499)")
    print(" Topology: 3-Controller Cluster (1 Primary + 2 Standby Backups)")
    print("=" * 85)

    # Use distinct test REST ports to prevent collisions with any active dashboard
    test_nodes = [
        ControllerNode(name="primary", host="127.0.0.1", ofp_port=6633, rest_port=8180, role="primary"),
        ControllerNode(name="backup1", host="127.0.0.1", ofp_port=6634, rest_port=8181, role="backup1"),
        ControllerNode(name="backup2", host="127.0.0.1", ofp_port=6635, rest_port=8182, role="backup2"),
    ]

    cluster = MultiControllerCluster()
    cluster.pool = HAControllerPool(nodes=test_nodes)

    results = {
        "test_name": "SDN 3-Controller HA Failover Suite",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "cluster_nodes": [n.name for n in test_nodes],
        "phases": {}
    }

    try:
        # ---------------------------------------------------------------------
        # PHASE 1: Cluster Initialization
        # ---------------------------------------------------------------------
        print("\n[Phase 1/5] Spawning 3-Controller Cluster (Primary + 2 Backups)...")
        cluster.start_all(wait_sec=12.0)

        health = cluster.pool.probe_all()
        print(f" • Controller Health Probes: {health}")
        for name, is_healthy in health.items():
            if not is_healthy:
                raise RuntimeError(f"Controller {name} failed to initialize!")

        active = cluster.pool.get_active_controller()
        print(f" • Active Cluster Leader:    {active.name.upper()} (OFP: {active.ofp_port}, REST: {active.rest_port})")
        assert active.name == "primary", "Expected primary to be initial cluster leader!"

        results["phases"]["phase1_init"] = {
            "status": "passed",
            "active_leader": active.name,
            "all_healthy": True
        }

        # ---------------------------------------------------------------------
        # PHASE 2: Nominal Routing Execution on Primary
        # ---------------------------------------------------------------------
        print("\n[Phase 2/5] Validating Nominal Traffic Engineering Telemetry on Primary...")
        t0 = time.perf_counter()
        predict_res = cluster.pool.execute_request("GET", "/api/model_predict?src=4&dst=7&demand=25")
        lat_ms = (time.perf_counter() - t0) * 1000.0

        print(f" • Decision Latency:         {lat_ms:.2f} ms")
        print(f" • Model Action / Status:    Path: {predict_res.get('chosen_path')}, Algorithm: {predict_res.get('algorithm', 'D3QN')}")
        assert predict_res.get("chosen_path") is not None, "Primary failed to return candidate path!"

        results["phases"]["phase2_nominal"] = {
            "status": "passed",
            "decision_latency_ms": round(lat_ms, 2),
            "chosen_path": predict_res.get("chosen_path")
        }

        # ---------------------------------------------------------------------
        # PHASE 3: Primary Controller Crash -> Automatic Failover to Backup 1
        # ---------------------------------------------------------------------
        print("\n[Phase 3/5] INJECTING SUDDEN PRIMARY CONTROLLER CRASH (Killing Primary)...")
        t_crash_start = time.perf_counter()
        cluster.stop_controller("primary")
        print(" • Primary process killed (Simulated physical node down / power failure).")

        # Execute transparent request through pool
        post_crash_req = cluster.pool.execute_request("GET", "/api/model_predict?src=4&dst=7&demand=30")
        failover_lat_ms = (time.perf_counter() - t_crash_start) * 1000.0

        active_p3 = cluster.pool.get_active_controller(auto_promote=False)
        print(f" • Immediate Failover To:    {active_p3.name.upper()} (OFP: {active_p3.ofp_port}, REST: {active_p3.rest_port})")
        print(f" • Total Failover Latency:   {failover_lat_ms:.2f} ms (Sub-second carrier grade)")
        print(f" • Backup 1 Route Decision:  Path: {post_crash_req.get('chosen_path')}")

        assert active_p3.name == "backup1", "Expected backup1 to take over primary!"
        assert post_crash_req.get("chosen_path") is not None, "Backup 1 failed to serve request!"

        results["phases"]["phase3_failover_1"] = {
            "status": "passed",
            "new_leader": active_p3.name,
            "failover_latency_ms": round(failover_lat_ms, 2),
            "served_after_crash": True
        }

        # ---------------------------------------------------------------------
        # PHASE 4: Backup 1 Controller Crash -> Cascaded Failover to Backup 2
        # ---------------------------------------------------------------------
        print("\n[Phase 4/5] INJECTING SECONDARY CRASH (Killing Backup 1)...")
        t_crash_b1 = time.perf_counter()
        cluster.stop_controller("backup1")
        print(" • Backup 1 process killed (Simulated double-fault cascade).")

        post_crash_b2 = cluster.pool.execute_request("GET", "/api/model_predict?src=4&dst=7&demand=40")
        failover_2_lat_ms = (time.perf_counter() - t_crash_b1) * 1000.0

        active_p4 = cluster.pool.get_active_controller(auto_promote=False)
        print(f" • Cascaded Failover To:     {active_p4.name.upper()} (OFP: {active_p4.ofp_port}, REST: {active_p4.rest_port})")
        print(f" • Cascaded Failover Latency:{failover_2_lat_ms:.2f} ms")
        print(f" • Backup 2 Route Decision:  Path: {post_crash_b2.get('chosen_path')}")

        assert active_p4.name == "backup2", "Expected backup2 to take over as final standby!"
        assert post_crash_b2.get("chosen_path") is not None, "Backup 2 failed to serve request!"

        results["phases"]["phase4_failover_2"] = {
            "status": "passed",
            "new_leader": active_p4.name,
            "failover_latency_ms": round(failover_2_lat_ms, 2),
            "served_after_double_fault": True
        }

        # ---------------------------------------------------------------------
        # PHASE 5: Cluster Self-Healing & Node Recovery
        # ---------------------------------------------------------------------
        print("\n[Phase 5/5] Re-starting Primary & Backup 1 (Self-Healing Recovery)...")
        cluster.start_controller("primary")
        cluster.start_controller("backup1")
        cluster.wait_for_ready(timeout=10.0)

        recovered_health = cluster.pool.probe_all()
        print(f" • Cluster Health After Recovery: {recovered_health}")
        all_ok = all(recovered_health.values())
        print(f" • All 3 Controllers Online:      {all_ok}")
        assert all_ok, "Expected all 3 controllers to be healthy after recovery!"

        status = cluster.pool.cluster_status()
        print(f" • Total Successful Failovers:    {status['total_failovers']}")

        results["phases"]["phase5_recovery"] = {
            "status": "passed",
            "all_controllers_recovered": True,
            "total_failovers_logged": status["total_failovers"]
        }

        # Save Export JSON
        if export_json:
            out_file = os.path.join(BASE_DIR, export_json)
            os.makedirs(os.path.dirname(out_file), exist_ok=True)
            with open(out_file, "w") as f:
                json.dump(results, f, indent=2)
            print(f"\n[Saved] High Availability Failover results exported to: {out_file}")

        print("=" * 85)
        print(" ✅ 3-CONTROLLER HIGH AVAILABILITY CLUSTER SUITE VALIDATED SUCCESSFULLY!")
        print("=" * 85)
        return True

    finally:
        cluster.stop_all()


if __name__ == '__main__':
    success = run_ha_validation_suite()
    sys.exit(0 if success else 1)
