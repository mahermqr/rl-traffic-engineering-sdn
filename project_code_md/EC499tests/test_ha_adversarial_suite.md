# `EC499tests/test_ha_adversarial_suite.py`

> **File:** `EC499tests/test_ha_adversarial_suite.py`  
> **Subsystem / Category:** 9. Publications, Documentation & Slide Generation  
> **Language:** `python`  
> **Lines of Code:** 538  
> **File Size:** 25.37 KB  

---

## Overview

Source code implementation for test_ha_adversarial_suite.py.

### Architecture & Symbols
- **Classes:** `TestHAAdversarialSuite`
- **Key Functions:** None (Module level / Declarative)

---

## Source Code

```python
#!/usr/bin/env python3
"""
Adversarial Stress Test Suite for Carrier-Grade High Availability (HA) Clustering (EC499).
Empirical Challenger 2 Test Harness.

Tests 4 Core Adversarial Dimensions:
  1. High-frequency crash/recover flapping under continuous concurrent HTTP traffic load.
  2. Split-brain resistance & priority ordering: exhaustive 2^N state-space validation,
     concurrent election race probing, and priority preemption analysis.
  3. Fail-Secure Autonomous Mode: total 3-controller outage simulation and flow table survival oracle.
  4. Sub-50ms carrier-grade failover latency verification under multi-threaded stress.
"""

import os
import sys
import time
import json
import socket
import random
import unittest
import threading
import subprocess
import urllib.request
import urllib.error
from typing import List, Dict, Any, Optional

# Ensure project paths
TEST_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(TEST_DIR) if os.path.exists(os.path.join(os.path.dirname(TEST_DIR), 'controller')) else TEST_DIR
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, 'controller'))
sys.path.insert(0, os.path.join(BASE_DIR, 'agent'))

from ha_controller_pool import HAControllerPool, ControllerNode, MultiControllerCluster
import web_dashboard


class TestHAAdversarialSuite(unittest.TestCase):
    """Adversarial Challenge Test Harness for HA Clustering."""

    @classmethod
    def setUpClass(cls):
        # We test against the primary live dashboard (port 8080) for REST state operations,
        # and spawn isolated MultiControllerCluster on ports 8280, 8281, 8282 for process tests.
        cls.live_base_url = "http://127.0.0.1:8080"
        cls.has_live_server = cls._check_url(f"{cls.live_base_url}/api/health")
        if not cls.has_live_server:
            # Fallback to local server if 8080 is not available
            cls.dashboard_inst = web_dashboard.DashboardServer(
                logger=None, host="127.0.0.1", port=8199
            )
            time.sleep(0.5)
            cls.live_base_url = "http://127.0.0.1:8199"

    @classmethod
    def _check_url(cls, url: str) -> bool:
        try:
            req = urllib.request.Request(url, method='GET')
            with urllib.request.urlopen(req, timeout=1.0) as resp:
                return resp.status == 200
        except Exception:
            return False

    def _http_get(self, path: str, timeout: float = 3.0) -> Dict[str, Any]:
        url = f"{self.live_base_url}{path}"
        req = urllib.request.Request(url, headers={'User-Agent': 'EmpiricalChallenger-HA'}, method='GET')
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode('utf-8'))

    def _http_post(self, path: str, payload: Optional[Dict] = None, timeout: float = 3.0) -> Dict[str, Any]:
        url = f"{self.live_base_url}{path}"
        data = json.dumps(payload).encode('utf-8') if payload else b""
        headers = {'Content-Type': 'application/json', 'User-Agent': 'EmpiricalChallenger-HA'}
        req = urllib.request.Request(url, data=data, headers=headers, method='POST')
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode('utf-8'))

    def setUp(self):
        # Ensure cluster is nominal before each test
        try:
            self._http_post("/api/simulate/controller_recover?target=all")
        except Exception:
            pass

    def tearDown(self):
        # Restore nominal cluster state after each test
        try:
            self._http_post("/api/simulate/controller_recover?target=all")
        except Exception:
            pass

    # =========================================================================
    # 1. HIGH-FREQUENCY FLAPPING UNDER CONTINUOUS CONCURRENT TRAFFIC LOAD
    # =========================================================================
    def test_01_high_frequency_flapping_under_continuous_traffic(self):
        """
        Adversarial Test 1: High-Frequency Flapping under Heavy Multi-Threaded Load.
        Continuously bombards the controller cluster with concurrent requests
        while injecting rapid crash/recover flapping cycles across all nodes.
        """
        print("\n" + "=" * 70)
        print(" [CHALLENGE 1] High-Frequency Flapping Under Continuous Load")
        print("=" * 70)

        num_worker_threads = 8
        duration_sec = 4.0
        stop_event = threading.Event()
        request_stats = {"success": 0, "fail_secure_handled": 0, "errors": 0, "exceptions": []}
        stats_lock = threading.Lock()

        # Target endpoints to hammer
        endpoints = [
            "/api/ha/status",
            "/api/telemetry",
            "/api/model_predict?src=4&dst=7&demand=20",
            "/api/flows"
        ]

        def traffic_worker(worker_id):
            while not stop_event.is_set():
                ep = random.choice(endpoints)
                try:
                    res = self._http_get(ep, timeout=1.5)
                    with stats_lock:
                        request_stats["success"] += 1
                except urllib.error.HTTPError as he:
                    with stats_lock:
                        request_stats["errors"] += 1
                        request_stats["exceptions"].append(f"HTTPError {he.code} on {ep}")
                except Exception as e:
                    # In total outage, some connections might fail if not retried
                    with stats_lock:
                        request_stats["errors"] += 1
                        request_stats["exceptions"].append(f"{type(e).__name__}: {e}")
                time.sleep(random.uniform(0.005, 0.020))

        # Start traffic threads
        workers = [threading.Thread(target=traffic_worker, args=(i,), daemon=True) for i in range(num_worker_threads)]
        for w in workers:
            w.start()

        # Flapping loop
        flap_actions = [
            ("fail", "primary"),
            ("recover", "primary"),
            ("fail", "backup1"),
            ("recover", "backup1"),
            ("fail", "primary"),
            ("fail", "backup1"),
            ("recover", "primary"),
            ("recover", "backup1"),
            ("fail", "all"),
            ("recover", "all"),
        ]

        flap_count = 0
        t_start = time.time()
        while time.time() - t_start < duration_sec:
            action, target = random.choice(flap_actions)
            if action == "fail":
                self._http_post(f"/api/simulate/controller_fail?target={target}")
            else:
                self._http_post(f"/api/simulate/controller_recover?target={target}")
            flap_count += 1
            time.sleep(random.uniform(0.02, 0.05))

        stop_event.set()
        for w in workers:
            w.join(timeout=1.0)

        # Restore nominal state
        self._http_post("/api/simulate/controller_recover?target=all")
        status = self._http_get("/api/ha/status")

        print(f" • Executed {flap_count} high-frequency flap transitions in {duration_sec:.1f}s")
        print(f" • Client requests completed: {request_stats['success']} successful, {request_stats['errors']} errors")
        print(f" • Final cluster state: {status.get('cluster_status')} (Active Leader: {status.get('active_leader')})")

        self.assertEqual(status.get("active_leader"), "primary", "Cluster failed to restore Primary after flapping!")
        self.assertEqual(status.get("cluster_status"), "NOMINAL", "Cluster did not return to NOMINAL after recovery!")
        self.assertGreater(request_stats["success"], 50, "Traffic workers failed to complete sufficient requests")
        self.assertEqual(len(request_stats["exceptions"]), 0, f"Encountered unexpected unhandled exceptions: {request_stats['exceptions'][:5]}")

    # =========================================================================
    # 2. SPLIT-BRAIN RESISTANCE & DETERMINISTIC PRIORITY ORDERING
    # =========================================================================
    def test_02_split_brain_exhaustive_truth_table(self):
        """
        Adversarial Test 2.1: Exhaustive 2^N State-Space Truth Table Search.
        Validates that across all 2^3 = 8 alive/dead node combinations,
        the cluster strictly maintains Split-Brain Index S <= 1 (exactly 1 master if >= 1 alive,
        and exactly 0 masters if all dead).
        """
        print("\n" + "=" * 70)
        print(" [CHALLENGE 2.1] Split-Brain Exhaustive Truth Table (2^3 States)")
        print("=" * 70)

        nodes = ["primary", "backup1", "backup2"]
        states_tested = 0

        # Iterate all 8 states: (P, B1, B2)
        for p_alive in [True, False]:
            for b1_alive in [True, False]:
                for b2_alive in [True, False]:
                    state_map = {"primary": p_alive, "backup1": b1_alive, "backup2": b2_alive}

                    # Apply state
                    for nid, is_alive in state_map.items():
                        if is_alive:
                            self._http_post(f"/api/simulate/controller_recover?target={nid}")
                        else:
                            self._http_post(f"/api/simulate/controller_fail?target={nid}")

                    status = self._http_get("/api/ha/status")
                    nodes_detail = status.get("nodes_detail", [])
                    active_leader = status.get("active_leader")

                    # Count how many nodes claim to be MASTER
                    masters = [n for n in nodes_detail if n.get("role") == "MASTER"]
                    master_count = len(masters)

                    # Determine expected leader based on strict priority ordering
                    if p_alive:
                        expected_leader = "primary"
                    elif b1_alive:
                        expected_leader = "backup1"
                    elif b2_alive:
                        expected_leader = "backup2"
                    else:
                        expected_leader = "none"

                    # INVARIANT 1: Split-Brain Index S <= 1
                    if expected_leader == "none":
                        self.assertEqual(master_count, 0, f"Split-brain! Found masters when all dead: {masters}")
                        self.assertEqual(active_leader, "none")
                    else:
                        self.assertEqual(master_count, 1, f"Split-brain violation! Found {master_count} masters: {masters}")
                        self.assertEqual(active_leader, expected_leader,
                                         f"Priority Inversion! State {state_map} expected {expected_leader}, got {active_leader}")
                        self.assertEqual(masters[0]["id"], expected_leader)

                    states_tested += 1

        print(f" • Verified {states_tested}/8 combinatorial states. Split-brain index strictly S <= 1 everywhere.")

    def test_03_priority_preemption_inversion_probe(self):
        """
        Adversarial Test 2.2: Priority Preemption Inversion Probe.
        Probes the system for priority inversion when an intermediate priority node recovers.
        Sequence: Primary dead -> Backup1 dead -> Backup2 active.
        Action: Backup1 recovers while Primary is still dead.
        Oracle: Backup1 (Priority 2) MUST preempt Backup2 (Priority 3).
        """
        print("\n" + "=" * 70)
        print(" [CHALLENGE 2.2] Priority Preemption Inversion Probe")
        print("=" * 70)

        # 1. Fail Primary -> Backup1 promoted
        self._http_post("/api/simulate/controller_fail?target=primary")
        s1 = self._http_get("/api/ha/status")
        self.assertEqual(s1.get("active_leader"), "backup1")

        # 2. Fail Backup1 -> Backup2 promoted
        self._http_post("/api/simulate/controller_fail?target=backup1")
        s2 = self._http_get("/api/ha/status")
        self.assertEqual(s2.get("active_leader"), "backup2")
        self.assertEqual(s2.get("cluster_mode"), "DEGRADED_STANDBY_FAILOVER")

        # 3. Recover Backup1 while Primary remains DEAD
        rec_res = self._http_post("/api/simulate/controller_recover?target=backup1")
        s3 = self._http_get("/api/ha/status")

        print(f" • After Backup1 recovery (Primary still dead): Active Leader = {s3.get('active_leader')}")
        self.assertEqual(s3.get("active_leader"), "backup1",
                         "Priority Inversion Bug! Backup1 failed to preempt lower-priority Backup2!")

        # 4. Now recover Primary -> Primary MUST preempt Backup1
        self._http_post("/api/simulate/controller_recover?target=primary")
        s4 = self._http_get("/api/ha/status")
        print(f" • After Primary recovery: Active Leader = {s4.get('active_leader')}")
        self.assertEqual(s4.get("active_leader"), "primary",
                         "Priority Inversion Bug! Primary failed to preempt Backup1!")

    def test_04_concurrent_failover_race_condition_probe(self):
        """
        Adversarial Test 2.3: Concurrent Failover Race Condition Probe.
        Simultaneously triggers multiple failover requests across 10 threads
        to attempt to induce multi-master split-brain or inconsistent state.
        """
        print("\n" + "=" * 70)
        print(" [CHALLENGE 2.3] Concurrent Failover Race Condition Probe")
        print("=" * 70)

        race_threads = 10
        barrier = threading.Barrier(race_threads)
        results = []

        def race_worker():
            barrier.wait()
            try:
                res = self._http_post("/api/simulate/controller_fail?target=primary")
                results.append(res)
            except Exception as e:
                results.append({"error": str(e)})

        threads = [threading.Thread(target=race_worker) for _ in range(race_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Check post-race cluster status
        status = self._http_get("/api/ha/status")
        masters = [n for n in status.get("nodes_detail", []) if n.get("role") == "MASTER"]
        print(f" • Completed {race_threads} simultaneous failover triggers.")
        print(f" • Post-race active leader: {status.get('active_leader')}, Masters count: {len(masters)}")

        self.assertEqual(len(masters), 1, f"Split-brain detected during race! Found {len(masters)} masters.")
        self.assertEqual(status.get("active_leader"), "backup1")

    # =========================================================================
    # 3. FAIL-SECURE AUTONOMOUS MODE TOTAL OUTAGE & FLOW TABLE SURVIVAL
    # =========================================================================
    def test_05_fail_secure_autonomous_mode_and_flow_survival(self):
        """
        Adversarial Test 3: Total 3-Controller Outage & Flow Table Survival.
        Simulates total catastrophic failure of all 3 SDN controllers.
        Verifies:
          - Data plane transitions to FAIL_SECURE_AUTONOMOUS.
          - Cluster mode is CRITICAL_ALL_DOWN.
          - Pre-installed flows in flow table survive without loss.
          - New dynamic flow installations are safely blocked.
          - Cluster successfully recovers via self-healing.
        """
        print("\n" + "=" * 70)
        print(" [CHALLENGE 3] Fail-Secure Autonomous Mode & Flow Table Survival")
        print("=" * 70)

        # 1. Install 5 distinct dynamic flows into the data plane
        test_flows = [
            (1, 4, 15.0),
            (2, 5, 20.0),
            (3, 6, 25.0),
            (4, 7, 30.0),
            (1, 7, 35.0),
        ]
        installed_count = 0
        for src, dst, demand in test_flows:
            res = self._http_post(f"/api/simulate/apply_flow?src={src}&dst={dst}&demand={demand}&duration=60.0")
            if res.get("status") == "success":
                installed_count += 1

        self.assertGreater(installed_count, 0, "Failed to pre-install test flows!")

        # Query and snapshot existing flows
        initial_flows = self._http_get("/api/flows")
        initial_flow_count = len(initial_flows)
        print(f" • Pre-outage active flow records in data plane: {initial_flow_count}")
        self.assertGreaterEqual(initial_flow_count, installed_count)

        # 2. Trigger Total Outage: Kill all 3 controllers
        outage_res = self._http_post("/api/simulate/controller_fail?target=all")
        print(f" • Injected Total Catastrophic Cluster Failure: {outage_res.get('cluster_status')}")

        self.assertEqual(outage_res.get("cluster_status"), "CRITICAL_ALL_DOWN")
        self.assertEqual(outage_res.get("data_plane_mode"), "FAIL_SECURE_AUTONOMOUS")
        self.assertEqual(outage_res.get("active_leader"), "none")

        # 3. Check Flow Table Survival Oracle
        post_outage_flows = self._http_get("/api/flows")
        print(f" • Post-outage active flow records preserved: {len(post_outage_flows)}")

        # Verify all flows survived intact
        self.assertEqual(len(post_outage_flows), initial_flow_count,
                         f"Flow Table Loss! Expected {initial_flow_count} flows, but only found {len(post_outage_flows)}")

        # 4. Verify Policy Enforcement: New flows MUST be blocked
        blocked_attempt = self._http_post("/api/simulate/apply_flow?src=2&dst=6&demand=50.0")
        print(f" • Attempt to install flow during total outage: status={blocked_attempt.get('status')}, error={blocked_attempt.get('error_type')}")

        self.assertEqual(blocked_attempt.get("status"), "error")
        self.assertEqual(blocked_attempt.get("error_type"), "FAIL_SECURE_AUTONOMOUS_MODE",
                         "Switches failed to enforce Fail-Secure Autonomous drop for new flows!")

        # Verify flows are still intact after blocked attempt
        post_blocked_flows = self._http_get("/api/flows")
        self.assertEqual(len(post_blocked_flows), initial_flow_count)

        # 5. Full Self-Healing Cluster Recovery
        rec_res = self._http_post("/api/simulate/controller_recover?target=all")
        print(f" • Cluster Self-Healing Recovery: status={rec_res.get('cluster_status')}, leader={rec_res.get('active_leader')}")

        self.assertEqual(rec_res.get("cluster_status"), "NOMINAL_HEALTHY")
        self.assertEqual(rec_res.get("data_plane_mode"), "OPENFLOW_ACTIVE")
        self.assertEqual(rec_res.get("active_leader"), "primary")

        # Post-recovery flow preservation
        recovered_flows = self._http_get("/api/flows")
        self.assertEqual(len(recovered_flows), initial_flow_count,
                         "Flow tables were corrupted or wiped during self-healing recovery!")

    # =========================================================================
    # 4. SUB-50MS CARRIER-GRADE FAILOVER LATENCY UNDER STRESS
    # =========================================================================
    def test_06_carrier_grade_failover_latency_under_stress(self):
        """
        Adversarial Test 4: Physical Process Kill Failover Latency Under Stress.
        Spawns 3 independent physical controller processes via MultiControllerCluster,
        generates continuous multi-threaded HTTP request stress,
        and injects abrupt process terminations (SIGTERM/SIGKILL).
        Asserts physical failover latency is strictly < 50.0 ms.
        """
        print("\n" + "=" * 70)
        print(" [CHALLENGE 4] Sub-50ms Carrier-Grade Failover Under Multi-Threaded Stress")
        print("=" * 70)

        # Dedicated test cluster on isolated ports
        test_ports = [8280, 8281, 8282]
        test_nodes = [
            ControllerNode(name="primary", host="127.0.0.1", ofp_port=6633, rest_port=test_ports[0], role="primary"),
            ControllerNode(name="backup1", host="127.0.0.1", ofp_port=6634, rest_port=test_ports[1], role="backup1"),
            ControllerNode(name="backup2", host="127.0.0.1", ofp_port=6635, rest_port=test_ports[2], role="backup2"),
        ]

        cluster = MultiControllerCluster()
        cluster.pool = HAControllerPool(nodes=test_nodes)

        try:
            print(" • Spawning 3-Controller physical processes...")
            cluster.start_all(wait_sec=10.0)
            health = cluster.pool.probe_all()
            print(f" • Physical cluster health: {health}")
            for n, h in health.items():
                self.assertTrue(h, f"Controller node {n} failed to start on port {test_ports}!")

            # -------------------------------------------------------------
            # BENCHMARK 1: Baseline Failover (No Stress)
            # -------------------------------------------------------------
            t_start = time.perf_counter()
            cluster.stop_controller("primary")
            # Request through transparent pool
            res_p3 = cluster.pool.execute_request("GET", "/api/model_predict?src=4&dst=7&demand=25")
            base_failover_ms = (time.perf_counter() - t_start) * 1000.0

            active_p3 = cluster.pool.get_active_controller(auto_promote=False)
            print(f" • Baseline Failover (Primary -> Backup1): {base_failover_ms:.2f} ms (Target < 50ms)")
            self.assertEqual(active_p3.name, "backup1")
            self.assertIsNotNone(res_p3.get("chosen_path"))
            self.assertLess(base_failover_ms, 50.0, f"Baseline failover exceeded 50ms: {base_failover_ms:.2f}ms")

            # -------------------------------------------------------------
            # BENCHMARK 2: Stressed Cascaded Failover Under Multi-Thread Load
            # -------------------------------------------------------------
            stop_stress = threading.Event()
            stress_errors = []

            def stress_worker():
                while not stop_stress.is_set():
                    try:
                        cluster.pool.execute_request("GET", "/api/ha/status", timeout=1.0)
                    except Exception as e:
                        stress_errors.append(str(e))
                    time.sleep(0.01)

            # Start 5 stress worker threads targeting Backup1
            stress_threads = [threading.Thread(target=stress_worker, daemon=True) for _ in range(5)]
            for st in stress_threads:
                st.start()
            time.sleep(0.2)  # Allow stress to ramp up

            # Inject crash of Backup1 under active stress
            t_stress_crash = time.perf_counter()
            cluster.stop_controller("backup1")
            res_p4 = cluster.pool.execute_request("GET", "/api/model_predict?src=4&dst=7&demand=30")
            stressed_failover_ms = (time.perf_counter() - t_stress_crash) * 1000.0

            stop_stress.set()
            for st in stress_threads:
                st.join(timeout=1.0)

            active_p4 = cluster.pool.get_active_controller(auto_promote=False)
            print(f" • Stressed Failover (Backup1 -> Backup2): {stressed_failover_ms:.2f} ms (Target < 50ms)")
            print(f" • Backup 2 Serving Route Decision: Path: {res_p4.get('chosen_path')}")

            self.assertEqual(active_p4.name, "backup2")
            self.assertIsNotNone(res_p4.get("chosen_path"))
            self.assertLess(stressed_failover_ms, 50.0,
                            f"Stressed failover latency exceeded 50ms: {stressed_failover_ms:.2f}ms")

            # Verify internal logged failover latencies
            status = cluster.pool.cluster_status()
            failover_history = status.get("failover_history", [])
            print(f" • Total failovers logged by pool: {len(failover_history)}")
            for idx, event in enumerate(failover_history):
                internal_lat = event.get("failover_latency_ms", 0.0)
                print(f"   [Event {idx+1}] {event.get('from')} -> {event.get('to')} in {internal_lat:.3f} ms ({event.get('reason')})")
                self.assertLess(internal_lat, 10.0, f"Internal pool failover latency exceeded 10ms: {internal_lat}ms")

        finally:
            cluster.stop_all()

    def test_07_ha_pool_recover_node_priority_rebalance(self):
        """
        Adversarial Test 2.4: HAControllerPool Object-Level Priority Preemption Probe.
        Probes HAControllerPool.recover_node() when Backup 1 recovers while Primary is dead.
        Specification requires strict priority ordering: Primary (0) > Backup 1 (1) > Backup 2 (2).
        If Primary is down and Backup 2 is active, recovering Backup 1 must rebalance to Backup 1.
        """
        print("\n" + "=" * 70)
        print(" [CHALLENGE 2.4] HAControllerPool recover_node() Priority Rebalance")
        print("=" * 70)
        pool = HAControllerPool()
        # Initial: primary is active
        self.assertEqual(pool.nodes[pool.active_index].name, "primary")

        # Step 1: Fail primary -> fails over to backup1
        pool.fail_node("primary")
        self.assertEqual(pool.nodes[pool.active_index].name, "backup1")

        # Step 2: Fail backup1 -> fails over to backup2
        pool.fail_node("backup1")
        self.assertEqual(pool.nodes[pool.active_index].name, "backup2")

        # Step 3: Recover backup1 while primary is still failed
        pool.recover_node("backup1")
        active_after_b1_rec = pool.nodes[pool.active_index].name
        print(f" • Active controller after Backup 1 recovery (Primary still dead): {active_after_b1_rec}")
        self.assertEqual(active_after_b1_rec, "backup1",
                         f"HAControllerPool Priority Inversion! Expected 'backup1' (Priority 2) to preempt 'backup2' (Priority 3), but remained on '{active_after_b1_rec}'")


if __name__ == '__main__':
    # Save results to logs/ha_adversarial_results.json
    runner = unittest.TextTestRunner(verbosity=2)
    suite = unittest.TestLoader().loadTestsFromTestCase(TestHAAdversarialSuite)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
```
