# `EC499tests/test_e2e_opaque_box.py`

> **File:** `EC499tests/test_e2e_opaque_box.py`  
> **Subsystem / Category:** 9. Publications, Documentation & Slide Generation  
> **Language:** `python`  
> **Lines of Code:** 829  
> **File Size:** 36.48 KB  

---

## Overview

Source code implementation for test_e2e_opaque_box.py.

### Architecture & Symbols
- **Classes:** `BaseE2ETestCase`, `Tier1FeatureCoverage`, `Tier2BoundaryAndCornerCases`, `Tier3CrossFeatureCombinations`, `Tier4RealWorldApplicationScenarios`
- **Key Functions:** `_bootstrap_environment`, `setUpModule`, `tearDownModule`, `run_e2e_opaque_box_suite`

---

## Source Code

```python
#!/usr/bin/env python3
"""
Comprehensive 4-Tier Opaque-Box End-to-End Validation Test Runner (EC499).
SDN Traffic Engineering with Deep Reinforcement Learning (D3QN) & Carrier-Grade HA.

Candidate: Maher Abdulnasir Alqadhi (Reg. No. 2210249576)
Supervisor: Dr. Suad El-Geder
Institution: University of Tripoli — Computer Engineering

Taxonomy:
  - Tier 1: Comprehensive Feature Coverage (REST, D3QN, Baselines, HA, Docs/Archives)
  - Tier 2: Boundary & Corner Cases (405 Method Guards, 400 Bad Requests, 413/409 Limits, Topology Boundaries)
  - Tier 3: Cross-Feature Integration (HA Failover + Dynamic Flows, Tournaments + Topology Switching, Model + Policy)
  - Tier 4: Real-World Application Scenarios (100-step burst simulation, cascaded failover, graduation packaging)
"""

import os
import sys
import time
import json
import socket
import zipfile
import unittest
import urllib.request
import urllib.error
from urllib.parse import urlparse

# Auto-detect and activate virtualenv
def _bootstrap_environment():
    try:
        import numpy  # noqa: F401
        import torch  # noqa: F401
        import pypdf  # noqa: F401
        return
    except ImportError:
        pass

    candidate_venvs = [
        os.path.expanduser('~/ec499_env/bin/python3'),
        os.path.expanduser('~/ec499_env/bin/python'),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.venv', 'bin', 'python3'),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.venv', 'bin', 'python'),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'venv', 'bin', 'python3'),
        os.path.expanduser('~/.venv/bin/python3'),
    ]
    for cand in candidate_venvs:
        cand_prefix = os.path.dirname(os.path.dirname(os.path.abspath(cand)))
        if os.path.exists(cand) and os.access(cand, os.X_OK) and cand_prefix != sys.prefix:
            try:
                os.execv(cand, [cand] + sys.argv)
            except Exception:
                pass

_bootstrap_environment()

# Setup import paths
_REAL_FILE = os.path.realpath(__file__)
_CURR_DIR = os.path.dirname(_REAL_FILE)
BASE_DIR = os.path.dirname(_CURR_DIR) if os.path.basename(_CURR_DIR) == 'EC499tests' else _CURR_DIR
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
for subdir in ['agent', 'controller', 'topology']:
    p = os.path.join(BASE_DIR, subdir)
    if p not in sys.path:
        sys.path.insert(0, p)

# Root directory (holding Project_Report_EC499_Final.pdf, mahermqr.pdf, etc.)
PROJECT_ROOT = os.path.dirname(BASE_DIR) if os.path.basename(BASE_DIR) == 'Reinforcement_Learning_for_Adaptive_Traffic_Engineering_in_an_SDN_Network' else BASE_DIR

import numpy as np
import torch
import networkx as nx
import pypdf
import config

from web_dashboard import DashboardServer
from state_manager import StateManager
from dqn_router import DQNRoutingAgent
from topology_library import get_topology


# Shared server reference and port allocation
_TEST_SERVER = None
_TEST_PORT = 8196


def setUpModule():
    """Start an isolated DashboardServer instance for end-to-end HTTP validation."""
    global _TEST_SERVER, _TEST_PORT
    if _TEST_SERVER is not None:
        return
    port = 8196
    while port < 8250:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', port)) != 0:
                _TEST_PORT = port
                break
        port += 1

    _TEST_SERVER = DashboardServer(host="127.0.0.1", port=_TEST_PORT)
    time.sleep(0.6)


def tearDownModule():
    """Tear down the test DashboardServer instance."""
    global _TEST_SERVER
    if _TEST_SERVER is not None:
        _TEST_SERVER.stop()
        _TEST_SERVER = None


class BaseE2ETestCase(unittest.TestCase):
    """Base class providing HTTP client helpers and state hygiene for opaque-box testing."""

    @property
    def server_url(self):
        return f"http://127.0.0.1:{_TEST_PORT}"

    def get_json(self, path):
        url = f"{self.server_url}{path}"
        req = urllib.request.Request(url, headers={'Accept': 'application/json'})
        with urllib.request.urlopen(req, timeout=12) as resp:
            self.assertEqual(resp.status, 200)
            return json.loads(resp.read().decode('utf-8'))

    def post_json(self, path, data=None):
        url = f"{self.server_url}{path}"
        payload = json.dumps(data if data is not None else {}).encode('utf-8')
        req = urllib.request.Request(
            url, data=payload,
            headers={'Content-Type': 'application/json', 'Accept': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=12) as resp:
            self.assertEqual(resp.status, 200)
            return json.loads(resp.read().decode('utf-8'))

    def raw_request(self, method, path, data=None, headers=None):
        url = f"{self.server_url}{path}"
        hdrs = headers or {}
        req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                return resp.status, resp.read(), dict(resp.headers)
        except urllib.error.HTTPError as e:
            code = e.code
            body = e.read()
            hdrs = dict(e.headers)
            e.close()
            return code, body, hdrs

    def reset_cluster_and_sim(self):
        """Clean up simulated dynamic flows, link failures, and restore nominal cluster roles."""
        try:
            self.post_json("/api/simulate/reset")
        except Exception:
            pass


# ==============================================================================
# TIER 1: FEATURE COVERAGE (>=5 Test Cases per Feature Category)
# ==============================================================================
class Tier1FeatureCoverage(BaseE2ETestCase):
    """
    Tier 1: Comprehensive feature coverage across all 5 core subsystems:
      1. REST API Endpoints (6 tests)
      2. D3QN Inference & Policy (5 tests)
      3. Traditional Routing Baselines (5 tests)
      4. HA Clustering Status & Roles (5 tests)
      5. Defense Deliverables & Packaging (5 tests)
    """

    def tearDown(self):
        self.reset_cluster_and_sim()

    # --- 1. REST API Endpoints ---
    def test_01_rest_health_probe(self):
        data = self.get_json("/api/health")
        self.assertEqual(data.get("status"), "healthy")
        self.assertIn("topology", data)
        self.assertGreaterEqual(data.get("nodes", 0), 2)
        self.assertGreaterEqual(data.get("links", 0), 1)

    def test_02_rest_topology_metadata(self):
        data = self.get_json("/api/topology?topo=tree")
        self.assertIn("nodes", data)
        self.assertIn("links", data)
        self.assertIn("current_topology", data)
        self.assertEqual(data.get("current_topology"), "tree")
        self.assertGreaterEqual(len(data["nodes"]), 7)

    def test_03_rest_telemetry_bundle(self):
        data = self.get_json("/api/telemetry")
        self.assertEqual(data.get("status"), "success")
        self.assertIn("timestamp", data)
        self.assertIn("stats", data)
        self.assertIn("overhead", data)
        self.assertIn("rl_metrics", data)
        self.assertIn("flows", data)
        self.assertIn("model_info", data)
        self.assertIn("ha_cluster", data)
        self.assertAlmostEqual(data["timestamp"], time.time(), delta=10.0)

    def test_04_rest_stats_and_overhead(self):
        stats = self.get_json("/api/stats")
        overhead = self.get_json("/api/control_overhead")
        self.assertIn("total_throughput_mbps", stats)
        self.assertIn("mean_latency_ms", stats)
        self.assertIn("mean_jitter_ms", stats)
        self.assertIn("packet_in_count", overhead)
        self.assertIn("flow_mod_count", overhead)
        self.assertIn("total_control_overhead_kb", overhead)

    def test_05_rest_topologies_catalog(self):
        topos = self.get_json("/api/topologies")
        self.assertIsInstance(topos, list)
        topo_ids = [t.get("id") for t in topos if isinstance(t, dict)]
        self.assertIn("tree", topo_ids)
        self.assertIn("fattree", topo_ids)
        self.assertIn("abilene", topo_ids)
        self.assertIn("nsfnet", topo_ids)

    def test_06_rest_plots_catalog(self):
        plots = self.get_json("/api/plot_list")
        self.assertEqual(plots.get("status"), "success")
        self.assertIn("plots", plots)
        self.assertIsInstance(plots["plots"], list)

    # --- 2. D3QN Inference & Policy ---
    def test_07_d3qn_model_inspect(self):
        insp = self.get_json("/api/model_inspect")
        arch = insp.get("architecture", {})
        self.assertEqual(arch.get("type"), "Dueling Double Deep Q-Network (D3QN)")
        self.assertEqual(arch.get("state_dim"), 10)
        self.assertEqual(arch.get("action_dim"), 4)
        self.assertIn("features", arch)
        self.assertIn("value_stream", arch)
        self.assertIn("advantage_stream", arch)

    def test_08_d3qn_model_prediction_nominal(self):
        pred = self.get_json("/api/model_predict?src=4&dst=7&demand=25.0")
        self.assertEqual(pred.get("src"), 4)
        self.assertEqual(pred.get("dst"), 7)
        self.assertIn("chosen_path", pred)
        self.assertEqual(pred["chosen_path"][0], 4)
        self.assertEqual(pred["chosen_path"][-1], 7)
        self.assertEqual(len(pred.get("candidate_paths", [])), 4)
        self.assertLess(pred.get("inference_time_ms", 100), 50.0)

    def test_09_d3qn_model_prediction_alternative_pair(self):
        pred = self.get_json("/api/model_predict?src=5&dst=6&demand=15.0")
        self.assertIn("chosen_path", pred)
        self.assertEqual(pred["chosen_path"][0], 5)
        self.assertEqual(pred["chosen_path"][-1], 6)
        self.assertEqual(len(pred.get("candidate_paths", [])), 4)

    def test_10_d3qn_rl_metrics(self):
        rl = self.get_json("/api/rl_metrics")
        self.assertTrue(rl.get("model_loaded"))
        self.assertGreater(rl.get("parameter_count", 0), 20000)
        self.assertIn(rl.get("router_device", "").upper(), ["CPU", "CUDA"])
        self.assertLessEqual(rl.get("router_epsilon", 0.0), 1.0)

    def test_11_d3qn_state_vector_bounds(self):
        sm = _TEST_SERVER.state_manager
        state = sm.get_routing_state(4, 7)
        self.assertEqual(len(state), 10)
        self.assertFalse(np.isnan(state).any(), "State vector contains NaN values")
        self.assertFalse(np.isinf(state).any(), "State vector contains infinite values")
        self.assertGreaterEqual(state[0], 0.0)
        self.assertLessEqual(state[0], 1.5)

    # --- 3. Traditional Routing Baselines ---
    def test_12_baseline_ospf_rfc2328(self):
        res = self.get_json("/api/verse?topo=tree&protocol=ospf&pattern=jam&flows=10")
        self.assertEqual(res.get("status"), "success")
        self.assertIn("OSPF (RFC 2328)", res.get("metrics", {}))
        ospf_m = res["metrics"]["OSPF (RFC 2328)"]
        self.assertGreater(ospf_m.get("latency_ms", 0), 0)
        self.assertGreater(ospf_m.get("bottleneck_util", 0), 0)

    def test_13_baseline_ecmp_multipath(self):
        res = self.get_json("/api/verse?topo=fattree&protocol=ecmp&pattern=burst&flows=10")
        self.assertEqual(res.get("status"), "success")
        self.assertIn("ECMP Multi-Path", res.get("metrics", {}))
        ecmp_m = res["metrics"]["ECMP Multi-Path"]
        self.assertIn("estimated_delivered_mbps", ecmp_m)
        self.assertIn("packet_loss_pct", ecmp_m)
        self.assertIn("bottleneck_util", ecmp_m)

    def test_14_baseline_wsp_widest_shortest(self):
        res = self.get_json("/api/verse?topo=nsfnet&protocol=wsp&pattern=jam&flows=10")
        self.assertEqual(res.get("status"), "success")
        self.assertIn("WSP Widest Path", res.get("metrics", {}))

    def test_15_baseline_llr_least_loaded(self):
        res = self.get_json("/api/verse?topo=tree&protocol=llr&pattern=burst&flows=10")
        self.assertEqual(res.get("status"), "success")
        self.assertIn("LLR Least Loaded", res.get("metrics", {}))

    def test_16_baseline_dijkstra_spf(self):
        res = self.get_json("/api/verse?topo=abilene&protocol=dijkstra&pattern=jam&flows=10")
        self.assertEqual(res.get("status"), "success")
        self.assertIn("Dijkstra SPF", res.get("metrics", {}))

    # --- 4. HA Clustering Status & Roles ---
    def test_17_ha_status_master_active(self):
        ha = self.get_json("/api/ha/status")
        self.assertEqual(ha.get("status"), "ok")
        self.assertEqual(ha.get("role"), "primary")
        self.assertEqual(ha.get("active_leader"), "primary")
        self.assertTrue(ha.get("is_primary"))
        self.assertEqual(ha.get("cluster_mode"), "NOMINAL_ACTIVE")

    def test_18_ha_three_node_roster(self):
        ha = self.get_json("/api/ha/status")
        self.assertEqual(ha.get("cluster_nodes"), ["primary", "backup1", "backup2"])
        nodes = ha.get("nodes_detail", [])
        self.assertEqual(len(nodes), 3)
        node_ids = [n["id"] for n in nodes]
        self.assertEqual(node_ids, ["primary", "backup1", "backup2"])

    def test_19_ha_node_health_roles(self):
        ha = self.get_json("/api/ha/status")
        nodes_by_id = {n["id"]: n for n in ha.get("nodes_detail", [])}
        self.assertEqual(nodes_by_id["primary"]["role"], "MASTER")
        self.assertEqual(nodes_by_id["primary"]["health"], "HEALTHY")
        self.assertEqual(nodes_by_id["backup1"]["role"], "SLAVE")
        self.assertEqual(nodes_by_id["backup1"]["health"], "READY")
        self.assertEqual(nodes_by_id["backup2"]["role"], "SLAVE")
        self.assertEqual(nodes_by_id["backup2"]["health"], "READY")

    def test_20_ha_ovs_controller_targets(self):
        ha = self.get_json("/api/ha/status")
        bench = ha.get("benchmarks", {})
        ovs_cmd = bench.get("ovs_binding_command", "")
        self.assertIn("6633", ovs_cmd)
        self.assertIn("6634", ovs_cmd)
        self.assertIn("6635", ovs_cmd)

    def test_21_ha_failover_history_and_benchmarks(self):
        ha = self.get_json("/api/ha/status")
        bench = ha.get("benchmarks", {})
        self.assertIn("switch_promotion_latency_ms", bench)
        self.assertIn("total_failovers", bench)
        self.assertIn("failover_history", bench)
        self.assertIsInstance(bench["failover_history"], list)

    # --- 5. Defense Deliverables & Packaging ---
    def test_22_artifact_handout_strictly_four_pages(self):
        handout_pdf = os.path.join(PROJECT_ROOT, "mahermqr.pdf")
        self.assertTrue(os.path.exists(handout_pdf), f"Handout missing at {handout_pdf}")
        reader = pypdf.PdfReader(handout_pdf)
        page_count = len(reader.pages)
        self.assertEqual(page_count, 4, f"Committee handout strictly requires 4 pages, found {page_count}")

    def test_23_artifact_thesis_strictly_seventy_three_pages(self):
        thesis_pdf = os.path.join(PROJECT_ROOT, "Project_Report_EC499_Final.pdf")
        self.assertTrue(os.path.exists(thesis_pdf), f"Thesis report missing at {thesis_pdf}")
        reader = pypdf.PdfReader(thesis_pdf)
        page_count = len(reader.pages)
        self.assertEqual(page_count, 73, f"Master dissertation strictly requires 73 pages, found {page_count}")

    def test_24_artifact_defense_slides_pptx_and_web(self):
        pptx_path = os.path.join(PROJECT_ROOT, "EC499_Final_Defense_Presentation.pptx")
        web_index = os.path.join(PROJECT_ROOT, "EC499sildes", "index.html")
        self.assertTrue(os.path.exists(pptx_path), "Defense presentation PPTX missing")
        self.assertGreater(os.path.getsize(pptx_path), 1_000_000, "PPTX file size too small")
        self.assertTrue(os.path.exists(web_index), "Interactive web slides missing")

    def test_25_artifact_graduation_submission_zip_contents(self):
        zip_path = os.path.join(PROJECT_ROOT, "Maher_Alqadhi_2210249576_EC499_Final_Graduation_Submission.zip")
        self.assertTrue(os.path.exists(zip_path), "Graduation submission ZIP missing")
        self.assertGreater(os.path.getsize(zip_path), 50_000_000, "Graduation submission ZIP size < 50MB")
        with zipfile.ZipFile(zip_path, 'r') as z:
            names = z.namelist()
            self.assertTrue(any("01_Final_Thesis_Report" in n for n in names), "Missing 01_Final_Thesis_Report")
            self.assertTrue(any("02_Defense_Presentation" in n for n in names), "Missing 02_Defense_Presentation")
            self.assertTrue(any("05_Trained_D3QN_Model" in n for n in names), "Missing 05_Trained_D3QN_Model")
            self.assertTrue(any("06_Source_Code_and_Dashboard" in n for n in names), "Missing 06_Source_Code_and_Dashboard")

    def test_26_artifact_delivery_and_prism_archives(self):
        delivery_zip = os.path.join(PROJECT_ROOT, "delivery", "Maher_Alqadhi_2210249576_EC499_Final_Delivery.zip")
        prism_zip = os.path.join(PROJECT_ROOT, "prism", "EC499_Final_Report_Prism.zip")
        self.assertTrue(os.path.exists(delivery_zip), "Delivery bundle ZIP missing")
        self.assertTrue(os.path.exists(prism_zip), "OpenAI Prism ZIP missing")
        with zipfile.ZipFile(delivery_zip, 'r') as z:
            self.assertGreater(len(z.namelist()), 5)
        with zipfile.ZipFile(prism_zip, 'r') as z:
            self.assertGreater(len(z.namelist()), 5)


# ==============================================================================
# TIER 2: BOUNDARY & CORNER CASES (>=5 Test Cases per Boundary Category)
# ==============================================================================
class Tier2BoundaryAndCornerCases(BaseE2ETestCase):
    """
    Tier 2: Boundary, error resilience, and corner cases:
      1. HTTP Method Guards (405 Method Not Allowed) (6 tests)
      2. Parameter Validation & Malformed Inputs (400 Bad Request) (5 tests)
      3. Payload & Operational Limits (413/409/404) (5 tests)
      4. Topology & Traffic Boundary Conditions (5 tests)
    """

    def tearDown(self):
        self.reset_cluster_and_sim()

    # --- 1. HTTP Method Guards (405) ---
    def test_01_get_on_simulate_reset_returns_405(self):
        status, body, _ = self.raw_request("GET", "/api/simulate/reset")
        self.assertEqual(status, 405)
        self.assertIn(b"require POST", body)

    def test_02_get_on_traffic_burst_returns_405(self):
        status, body, _ = self.raw_request("GET", "/api/simulate/traffic_burst")
        self.assertEqual(status, 405)
        self.assertIn(b"require POST", body)

    def test_03_get_on_link_fail_returns_405(self):
        status, body, _ = self.raw_request("GET", "/api/simulate/link_fail")
        self.assertEqual(status, 405)
        self.assertIn(b"require POST", body)

    def test_04_get_on_wcmp_returns_405(self):
        status, body, _ = self.raw_request("GET", "/api/simulate/wcmp")
        self.assertEqual(status, 405)
        self.assertIn(b"require POST", body)

    def test_05_get_on_controller_fail_returns_405(self):
        status, body, _ = self.raw_request("GET", "/api/simulate/controller_fail")
        self.assertEqual(status, 405)
        self.assertIn(b"require POST", body)

    def test_06_options_cors_preflight_returns_200(self):
        status, _, hdrs = self.raw_request("OPTIONS", "/api/telemetry")
        self.assertEqual(status, 200)
        self.assertIn("Access-Control-Allow-Methods", hdrs)
        self.assertIn("POST", hdrs["Access-Control-Allow-Methods"])

    # --- 2. Parameter Validation & Malformed Inputs (400) ---
    def test_07_invalid_demand_string_returns_400(self):
        status, body, _ = self.raw_request("GET", "/api/model_predict?src=4&dst=7&demand=not_a_number")
        self.assertEqual(status, 400)
        self.assertIn(b"must be a positive float", body)

    def test_08_invalid_src_string_returns_400(self):
        status, body, _ = self.raw_request("GET", "/api/model_predict?src=string_node&dst=7&demand=25")
        self.assertEqual(status, 400)
        self.assertIn(b"must be integers", body)

    def test_09_invalid_dst_string_returns_400(self):
        status, body, _ = self.raw_request("GET", "/api/model_predict?src=4&dst=string_node&demand=25")
        self.assertEqual(status, 400)
        self.assertIn(b"must be integers", body)

    def test_10_malformed_json_body_returns_400(self):
        raw_broken = b"{\"invalid_json\": not_terminated"
        status, body, _ = self.raw_request(
            "POST", "/api/simulate/apply_flow",
            data=raw_broken, headers={'Content-Type': 'application/json'}
        )
        self.assertEqual(status, 400)
        self.assertIn(b"Invalid JSON body", body)

    def test_11_json_body_non_dict_array_returns_400(self):
        raw_list = b"[1, 2, 3, 4]"
        status, body, _ = self.raw_request(
            "POST", "/api/simulate/apply_flow",
            data=raw_list, headers={'Content-Type': 'application/json'}
        )
        self.assertEqual(status, 400)
        self.assertIn(b"must be an object", body)

    # --- 3. Payload & Operational Limits (413/409/404) ---
    def test_12_oversized_payload_returns_413(self):
        import http.client
        conn = http.client.HTTPConnection("127.0.0.1", _TEST_PORT)
        try:
            conn.putrequest("POST", "/api/simulate/apply_flow")
            conn.putheader("Content-Type", "application/json")
            conn.putheader("Content-Length", "2000000")
            conn.endheaders()
            resp = conn.getresponse()
            self.assertEqual(resp.status, 413)
            body = resp.read()
            self.assertIn(b"Request body too large", body)
        finally:
            conn.close()

    def test_13_negative_content_length_returns_413_or_400(self):
        status, body, _ = self.raw_request(
            "POST", "/api/simulate/apply_flow",
            data=b"{}", headers={'Content-Type': 'application/json', 'Content-Length': '-10'}
        )
        self.assertIn(status, [400, 413])

    def test_14_simulation_lockout_in_live_mode_returns_409(self):
        orig_mode = getattr(config, 'RUNTIME_MODE', 'simulation')
        try:
            config.RUNTIME_MODE = 'live'
            status, body, _ = self.raw_request(
                "POST", "/api/simulate/traffic_burst",
                data=b"{}", headers={'Content-Type': 'application/json'}
            )
            self.assertEqual(status, 409)
            self.assertIn(b"disabled in live OpenFlow mode", body)
        finally:
            config.RUNTIME_MODE = orig_mode

    def test_15_nonexistent_endpoint_returns_404(self):
        status, _, _ = self.raw_request("GET", "/api/nonexistent_sdn_resource_404")
        self.assertEqual(status, 404)

    def test_16_nonexistent_plot_returns_404(self):
        status, _, _ = self.raw_request("GET", "/api/plots/missing_plot_xyz.png")
        self.assertEqual(status, 404)

    # --- 4. Network Topology & Traffic Boundary Conditions ---
    def test_17_single_link_minimal_topology(self):
        g = nx.Graph()
        g.add_edge(1, 2, bandwidth=100.0, delay=1.0)
        meta = {'edge_nodes': [1, 2]}
        sm = StateManager()
        sm.set_topology('single_link', g, meta)
        paths = sm.get_candidate_paths(1, 2)
        self.assertEqual(paths, [[1, 2]])

    def test_18_zero_traffic_demand_prediction(self):
        pred = self.get_json("/api/model_predict?src=4&dst=7&demand=0.0")
        self.assertEqual(pred.get("status"), "error")
        self.assertIn("strictly positive", pred.get("message", ""))

    def test_19_extreme_traffic_demand_prediction(self):
        pred = self.get_json("/api/model_predict?src=4&dst=7&demand=10000.0")
        self.assertIn("chosen_path", pred)
        self.assertEqual(pred["chosen_path"][0], 4)
        self.assertEqual(pred["chosen_path"][-1], 7)

    def test_20_identical_source_and_destination(self):
        sm = _TEST_SERVER.state_manager
        paths = sm.get_candidate_paths(4, 4)
        self.assertEqual(paths, [[4]])
        pred = self.get_json("/api/model_predict?src=4&dst=4&demand=25.0")
        self.assertEqual(pred.get("status"), "error")
        self.assertIn("distinct", pred.get("message", ""))

    def test_21_disconnected_graph_handling(self):
        g = nx.Graph()
        g.add_edge(1, 2, bandwidth=100.0, delay=1.0)
        g.add_node(3)
        meta = {'edge_nodes': [1, 2, 3]}
        sm = StateManager()
        sm.set_topology('disconnected', g, meta)
        paths = sm.get_candidate_paths(1, 3)
        self.assertEqual(paths, [])


# ==============================================================================
# TIER 3: CROSS-FEATURE INTEGRATION SCENARIOS
# ==============================================================================
class Tier3CrossFeatureCombinations(BaseE2ETestCase):
    """
    Tier 3: Complex multi-subsystem workflows and state interactions:
      1. HA Leader Promotion + Dynamic Flow Injection
      2. Multi-Protocol Tournament + Topology Switching
      3. Model Weight Inspection + Policy Prediction
      4. Dynamic Link Severing + WCMP Path Redistribution
      5. QoS SLA & Telemetry History Time-Series Aggregation
    """

    def tearDown(self):
        self.reset_cluster_and_sim()

    def test_01_ha_leader_promotion_and_dynamic_traffic_injection(self):
        fail_res = self.post_json("/api/simulate/controller_fail?target=primary")
        self.assertEqual(fail_res.get("status"), "success")
        self.assertEqual(fail_res.get("active_leader"), "backup1")
        self.assertLess(fail_res.get("failover_latency_ms", 100), 50.0)

        flow_res = self.post_json("/api/simulate/apply_flow?src=4&dst=7&demand=20.0&duration=15.0")
        self.assertEqual(flow_res.get("status"), "success")
        self.assertIn("chosen_path", flow_res)

        telem = self.get_json("/api/telemetry")
        self.assertEqual(telem["ha_status"]["active_leader"], "backup1")
        self.assertEqual(telem["ha_status"]["cluster_mode"], "DEGRADED_STANDBY_FAILOVER")
        self.assertGreater(len(telem.get("flows", [])), 0)

        rec_res = self.post_json("/api/simulate/controller_recover?target=all")
        self.assertEqual(rec_res.get("status"), "success")
        self.assertEqual(rec_res.get("active_leader"), "primary")

    def test_02_multi_protocol_tournament_and_topology_switching(self):
        sw1 = self.post_json("/api/simulate/switch_topology", {"topo": "fattree"})
        self.assertEqual(sw1.get("status"), "success")

        res_ft = self.get_json("/api/verse?topo=fattree&protocol=ospf,ecmp,wsp&pattern=jam&flows=12")
        self.assertEqual(res_ft.get("status"), "success")
        self.assertEqual(len(res_ft.get("algorithms", [])), 4)
        self.assertIn("DQN (Ours)", res_ft["algorithms"])
        self.assertIn("ECMP Multi-Path", res_ft["algorithms"])

        sw2 = self.post_json("/api/simulate/switch_topology", {"topo": "abilene"})
        self.assertEqual(sw2.get("status"), "success")

        res_ab = self.get_json("/api/verse?topo=abilene&protocol=ospf,ecmp,wsp&pattern=burst&flows=12")
        self.assertEqual(res_ab.get("status"), "success")
        self.assertIn("verdict", res_ab)

        self.post_json("/api/simulate/switch_topology", {"topo": "tree"})

    def test_03_model_weight_inspection_and_policy_prediction(self):
        insp = self.get_json("/api/model_inspect")
        arch = insp.get("architecture", {})
        self.assertIn("features", arch)
        self.assertIn("value_stream", arch)
        self.assertIn("advantage_stream", arch)

        pred = self.get_json("/api/model_predict?src=4&dst=7&demand=30.0")
        cand_paths = pred.get("candidate_paths", [])
        self.assertEqual(len(cand_paths), 4)
        selected = [cp for cp in cand_paths if cp.get("is_selected")]
        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0]["path"], pred.get("chosen_path"))

    def test_04_dynamic_link_failure_and_wcmp_distribution(self):
        self.post_json("/api/simulate/apply_flow?src=4&dst=7&demand=25.0&duration=30.0")

        fail_res = self.post_json("/api/simulate/link_fail", {"u": 1, "v": 2})
        self.assertEqual(fail_res.get("status"), "success")
        self.assertIn("severed", fail_res.get("active_scenario", ""))

        wcmp_res = self.post_json("/api/simulate/wcmp")
        self.assertEqual(wcmp_res.get("status"), "success")

        rest_res = self.post_json("/api/simulate/link_restore")
        self.assertEqual(rest_res.get("status"), "success")

    def test_05_qos_sla_and_telemetry_history_aggregation(self):
        self.post_json("/api/simulate/inject_burst", {"u": 1, "mbps": 50.0})

        telem = self.get_json("/api/telemetry")
        stats = telem.get("stats", {})
        self.assertIn("jains_fairness_index", stats)
        self.assertIn("bottleneck_utilization_pct", stats)

        history = self.get_json("/api/history")
        self.assertIsInstance(history, list)

        res = self.get_json("/api/verse?topo=tree&protocol=ospf&pattern=jam&flows=10")
        self.assertIn("qos_sla_score", res["metrics"]["DQN (Ours)"])


# ==============================================================================
# TIER 4: REAL-WORLD APPLICATION SCENARIOS
# ==============================================================================
class Tier4RealWorldApplicationScenarios(BaseE2ETestCase):
    """
    Tier 4: Realistic production scenarios, long-running stress loops, and complete pipelines:
      1. 100-Step Dynamic Burst Simulation with Telemetry Streaming
      2. Cascaded Double-Fault Failover Recovery Under Active Traffic
      3. Complete Academic Defense Deliverables Compilation Pipeline
    """

    def tearDown(self):
        self.reset_cluster_and_sim()

    def test_01_one_hundred_step_dynamic_burst_simulation_with_telemetry(self):
        """Exercises 100 consecutive operational cycles simulating stochastic traffic arrival."""
        print("\n [Tier 4] Starting 100-step dynamic burst simulation...")
        start_time = time.time()
        latencies = []

        for step in range(1, 101):
            t0 = time.perf_counter()
            if step % 2 == 0:
                self.post_json("/api/simulate/traffic_burst")
            else:
                s, d = (4, 7) if (step % 4 == 1) else (5, 6)
                self.post_json(f"/api/simulate/apply_flow?src={s}&dst={d}&demand=15.0&duration=10.0")

            telem = self.get_json("/api/telemetry")
            step_lat = (time.perf_counter() - t0) * 1000.0
            latencies.append(step_lat)

            self.assertEqual(telem.get("status"), "success")
            self.assertGreaterEqual(telem.get("stats", {}).get("total_throughput_mbps", 0), 0.0)

        elapsed = time.time() - start_time
        avg_lat = sum(latencies) / len(latencies)
        print(f" [Tier 4] 100-step dynamic simulation completed in {elapsed:.2f}s (Avg step query latency: {avg_lat:.2f}ms)")
        self.assertLess(avg_lat, 150.0, "Average step query latency exceeded 150ms limit")

    def test_02_cascaded_failover_recovery_under_traffic(self):
        """Simulates primary crash -> Standby 1 promotion -> Standby 2 promotion -> Fail-Secure fallback -> Self-healing."""
        self.post_json("/api/simulate/apply_flow?src=4&dst=7&demand=25.0&duration=30.0")

        # Phase 1 Crash: Primary goes down
        res1 = self.post_json("/api/simulate/controller_fail?target=primary")
        self.assertEqual(res1.get("active_leader"), "backup1")
        self.assertLess(res1.get("failover_latency_ms", 100), 50.0)

        # Phase 2 Crash: Backup 1 goes down (double fault cascade)
        res2 = self.post_json("/api/simulate/controller_fail?target=backup1")
        self.assertEqual(res2.get("active_leader"), "backup2")
        self.assertLess(res2.get("failover_latency_ms", 100), 50.0)

        # Phase 3 Crash: Backup 2 goes down (total cluster outage)
        res3 = self.post_json("/api/simulate/controller_fail?target=backup2")
        self.assertEqual(res3.get("active_leader"), "none")
        self.assertEqual(res3.get("cluster_status"), "CRITICAL_ALL_DOWN")
        self.assertEqual(res3.get("data_plane_mode"), "FAIL_SECURE_AUTONOMOUS")

        # Check data plane survival: flow records preserved
        flows = self.get_json("/api/flows")
        self.assertIsInstance(flows, list)

        # Phase 4 Recovery: Self-healing restore of entire cluster
        rec = self.post_json("/api/simulate/controller_recover?target=all")
        self.assertEqual(rec.get("active_leader"), "primary")
        self.assertEqual(rec.get("cluster_status"), "NOMINAL_HEALTHY")

    def test_03_complete_defense_deliverables_compilation_pipeline(self):
        """Validates all academic artifacts, strict page boundaries, and delivery archives."""
        # Check Thesis
        thesis = os.path.join(PROJECT_ROOT, "Project_Report_EC499_Final.pdf")
        self.assertTrue(os.path.exists(thesis))
        r_thesis = pypdf.PdfReader(thesis)
        self.assertEqual(len(r_thesis.pages), 73)

        # Check Handout (Strictly 4 Pages)
        handout = os.path.join(PROJECT_ROOT, "mahermqr.pdf")
        self.assertTrue(os.path.exists(handout))
        r_handout = pypdf.PdfReader(handout)
        self.assertEqual(len(r_handout.pages), 4)

        # Check Companion Handout files
        self.assertTrue(os.path.exists(os.path.join(PROJECT_ROOT, "mahermqr.docx")))
        self.assertTrue(os.path.exists(os.path.join(PROJECT_ROOT, "mahermqr.md")))

        # Check Slides
        self.assertTrue(os.path.exists(os.path.join(PROJECT_ROOT, "EC499_Final_Defense_Presentation.pptx")))
        self.assertTrue(os.path.exists(os.path.join(PROJECT_ROOT, "EC499sildes", "index.html")))

        # Check Graduation Submission ZIP
        sub_zip = os.path.join(PROJECT_ROOT, "Maher_Alqadhi_2210249576_EC499_Final_Graduation_Submission.zip")
        self.assertTrue(os.path.exists(sub_zip))
        self.assertGreater(os.path.getsize(sub_zip), 50_000_000)

        # Check Delivery & Prism packages
        self.assertTrue(os.path.exists(os.path.join(PROJECT_ROOT, "delivery", "Maher_Alqadhi_2210249576_EC499_Final_Delivery.zip")))
        self.assertTrue(os.path.exists(os.path.join(PROJECT_ROOT, "prism", "EC499_Final_Report_Prism.zip")))


# ==============================================================================
# CLI EXECUTION HARNESS & SUMMARY EXPORTER
# ==============================================================================
def run_e2e_opaque_box_suite():
    print("=" * 85)
    print(" 🚀 STARTING EC499 OPAQUE-BOX E2E VALIDATION TEST RUNNER")
    print(" Methodology: 4-Tier Opaque-Box Requirement-Driven Testing")
    print(" Subsystems: REST API, D3QN Model, Routing Baselines, HA Cluster, Deliverables")
    print("=" * 85)

    suite = unittest.TestSuite()
    loader = unittest.TestLoader()

    tier1 = loader.loadTestsFromTestCase(Tier1FeatureCoverage)
    tier2 = loader.loadTestsFromTestCase(Tier2BoundaryAndCornerCases)
    tier3 = loader.loadTestsFromTestCase(Tier3CrossFeatureCombinations)
    tier4 = loader.loadTestsFromTestCase(Tier4RealWorldApplicationScenarios)

    suite.addTests(tier1)
    suite.addTests(tier2)
    suite.addTests(tier3)
    suite.addTests(tier4)

    total_tests = suite.countTestCases()
    print(f"\nDiscovered {total_tests} test cases across 4 tiers:")
    print(f" • Tier 1 (Feature Coverage):            {tier1.countTestCases()} test cases")
    print(f" • Tier 2 (Boundary & Corner Cases):     {tier2.countTestCases()} test cases")
    print(f" • Tier 3 (Cross-Feature Combinations):   {tier3.countTestCases()} test cases")
    print(f" • Tier 4 (Real-World Applications):     {tier4.countTestCases()} test cases\n")

    t_start = time.time()
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    t_duration = time.time() - t_start

    passed = result.wasSuccessful()
    pass_count = total_tests - len(result.failures) - len(result.errors) - len(result.skipped)

    summary = {
        "suite_name": "EC499 Opaque-Box E2E Validation Runner",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "duration_seconds": round(t_duration, 2),
        "total_tests": total_tests,
        "passed_tests": pass_count,
        "failed_tests": len(result.failures),
        "error_tests": len(result.errors),
        "skipped_tests": len(result.skipped),
        "all_passed": passed,
        "tier_breakdown": {
            "tier_1_feature_coverage": tier1.countTestCases(),
            "tier_2_boundary_corner": tier2.countTestCases(),
            "tier_3_cross_feature": tier3.countTestCases(),
            "tier_4_real_world_scenarios": tier4.countTestCases()
        }
    }

    log_dir = os.path.join(BASE_DIR, "logs")
    os.makedirs(log_dir, exist_ok=True)
    results_path = os.path.join(log_dir, "e2e_opaque_box_results.json")
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("\n" + "=" * 85)
    if passed:
        print(f" ✅ ALL {total_tests} E2E OPAQUE-BOX TESTS PASSED CLEANLY IN {t_duration:.2f}s!")
    else:
        print(f" ❌ E2E TEST RUNNER FAILED: {len(result.failures)} Failures, {len(result.errors)} Errors")
    print(f" Summary exported to: {results_path}")
    print("=" * 85)

    return 0 if passed else 1


if __name__ == '__main__':
    sys.exit(run_e2e_opaque_box_suite())
```
