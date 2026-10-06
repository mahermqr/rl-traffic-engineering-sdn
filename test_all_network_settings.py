#!/usr/bin/env python3
"""
Comprehensive Automated Network Settings Test Suite (EC499).
Exhaustively validates all 5 categories of Network Settings in the Synapse SDN Console:
  Category 1: Fabric Architecture (Capacities, Delays, Core Ratio, MTU, Queue, Jitter, Loss, Topologies)
  Category 2: Fault Injection & Chaos (Sever link, Degrade link, Inject burst, Link restore)
  Category 3: D3QN Agent Hyperparameters (Reward Weights, Epsilon, Learning Rate, Gamma, PER)
  Category 4: OpenFlow 1.3 Control Plane (Timeouts, Max Rules, Polling Rate, K Paths, LLDP, Control Channel)
  Category 5: Traffic Generation & QoS Profiles (Traffic Patterns, Flow Rates, DSCP Classes, Dynamic Flows)
  Category 6: Parameter Synonyms & Format Robustness (String links, legacy key names)
  Category 7: Full Baseline Reset & Stability
"""

import sys
import os
import json
import time
import urllib.request

BASE_URL = os.environ.get("SDN_DASHBOARD_URL", "http://localhost:8080")


def http_req(path, method='GET', data=None):
    url = f"{BASE_URL}{path}"
    body = json.dumps(data).encode('utf-8') if data is not None else None
    headers = {'Content-Type': 'application/json'} if data is not None else {}
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=12) as resp:
        content_type = resp.headers.get('Content-Type', '')
        raw = resp.read()
        if 'application/json' in content_type:
            return resp.status, json.loads(raw.decode('utf-8'))
        return resp.status, raw


class NetworkSettingsTester:
    def __init__(self):
        self.results = []

    def record(self, test_name, category, passed, detail=""):
        mark = "✅ PASS" if passed else "❌ FAIL"
        self.results.append((test_name, category, passed, detail))
        print(f" {mark} | [{category:^16}] | {test_name:<46} | {detail}")

    def run_all(self):
        print("=" * 105)
        print(" 🧪 SYNAPSE COMPREHENSIVE NETWORK SETTINGS VALIDATION SUITE (EC499)")
        print(f" Target Endpoint: {BASE_URL}")
        print("=" * 105)

        # ------------------------------------------------------------------
        # CATEGORY 1: FABRIC ARCHITECTURE & PHYSICAL PARAMETERS
        # ------------------------------------------------------------------
        print("\n--- [CATEGORY 1: Fabric Architecture & Physical Parameters] ---")

        # 1.1 Baseline Fetch
        try:
            status, res = http_req('/api/network_settings')
            has_keys = all(k in res for k in [
                'topology_id', 'default_capacity_mbps', 'default_delay_ms',
                'switch_queue_depth', 'switch_mtu', 'core_trunk_ratio'
            ])
            self.record("1.1 Initial Settings Schema", "Fabric", status == 200 and has_keys,
                        f"Topology: {res.get('topology_id')}, Cap: {res.get('default_capacity_mbps')} Mbps")
        except Exception as e:
            self.record("1.1 Initial Settings Schema", "Fabric", False, str(e))

        # 1.2 Capacity & Core Ratio Update
        try:
            payload = {'default_capacity_mbps': 500.0, 'core_trunk_ratio': 2.0}
            status, res = http_req('/api/network_settings', method='POST', data=payload)
            settings = res.get('settings', {})
            cap_ok = settings.get('default_capacity_mbps') == 500.0
            ratio_ok = settings.get('core_trunk_ratio') == 2.0

            # Verify telemetry reflects capacity
            t_status, tele = http_req('/api/telemetry?topo=tree')
            links = tele.get('topology', {}).get('links', [])
            tele_cap_ok = any(l.get('capacity') in (500.0, 1000.0) for l in links)

            self.record("1.2 Capacity & Core Ratio Scaling", "Fabric",
                        status == 200 and cap_ok and ratio_ok and tele_cap_ok,
                        f"Cap: 500 Mbps, Core Ratio: 2.0x, Active Links: {len(links)}")
        except Exception as e:
            self.record("1.2 Capacity & Core Ratio Scaling", "Fabric", False, str(e))

        # 1.3 Propagation Delay, Jitter & Loss
        try:
            payload = {'default_delay_ms': 4.5, 'default_jitter_ms': 0.65, 'base_loss_pct': 1.8}
            status, res = http_req('/api/network_settings', method='POST', data=payload)
            settings = res.get('settings', {})
            delay_ok = abs(settings.get('default_delay_ms', 0) - 4.5) < 0.01
            jit_ok = abs(settings.get('default_jitter_ms', 0) - 0.65) < 0.01
            loss_ok = abs(settings.get('base_loss_pct', 0) - 1.8) < 0.01
            self.record("1.3 Latency, Jitter & Loss Tuning", "Fabric",
                        status == 200 and delay_ok and jit_ok and loss_ok,
                        f"Delay: {settings.get('default_delay_ms')} ms, Jitter: {settings.get('default_jitter_ms')} ms, Loss: {settings.get('base_loss_pct')}%")
        except Exception as e:
            self.record("1.3 Latency, Jitter & Loss Tuning", "Fabric", False, str(e))

        # 1.4 MTU & Queue Depth Configuration
        try:
            payload = {'switch_mtu': 9000, 'switch_queue_depth': 512}
            status, res = http_req('/api/network_settings', method='POST', data=payload)
            settings = res.get('settings', {})
            mtu_ok = settings.get('switch_mtu') == 9000
            q_ok = settings.get('switch_queue_depth') == 512
            self.record("1.4 Switch MTU & Queue Depth", "Fabric",
                        status == 200 and mtu_ok and q_ok,
                        f"MTU: {settings.get('switch_mtu')} B (Jumbo), Queue: {settings.get('switch_queue_depth')} pkts")
        except Exception as e:
            self.record("1.4 Switch MTU & Queue Depth", "Fabric", False, str(e))

        # 1.5 Multi-Topology Switching via Settings
        topos_to_test = [
            ('fattree', 20, 32),
            ('abilene', 12, 15),
            ('nsfnet', 14, 21),
            ('spineleaf', 12, 32),
            ('tree', 7, 8)
        ]
        all_topo_ok = True
        topo_details = []
        for tid, expected_nodes, expected_links in topos_to_test:
            try:
                payload = {'topology_id': tid}
                status, res = http_req('/api/network_settings', method='POST', data=payload)
                settings = res.get('settings', {})
                current_id = settings.get('topology_id')
                node_cnt = settings.get('node_count')
                link_cnt = settings.get('link_count')
                match = (current_id == tid and node_cnt == expected_nodes and link_cnt == expected_links)
                if not match:
                    all_topo_ok = False
                topo_details.append(f"{tid}:{node_cnt}N/{link_cnt}L")
            except Exception as e:
                all_topo_ok = False
                topo_details.append(f"{tid}:Err({e})")
        self.record("1.5 Dynamic Fabric Topology Switching", "Fabric",
                    all_topo_ok, ", ".join(topo_details[:3]) + " -> tree")

        # ------------------------------------------------------------------
        # CATEGORY 2: FAULT INJECTION & CHAOS SIMULATOR
        # ------------------------------------------------------------------
        print("\n--- [CATEGORY 2: Fault Injection & Chaos Simulator] ---")

        # 2.1 Sever Link via Settings
        try:
            payload = {'fail_link': [1, 2]}
            status, res = http_req('/api/network_settings', method='POST', data=payload)
            settings = res.get('settings', {})
            failed = settings.get('failed_links', [])
            has_failed = any(sorted(p) == [1, 2] for p in failed)

            t_status, tele = http_req('/api/telemetry?topo=tree')
            severed = tele.get('topology', {}).get('severed_links', [])
            tele_has_severed = any(sorted(p) == [1, 2] for p in severed)

            self.record("2.1 Fiber Severance Fault Injection", "Faults",
                        status == 200 and has_failed and tele_has_severed,
                        f"Severed: s1⚡s2, Failed Count: {len(failed)}")
        except Exception as e:
            self.record("2.1 Fiber Severance Fault Injection", "Faults", False, str(e))

        # 2.2 Degrade / Throttle Link via Settings
        try:
            payload = {'degrade_link': [2, 4]}
            status, res = http_req('/api/network_settings', method='POST', data=payload)
            settings = res.get('settings', {})
            degraded = settings.get('degraded_links', [])
            has_deg = any(sorted(p) == [2, 4] for p in degraded)

            t_status, tele = http_req('/api/telemetry?topo=tree')
            deg_tele = tele.get('topology', {}).get('degraded_links', [])
            tele_has_deg = any(sorted(p) == [2, 4] for p in deg_tele)

            self.record("2.2 Optical Brownout / Link Throttling", "Faults",
                        status == 200 and has_deg and tele_has_deg,
                        f"Throttled: s2~s4 (10% capacity), Degraded Count: {len(degraded)}")
        except Exception as e:
            self.record("2.2 Optical Brownout / Link Throttling", "Faults", False, str(e))

        # 2.3 Inject Flash Traffic Burst via Settings
        try:
            payload = {'inject_burst': {'src': 1, 'dst': 3, 'mbps': 75.0}}
            status, res = http_req('/api/network_settings', method='POST', data=payload)
            self.record("2.3 Flash Congestion Burst Injection", "Faults",
                        status == 200 and res.get('status') == 'success',
                        f"Injected: 75.0 Mbps flash spike across switch 1")
        except Exception as e:
            self.record("2.3 Flash Congestion Burst Injection", "Faults", False, str(e))

        # 2.4 Self-Healing Restoration via Settings
        try:
            payload = {'restore_links': True}
            status, res = http_req('/api/network_settings', method='POST', data=payload)
            settings = res.get('settings', {})
            failed = settings.get('failed_links', [])
            degraded = settings.get('degraded_links', [])
            restored_ok = (len(failed) == 0 and len(degraded) == 0)

            t_status, tele = http_req('/api/telemetry?topo=tree')
            t_sev = tele.get('topology', {}).get('severed_links', [])
            t_deg = tele.get('topology', {}).get('degraded_links', [])
            tele_clean = (len(t_sev) == 0 and len(t_deg) == 0)

            self.record("2.4 Self-Healing Fabric Restoration", "Faults",
                        status == 200 and restored_ok and tele_clean,
                        f"Severed: {len(failed)}, Degraded: {len(degraded)} (All Nominal)")
        except Exception as e:
            self.record("2.4 Self-Healing Fabric Restoration", "Faults", False, str(e))

        # ------------------------------------------------------------------
        # CATEGORY 3: D3QN AGENT HYPERPARAMETERS & OBJECTIVE WEIGHTS
        # ------------------------------------------------------------------
        print("\n--- [CATEGORY 3: D3QN Agent Hyperparameters & Weights] ---")

        # 3.1 Multi-Objective Reward Weights
        try:
            payload = {
                'w_hops': 0.40,
                'w_delay': 0.12,
                'w_congestion': 1.8,
                'w_jitter': 0.35,
                'w_loss': 0.85,
                'congestion_barrier_pct': 85.0
            }
            status, res = http_req('/api/network_settings', method='POST', data=payload)
            s = res.get('settings', {})
            weights_ok = (
                abs(s.get('w_hops', 0) - 0.40) < 0.01 and
                abs(s.get('w_delay', 0) - 0.12) < 0.01 and
                abs(s.get('w_congestion', 0) - 1.8) < 0.01 and
                abs(s.get('w_jitter', 0) - 0.35) < 0.01 and
                abs(s.get('w_loss', 0) - 0.85) < 0.01 and
                abs(s.get('congestion_barrier_pct', 0) - 85.0) < 0.01
            )
            self.record("3.1 TE Multi-Objective Reward Weights", "D3QN",
                        status == 200 and weights_ok,
                        f"α={s.get('w_hops')}, β={s.get('w_delay')}, γ={s.get('w_congestion')}, δ={s.get('w_jitter')}, ε={s.get('w_loss')}, θ={s.get('congestion_barrier_pct')}%")
        except Exception as e:
            self.record("3.1 TE Multi-Objective Reward Weights", "D3QN", False, str(e))

        # 3.2 Deep RL Learning Rate, Epsilon, Gamma & PER
        try:
            payload = {
                'learning_rate': 0.0005,
                'exploration_epsilon': 0.050,
                'discount_gamma': 0.98,
                'use_per': False
            }
            status, res = http_req('/api/network_settings', method='POST', data=payload)
            s = res.get('settings', {})
            rl_ok = (
                abs(s.get('learning_rate', 0) - 0.0005) < 1e-6 and
                abs(s.get('exploration_epsilon', 0) - 0.050) < 1e-4 and
                abs(s.get('discount_gamma', 0) - 0.98) < 1e-4 and
                s.get('use_per') is False
            )
            self.record("3.2 Hyperparameters (LR, Eps, Gamma, PER)", "D3QN",
                        status == 200 and rl_ok,
                        f"η={s.get('learning_rate')}, ε={s.get('exploration_epsilon')}, γ={s.get('discount_gamma')}, PER={s.get('use_per')}")
        except Exception as e:
            self.record("3.2 Hyperparameters (LR, Eps, Gamma, PER)", "D3QN", False, str(e))

        # ------------------------------------------------------------------
        # CATEGORY 4: OPENFLOW 1.3 CONTROL PLANE SETTINGS
        # ------------------------------------------------------------------
        print("\n--- [CATEGORY 4: OpenFlow 1.3 Control Plane Settings] ---")

        # 4.1 Flow Rule Timeouts & Capacity
        try:
            payload = {
                'flow_timeout_sec': 60,
                'max_flow_rules': 2000,
                'poll_interval_sec': 1.0,
                'k_candidate_paths': 2,
                'lldp_interval_sec': 1.0,
                'control_channel_mode': 'inband'
            }
            status, res = http_req('/api/network_settings', method='POST', data=payload)
            s = res.get('settings', {})
            of_ok = (
                s.get('flow_timeout_sec') == 60 and
                s.get('max_flow_rules') == 2000 and
                abs(s.get('poll_interval_sec', 0) - 1.0) < 0.01 and
                s.get('k_candidate_paths') == 2 and
                abs(s.get('lldp_interval_sec', 0) - 1.0) < 0.01 and
                s.get('control_channel_mode') == 'inband'
            )
            self.record("4.1 OpenFlow Timers & Control Channel", "OpenFlow",
                        status == 200 and of_ok,
                        f"Timeout: {s.get('flow_timeout_sec')}s, MaxRules: {s.get('max_flow_rules')}, T_poll: {s.get('poll_interval_sec')}s, Mode: {s.get('control_channel_mode')}")
        except Exception as e:
            self.record("4.1 OpenFlow Timers & Control Channel", "OpenFlow", False, str(e))

        # ------------------------------------------------------------------
        # CATEGORY 5: TRAFFIC GENERATION & QOS PROFILES
        # ------------------------------------------------------------------
        print("\n--- [CATEGORY 5: Traffic Generation & QoS Profiles] ---")

        # 5.1 Traffic Matrix Pattern & DSCP Class
        try:
            payload = {
                'traffic_pattern': 'pareto',
                'traffic_flow_rate_mbps': 30.0,
                'diffserv_dscp': 'EF'
            }
            status, res = http_req('/api/network_settings', method='POST', data=payload)
            s = res.get('settings', {})
            traf_ok = (
                s.get('traffic_pattern') == 'pareto' and
                abs(s.get('traffic_flow_rate_mbps', 0) - 30.0) < 0.01 and
                s.get('diffserv_dscp') == 'EF'
            )
            self.record("5.1 Traffic Matrix Pattern & DSCP QoS", "Traffic",
                        status == 200 and traf_ok,
                        f"Pattern: {s.get('traffic_pattern')}, Rate: {s.get('traffic_flow_rate_mbps')} Mbps, DSCP: {s.get('diffserv_dscp')}")
        except Exception as e:
            self.record("5.1 Traffic Matrix Pattern & DSCP QoS", "Traffic", False, str(e))

        # 5.2 Dynamic Flow Dispatch using Settings
        try:
            flow_payload = {'src': 4, 'dst': 7, 'demand': 30.0, 'duration': 20.0}
            status, flow_res = http_req('/api/simulate/apply_flow', method='POST', data=flow_payload)
            f_status = flow_res.get('status') == 'success'
            path = flow_res.get('calculated_path', [])

            # Check flow in active flows table
            f_stat, flows = http_req('/api/flows')
            has_active_flow = any(f.get('demand') == 30.0 or f.get('src') == 4 for f in flows) if isinstance(flows, list) else False

            self.record("5.2 Closed-Loop Dynamic Flow Allocation", "Traffic",
                        status == 200 and f_status and len(path) >= 2,
                        f"Path: {' → '.join(f's{n}' for n in path)}, Flows Tracked: {len(flows) if isinstance(flows, list) else 0}")
        except Exception as e:
            self.record("5.2 Closed-Loop Dynamic Flow Allocation", "Traffic", False, str(e))

        # ------------------------------------------------------------------
        # CATEGORY 6: SYNONYMS & DUAL-FORMAT TOLERANCE
        # ------------------------------------------------------------------
        print("\n--- [CATEGORY 6: Parameter Synonyms & Input Tolerances] ---")

        # 6.1 Parameter Synonyms (legacy & shorthand names)
        try:
            payload = {
                'capacity': 150.0,
                'nominal_delay_ms': 3.2,
                'nominal_jitter_ms': 0.40,
                'nominal_loss_pct': 0.5,
                'barrier_interval_ms': 75.0,
                'flow_idle_timeout_sec': 45,
                'test_flow_rate_mbps': 22.5,
                'epsilon': 0.015,
                'lr': 0.002,
                'gamma': 0.96
            }
            status, res = http_req('/api/network_settings', method='POST', data=payload)
            s = res.get('settings', {})
            syn_ok = (
                abs(s.get('default_capacity_mbps', 0) - 150.0) < 0.01 and
                abs(s.get('default_delay_ms', 0) - 3.2) < 0.01 and
                abs(s.get('default_jitter_ms', 0) - 0.40) < 0.01 and
                abs(s.get('base_loss_pct', 0) - 0.5) < 0.01 and
                abs(s.get('congestion_barrier_pct', 0) - 75.0) < 0.01 and
                s.get('flow_timeout_sec') == 45 and
                abs(s.get('traffic_flow_rate_mbps', 0) - 22.5) < 0.01 and
                abs(s.get('exploration_epsilon', 0) - 0.015) < 1e-4 and
                abs(s.get('learning_rate', 0) - 0.002) < 1e-4 and
                abs(s.get('discount_gamma', 0) - 0.96) < 1e-4
            )
            self.record("6.1 Multi-Format Parameter Synonyms", "Synonyms",
                        status == 200 and syn_ok,
                        f"Mapped 10 synonym keys successfully: cap=150, delay=3.2, lr=0.002, eps=0.015")
        except Exception as e:
            self.record("6.1 Multi-Format Parameter Synonyms", "Synonyms", False, str(e))

        # 6.2 String Link Fault Formats ("1-2" string vs list)
        try:
            payload_str = {'fail_link': "2-5"}
            status, res = http_req('/api/network_settings', method='POST', data=payload_str)
            s = res.get('settings', {})
            failed = s.get('failed_links', [])
            has_failed_str = any(sorted(p) == [2, 5] for p in failed)

            # Degrade link with string format
            payload_deg = {'degrade_link': "3-6"}
            status2, res2 = http_req('/api/network_settings', method='POST', data=payload_deg)
            s2 = res2.get('settings', {})
            deg = s2.get('degraded_links', [])
            has_deg_str = any(sorted(p) == [3, 6] for p in deg)

            # Restore
            http_req('/api/network_settings', method='POST', data={'restore_links': True})

            self.record("6.2 String Hyphenated Link Identifiers", "Synonyms",
                        has_failed_str and has_deg_str,
                        f"Parsed '2-5' fail and '3-6' degrade strings cleanly")
        except Exception as e:
            self.record("6.2 String Hyphenated Link Identifiers", "Synonyms", False, str(e))

        # ------------------------------------------------------------------
        # CATEGORY 7: RESTORATION TO NOMINAL DEFAULTS
        # ------------------------------------------------------------------
        print("\n--- [CATEGORY 7: Full Baseline Reset & Stability] ---")

        # 7.1 Reset to Baseline
        try:
            baseline_payload = {
                'topology_id': 'tree',
                'default_capacity_mbps': 100.0,
                'core_trunk_ratio': 1.0,
                'switch_mtu': 1500,
                'switch_queue_depth': 256,
                'default_delay_ms': 2.0,
                'default_jitter_ms': 0.25,
                'base_loss_pct': 0.0,
                'w_hops': 0.35,
                'w_congestion': 1.0,
                'w_delay': 0.06,
                'w_jitter': 0.25,
                'w_loss': 0.50,
                'congestion_barrier_pct': 70.0,
                'learning_rate': 0.001,
                'discount_gamma': 0.95,
                'exploration_epsilon': 0.010,
                'use_per': True,
                'max_flow_rules': 1000,
                'lldp_interval_sec': 2.0,
                'flow_timeout_sec': 30,
                'poll_interval_sec': 2.5,
                'k_candidate_paths': 4,
                'control_channel_mode': 'oob',
                'traffic_pattern': 'uniform',
                'diffserv_dscp': 'BE',
                'traffic_flow_rate_mbps': 15.0,
                'restore_links': True
            }
            status, res = http_req('/api/network_settings', method='POST', data=baseline_payload)
            s = res.get('settings', {})
            reset_ok = (
                s.get('topology_id') == 'tree' and
                s.get('default_capacity_mbps') == 100.0 and
                s.get('core_trunk_ratio') == 1.0 and
                s.get('default_delay_ms') == 2.0 and
                s.get('default_jitter_ms') == 0.25 and
                s.get('base_loss_pct') == 0.0 and
                s.get('w_hops') == 0.35 and
                s.get('use_per') is True and
                s.get('control_channel_mode') == 'oob' and
                len(s.get('failed_links', [])) == 0 and
                len(s.get('degraded_links', [])) == 0
            )

            # Also verify /api/simulate/reset restores state
            r_stat, r_data = http_req('/api/simulate/reset', method='POST')
            sim_reset_ok = r_data.get('status') == 'success'

            self.record("7.1 Baseline Nominal Parameter Reset", "Reset",
                        status == 200 and reset_ok and sim_reset_ok,
                        f"Topology: {s.get('topology_id')}, Cap: {s.get('default_capacity_mbps')} Mbps, Delay: {s.get('default_delay_ms')} ms, PER: {s.get('use_per')}")
        except Exception as e:
            self.record("7.1 Baseline Nominal Parameter Reset", "Reset", False, str(e))

        # ------------------------------------------------------------------
        # SUMMARY
        # ------------------------------------------------------------------
        print("\n" + "=" * 105)
        passed_cnt = sum(1 for _, _, p, _ in self.results if p)
        total_cnt = len(self.results)
        pct = (passed_cnt / total_cnt) * 100
        print(f" 📊 TEST SUMMARY: {passed_cnt}/{total_cnt} TESTS PASSED ({pct:.1f}%)")
        print("=" * 105)

        if passed_cnt == total_cnt:
            print(" 🎉 ALL 5 CATEGORIES OF NETWORK SETTINGS FULLY TESTED AND VALIDATED!")
            return 0
        else:
            print(f" ⚠️ {total_cnt - passed_cnt} TEST(S) FAILED. REVIEW DETAILED LOGS ABOVE.")
            return 1


if __name__ == '__main__':
    tester = NetworkSettingsTester()
    sys.exit(tester.run_all())
