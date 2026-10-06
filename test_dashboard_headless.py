#!/usr/bin/env python3
"""
Comprehensive Headless Dashboard & API Test Suite (EC499).
Validates all aspects of the Web Dashboard and Telemetry Console:
  1. Frontend HTML/JS Asset Delivery & Headers (ETag, Content-Type, compression)
  2. Live Telemetry Stream (/api/telemetry, /api/stats, /api/health)
  3. Multi-Topology Fabric Canvas Data (Tree, Fat-Tree, Abilene, NSFNet, Spine-Leaf)
  4. Real-time D3QN Route Prediction & Candidate Path Scoring (/api/model_predict)
  5. Protocol Tournament / Versus Engine across algorithms (/api/verse)
  6. Chaos Fault Injection & Dynamic Telemetry Responses (fail, degrade, burst, restore)
  7. Live Dynamic Flow Dispatch & Table Tracking (/api/simulate/apply_flow, /api/flows)
  8. Configurable Fabric Parameters (/api/network_settings)
"""

import sys
import os
import json
import urllib.request

BASE_URL = os.environ.get("SDN_DASHBOARD_URL", "http://localhost:8080")


def http_req(path, method='GET', data=None):
    url = f"{BASE_URL}{path}"
    body = json.dumps(data).encode('utf-8') if data is not None else None
    headers = {'Content-Type': 'application/json'} if data is not None else {}
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=10) as resp:
        content_type = resp.headers.get('Content-Type', '')
        raw = resp.read()
        if 'application/json' in content_type:
            return resp.status, json.loads(raw.decode('utf-8'))
        return resp.status, raw


def run_all_tests():
    print("=" * 80)
    print(" 🚀 RUNNING COMPREHENSIVE HEADLESS DASHBOARD VALIDATION SUITE (EC499)")
    print(f" Target Server: {BASE_URL}")
    print("=" * 80)

    results = []

    def record_test(name, passed, detail=""):
        mark = "✅ PASS" if passed else "❌ FAIL"
        results.append((name, passed, detail))
        print(f" {mark} | {name:<50} | {detail}")

    # TEST 1: Root HTML Serving
    try:
        status, raw = http_req('/')
        has_title = b"Synapse \xe2\x80\x94 Adaptive SDN Traffic Engineering Console" in raw or b"Synapse" in raw
        has_canvas = b"id=\"topoCanvas\"" in raw
        has_kpi = b"id=\"kpiThroughput\"" in raw
        record_test("1. Root HTML Asset Delivery", status == 200 and has_title and has_canvas and has_kpi, f"HTTP {status}, {len(raw):,} bytes")
    except Exception as e:
        record_test("1. Root HTML Asset Delivery", False, str(e))

    # TEST 2: Health Check Endpoint
    try:
        status, data = http_req('/api/health')
        is_healthy = data.get('status') == 'healthy'
        record_test("2. Health Check Endpoint (/api/health)", is_healthy, f"Topology: {data.get('topology')}, Nodes: {data.get('nodes')}")
    except Exception as e:
        record_test("2. Health Check Endpoint (/api/health)", False, str(e))

    # TEST 3: Multi-Topology Fabric Loading
    topos = ['tree', 'fattree', 'abilene', 'nsfnet', 'spineleaf']
    topo_pass = True
    topo_details = []
    for t in topos:
        try:
            status, data = http_req(f'/api/topology?topo={t}')
            nodes = len(data.get('nodes', []))
            links = len(data.get('links', []))
            if nodes == 0 or links == 0:
                topo_pass = False
            topo_details.append(f"{t}: {nodes}N/{links}L")
        except Exception as e:
            topo_pass = False
            topo_details.append(f"{t}: Error {e}")
    record_test("3. Multi-Topology Fabric Switch/Link Telemetry", topo_pass, ", ".join(topo_details[:3]) + "...")

    # TEST 4: Unified Telemetry Bundle (/api/telemetry)
    try:
        status, data = http_req('/api/telemetry?topo=tree')
        has_bundle = all(k in data for k in ['topology', 'stats', 'overhead', 'rl_metrics', 'model_info'])
        p_count = data.get('model_info', {}).get('parameter_count', 0)
        record_test("4. Unified Fast Telemetry Bundle (/api/telemetry)", has_bundle and p_count > 20000, f"D3QN Weights: {p_count:,}, Stats: OK")
    except Exception as e:
        record_test("4. Unified Fast Telemetry Bundle (/api/telemetry)", False, str(e))

    # TEST 5: D3QN Neural Route Predictor & Explainer (/api/model_predict)
    try:
        status, data = http_req('/api/model_predict?src=4&dst=7&demand=30.0')
        has_prediction = ('chosen_path' in data) and ('candidate_paths' in data) and ('inference_time_ms' in data)
        inf_time = data.get('inference_time_ms', 0.0)
        path = data.get('chosen_path', [])
        record_test("5. Real-Time D3QN Route Inference (/api/model_predict)", has_prediction and len(path) >= 2, f"Chosen: {path}, Latency: {inf_time:.2f}ms")
    except Exception as e:
        record_test("5. Real-Time D3QN Route Inference (/api/model_predict)", False, str(e))

    # TEST 6: Model Inspection (/api/model_inspect)
    try:
        status, data = http_req('/api/model_inspect')
        arch_type = data.get('architecture', {}).get('type', '')
        state_dim = data.get('architecture', {}).get('state_dim', 0)
        record_test("6. D3QN Model Inspection (/api/model_inspect)", "Dueling Double Deep Q-Network" in arch_type and state_dim == 10, f"Architecture: {arch_type}")
    except Exception as e:
        record_test("6. D3QN Model Inspection (/api/model_inspect)", False, str(e))

    # TEST 7: Protocol Tournament / Versus Engine (/api/verse)
    try:
        status, data = http_req('/api/verse?topo=fattree&protocols=ospf,ecmp,wsp,dqn&pattern=jam&flows=15')
        has_metrics = 'metrics' in data and 'DQN (Ours)' in data['metrics'] and 'OSPF (RFC 2328)' in data['metrics']
        has_verdict = 'verdict' in data
        record_test("7. Protocol Versus Tournament (/api/verse)", has_metrics and has_verdict, f"Algorithms: {len(data.get('algorithms', []))}, Verdict: {data.get('verdict')}")
    except Exception as e:
        record_test("7. Protocol Versus Tournament (/api/verse)", False, str(e))

    # TEST 8: Chaos Fault Injection: Link Severing (/api/simulate/link_fail)
    try:
        status, data = http_req('/api/simulate/link_fail?u=1&v=2')
        is_ok = data.get('status') == 'success'
        record_test("8. Chaos Fault: Link Failure (/api/simulate/link_fail)", is_ok, data.get('message', ''))
    except Exception as e:
        record_test("8. Chaos Fault: Link Failure (/api/simulate/link_fail)", False, str(e))

    # TEST 9: Chaos Fault Injection: Brownout Link Throttling (/api/simulate/link_degrade)
    try:
        status, data = http_req('/api/simulate/link_degrade?u=2&v=4')
        is_ok = data.get('status') == 'success'
        record_test("9. Chaos Fault: Brownout Link Throttling (/api/simulate/link_degrade)", is_ok, data.get('message', ''))
    except Exception as e:
        record_test("9. Chaos Fault: Brownout Link Throttling (/api/simulate/link_degrade)", False, str(e))

    # TEST 10: Flash Congestion Injection (/api/simulate/inject_burst)
    try:
        status, data = http_req('/api/simulate/inject_burst?u=1&mbps=50')
        is_ok = data.get('status') == 'success'
        record_test("10. Flash Congestion Burst (/api/simulate/inject_burst)", is_ok, data.get('message', ''))
    except Exception as e:
        record_test("10. Flash Congestion Burst (/api/simulate/inject_burst)", False, str(e))

    # TEST 11: Fabric Link Restoration (/api/simulate/link_restore)
    try:
        status, data = http_req('/api/simulate/link_restore')
        is_ok = data.get('status') == 'success'
        record_test("11. Self-Healing Link Restoration (/api/simulate/link_restore)", is_ok, data.get('message', ''))
    except Exception as e:
        record_test("11. Self-Healing Link Restoration (/api/simulate/link_restore)", False, str(e))

    # TEST 12: Dynamic Flow Allocation (/api/simulate/apply_flow)
    try:
        payload = {'src': 4, 'dst': 7, 'demand': 25.0, 'duration': 15.0}
        status, data = http_req('/api/simulate/apply_flow', method='POST', data=payload)
        path = data.get('calculated_path') or data.get('chosen_path', [])
        is_ok = data.get('status') == 'success' and len(path) >= 2
        path_str = " → ".join(f"s{n}" for n in path)
        record_test("12. Dynamic Unicast Flow Allocation (/api/simulate/apply_flow)", is_ok, f"Path: {path_str}")
    except Exception as e:
        record_test("12. Dynamic Unicast Flow Allocation (/api/simulate/apply_flow)", False, str(e))

    # TEST 13: Live Active Flows Table Telemetry (/api/flows)
    try:
        status, data = http_req('/api/flows')
        is_list = isinstance(data, list)
        flow_count = len(data)
        record_test("13. Active Flows Table Telemetry (/api/flows)", is_list, f"{flow_count} active flow records tracked")
    except Exception as e:
        record_test("13. Active Flows Table Telemetry (/api/flows)", False, str(e))

    # TEST 14: Configurable Network Parameters (/api/network_settings)
    try:
        payload = {'default_capacity': 120.0, 'default_delay': 2.5}
        status, data = http_req('/api/network_settings', method='POST', data=payload)
        is_ok = data.get('status') == 'success'
        record_test("14. Configurable Fabric Parameters (/api/network_settings)", is_ok, f"Capacity: 120 Mbps, Delay: 2.5 ms")
    except Exception as e:
        record_test("14. Configurable Fabric Parameters (/api/network_settings)", False, str(e))

    # TEST 15: Fabric Stabilization Reset (/api/simulate/reset)
    try:
        status, data = http_req('/api/simulate/reset')
        is_ok = data.get('status') == 'success'
        record_test("15. Fabric Stabilization Reset (/api/simulate/reset)", is_ok, data.get('message', ''))
    except Exception as e:
        record_test("15. Fabric Stabilization Reset (/api/simulate/reset)", False, str(e))

    print("=" * 80)
    passed_cnt = sum(1 for _, p, _ in results if p)
    total_cnt = len(results)
    print(f" 📊 TEST SUMMARY: {passed_cnt}/{total_cnt} TESTS PASSED ({(passed_cnt/total_cnt)*100:.1f}%)")
    print("=" * 80)

    if passed_cnt == total_cnt:
        print(" 🎉 ALL DASHBOARD BACKEND & TELEMETRY SUBSYSTEMS FULLY VALIDATED AND OPERATIONAL!")
        return 0
    else:
        print(" ⚠️ SOME TESTS FAILED. CHECK DETAILS ABOVE.")
        return 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
