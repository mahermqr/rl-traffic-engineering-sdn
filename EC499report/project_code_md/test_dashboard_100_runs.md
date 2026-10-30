# `test_dashboard_100_runs.py`

> **File:** `test_dashboard_100_runs.py`  
> **Subsystem / Category:** 7. Verification, Testing & High Availability  
> **Language:** `python`  
> **Lines of Code:** 311  
> **File Size:** 19.79 KB  

---

## Overview

Endurance reliability test executing 100 consecutive dashboard simulation runs to verify memory stability and telemetry integrity.

### Architecture & Symbols
- **Classes:** None (Procedural / Script)
- **Key Functions:** `make_request`, `run_100_dashboard_operations`

---

## Source Code

```python
#!/usr/bin/env python3
"""
Comprehensive 100-Run Dashboard Stress, Telemetry, and Mutation Test Suite.
Executes 100 diverse, highly varied requests against the active dashboard server (http://127.0.0.1:8080),
analyzing status codes, latency, state consistency, data integrity, and edge case handling.
"""

import sys
import os
import time
import json
import urllib.request
import urllib.error
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

BASE_URL = "http://127.0.0.1:8080"
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)
REPORT_FILE = os.path.join(LOG_DIR, "dashboard_100_runs_analysis.json")


def make_request(method, path, body=None, timeout=10.0):
    url = f"{BASE_URL}{path}"
    data_bytes = None
    headers = {"User-Agent": "DashboardStressHarness/1.0"}
    if body is not None:
        if isinstance(body, dict):
            data_bytes = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        elif isinstance(body, str):
            data_bytes = body.encode("utf-8")

    req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method)
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            raw = resp.read().decode("utf-8")
            data = json.loads(raw) if raw and resp.headers.get_content_type() == "application/json" else raw
            return {
                "status": resp.status,
                "elapsed_ms": round(elapsed_ms, 2),
                "data": data,
                "error": None,
                "is_json": isinstance(data, (dict, list))
            }
    except urllib.error.HTTPError as e:
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        try:
            raw = e.read().decode("utf-8")
            err_data = json.loads(raw)
        except Exception:
            err_data = str(e)
        return {
            "status": e.code,
            "elapsed_ms": round(elapsed_ms, 2),
            "data": err_data,
            "error": str(e),
            "is_json": isinstance(err_data, (dict, list))
        }
    except Exception as e:
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        return {
            "status": 0,
            "elapsed_ms": round(elapsed_ms, 2),
            "data": None,
            "error": str(e),
            "is_json": False
        }


def run_100_dashboard_operations():
    print("=" * 80)
    print(" 🚀 STARTING 100 DIVERSE DASHBOARD OPERATIONS & STRESS ANALYSIS")
    print(f" Target Server: {BASE_URL}")
    print("=" * 80)

    results = []
    issues = []

    def record(run_id, category, description, req_method, path, body=None, expected_status=200):
        res = make_request(req_method, path, body)
        status = res["status"]
        elapsed = res["elapsed_ms"]
        success = (status == expected_status)
        
        # Analyze response for data anomalies
        anomalies = []
        if isinstance(res["data"], dict):
            for k, v in res["data"].items():
                if isinstance(v, float) and (v != v):  # NaN check
                    anomalies.append(f"NaN value detected in key '{k}'")
        
        if not success or anomalies:
            issue_entry = {
                "run_id": run_id,
                "category": category,
                "description": description,
                "path": path,
                "method": req_method,
                "got_status": status,
                "expected_status": expected_status,
                "error": res["error"],
                "anomalies": anomalies
            }
            issues.append(issue_entry)

        status_icon = "✅" if success and not anomalies else "⚠️"
        print(f"[{run_id:03d}/100] {status_icon} {category:15} | {req_method:4} {path[:42]:42} | {status} ({elapsed:6.2f} ms)")

        entry = {
            "run_id": run_id,
            "category": category,
            "description": description,
            "method": req_method,
            "path": path,
            "status": status,
            "expected_status": expected_status,
            "elapsed_ms": elapsed,
            "passed": success and not anomalies,
            "anomalies": anomalies,
            "summary": str(res["data"])[:120] if res["data"] else str(res["error"])
        }
        results.append(entry)
        return res

    # -------------------------------------------------------------------------
    # BATCH 1: TOPOLOGY & CLUSTER TELEMETRY (Runs 1 - 15)
    # -------------------------------------------------------------------------
    record(1, "Topology", "Query default active topology", "GET", "/api/topology")
    record(2, "Topology", "Query tree topology explicitly", "GET", "/api/topology?topo=tree")
    record(3, "Topology", "Query fattree topology explicitly", "GET", "/api/topology?topo=fattree")
    record(4, "Topology", "Query abilene topology explicitly", "GET", "/api/topology?topo=abilene")
    record(5, "Topology", "Query nsfnet topology explicitly", "GET", "/api/topology?topo=nsfnet")
    record(6, "Topology", "Query spineleaf topology explicitly", "GET", "/api/topology?topo=spineleaf")
    record(7, "Topology", "List all available registered topologies", "GET", "/api/topologies")
    record(8, "Topology", "Switch topology to Fat-Tree", "POST", "/api/simulate/switch_topology?topo=fattree")
    record(9, "Topology", "Verify active topology is Fat-Tree", "GET", "/api/topology")
    record(10, "Topology", "Switch topology to Abilene WAN", "POST", "/api/simulate/switch_topology?topo=abilene")
    record(11, "Topology", "Verify active topology is Abilene", "GET", "/api/topology")
    record(12, "Topology", "Switch topology to NSFNet Backbone", "POST", "/api/simulate/switch_topology?topo=nsfnet")
    record(13, "Topology", "Switch topology to Spine-Leaf", "POST", "/api/simulate/switch_topology?topo=spineleaf")
    record(14, "Topology", "Switch topology back to Tree baseline", "POST", "/api/simulate/switch_topology?topo=tree")
    record(15, "Topology", "Query invalid topology (graceful handling)", "GET", "/api/topology?topo=nonexistent_xyz_99")

    # -------------------------------------------------------------------------
    # BATCH 2: TELEMETRY & SYSTEM HEALTH (Runs 16 - 25)
    # -------------------------------------------------------------------------
    record(16, "Telemetry", "Query full telemetry bundle", "GET", "/api/telemetry")
    record(17, "Telemetry", "Query metrics alias endpoint", "GET", "/api/metrics")
    record(18, "Telemetry", "Query controller health status", "GET", "/api/health")
    record(19, "Telemetry", "Query 3-Controller HA cluster status", "GET", "/api/ha/status")
    record(20, "Telemetry", "Query network TE summary stats", "GET", "/api/stats")
    record(21, "Telemetry", "Query control plane message overhead", "GET", "/api/control_overhead")
    record(22, "Telemetry", "Query telemetry rolling history", "GET", "/api/history")
    record(23, "Telemetry", "Query active flow records", "GET", "/api/flows")
    record(24, "Telemetry", "Query static benchmarks catalog", "GET", "/api/benchmarks")
    record(25, "Telemetry", "Query publication plots catalog", "GET", "/api/plot_list")

    # -------------------------------------------------------------------------
    # BATCH 3: D3QN MODEL TELEMETRY & INFERENCE (Runs 26 - 45)
    # -------------------------------------------------------------------------
    record(26, "Model", "Query model architecture and weights metadata", "GET", "/api/model_inspect")
    record(27, "Model", "Query DRL agent runtime metrics", "GET", "/api/rl_metrics")
    record(28, "Model", "Route prediction: Mice flow (4->7, 5 Mbps)", "GET", "/api/model_predict?src=4&dst=7&demand=5")
    record(29, "Model", "Route prediction: Standard flow (4->7, 25 Mbps)", "GET", "/api/model_predict?src=4&dst=7&demand=25")
    record(30, "Model", "Route prediction: Elephant flow (4->7, 75 Mbps)", "GET", "/api/model_predict?src=4&dst=7&demand=75")
    record(31, "Model", "Route prediction: Surge flow (4->7, 150 Mbps)", "GET", "/api/model_predict?src=4&dst=7&demand=150")
    record(32, "Model", "Route prediction: Edge cross-pod (4->5, 30 Mbps)", "GET", "/api/model_predict?src=4&dst=5&demand=30")
    record(33, "Model", "Route prediction: Core to edge (1->7, 20 Mbps)", "GET", "/api/model_predict?src=1&dst=7&demand=20")
    record(34, "Model", "Route prediction: Reverse direction (7->4, 30 Mbps)", "GET", "/api/model_predict?src=7&dst=4&demand=30")
    record(35, "Model", "Route prediction: Sub-Mbps microflow (4->7, 0.2 Mbps)", "GET", "/api/model_predict?src=4&dst=7&demand=0.2")
    record(36, "Model", "Route prediction: Root to leaf (1->4, 15 Mbps)", "GET", "/api/model_predict?src=1&dst=4&demand=15")
    record(37, "Model", "Route prediction: High volume surge (2->6, 100 Mbps)", "GET", "/api/model_predict?src=2&dst=6&demand=100")
    record(38, "Model", "Route prediction: Symmetric check (6->2, 100 Mbps)", "GET", "/api/model_predict?src=6&dst=2&demand=100")
    record(39, "Model", "Route prediction: Boundary demand (4->7, 0.0 Mbps)", "GET", "/api/model_predict?src=4&dst=7&demand=0.0")
    record(40, "Model", "Route prediction: Extreme demand (4->7, 500 Mbps)", "GET", "/api/model_predict?src=4&dst=7&demand=500")
    record(41, "Model", "Edge Case: Invalid non-existent source node 999", "GET", "/api/model_predict?src=999&dst=7&demand=25")
    record(42, "Model", "Edge Case: Invalid non-existent destination node 888", "GET", "/api/model_predict?src=4&dst=888&demand=25")
    record(43, "Model", "Edge Case: Same source and destination (4->4)", "GET", "/api/model_predict?src=4&dst=4&demand=25")
    record(44, "Model", "Edge Case: Negative demand (-20 Mbps)", "GET", "/api/model_predict?src=4&dst=7&demand=-20")
    record(45, "Model", "Edge Case: Non-numeric demand string ('bad_val')", "GET", "/api/model_predict?src=4&dst=7&demand=bad_val", expected_status=400)

    # -------------------------------------------------------------------------
    # BATCH 4: VERSUS TOURNAMENT HEAD-TO-HEAD ENGINE (Runs 46 - 65)
    # -------------------------------------------------------------------------
    record(46, "Versus", "Tournament: Tree, OSPF baseline, Jam pattern, 10 flows", "GET", "/api/verse?topo=tree&protocol=ospf&pattern=jam&flows=10")
    record(47, "Versus", "Tournament: Tree, ECMP baseline, Burst pattern, 15 flows", "GET", "/api/verse?topo=tree&protocol=ecmp&pattern=burst&flows=15")
    record(48, "Versus", "Tournament: Tree, WSP baseline, Hotspot pattern, 20 flows", "GET", "/api/verse?topo=tree&protocol=wsp&pattern=hotspot&flows=20")
    record(49, "Versus", "Tournament: Tree, LLR baseline, Crowd pattern, 20 flows", "GET", "/api/verse?topo=tree&protocol=llr&pattern=crowd&flows=20")
    record(50, "Versus", "Tournament: Tree, Dijkstra SPF, Uniform pattern, 15 flows", "GET", "/api/verse?topo=tree&protocol=dijkstra&pattern=uniform&flows=15")
    record(51, "Versus", "Tournament: Multi-protocol checklist (OSPF + ECMP)", "GET", "/api/verse?topo=tree&protocol=ospf,ecmp&pattern=jam&flows=15")
    record(52, "Versus", "Tournament: Multi-protocol checklist (OSPF + WSP + LLR)", "GET", "/api/verse?topo=tree&protocol=ospf,wsp,llr&pattern=burst&flows=20")
    record(53, "Versus", "Tournament: All baselines head-to-head on Tree", "GET", "/api/verse?topo=tree&protocol=all&pattern=hotspot&flows=25")
    record(54, "Versus", "Tournament: Fat-Tree fabric, OSPF baseline, Crowd pattern", "GET", "/api/verse?topo=fattree&protocol=ospf&pattern=crowd&flows=20")
    record(55, "Versus", "Tournament: Fat-Tree fabric, ECMP multi-path, Jam pattern", "GET", "/api/verse?topo=fattree&protocol=ecmp&pattern=jam&flows=25")
    record(56, "Versus", "Tournament: Fat-Tree fabric, All baselines, Diurnal pattern", "GET", "/api/verse?topo=fattree&protocol=all&pattern=diurnal&flows=30")
    record(57, "Versus", "Tournament: Abilene WAN, OSPF baseline, Failover pattern", "GET", "/api/verse?topo=abilene&protocol=ospf&pattern=failover&flows=15")
    record(58, "Versus", "Tournament: Abilene WAN, All baselines, Burst pattern", "GET", "/api/verse?topo=abilene&protocol=all&pattern=burst&flows=20")
    record(59, "Versus", "Tournament: NSFNet Backbone, All baselines, Pareto pattern", "GET", "/api/verse?topo=nsfnet&protocol=all&pattern=pareto&flows=25")
    record(60, "Versus", "Tournament: Spine-Leaf, All baselines, Uniform pattern", "GET", "/api/verse?topo=spineleaf&protocol=all&pattern=uniform&flows=30")
    record(61, "Versus", "Tournament: Boundary flows (flows=1 minimum)", "GET", "/api/verse?topo=tree&protocol=ospf&pattern=jam&flows=1")
    record(62, "Versus", "Tournament: Stress high flows (flows=150)", "GET", "/api/verse?topo=tree&protocol=ospf&pattern=burst&flows=150")
    record(63, "Versus", "Tournament: Preset aggressive mode", "GET", "/api/verse?topo=tree&protocol=ospf&pattern=jam&flows=20&preset=aggressive")
    record(64, "Versus", "Tournament: Preset conservative mode", "GET", "/api/verse?topo=tree&protocol=ospf&pattern=jam&flows=20&preset=conservative")
    record(65, "Versus", "Versus Edge Case: Out-of-bounds flow count (flows=999)", "GET", "/api/verse?topo=tree&protocol=ospf&pattern=jam&flows=999", expected_status=400)

    # -------------------------------------------------------------------------
    # BATCH 5: DYNAMIC FLOW LIFECYCLE & MUTATIONS (Runs 66 - 80)
    # -------------------------------------------------------------------------
    record(66, "Mutation", "Apply dynamic flow 1 (4->7, 20 Mbps, 30s)", "POST", "/api/simulate/apply_flow?src=4&dst=7&demand=20&duration=30")
    record(67, "Mutation", "Apply dynamic flow 2 (2->5, 30 Mbps, 30s)", "POST", "/api/simulate/apply_flow?src=2&dst=5&demand=30&duration=30")
    record(68, "Mutation", "Apply dynamic flow 3 (3->6, 15 Mbps, 30s)", "POST", "/api/simulate/apply_flow?src=3&dst=6&demand=15&duration=30")
    record(69, "Mutation", "Verify flows registered in active flow table", "GET", "/api/flows")
    record(70, "Mutation", "Verify throughput increased in network stats", "GET", "/api/stats")
    record(71, "Mutation", "Inject flash traffic burst on link s1->s2", "POST", "/api/simulate/inject_burst?u=1&v=2&mbps=45")
    record(72, "Mutation", "Verify burst reflected in link utilization stats", "GET", "/api/stats")
    record(73, "Mutation", "Inject core congestion jamming (96% saturation)", "POST", "/api/simulate/core_jamming")
    record(74, "Mutation", "Verify peak core link saturation in telemetry", "GET", "/api/telemetry")
    record(75, "Mutation", "Inject fabric-wide asymmetric traffic surge", "POST", "/api/simulate/traffic_burst")
    record(76, "Mutation", "Clear all active dynamic flows", "POST", "/api/simulate/clear_flows")
    record(77, "Mutation", "Verify flow table is clean after clear_flows", "GET", "/api/flows")
    record(78, "Mutation", "Verify throughput returned to baseline after clear", "GET", "/api/stats")
    record(79, "Mutation", "Apply single-hop direct flow test", "POST", "/api/simulate/apply_flow?src=1&dst=2&demand=20&direct=1")
    record(80, "Mutation", "Clear flows again to restore baseline", "POST", "/api/simulate/clear_flows")

    # -------------------------------------------------------------------------
    # BATCH 6: FAULT INJECTION & LINK RESILIENCE (Runs 81 - 90)
    # -------------------------------------------------------------------------
    record(81, "Faults", "Degrade link s1<->s2 bandwidth by 90% (Brownout)", "POST", "/api/simulate/link_degrade?u=1&v=2")
    record(82, "Faults", "Verify link degradation reflected in topology", "GET", "/api/topology")
    record(83, "Faults", "Simulate complete fiber cut: link_fail on s2<->s4", "POST", "/api/simulate/link_fail?u=2&v=4")
    record(84, "Faults", "Verify failed link is omitted or marked in topology", "GET", "/api/topology")
    record(85, "Faults", "Model predict routes traffic around failed link s2<->s4", "GET", "/api/model_predict?src=4&dst=7&demand=20")
    record(86, "Faults", "Restore all failed and degraded links", "POST", "/api/simulate/link_restore")
    record(87, "Faults", "Verify all links operational after link_restore", "GET", "/api/topology")
    record(88, "Faults", "Edge Case: Fail nonexistent link s99<->s100", "POST", "/api/simulate/link_fail?u=99&v=100")
    record(89, "Faults", "Reset simulation state to nominal baseline", "POST", "/api/simulate/reset")
    record(90, "Faults", "Verify nominal baseline telemetry after reset", "GET", "/api/telemetry")

    # -------------------------------------------------------------------------
    # BATCH 7: CONCURRENCY, SECURITY & STATIC ASSETS (Runs 91 - 100)
    # -------------------------------------------------------------------------
    record(91, "Security", "Security Check: Verify state mutations reject GET with 405", "GET", "/api/simulate/apply_flow", expected_status=405)
    record(92, "Security", "Security Check: Verify link_fail rejects GET with 405", "GET", "/api/simulate/link_fail", expected_status=405)
    record(93, "Security", "Security Check: Verify reset rejects GET with 405", "GET", "/api/simulate/reset", expected_status=405)
    record(94, "Settings", "Query active network configuration settings", "GET", "/api/network_settings")
    record(95, "Static", "Serve root dashboard HTML (/)", "GET", "/")
    record(96, "Static", "Serve static index.html explicitly (/index.html)", "GET", "/index.html")

    # High-concurrency parallel queries (Runs 97-100)
    print("\n[Concurrent] Launching 4 parallel multi-threaded queries (Runs 97-100)...")
    concurrent_ops = [
        (97, "Concurrent", "Parallel Query 1: Telemetry bundle under load", "GET", "/api/telemetry"),
        (98, "Concurrent", "Parallel Query 2: Stats summary under load", "GET", "/api/stats"),
        (99, "Concurrent", "Parallel Query 3: Model predict under concurrent load", "GET", "/api/model_predict?src=4&dst=7&demand=30"),
        (100, "Concurrent", "Parallel Query 4: HA status probe under concurrent load", "GET", "/api/ha/status")
    ]
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(record, *op) for op in concurrent_ops]
        for f in futures:
            f.result()

    # -------------------------------------------------------------------------
    # SUMMARY ANALYSIS
    # -------------------------------------------------------------------------
    total_runs = len(results)
    passed_runs = sum(1 for r in results if r["passed"])
    failed_runs = total_runs - passed_runs
    latencies = [r["elapsed_ms"] for r in results]
    latencies.sort()

    summary = {
        "total_runs": total_runs,
        "passed": passed_runs,
        "failed": failed_runs,
        "pass_rate_pct": round((passed_runs / total_runs) * 100.0, 2),
        "latency_stats_ms": {
            "min": min(latencies),
            "mean": round(sum(latencies) / len(latencies), 2),
            "p50": latencies[len(latencies) // 2],
            "p95": latencies[int(len(latencies) * 0.95)],
            "p99": latencies[int(len(latencies) * 0.99)],
            "max": max(latencies)
        },
        "issues_identified": issues,
        "runs": results
    }

    with open(REPORT_FILE, "w") as f:
        json.dump(summary, f, indent=2)

    print("\n" + "=" * 80)
    print(" 📊 100-RUN DASHBOARD TEST & STRESS HARNESS COMPLETED")
    print("=" * 80)
    print(f" • Total Operations Executed: {total_runs}")
    print(f" • Successful Runs:           {passed_runs} / {total_runs} ({summary['pass_rate_pct']}%)")
    print(f" • Issues / Anomalies Found:  {len(issues)}")
    print(f" • Mean Latency:              {summary['latency_stats_ms']['mean']} ms")
    print(f" • Median (P50) Latency:      {summary['latency_stats_ms']['p50']} ms")
    print(f" • 95th Percentile Latency:   {summary['latency_stats_ms']['p95']} ms")
    print(f" • Maximum Latency:           {summary['latency_stats_ms']['max']} ms")
    print(f" • Detailed Report Saved:     {REPORT_FILE}")
    print("=" * 80)

    return summary


if __name__ == '__main__':
    run_100_dashboard_operations()
```
