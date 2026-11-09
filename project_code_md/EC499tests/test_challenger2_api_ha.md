# `EC499tests/test_challenger2_api_ha.py`

> **File:** `EC499tests/test_challenger2_api_ha.py`  
> **Subsystem / Category:** 9. Publications, Documentation & Slide Generation  
> **Language:** `python`  
> **Lines of Code:** 273  
> **File Size:** 11.38 KB  

---

## Overview

Source code implementation for test_challenger2_api_ha.py.

### Architecture & Symbols
- **Classes:** `TestChallenger2RESTAPI`, `TestChallenger2HAClustering`
- **Key Functions:** None (Module level / Declarative)

---

## Source Code

```python
#!/usr/bin/env python3
"""
Challenger 2 Empirical Verification Harness:
1. Exhaustive REST API adversarial verification (/api/versus, /api/verse, normal, edge, malformed).
2. HA Clustering & Failover state machine verification.
"""

import sys
import os
import time
import json
import urllib.request
import urllib.error
import urllib.parse
import unittest

# Auto-detect base directory and path imports
_REAL_FILE = os.path.realpath(__file__)
_CURR_DIR = os.path.dirname(_REAL_FILE)
BASE_DIR = os.path.dirname(_CURR_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
for subdir in ['agent', 'controller', 'topology']:
    p = os.path.join(BASE_DIR, subdir)
    if p not in sys.path:
        sys.path.insert(0, p)

import web_dashboard
from ha_controller_pool import HAControllerPool, ControllerNode


class TestChallenger2RESTAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.port = 8195
        cls.server = web_dashboard.DashboardServer(host="127.0.0.1", port=cls.port)
        time.sleep(0.5)

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'server') and cls.server:
            cls.server.stop()

    def _get(self, path):
        url = f"http://127.0.0.1:{self.port}{path}"
        req = urllib.request.Request(url, method='GET')
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                code = resp.status
                body = resp.read().decode('utf-8')
                data = json.loads(body) if body else None
                return code, data
        except urllib.error.HTTPError as e:
            body = e.read().decode('utf-8')
            try:
                data = json.loads(body)
            except Exception:
                data = body
            return e.code, data

    def _post(self, path, body=None, content_type='application/json'):
        url = f"http://127.0.0.1:{self.port}{path}"
        if isinstance(body, dict):
            data_bytes = json.dumps(body).encode('utf-8')
        elif isinstance(body, str):
            data_bytes = body.encode('utf-8')
        elif body is None:
            data_bytes = b""
        else:
            data_bytes = bytes(body)

        headers = {'Content-Type': content_type} if content_type else {}
        req = urllib.request.Request(url, data=data_bytes, headers=headers, method='POST')
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                code = resp.status
                body = resp.read().decode('utf-8')
                data = json.loads(body) if body else None
                return code, data
        except urllib.error.HTTPError as e:
            body = e.read().decode('utf-8')
            try:
                data = json.loads(body)
            except Exception:
                data = body
            return e.code, data

    # -------------------------------------------------------------
    # 1. Parameter variations on /api/versus and alias /api/verse
    # -------------------------------------------------------------
    def test_topologies_and_protocols(self):
        topos = ['tree', 'fattree', 'abilene', 'nsfnet', 'spineleaf', 'random']
        protocols = ['ospf', 'ecmp', 'wsp', 'llr', 'dijkstra', 'spf', 'all']

        for topo in topos:
            for proto in protocols:
                for endpoint in ('/api/versus', '/api/verse'):
                    code, data = self._get(f"{endpoint}?topo={topo}&protocol={proto}&pattern=burst&flows=5")
                    self.assertEqual(code, 200, f"Failed on {endpoint} with topo={topo}, proto={proto}")
                    self.assertEqual(data.get("status"), "success")
                    self.assertIn("DQN (Ours)", data.get("algorithms", []))
                    self.assertIn("metrics", data)
                    self.assertIn("radar", data)
                    self.assertIn("deltas", data)

    def test_multi_protocol_list(self):
        for endpoint in ('/api/versus', '/api/verse'):
            code, data = self._get(f"{endpoint}?topo=fattree&protocol=ospf,ecmp,wsp,llr&pattern=jam&flows=10")
            self.assertEqual(code, 200)
            self.assertEqual(data.get("status"), "success")
            self.assertEqual(len(data.get("algorithms", [])), 5) # DQN + 4 baselines
            self.assertEqual(data["deltas"]["competitors_count"], 4)

    def test_all_traffic_patterns(self):
        patterns = ['jam', 'crowd', 'burst', 'hotspot', 'pareto', 'diurnal', 'failover', 'uniform', 'poisson']
        for pat in patterns:
            code, data = self._get(f"/api/versus?topo=tree&protocol=ospf&pattern={pat}&flows=5")
            self.assertEqual(code, 200, f"Pattern {pat} failed")
            self.assertEqual(data.get("status"), "success")

    def test_flow_count_boundaries(self):
        # Min valid = 1, Max valid = 500
        for flows in (1, 10, 50, 100, 500):
            code, data = self._get(f"/api/versus?topo=tree&protocol=ospf&flows={flows}")
            self.assertEqual(code, 200, f"flows={flows} failed")
            self.assertEqual(data.get("status"), "success")

    def test_post_json_payload(self):
        payload = {
            "topo": "nsfnet",
            "protocol": "all",
            "pattern": "hotspot",
            "flows": 8,
            "preset": "performance"
        }
        for endpoint in ('/api/versus', '/api/verse'):
            code, data = self._post(endpoint, body=payload)
            self.assertEqual(code, 200)
            self.assertEqual(data.get("status"), "success")
            self.assertGreaterEqual(len(data.get("algorithms", [])), 6)

    # -------------------------------------------------------------
    # 2. Adversarial & Malformed Input Handling
    # -------------------------------------------------------------
    def test_empty_query_string_defaults(self):
        # Empty query should default to tree, ospf, jam, 30
        for endpoint in ('/api/versus', '/api/verse'):
            code, data = self._get(endpoint)
            self.assertEqual(code, 200)
            self.assertEqual(data.get("status"), "success")
            self.assertEqual(data.get("topology_id"), "tree")
            self.assertIn("OSPF (RFC 2328)", data.get("algorithms", []))

    def test_invalid_topology_error_handling(self):
        code, data = self._get("/api/versus?topo=nonexistent_topology")
        self.assertEqual(code, 400)
        self.assertEqual(data.get("status"), "error")
        self.assertIn("Unknown topology", data.get("error", ""))

    def test_invalid_traffic_pattern_error_handling(self):
        code, data = self._get("/api/versus?pattern=supernova")
        self.assertEqual(code, 400)
        self.assertEqual(data.get("status"), "error")
        self.assertIn("Unsupported traffic pattern", data.get("error", ""))

    def test_non_integer_flows_error_handling(self):
        code, data = self._get("/api/versus?flows=not_a_number")
        self.assertEqual(code, 400)
        self.assertEqual(data.get("status"), "error")

    def test_out_of_bounds_flows_error_handling(self):
        for bad_flow in (0, -1, -50, 501, 9999):
            code, data = self._get(f"/api/versus?flows={bad_flow}")
            self.assertEqual(code, 400)
            self.assertEqual(data.get("status"), "error")
            self.assertIn("must be between 1 and 500", data.get("error", ""))

    def test_unknown_protocol_fallback(self):
        # Unknown protocol should fallback gracefully to OSPF
        code, data = self._get("/api/versus?protocol=bgp,rip,eigrp")
        self.assertEqual(code, 200)
        self.assertEqual(data.get("status"), "success")
        self.assertIn("OSPF (RFC 2328)", data.get("algorithms", []))

    def test_malformed_post_body_handling(self):
        # Corrupted JSON
        code, data = self._post("/api/versus", body="{not valid json:")
        self.assertEqual(code, 400)
        self.assertEqual(data.get("status"), "error")

        # Empty body POST
        code, data = self._post("/api/versus", body="")
        self.assertEqual(code, 200) # Should use defaults gracefully
        self.assertEqual(data.get("status"), "success")

    def test_concurrent_versus_requests(self):
        from concurrent.futures import ThreadPoolExecutor
        urls = [
            "/api/versus?topo=tree&protocol=ospf&flows=5",
            "/api/verse?topo=fattree&protocol=ecmp&flows=5",
            "/api/versus?topo=abilene&protocol=wsp&flows=5",
            "/api/verse?topo=nsfnet&protocol=llr&flows=5",
            "/api/versus?topo=spineleaf&protocol=all&flows=5",
            "/api/verse?topo=random&protocol=ospf,ecmp&flows=5",
            "/api/versus?topo=tree&protocol=all&flows=5",
            "/api/verse?topo=fattree&protocol=ospf&flows=5",
        ]
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(self._get, u) for u in urls]
            for fut in futures:
                code, data = fut.result()
                self.assertEqual(code, 200)
                self.assertEqual(data.get("status"), "success")

    def test_server_healthy_after_stress(self):
        # Ensure server remained completely intact and healthy after all adversarial requests
        code, data = self._get("/api/health")
        self.assertEqual(code, 200)
        self.assertEqual(data.get("status"), "healthy")


class TestChallenger2HAClustering(unittest.TestCase):
    """Adversarial Verification of HA Controller Pool mechanics."""

    def test_ha_pool_state_transitions_and_preemption(self):
        nodes = [
            ControllerNode(name="c1", host="127.0.0.1", ofp_port=6633, rest_port=8180, role="primary"),
            ControllerNode(name="c2", host="127.0.0.1", ofp_port=6634, rest_port=8181, role="backup1"),
            ControllerNode(name="c3", host="127.0.0.1", ofp_port=6635, rest_port=8182, role="backup2"),
        ]
        pool = HAControllerPool(nodes=nodes)

        # Initial state: c1 active
        self.assertEqual(pool.get_active_controller().name, "c1")
        self.assertEqual(pool.active_index, 0)
        self.assertEqual(pool.total_failovers, 0)

        # Failover 1: c1 -> c2 via fail_node
        new_active = pool.fail_node("c1")
        self.assertEqual(new_active.name, "c2")
        self.assertEqual(pool.active_index, 1)
        self.assertEqual(pool.total_failovers, 1)

        # Failover 2: c2 -> c3 via fail_node
        new_active_2 = pool.fail_node("c2")
        self.assertEqual(new_active_2.name, "c3")
        self.assertEqual(pool.active_index, 2)
        self.assertEqual(pool.total_failovers, 2)

        # Total cluster outage: c3 fails -> fail_node returns None and marks is_all_failed() == True
        last_active = pool.fail_node("c3")
        self.assertIsNone(last_active)
        self.assertTrue(pool.is_all_failed())

        # Self healing: recover_all
        pool.recover_all()
        self.assertFalse(pool.is_all_failed())
        self.assertEqual(pool.get_active_controller(auto_promote=False).name, "c1")

    def test_ha_history_audit_trail(self):
        pool = HAControllerPool()
        pool.failover(reason="test_fail_1")
        pool.failover(reason="test_fail_2")
        status = pool.cluster_status()
        self.assertEqual(len(status["failover_history"]), 2)
        self.assertEqual(status["failover_history"][0]["from"], "primary")
        self.assertEqual(status["failover_history"][0]["to"], "backup1")
        self.assertEqual(status["failover_history"][1]["from"], "backup1")
        self.assertEqual(status["failover_history"][1]["to"], "backup2")


if __name__ == '__main__':
    unittest.main(verbosity=2)
```
