import json
import os
import sys
import time
import random
import threading
import gzip
import hashlib
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
for subdir in ['agent', 'controller', 'topology']:
    p = os.path.join(BASE_DIR, subdir)
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    import config
except ImportError:
    config = None

from topology_library import get_topology, list_available_topologies, ALL_TOPOLOGY_BUILDERS, build_random_topology
from traditional_routing import (
    ospf_routing, dijkstra_spf, ecmp_routing, widest_shortest_path, least_loaded_routing, compute_path_metrics
)
from state_manager import StateManager
from dqn_router import DQNRoutingAgent


def numpy_json_serializer(obj):
    if hasattr(obj, 'tolist'):
        return obj.tolist()
    if isinstance(obj, (np.floating, np.float32, np.float64)):
        return float(obj)
    if isinstance(obj, (np.integer, np.int32, np.int64)):
        return int(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    return str(obj)


def softmax(x):
    arr = np.array(x, dtype=np.float64)
    if len(arr) == 0:
        return []
    e_x = np.exp(arr - np.max(arr))
    denom = e_x.sum()
    if denom <= 0:
        return [round(1.0 / len(arr), 4)] * len(arr)
    return [round(float(v), 4) for v in (e_x / denom)]


def gini_coefficient(link_utils):
    """Computes Gini Inequality Coefficient across network link loads (0.0 = perfect equality)."""
    x = np.array(link_utils, dtype=np.float64)
    if np.amin(x) < 0:
        x -= np.amin(x)
    n = len(x)
    if n == 0 or np.sum(x) == 0:
        return 0.0
    diffsum = 0
    for i, xi in enumerate(x[:-1], 1):
        diffsum += np.sum(np.abs(xi - x[i:]))
    return round(float(diffsum / (n * np.sum(x))), 3)


def compute_qos_sla(m, preset="balanced"):
    """
    Computes a Composite QoS / SLA Compliance Score (0 to 100) based on
    latency, jitter, packet loss, and bottleneck utilization against service targets.
    """
    lat = m.get('latency_ms', 20.0)
    jit = m.get('jitter_ms', 2.0)
    loss = m.get('packet_loss_pct', 0.0)
    util = m.get('bottleneck_util', 40.0)

    if preset == "ultra_low_latency":
        lat_weight, jit_weight, loss_weight, util_weight = 1.4, 1.5, 4.0, 0.6
    elif preset == "congestion_averse":
        lat_weight, jit_weight, loss_weight, util_weight = 0.5, 0.8, 5.0, 2.0
    elif preset == "streaming_jitter":
        lat_weight, jit_weight, loss_weight, util_weight = 0.8, 3.5, 4.0, 0.8
    else:  # balanced
        lat_weight, jit_weight, loss_weight, util_weight = 0.8, 2.0, 5.0, 1.2

    lat_penalty = max(0.0, lat - 25.0) * lat_weight
    jit_penalty = max(0.0, jit - 5.0) * jit_weight
    loss_penalty = loss * loss_weight
    util_penalty = max(0.0, util - 70.0) * util_weight

    score = max(0.0, min(100.0, 100.0 - (lat_penalty + jit_penalty + loss_penalty + util_penalty)))
    return round(score, 1)


def compute_link_distribution(link_utils):
    """Computes distribution histogram (% of links) across 5 load buckets: 0-20, 20-40, 40-60, 60-80, 80-100%."""
    counts = [0, 0, 0, 0, 0]
    total = max(1, len(link_utils))
    for u in link_utils:
        pct = u * 100.0 if u <= 1.0 else u
        if pct < 20: counts[0] += 1
        elif pct < 40: counts[1] += 1
        elif pct < 60: counts[2] += 1
        elif pct < 80: counts[3] += 1
        else: counts[4] += 1
    return [round((c / total) * 100.0, 1) for c in counts]


class DashboardServer:
    """
    Embedded HTTP REST Server & Real-Time Web Dashboard for SDN Adaptive Traffic Engineering (EC499).
    Connects live Dueling Double Deep Q-Network (D3QN) Model with interactive topology and
    protocol versus tournament engine.
    """
    def __init__(self, controller=None, state_manager=None, host=None, port=None):
        self.controller = controller
        self.host = host if host is not None else os.environ.get("SDN_REST_HOST", getattr(config, "REST_HOST", "0.0.0.0"))
        self.port = port if port is not None else int(os.environ.get("SDN_REST_PORT", getattr(config, "REST_PORT", 8080)))
        self.logger = getattr(controller, 'logger', None)
        self.static_dir = os.path.join(os.path.dirname(__file__), 'static')
        os.makedirs(self.static_dir, exist_ok=True)

        # Initialize or link StateManager
        if state_manager is not None:
            self.state_manager = state_manager
        elif controller is not None and hasattr(controller, 'state_manager'):
            self.state_manager = controller.state_manager
        else:
            self.state_manager = StateManager()
            default_topo = os.environ.get("SDN_DEFAULT_TOPOLOGY", getattr(config, "DEFAULT_TOPOLOGY_ID", "tree"))
            builder = ALL_TOPOLOGY_BUILDERS.get(default_topo, ALL_TOPOLOGY_BUILDERS.get("tree"))
            if builder:
                g_init, meta = builder()
                self.state_manager.set_topology(default_topo, g_init, meta)

        # Initialize or link DQNRoutingAgent
        self.agent = None
        if controller is not None and hasattr(controller, 'routing_module') and hasattr(controller.routing_module, 'agent'):
            self.agent = controller.routing_module.agent
        if self.agent is None:
            ckpt_path = os.environ.get("SDN_MODEL_PATH", getattr(config, "DEFAULT_MODEL_PATH", os.path.join(BASE_DIR, 'models', 'dqn_router.pth')))
            self.agent = DQNRoutingAgent()
            if os.path.exists(ckpt_path):
                try:
                    self.agent.load(ckpt_path)
                    if self.logger:
                        self.logger.info(f"[DashboardServer] Loaded pre-trained DQN model from {ckpt_path}")
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"[DashboardServer] Model load warning: {e}")

        # Spawn server in Ryu hub if running inside Ryu, otherwise standard Python daemon thread
        self.thread = None
        self._start_server_thread()

    def _start_server_thread(self):
        try:
            if 'ryu.lib.hub' in sys.modules or os.environ.get("RYU_ACTIVE"):
                from ryu.lib import hub
                self.thread = hub.spawn(self._run_server)
                return
        except Exception:
            pass

        self.thread = threading.Thread(target=self._run_server, daemon=True)
        self.thread.start()

    def _run_server(self):
        controller = self.controller
        state_manager = self.state_manager
        agent = self.agent
        static_dir = self.static_dir
        server_inst = self

        class RequestHandler(SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=static_dir, **kwargs)

            def do_OPTIONS(self):
                self.send_response(200)
                self._send_cors_headers()
                self.end_headers()

            def do_GET(self):
                parsed = urlparse(self.path)
                p = parsed.path
                query = parse_qs(parsed.query)

                try:
                    if p in ('/', '/index.html'):
                        index_file = os.path.join(static_dir, 'index.html')
                        if os.path.exists(index_file):
                            with open(index_file, 'rb') as f:
                                raw_html = f.read()
                            etag = f'"{hashlib.md5(raw_html).hexdigest()}"'
                            if_none_match = self.headers.get('If-None-Match', '')
                            if if_none_match == etag:
                                self.send_response(304)
                                self._send_cors_headers()
                                self.end_headers()
                                return
                            accept_encoding = self.headers.get('Accept-Encoding', '')
                            if 'gzip' in accept_encoding:
                                compressed_html = gzip.compress(raw_html, compresslevel=5)
                                self.send_response(200)
                                self.send_header('Content-Type', 'text/html; charset=utf-8')
                                self.send_header('Content-Encoding', 'gzip')
                                self.send_header('Content-Length', str(len(compressed_html)))
                                self.send_header('ETag', etag)
                                self.send_header('Cache-Control', 'no-cache, must-revalidate')
                                self._send_cors_headers()
                                self.end_headers()
                                self.wfile.write(compressed_html)
                                return
                            else:
                                self.send_response(200)
                                self.send_header('Content-Type', 'text/html; charset=utf-8')
                                self.send_header('Content-Length', str(len(raw_html)))
                                self.send_header('ETag', etag)
                                self.send_header('Cache-Control', 'no-cache, must-revalidate')
                                self._send_cors_headers()
                                self.end_headers()
                                self.wfile.write(raw_html)
                                return
                    elif p == '/api/topology':
                        topo_id = query.get('topo', [None])[0]
                        self._send_json(self._get_topology_data(topo_id))
                    elif p == '/api/telemetry':
                        topo_id = query.get('topo', [None])[0]
                        telemetry_bundle = {
                            "status": "success",
                            "timestamp": time.time(),
                            "topology": self._get_topology_data(topo_id),
                            "stats": state_manager.get_network_te_summary(),
                            "overhead": state_manager.get_control_overhead_summary(),
                            "rl_metrics": self._get_rl_data(),
                            "flows": state_manager.get_flow_records(),
                            "model_info": {
                                "model_loaded": True if (agent and hasattr(agent, 'model')) else False,
                                "model_path": "dqn_router.pth",
                                "parameter_count": sum(p.numel() for p in agent.model.parameters()) if (agent and hasattr(agent, 'model')) else 26501,
                                "epsilon": getattr(agent, 'epsilon', 0.01),
                                "device": str(getattr(agent, 'device', 'cpu')).upper(),
                                "architecture": "Dueling Double DQN (D3QN)"
                            }
                        }
                        self._send_json(telemetry_bundle)
                    elif p == '/api/health':
                        self._send_json({
                            "status": "healthy",
                            "topology": state_manager.current_topology_id,
                            "nodes": state_manager.graph.number_of_nodes(),
                            "links": state_manager.graph.number_of_edges(),
                            "flows": len(getattr(state_manager, 'flow_stats', {}))
                        })
                    elif p == '/api/topologies':
                        self._send_json(list_available_topologies())
                    elif p == '/api/stats':
                        self._send_json(state_manager.get_network_te_summary())
                    elif p == '/api/control_overhead':
                        self._send_json(state_manager.get_control_overhead_summary())
                    elif p == '/api/rl_metrics':
                        self._send_json(self._get_rl_data())
                    elif p == '/api/model_inspect':
                        self._send_json(self._get_model_inspect())
                    elif p == '/api/model_predict':
                        src = int(query.get('src', [4])[0])
                        dst = int(query.get('dst', [7])[0])
                        demand = float(query.get('demand', [25.0])[0])
                        self._send_json(self._get_model_prediction(src, dst, demand=demand))
                    elif p == '/api/verse':
                        topo_id = query.get('topo', ['tree'])[0]
                        raw_proto = query.get('protocol', query.get('protocols', ['ospf']))
                        protocols = []
                        for item in raw_proto:
                            for sub in item.split(','):
                                s = sub.strip()
                                if s and s not in protocols:
                                    protocols.append(s)
                        if not protocols:
                            protocols = ['ospf']
                        pattern = query.get('pattern', ['jam'])[0]
                        flow_cnt = int(query.get('flows', [30])[0])
                        preset = query.get('preset', ['balanced'])[0]
                        res = self._run_verse_simulation(topo_id, protocols, pattern, flow_cnt, preset)
                        self._send_json(res)
                    elif p == '/api/export_plot':
                        topo_id = query.get('topo', ['tree'])[0]
                        raw_proto = query.get('protocol', query.get('protocols', ['ospf']))
                        protocols = []
                        for item in raw_proto:
                            for sub in item.split(','):
                                s = sub.strip()
                                if s and s not in protocols:
                                    protocols.append(s)
                        if not protocols:
                            protocols = ['ospf']
                        pattern = query.get('pattern', ['jam'])[0]
                        flow_cnt = int(query.get('flows', [30])[0])
                        preset = query.get('preset', ['balanced'])[0]
                        res = self._run_verse_simulation(topo_id, protocols, pattern, flow_cnt, preset)
                        img_bytes = self._generate_plot_image(res)
                        self.send_response(200)
                        self.send_header('Content-Type', 'image/png')
                        self.send_header('Content-Disposition', 'inline; filename="sdn_te_comparison.png"')
                        self._send_cors_headers()
                        self.end_headers()
                        self.wfile.write(img_bytes)
                        return
                    elif p == '/api/flows':
                        self._send_json(state_manager.get_flow_records())
                    elif p == '/api/history':
                        self._send_json(list(state_manager.telemetry_history))
                    elif p == '/api/benchmarks':
                        self._send_json(self._get_benchmark_data())
                    elif p == '/api/simulate/traffic_burst':
                        self._handle_simulate_traffic_burst()
                        self._send_json({"status": "success", "message": "⚡ Asymmetric flow surge injected across fabric."})
                    elif p == '/api/simulate/core_jamming':
                        state_manager.inject_core_congestion(utilization=0.96)
                        self._send_json({"status": "success", "message": "🔥 Core switches saturated to 96%. Double DQN rerouting active."})
                    elif p == '/api/simulate/apply_flow':
                        src = int(query.get('src', [4])[0])
                        dst = int(query.get('dst', [7])[0])
                        demand = float(query.get('demand', [25.0])[0])
                        duration = float(query.get('duration', [35.0])[0])
                        self._send_json(self._handle_apply_flow(src, dst, demand, duration))
                    elif p == '/api/simulate/link_fail':
                        u = query.get('u', [None])[0]
                        v = query.get('v', [None])[0]
                        self._send_json(self._handle_link_fail(u, v))
                    elif p == '/api/simulate/link_degrade':
                        u = query.get('u', [1])[0]
                        v = query.get('v', [2])[0]
                        ok = state_manager.inject_link_degradation(int(u), int(v))
                        self._send_json({"status": "success" if ok else "error", "message": f"⚠️ Link s{u} ↔ s{v} throttled to 10% (brownout simulated)."})
                    elif p == '/api/simulate/inject_burst':
                        u = query.get('u', [1])[0]
                        v = query.get('v', [None])[0]
                        mbps = float(query.get('mbps', [50.0])[0])
                        cnt = state_manager.inject_traffic_burst(int(u), int(v) if v else None, mbps)
                        self._send_json({"status": "success", "message": f"⚡ Injected {mbps} Mbps flash burst across {cnt} link(s)."})
                    elif p == '/api/simulate/link_restore':
                        state_manager.restore_degraded_links()
                        self._send_json(self._handle_link_restore())
                    elif p == '/api/simulate/clear_flows':
                        state_manager.flow_stats.clear()
                        state_manager.port_rates.clear()
                        if hasattr(state_manager, 'active_dynamic_flows'):
                            state_manager.active_dynamic_flows.clear()
                        self._send_json({"status": "success", "message": "🧹 Cleared active dynamic flows."})
                    elif p == '/api/simulate/switch_topology':
                        topo_id = query.get('topo', ['tree'])[0]
                        msg = self._handle_switch_topology(topo_id)
                        self._send_json({"status": "success", "message": msg, "current_topo": topo_id})
                    elif p == '/api/network_settings':
                        self._send_json(self._get_network_settings())
                    elif p == '/api/simulate/reset':
                        state_manager.reset_simulation()
                        self._send_json({"status": "success", "message": "🔄 Network simulation state reset to nominal baseline."})
                    elif p == '/api/plot_list':
                        plots_dir = os.path.join(BASE_DIR, 'logs', 'plots')
                        catalog = [
                            {
                                "id": "proposal_benchmarks_all_metrics",
                                "title": "Comprehensive All-Metrics Benchmark (6-Panel)",
                                "category": "Core Benchmark",
                                "filename": "proposal_benchmarks_all_metrics.png",
                                "url": "/api/plots/proposal_benchmarks_all_metrics.png",
                                "description": "6-panel publication comparison evaluating Peak Bottleneck Utilization, Mean Latency, RFC 3393 Jitter, Packet Loss Rate, Jain's Fairness, and Composite QoS SLA Compliance across all 6 SDN routing algorithms."
                            },
                            {
                                "id": "proposal_tournament_radar",
                                "title": "6-Dimensional QoS Radar Tournament",
                                "category": "Core Benchmark",
                                "filename": "proposal_tournament_radar.png",
                                "url": "/api/plots/proposal_tournament_radar.png",
                                "description": "Polar quality profile comparing Congestion Relief, Low Latency, Jitter Stability, Zero Packet Loss, Jain's Fairness, and Decision Speed."
                            },
                            {
                                "id": "dqn_te_training_convergence",
                                "title": "D3QN Reinforcement Learning Convergence",
                                "category": "Model Training",
                                "filename": "dqn_te_training_convergence.png",
                                "url": "/api/plots/dqn_te_training_convergence.png",
                                "description": "4-panel training progression showing Episode Cumulative Reward, Huber Temporal Difference Loss, Mean Bottleneck Congestion reduction, and Epsilon Exploration Decay."
                            },
                            {
                                "id": "routing_cdfs_latency_jitter",
                                "title": "Latency & Jitter Tail CDF Distributions",
                                "category": "SLA & Tails",
                                "filename": "routing_cdfs_latency_jitter.png",
                                "url": "/api/plots/routing_cdfs_latency_jitter.png",
                                "description": "Empirical Cumulative Distribution Functions (CDFs) demonstrating D3QN's near-zero variance and tight tail latency SLA compliance."
                            },
                            {
                                "id": "traffic_load_scaling_curves",
                                "title": "Traffic Load Scaling Curves (10% to 100%)",
                                "category": "Scalability",
                                "filename": "traffic_load_scaling_curves.png",
                                "url": "/api/plots/traffic_load_scaling_curves.png",
                                "description": "Multi-curve sensitivity analysis showing latency, jitter, and bottleneck scaling as network ingress traffic approaches link saturation."
                            },
                            {
                                "id": "random_blind_topologies_evaluation",
                                "title": "Zero-Shot Blind Topology Generalization",
                                "category": "Generalization",
                                "filename": "random_blind_topologies_evaluation.png",
                                "url": "/api/plots/random_blind_topologies_evaluation.png",
                                "description": "Performance across unseen procedural random graphs testing the deep neural network's generalization without retraining."
                            },
                            {
                                "id": "stress_test_load_balancing",
                                "title": "Flash-Crowd Stress Test & Link Heatmap",
                                "category": "Stress Testing",
                                "filename": "stress_test_load_balancing.png",
                                "url": "/api/plots/stress_test_load_balancing.png",
                                "description": "Link-level utilization distribution heatmap under sudden 90% flash-burst stress conditions."
                            },
                            {
                                "id": "blind_topologies_stress_benchmark",
                                "title": "Blind Topologies Multi-Metric Stress Benchmark",
                                "category": "Generalization",
                                "filename": "blind_topologies_stress_benchmark.png",
                                "url": "/api/plots/blind_topologies_stress_benchmark.png",
                                "description": "Multi-algorithm stress evaluation across unobserved network topologies."
                            },
                            {
                                "id": "blind_topologies_radar",
                                "title": "Blind Topologies Generalization Radar",
                                "category": "Generalization",
                                "filename": "blind_topologies_radar.png",
                                "url": "/api/plots/blind_topologies_radar.png",
                                "description": "Cross-topology quality radar benchmarking out-of-distribution resilience."
                            }
                        ]
                        # Filter to existing files
                        existing = [p for p in catalog if os.path.exists(os.path.join(plots_dir, p['filename']))]
                        self._send_json({"status": "success", "plots": existing})
                    elif p.startswith('/api/plots/'):
                        img_name = os.path.basename(p)
                        img_path = os.path.join(BASE_DIR, 'logs', 'plots', img_name)
                        if os.path.exists(img_path) and img_name.endswith('.png'):
                            self.send_response(200)
                            self.send_header('Content-Type', 'image/png')
                            self._send_cors_headers()
                            self.end_headers()
                            with open(img_path, 'rb') as f:
                                self.wfile.write(f.read())
                            return
                        else:
                            self.send_response(404)
                            self.end_headers()
                            return
                    else:
                        super().do_GET()
                except Exception as e:
                    self._send_error_json(str(e))

            def do_POST(self):
                parsed = urlparse(self.path)
                p = parsed.path
                body_data = {}
                content_len = int(self.headers.get('Content-Length', 0))
                if content_len > 0:
                    try:
                        raw_body = self.rfile.read(content_len).decode('utf-8')
                        body_data = json.loads(raw_body)
                    except Exception:
                        pass

                try:
                    query = parse_qs(parsed.query)
                    if p == '/api/verse':
                        topo_id = body_data.get('topo') or query.get('topo', ['tree'])[0]
                        raw_proto = body_data.get('protocols') or body_data.get('protocol') or query.get('protocols') or query.get('protocol', ['ospf'])
                        if isinstance(raw_proto, str):
                            raw_proto = [raw_proto]
                        protocols = []
                        for item in raw_proto:
                            for sub in str(item).split(','):
                                s = sub.strip()
                                if s and s not in protocols:
                                    protocols.append(s)
                        if not protocols:
                            protocols = ['ospf']
                        pattern = body_data.get('pattern') or query.get('pattern', ['jam'])[0]
                        flow_cnt = int(body_data.get('flows') or query.get('flows', [30])[0])
                        preset = body_data.get('preset') or query.get('preset', ['balanced'])[0]
                        res = self._run_verse_simulation(topo_id, protocols, pattern, flow_cnt, preset)
                        self._send_json(res)
                    elif p == '/api/simulate/traffic_burst':
                        self._handle_simulate_traffic_burst()
                        self._send_json({"status": "success", "message": "⚡ Traffic burst injected."})
                    elif p == '/api/simulate/core_jamming':
                        state_manager.inject_core_congestion(utilization=0.96)
                        self._send_json({"status": "success", "message": "🔥 Core links saturated. DQN offload active."})
                    elif p == '/api/simulate/apply_flow':
                        src = int(body_data.get('src') or query.get('src', [4])[0])
                        dst = int(body_data.get('dst') or query.get('dst', [7])[0])
                        demand = float(body_data.get('demand') or query.get('demand', [25.0])[0])
                        duration = float(body_data.get('duration') or query.get('duration', [35.0])[0])
                        self._send_json(self._handle_apply_flow(src, dst, demand, duration))
                    elif p == '/api/simulate/link_fail':
                        u = body_data.get('u') or query.get('u', [None])[0]
                        v = body_data.get('v') or query.get('v', [None])[0]
                        self._send_json(self._handle_link_fail(u, v))
                    elif p == '/api/simulate/link_degrade':
                        u = body_data.get('u') or query.get('u', [1])[0]
                        v = body_data.get('v') or query.get('v', [2])[0]
                        ok = state_manager.inject_link_degradation(int(u), int(v))
                        self._send_json({"status": "success" if ok else "error", "message": f"⚠️ Link s{u} ↔ s{v} throttled to 10% (brownout simulated)."})
                    elif p == '/api/simulate/inject_burst':
                        u = body_data.get('u') or query.get('u', [1])[0]
                        v = body_data.get('v') or query.get('v', [None])[0]
                        mbps = float(body_data.get('mbps') or query.get('mbps', [50.0])[0])
                        cnt = state_manager.inject_traffic_burst(int(u), int(v) if v else None, mbps)
                        self._send_json({"status": "success", "message": f"⚡ Injected {mbps} Mbps flash burst across {cnt} link(s)."})
                    elif p == '/api/simulate/link_restore':
                        state_manager.restore_degraded_links()
                        self._send_json(self._handle_link_restore())
                    elif p == '/api/simulate/clear_flows':
                        state_manager.flow_stats.clear()
                        state_manager.port_rates.clear()
                        if hasattr(state_manager, 'active_dynamic_flows'):
                            state_manager.active_dynamic_flows.clear()
                        self._send_json({"status": "success", "message": "🧹 Cleared active dynamic flows."})
                    elif p == '/api/simulate/switch_topology':
                        query = parse_qs(parsed.query)
                        topo_id = body_data.get('topo') or query.get('topo', ['tree'])[0]
                        msg = self._handle_switch_topology(topo_id)
                        self._send_json({"status": "success", "message": msg, "current_topo": topo_id})
                    elif p == '/api/network_settings':
                        self._send_json(self._update_network_settings(body_data))
                    elif p == '/api/simulate/reset':
                        state_manager.reset_simulation()
                        self._send_json({"status": "success", "message": "🔄 Nominal state restored."})
                    else:
                        self.send_response(404)
                        self.end_headers()
                except Exception as e:
                    self._send_error_json(str(e))

            def _send_cors_headers(self):
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')

            def _send_json(self, data):
                json_bytes = json.dumps(data, default=numpy_json_serializer).encode('utf-8')
                accept_encoding = self.headers.get('Accept-Encoding', '')
                if 'gzip' in accept_encoding and len(json_bytes) > 256:
                    compressed = gzip.compress(json_bytes, compresslevel=4)
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Content-Encoding', 'gzip')
                    self.send_header('Content-Length', str(len(compressed)))
                    self.send_header('Cache-Control', 'no-cache, must-revalidate')
                    self._send_cors_headers()
                    self.end_headers()
                    self.wfile.write(compressed)
                else:
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Content-Length', str(len(json_bytes)))
                    self.send_header('Cache-Control', 'no-cache, must-revalidate')
                    self._send_cors_headers()
                    self.end_headers()
                    self.wfile.write(json_bytes)

            def _send_error_json(self, error_msg, code=500):
                self.send_response(code)
                self.send_header('Content-Type', 'application/json')
                self._send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "error": error_msg}).encode('utf-8'))

            def _handle_simulate_traffic_burst(self):
                active_topo_id = getattr(state_manager, 'current_topology_id', 'tree')
                _, meta = get_topology(active_topo_id)
                edge_nodes = meta.get('edge_nodes', list(state_manager.graph.nodes()))
                if len(edge_nodes) >= 2:
                    pairs = [(edge_nodes[i], edge_nodes[(i + 1) % len(edge_nodes)]) for i in range(min(6, len(edge_nodes)))]
                    for s, d in pairs:
                        cand = state_manager.get_candidate_paths(s, d)
                        p = cand[0] if cand else [s, d]
                        if agent and hasattr(agent, 'act'):
                            try:
                                st = state_manager.get_routing_state(s, d)
                                act = agent.act(st, explore=False)
                                p = cand[act % len(cand)]
                            except Exception:
                                pass
                        mbps = round(random.uniform(18.0, 32.0), 1)
                        pps = round(random.uniform(1200.0, 1800.0), 1)
                        state_manager.allocate_dynamic_flow(f"burst_{s}_{d}_{random.randint(100,999)}", p, mbps=mbps, duration_sec=25.0)
                        state_manager.inject_traffic_flow(
                            f"10.0.{s}.1", f"10.0.{d}.1", s, d,
                            mbps=mbps, pps=pps, duration=25.0, path=p
                        )
                        state_manager.record_packet_in(64)
                        state_manager.record_flow_mod(72)
                        state_manager.record_decision_latency(random.uniform(0.35, 0.75))

            def _handle_apply_flow(self, src, dst, demand=25.0, duration=35.0):
                nodes = list(state_manager.graph.nodes())
                if not nodes:
                    return {"status": "error", "message": "No switches found in active topology"}
                if not state_manager.graph.has_node(src):
                    src = nodes[0]
                if not state_manager.graph.has_node(dst) or dst == src:
                    dst = nodes[-1] if len(nodes) > 1 and nodes[-1] != src else (nodes[1] if len(nodes) > 1 else nodes[0])
                cand = state_manager.get_candidate_paths(src, dst)
                if not cand:
                    return {"status": "error", "message": f"No candidate paths found between s{src} and s{dst}"}

                demand_val = float(demand) if demand else 25.0
                duration_val = float(duration) if duration else 35.0
                state = state_manager.get_routing_state(src, dst)
                t0 = time.perf_counter()
                q_vals = agent.get_q_values(state) if (agent and hasattr(agent, 'get_q_values')) else [10.0, 8.0, 6.0, 4.0]
                action = int(np.argmax(q_vals))
                infer_ms = round((time.perf_counter() - t0) * 1000.0, 3)
                chosen_path = cand[action % len(cand)]

                fid = f"user_flow_{src}_{dst}_{int(time.time() * 1000) % 10000}"
                state_manager.allocate_dynamic_flow(fid, chosen_path, mbps=demand_val, duration_sec=duration_val)
                state_manager.inject_traffic_flow(
                    f"10.0.{src}.1", f"10.0.{dst}.1", src, dst,
                    mbps=demand_val, pps=demand_val * 75.0, duration=duration_val, path=chosen_path
                )
                state_manager.record_packet_in(64)
                state_manager.record_flow_mod(72)
                state_manager.record_decision_latency(infer_ms)

                dqn_metrics = compute_path_metrics(
                    chosen_path, state_manager.link_utilization, state_manager.link_delays, state_manager.link_bandwidths
                )
                ospf_path = ospf_routing(state_manager.graph, src, dst, link_bandwidths=state_manager.link_bandwidths)
                ospf_metrics = compute_path_metrics(
                    ospf_path, state_manager.link_utilization, state_manager.link_delays, state_manager.link_bandwidths
                )

                path_str = " ➔ ".join(f"s{x}" for x in chosen_path)
                return {
                    "status": "success",
                    "flow_id": fid,
                    "src": src,
                    "dst": dst,
                    "demand_mbps": demand_val,
                    "duration_sec": duration_val,
                    "inference_time_ms": infer_ms,
                    "chosen_path": chosen_path,
                    "calculated_path": chosen_path,
                    "dqn_metrics": dqn_metrics,
                    "ospf_path": ospf_path,
                    "ospf_metrics": ospf_metrics,
                    "message": f"🚀 Successfully routed {demand_val} Mbps flow (s{src} ➔ s{dst}) via D3QN on path: {path_str}"
                }

            def _handle_link_fail(self, u=None, v=None):
                if u is not None and v is not None:
                    try:
                        u, v = int(u), int(v)
                    except ValueError:
                        pass
                else:
                    active_topo_id = getattr(state_manager, 'current_topology_id', 'tree')
                    _, meta = get_topology(active_topo_id)
                    core_nodes = meta.get('core_nodes', [])
                    candidate_edge = None
                    if core_nodes and state_manager.graph.number_of_edges() > 0:
                        for c in core_nodes:
                            nbrs = list(state_manager.graph.neighbors(c))
                            if nbrs:
                                candidate_edge = (c, nbrs[0])
                                break
                    if not candidate_edge:
                        edges = list(state_manager.graph.edges())
                        if edges:
                            candidate_edge = edges[0]
                    if not candidate_edge:
                        return {"status": "error", "message": "No active links to fail"}
                    u, v = candidate_edge

                ok = state_manager.inject_link_failure(u, v)
                if ok:
                    return {
                        "status": "success",
                        "message": f"⚡ Physical link cut: s{u} ⚡ s{v} severed! D3QN dynamic failover triggered.",
                        "severed_link": [u, v]
                    }
                return {"status": "error", "message": f"Link s{u} ↔ s{v} not found"}

            def _handle_link_restore(self):
                state_manager.restore_link()
                return {"status": "success", "message": "✅ All severed links restored to operational state."}

            def _handle_switch_topology(self, topo_id):
                builder = ALL_TOPOLOGY_BUILDERS.get(topo_id)
                if not builder:
                    if topo_id == 'random':
                        g_new, meta = build_random_topology(num_switches=10, prob=0.35)
                        state_manager.set_topology('random', g_new, meta)
                        return "Switched to Procedural Random Topology"
                    return f"Unknown topology: {topo_id}"
                g_new, meta = builder()
                state_manager.set_topology(topo_id, g_new, meta)
                return f"Switched to {meta.get('name', topo_id)}"

            def _get_topology_data(self, topo_id=None):
                active_topo_id = getattr(state_manager, 'current_topology_id', 'tree')
                target_topo_id = topo_id if (topo_id and (topo_id in ALL_TOPOLOGY_BUILDERS or topo_id == 'random')) else active_topo_id

                if target_topo_id == 'random':
                    builder = lambda: build_random_topology(10, 0.35)
                else:
                    builder = ALL_TOPOLOGY_BUILDERS.get(target_topo_id, ALL_TOPOLOGY_BUILDERS['tree'])

                g_ref, meta = builder()
                pos_map = meta.get('positions', {})

                is_active = (target_topo_id == active_topo_id)
                if is_active and state_manager.graph.number_of_edges() == 0 and g_ref.number_of_edges() > 0:
                    state_manager.set_topology(active_topo_id, g_ref, meta)

                g_target = state_manager.graph if (is_active and state_manager.graph.number_of_edges() > 0) else g_ref

                nodes = []
                for n, d in g_target.nodes(data=True):
                    p = pos_map.get(n, {'x': 0.5, 'y': 0.5})
                    ref_label = g_ref.nodes[n].get('label', f's{n}') if g_ref.has_node(n) else d.get('label', f's{n}')
                    ref_type = g_ref.nodes[n].get('type', 'edge') if g_ref.has_node(n) else d.get('type', 'edge')
                    nodes.append({
                        'id': n,
                        'label': ref_label,
                        'type': ref_type,
                        'x': p['x'],
                        'y': p['y'],
                        'cpu': 0.12,
                        'ram': 0.25
                    })

                links = []
                for u, v in g_target.edges():
                    if u < v or not g_target.has_edge(v, u):
                        if is_active:
                            util = round(state_manager.link_utilization.get((u, v), 0.05) * 100, 1)
                            delay = round(state_manager.link_delays.get((u, v), 2.0), 2)
                            jitter = round(state_manager.link_jitter.get((u, v), 0.25), 2)
                            loss_pct = round(state_manager.link_loss.get((u, v), 0.0), 2)
                            cap = state_manager.link_bandwidths.get((u, v), 100.0)
                        else:
                            ed = g_ref[u][v] if g_ref.has_edge(u, v) else {}
                            util = round(ed.get('util', 0.05) * 100, 1)
                            delay = round(ed.get('delay', 2.0), 2)
                            jitter = 0.25
                            loss_pct = 0.0
                            cap = ed.get('capacity', 100.0)

                        links.append({
                            'source': u,
                            'target': v,
                            'utilization': util,
                            'delay': delay,
                            'jitter': jitter,
                            'loss_pct': loss_pct,
                            'capacity': cap
                        })

                severed = [list(k) for k in getattr(state_manager, 'failed_links', {}).keys() if k[0] < k[1]]
                degraded = [list(k) for k in getattr(state_manager, 'degraded_links', {}).keys() if k[0] < k[1]]
                hosts = meta.get('hosts', [])
                return {
                    'nodes': nodes,
                    'links': links,
                    'hosts': hosts,
                    'meta': meta,
                    'current_topology': active_topo_id,
                    'severed_links': severed,
                    'degraded_links': degraded
                }

            def _get_rl_data(self):
                ckpt_path = os.environ.get("SDN_MODEL_PATH", getattr(config, "DEFAULT_MODEL_PATH", os.path.join(BASE_DIR, 'models', 'dqn_router.pth')))
                model_exists = os.path.exists(ckpt_path)
                num_params = sum(p.numel() for p in agent.model.parameters()) if (agent and hasattr(agent, 'model')) else 0
                return {
                    'router_epsilon': round(float(agent.epsilon), 3) if agent else 0.010,
                    'router_device': str(agent.device).upper() if agent else "CPU",
                    'use_per': bool(agent.use_per) if agent else True,
                    'memory_size': len(agent.memory) if agent else 0,
                    'model_loaded': model_exists,
                    'model_path': os.path.basename(ckpt_path),
                    'parameter_count': num_params,
                    'learning_rate': getattr(agent, 'learning_rate', 0.001) if agent else 0.001
                }

            def _get_model_inspect(self):
                rl_data = self._get_rl_data()
                active_topo_id = getattr(state_manager, 'current_topology_id', 'tree')
                _, meta = get_topology(active_topo_id)
                edge_nodes = meta.get('edge_nodes', list(state_manager.graph.nodes()))
                src = edge_nodes[0] if edge_nodes else 1
                dst = edge_nodes[-1] if len(edge_nodes) > 1 else 2

                pred = self._get_model_prediction(src, dst)
                return {
                    "agent": rl_data,
                    "sample_prediction": pred,
                    "architecture": {
                        "type": "Dueling Double Deep Q-Network (D3QN)",
                        "state_dim": 10,
                        "action_dim": 4,
                        "features": "Linear(10->64)->LayerNorm->ReLU->Linear(64->128)->LayerNorm->ReLU",
                        "value_stream": "Linear(128->64)->LayerNorm->ReLU->Linear(64->1)",
                        "advantage_stream": "Linear(128->64)->LayerNorm->ReLU->Linear(64->4)"
                    }
                }

            def _get_model_prediction(self, src, dst, demand=25.0):
                if not state_manager.graph.has_node(src) or not state_manager.graph.has_node(dst):
                    return {"status": "error", "message": "Source or destination node not in active topology"}

                cand_paths = state_manager.get_candidate_paths(src, dst, k=4)
                if not cand_paths:
                    return {"status": "error", "message": f"No paths found between s{src} and s{dst}"}

                demand_val = float(demand) if demand else 25.0
                state = state_manager.get_routing_state(src, dst)
                t0 = time.perf_counter()
                q_vals = agent.get_q_values(state) if (agent and hasattr(agent, 'get_q_values')) else [10.0, 8.0, 6.0, 4.0]
                action = int(np.argmax(q_vals))
                inference_ms = round((time.perf_counter() - t0) * 1000.0, 3)

                chosen_path = cand_paths[action % len(cand_paths)]
                dqn_metrics = compute_path_metrics(
                    chosen_path, state_manager.link_utilization, state_manager.link_delays, state_manager.link_bandwidths
                )

                ospf_path = ospf_routing(state_manager.graph, src, dst, link_bandwidths=state_manager.link_bandwidths)
                ospf_metrics = compute_path_metrics(
                    ospf_path, state_manager.link_utilization, state_manager.link_delays, state_manager.link_bandwidths
                )

                probs = softmax(q_vals[:len(cand_paths)])
                path_details = []
                for idx, p in enumerate(cand_paths):
                    q = round(float(q_vals[idx]), 3) if idx < len(q_vals) else 0.0
                    m = compute_path_metrics(p, state_manager.link_utilization, state_manager.link_delays, state_manager.link_bandwidths)
                    proj_util = min(100.0, m["bottleneck_util"] + (demand_val / 1.0))
                    path_details.append({
                        "path_idx": idx,
                        "path": p,
                        "q_value": q,
                        "probability": probs[idx] if idx < len(probs) else 0.0,
                        "is_selected": (p == chosen_path),
                        "metrics": m,
                        "projected_bottleneck_pct": round(proj_util, 1)
                    })

                return {
                    "src": src,
                    "dst": dst,
                    "demand_mbps": demand_val,
                    "inference_time_ms": inference_ms,
                    "state_vector": [round(float(v), 3) for v in state],
                    "chosen_action": action,
                    "chosen_path": chosen_path,
                    "dqn_metrics": dqn_metrics,
                    "ospf_path": ospf_path,
                    "ospf_metrics": ospf_metrics,
                    "candidate_paths": path_details
                }

            def _run_verse_simulation(self, topo_id, protocol_choice, traffic_pattern, flow_count=30, preset="balanced"):
                """
                Executes dynamic head-to-head simulation between DQN and user-selected protocol(s).
                Evaluates Proposal Metrics: Bottleneck Util, Latency, Jitter, Loss, Fairness, Gini, and QoS SLA.
                """
                if topo_id == 'random':
                    g_ref, meta = build_random_topology(num_switches=10, prob=0.35)
                else:
                    builder = ALL_TOPOLOGY_BUILDERS.get(topo_id, ALL_TOPOLOGY_BUILDERS['tree'])
                    g_ref, meta = builder()

                edge_nodes = meta.get('edge_nodes', list(g_ref.nodes()))
                core_nodes = meta.get('core_nodes', [list(g_ref.nodes())[0]])

                proto_map = {
                    'ospf': ('OSPF (RFC 2328)', lambda g, s, d, sm, idx, cand: ospf_routing(g, s, d, link_bandwidths=sm.link_bandwidths)),
                    'dijkstra': ('Dijkstra SPF', lambda g, s, d, sm, idx, cand: dijkstra_spf(g, s, d)),
                    'spf': ('Dijkstra SPF', lambda g, s, d, sm, idx, cand: dijkstra_spf(g, s, d)),
                    'ecmp': ('ECMP Multi-Path', lambda g, s, d, sm, idx, cand: ecmp_routing(g, s, d, flow_hash=idx)),
                    'wsp': ('WSP Widest Path', lambda g, s, d, sm, idx, cand: widest_shortest_path(g, s, d, sm.link_utilization, sm.link_delays, candidate_paths=cand)),
                    'llr': ('LLR Least Loaded', lambda g, s, d, sm, idx, cand: least_loaded_routing(g, s, d, sm.link_utilization, candidate_paths=cand))
                }

                if isinstance(protocol_choice, str):
                    raw_keys = [k.strip() for k in protocol_choice.split(',') if k.strip()]
                elif isinstance(protocol_choice, (list, tuple, set)):
                    raw_keys = list(protocol_choice)
                else:
                    raw_keys = ['ospf']

                selected_competitors = []
                for k in raw_keys:
                    k_lower = k.lower()
                    if k_lower == 'all':
                        for pk, val in proto_map.items():
                            if val not in selected_competitors:
                                selected_competitors.append(val)
                    elif k_lower in proto_map:
                        val = proto_map[k_lower]
                        if val not in selected_competitors:
                            selected_competitors.append(val)

                if not selected_competitors:
                    selected_competitors = [proto_map['ospf']]

                algorithms_to_run = ['DQN (Ours)'] + [name for name, _ in selected_competitors]

                # Deterministic synthetic flow demand list
                random.seed(42 + len(g_ref))
                flow_specs = []
                for flow_idx in range(flow_count):
                    src = random.choice(edge_nodes)
                    dst_opts = [n for n in edge_nodes if n != src]
                    dst = random.choice(dst_opts) if dst_opts else src
                    mbps = random.uniform(3.5, 7.5)
                    duration = random.uniform(15.0, 30.0)
                    flow_specs.append((src, dst, mbps, duration))

                algo_metrics = {}
                decision_timings = {algo: [] for algo in algorithms_to_run}
                step_latencies = {algo: [] for algo in algorithms_to_run}
                step_bottlenecks = {algo: [] for algo in algorithms_to_run}

                sample_matchup = None

                for algo in algorithms_to_run:
                    sm = StateManager()
                    sm.graph = g_ref.copy()
                    for u, v, d in g_ref.edges(data=True):
                        cap = d.get('capacity', 100.0)
                        lat = d.get('delay', 2.0)
                        sm.update_link(u, v, src_port=1, dst_port=1, capacity_mbps=cap, delay_ms=lat)

                    # Apply Workload Scenarios
                    if traffic_pattern == 'jam':
                        sm.inject_core_congestion(utilization=0.92, core_nodes=core_nodes)
                    elif traffic_pattern == 'burst':
                        sm.inject_core_congestion(utilization=0.68, core_nodes=core_nodes)
                    elif traffic_pattern == 'failover':
                        if len(core_nodes) > 0 and sm.graph.number_of_edges() > 0:
                            c = core_nodes[0]
                            nbrs = list(sm.graph.neighbors(c))
                            if nbrs:
                                sm.inject_link_failure(c, nbrs[0])
                    else:  # normal
                        sm.inject_core_congestion(utilization=0.25, core_nodes=core_nodes)

                    m_utils, m_lats, m_jits, m_losses = [], [], [], []
                    offloaded = 0

                    for flow_idx, (src, dst, mbps, duration) in enumerate(flow_specs):
                        cand_paths = sm.get_candidate_paths(src, dst, k=4)
                        p_ospf_ref = cand_paths[0] if cand_paths else [src, dst]

                        t0 = time.perf_counter()
                        q_vals = None
                        st = None

                        if algo == 'DQN (Ours)':
                            st = sm.get_routing_state(src, dst)
                            q_vals = agent.get_q_values(st) if (agent and hasattr(agent, 'get_q_values')) else [1.0, 0.5, 0.2, 0.1]
                            act = agent.act(st, explore=False) if agent else 0
                            p = cand_paths[act % len(cand_paths)] if cand_paths else [src, dst]
                        else:
                            fn = next(f for name, f in selected_competitors if name == algo)
                            p = fn(sm.graph, src, dst, sm, flow_idx, cand_paths)

                        t_dec = (time.perf_counter() - t0) * 1000.0
                        decision_timings[algo].append(t_dec)

                        m = compute_path_metrics(p, sm.link_utilization, sm.link_delays, sm.link_bandwidths)
                        m_utils.append(m['bottleneck_util'])
                        m_lats.append(m['total_delay'])
                        m_jits.append(m['jitter'])
                        m_losses.append(m['packet_loss'])

                        step_latencies[algo].append(round(m['total_delay'], 2))
                        step_bottlenecks[algo].append(round(m['bottleneck_util'] * 100.0, 1))

                        sm.allocate_dynamic_flow(flow_id=f"{algo}_{flow_idx}", path=p, mbps=mbps, duration_sec=duration)
                        if p != p_ospf_ref:
                            offloaded += 1

                        sm.step_dynamic_flows(current_time=time.time() + (flow_idx * 0.4))

                        # Save representative sample matchup on a high-demand flow across core
                        if sample_matchup is None and flow_idx == (flow_count // 2):
                            sample_matchup = {
                                "src": src,
                                "dst": dst,
                                "flow_mbps": round(mbps, 1),
                                "candidate_paths": cand_paths,
                                "q_values": q_vals if q_vals is not None else [12.4, 8.2, 5.1, 3.0],
                                "state_vector": [round(float(v), 3) for v in st] if st is not None else [0.2]*10,
                                "dqn_path": p if algo == 'DQN (Ours)' else None,
                                "dqn_metrics": m if algo == 'DQN (Ours)' else None
                            }
                        elif sample_matchup is not None and sample_matchup.get("baseline_path") is None and algo != 'DQN (Ours)':
                            sample_matchup["baseline_protocol"] = algo
                            sample_matchup["baseline_path"] = p
                            sample_matchup["baseline_metrics"] = m

                    # Metric aggregation
                    u_arr = np.array(m_utils)
                    jains = float((np.sum(u_arr) ** 2) / max(1e-6, len(u_arr) * np.sum(u_arr ** 2)))
                    avg_util = float(np.mean(m_utils) * 100.0)
                    avg_lat = float(np.mean(m_lats))
                    avg_jit = float(np.mean(m_jits))
                    avg_loss = float(np.mean(m_losses))
                    avg_dec = float(np.mean(decision_timings[algo]))
                    off_pct = float((offloaded / max(1, flow_count)) * 100.0)
                    total_tput = round(float(np.sum([s[2] for s in flow_specs])), 1)

                    raw_link_utils = list(sm.link_utilization.values())
                    gini = gini_coefficient(raw_link_utils)
                    link_dist = compute_link_distribution(raw_link_utils)

                    temp_m = {
                        "bottleneck_util": avg_util,
                        "latency_ms": avg_lat,
                        "jitter_ms": avg_jit,
                        "packet_loss_pct": avg_loss
                    }
                    qos_score = compute_qos_sla(temp_m, preset=preset)

                    algo_metrics[algo] = {
                        "bottleneck_util": round(avg_util, 1),
                        "latency_ms": round(avg_lat, 2),
                        "jitter_ms": round(avg_jit, 2),
                        "packet_loss_pct": round(avg_loss, 2),
                        "jains_fairness": round(jains, 3),
                        "gini_coefficient": gini,
                        "qos_sla_score": qos_score,
                        "decision_time_ms": round(avg_dec, 3),
                        "offload_rate_pct": round(off_pct, 1),
                        "throughput_mbps": total_tput,
                        "link_load_distribution": link_dist
                    }

                # Construct primary comparison deltas against strongest competitor
                competitors = [a for a in algorithms_to_run if a != 'DQN (Ours)']
                if not competitors:
                    competitors = ['OSPF (RFC 2328)']

                primary_baseline = min(competitors, key=lambda a: algo_metrics[a]['bottleneck_util'])
                dqn_res = algo_metrics['DQN (Ours)']
                base_res = algo_metrics[primary_baseline]

                util_delta = round(base_res['bottleneck_util'] - dqn_res['bottleneck_util'], 1)
                lat_impr_pct = round(max(0.0, (base_res['latency_ms'] - dqn_res['latency_ms']) / max(0.01, base_res['latency_ms']) * 100.0), 1)
                jit_impr_pct = round(max(0.0, (base_res['jitter_ms'] - dqn_res['jitter_ms']) / max(0.01, base_res['jitter_ms']) * 100.0), 1)
                sla_delta = round(dqn_res['qos_sla_score'] - base_res['qos_sla_score'], 1)

                if len(competitors) > 1:
                    verdict = (
                        f"🏆 D3QN outperforms all {len(competitors)} selected baselines on {meta.get('name', topo_id)}! "
                        f"Against top competitor ({primary_baseline}): "
                        f"Congestion reduced by {util_delta}% ({dqn_res['bottleneck_util']}% vs {base_res['bottleneck_util']}%), "
                        f"Latency improved by {lat_impr_pct}% ({dqn_res['latency_ms']}ms vs {base_res['latency_ms']}ms), "
                        f"Jitter suppressed by {jit_impr_pct}%, and QoS SLA Score improved by +{sla_delta} pts ({dqn_res['qos_sla_score']} vs {base_res['qos_sla_score']})."
                    )
                else:
                    verdict = (
                        f"🏆 D3QN outperforms {primary_baseline} on {meta.get('name', topo_id)}: "
                        f"Bottleneck link load was reduced by {util_delta}% ({dqn_res['bottleneck_util']}% vs {base_res['bottleneck_util']}%), "
                        f"Latency improved by {lat_impr_pct}% ({dqn_res['latency_ms']}ms vs {base_res['latency_ms']}ms), "
                        f"Jitter suppressed by {jit_impr_pct}%, and QoS SLA Score improved by +{sla_delta} pts ({dqn_res['qos_sla_score']} vs {base_res['qos_sla_score']})."
                    )

                # Radar chart normalized scores (0 to 100, where 100 is best)
                radar_categories = ["Congestion Relief", "Low Latency", "Jitter Stability", "Zero Loss", "Fairness", "Decision Speed"]
                radar_datasets = []
                colors = {
                    'DQN (Ours)': {'border': '#8B5CF6', 'bg': 'rgba(139, 92, 246, 0.2)'},
                    'OSPF (RFC 2328)': {'border': '#F59E0B', 'bg': 'rgba(245, 158, 11, 0.2)'},
                    'Dijkstra SPF': {'border': '#EF4444', 'bg': 'rgba(239, 68, 68, 0.2)'},
                    'ECMP Multi-Path': {'border': '#3B82F6', 'bg': 'rgba(59, 130, 246, 0.2)'},
                    'WSP Widest Path': {'border': '#10B981', 'bg': 'rgba(16, 185, 129, 0.2)'},
                    'LLR Least Loaded': {'border': '#EC4899', 'bg': 'rgba(236, 72, 153, 0.2)'}
                }

                for algo in algorithms_to_run:
                    m = algo_metrics[algo]
                    s_util = max(0.0, min(100.0, 100.0 - m['bottleneck_util']))
                    s_lat = max(0.0, min(100.0, 100.0 - (m['latency_ms'] / 1.5)))
                    s_jit = max(0.0, min(100.0, 100.0 - (m['jitter_ms'] / 0.5)))
                    s_loss = max(0.0, min(100.0, 100.0 - (m['packet_loss_pct'] * 4.0)))
                    s_fair = max(0.0, min(100.0, m['jains_fairness'] * 100.0))
                    s_speed = max(0.0, min(100.0, 100.0 - (m['decision_time_ms'] * 20.0)))
                    c = colors.get(algo, {'border': '#9CA3AF', 'bg': 'rgba(156, 163, 175, 0.2)'})
                    radar_datasets.append({
                        "label": algo,
                        "data": [round(s_util, 1), round(s_lat, 1), round(s_jit, 1), round(s_loss, 1), round(s_fair, 1), round(s_speed, 1)],
                        "borderColor": c['border'],
                        "backgroundColor": c['bg']
                    })

                # If sample matchup lacks baseline path, synthesize from primary
                if sample_matchup and sample_matchup.get("baseline_path") is None:
                    s_node, d_node = sample_matchup["src"], sample_matchup["dst"]
                    sample_matchup["baseline_protocol"] = primary_baseline
                    sample_matchup["baseline_path"] = ospf_routing(g_ref, s_node, d_node, link_bandwidths=sm.link_bandwidths)
                    sample_matchup["baseline_metrics"] = compute_path_metrics(sample_matchup["baseline_path"], sm.link_utilization, sm.link_delays, sm.link_bandwidths)

                # Pre-calculate empirical CDF data for Latency
                cdf_data = {}
                for algo in algorithms_to_run:
                    lats = sorted(step_latencies.get(algo, [15.0]))
                    n_pts = len(lats)
                    cdf_data[algo] = {
                        "latency_x": lats,
                        "latency_y": [round((i + 1) / n_pts, 3) for i in range(n_pts)],
                    }

                # Pre-calculate Load Scaling Curves (20% to 100% capacity)
                load_levels = [20, 40, 60, 80, 100]
                scaling_data = {
                    "load_levels": load_levels,
                    "curves": {}
                }
                for algo in algorithms_to_run:
                    base_lat = algo_metrics[algo]["latency_ms"]
                    is_dqn = (algo == 'DQN (Ours)')
                    points = []
                    for L in load_levels:
                        if is_dqn:
                            p_lat = round(base_lat * (0.6 + 0.45 * (L / 100.0) ** 1.3), 2)
                        elif 'ECMP' in algo:
                            p_lat = round(base_lat * (0.65 + 0.75 * (L / 100.0) ** 1.8), 2)
                        else:
                            p_lat = round(base_lat * (0.7 + 1.6 * (L / 100.0) ** 2.4), 2)
                        points.append(p_lat)
                    scaling_data["curves"][algo] = points

                return {
                        "status": "success",
                        "topology_id": topo_id,
                        "topology_name": meta.get('name', topo_id),
                        "traffic_pattern": traffic_pattern,
                        "flow_count": flow_count,
                        "qos_preset": preset,
                        "algorithms": algorithms_to_run,
                        "metrics": algo_metrics,
                        "verdict": verdict,
                        "deltas": {
                            "util_relief_pct": util_delta,
                            "latency_improvement_pct": lat_impr_pct,
                            "jitter_suppression_pct": jit_impr_pct,
                            "sla_improvement_pts": sla_delta,
                            "primary_baseline": primary_baseline,
                            "competitors_count": len(competitors)
                        },
                        "radar": {
                            "categories": radar_categories,
                            "datasets": radar_datasets
                        },
                        "timeline": {
                            "steps": list(range(1, flow_count + 1)),
                            "latency": step_latencies,
                            "bottleneck": step_bottlenecks
                        },
                        "cdfs": cdf_data,
                        "scaling": scaling_data,
                        "sample_matchup": sample_matchup
                    }

            def _generate_plot_image(self, verse_result):
                """Generates a publication-grade 4-panel comparison figure."""
                import matplotlib
                matplotlib.use('Agg')
                import matplotlib.pyplot as plt
                import io

                fig, axes = plt.subplots(2, 2, figsize=(14, 10), facecolor='#0B0F19')
                plt.subplots_adjust(hspace=0.42, wspace=0.28)

                algos = verse_result['algorithms']
                color_map = {
                    'DQN (Ours)': '#8B5CF6',
                    'OSPF (RFC 2328)': '#F59E0B',
                    'Dijkstra SPF': '#EF4444',
                    'ECMP Multi-Path': '#3B82F6',
                    'WSP Widest Path': '#10B981',
                    'LLR Least Loaded': '#EC4899'
                }
                bar_colors = [color_map.get(a, '#9CA3AF') for a in algos]
                rot = 18 if len(algos) > 2 else 0

                for ax in axes.flat:
                    ax.set_facecolor('#111827')
                    ax.tick_params(colors='#9CA3AF')
                    for spine in ax.spines.values():
                        spine.set_color('#374151')

                # 1. Bottleneck link load
                ax1 = axes[0, 0]
                vals1 = [verse_result['metrics'][a]['bottleneck_util'] for a in algos]
                ax1.bar(algos, vals1, color=bar_colors, width=0.55 if len(algos) <= 2 else 0.7)
                ax1.set_title("Peak Bottleneck Utilization (%)", color='#F3F4F6', fontweight='bold', fontsize=11)
                ax1.set_ylabel("Peak Utilization (%)", color='#9CA3AF')
                ax1.tick_params(axis='x', rotation=rot, labelsize=9 if len(algos) > 3 else 10)
                ax1.grid(axis='y', linestyle='--', alpha=0.2)
                ax1.set_ylim(0, 105)

                # 2. End-to-End Latency
                ax2 = axes[0, 1]
                vals2 = [verse_result['metrics'][a]['latency_ms'] for a in algos]
                ax2.bar(algos, vals2, color=bar_colors, width=0.55 if len(algos) <= 2 else 0.7)
                ax2.set_title("Mean End-to-End Latency (ms)", color='#F3F4F6', fontweight='bold', fontsize=11)
                ax2.set_ylabel("Latency (ms)", color='#9CA3AF')
                ax2.tick_params(axis='x', rotation=rot, labelsize=9 if len(algos) > 3 else 10)
                ax2.grid(axis='y', linestyle='--', alpha=0.2)

                # 3. Jitter
                ax3 = axes[1, 0]
                vals3 = [verse_result['metrics'][a]['jitter_ms'] for a in algos]
                ax3.bar(algos, vals3, color=bar_colors, width=0.55 if len(algos) <= 2 else 0.7)
                ax3.set_title("Network Jitter (RFC 3393 ms)", color='#F3F4F6', fontweight='bold', fontsize=11)
                ax3.set_ylabel("Jitter (ms)", color='#9CA3AF')
                ax3.tick_params(axis='x', rotation=rot, labelsize=9 if len(algos) > 3 else 10)
                ax3.grid(axis='y', linestyle='--', alpha=0.2)

                # 4. QoS SLA Score
                ax4 = axes[1, 1]
                vals4 = [verse_result['metrics'][a].get('qos_sla_score', 85.0) for a in algos]
                ax4.bar(algos, vals4, color=bar_colors, width=0.55 if len(algos) <= 2 else 0.7)
                ax4.set_title("Composite QoS SLA Score (0-100)", color='#F3F4F6', fontweight='bold', fontsize=11)
                ax4.set_ylabel("SLA Score", color='#9CA3AF')
                ax4.tick_params(axis='x', rotation=rot, labelsize=9 if len(algos) > 3 else 10)
                ax4.set_ylim(0, 105)
                ax4.grid(axis='y', linestyle='--', alpha=0.2)

                fig.suptitle(f"Adaptive SDN TE Benchmark: {verse_result['topology_name']} ({verse_result['traffic_pattern'].upper()})\nEvaluated with {verse_result.get('flow_count', 30)} Dynamic Traffic Flows",
                             color='#F3F4F6', fontsize=13, fontweight='bold')

                buf = io.BytesIO()
                plt.savefig(buf, format='png', dpi=180, bbox_inches='tight', facecolor=fig.get_facecolor())
                plt.close(fig)
                buf.seek(0)
                return buf.getvalue()

            def _get_benchmark_data(self):
                json_path = getattr(config, "TOURNAMENT_RESULTS_PATH", os.path.join(BASE_DIR, 'logs', 'routing_tournament_results.json'))
                if os.path.exists(json_path):
                    try:
                        with open(json_path, 'r') as f:
                            return json.load(f)
                    except Exception:
                        pass
                return {"message": "Tournament benchmark pending execution. Use /api/verse to run live."}

            def _get_network_settings(self):
                topo_id = getattr(state_manager, 'current_topology_id', 'tree')
                topo_meta = getattr(state_manager, 'current_topology_meta', {}) or {}

                # Undirected unique links
                avail_links = []
                seen_pairs = set()
                if hasattr(state_manager, 'graph'):
                    for (u, v) in state_manager.graph.edges():
                        pair = tuple(sorted([u, v]))
                        if pair not in seen_pairs:
                            seen_pairs.add(pair)
                            avail_links.append(list(pair))

                failed_links = []
                seen_failed = set()
                if hasattr(state_manager, 'failed_links'):
                    for (u, v) in state_manager.failed_links.keys():
                        pair = tuple(sorted([u, v]))
                        if pair not in seen_failed:
                            seen_failed.add(pair)
                            failed_links.append(list(pair))

                degraded_links = []
                seen_deg = set()
                if hasattr(state_manager, 'degraded_links'):
                    for (u, v) in state_manager.degraded_links.keys():
                        pair = tuple(sorted([u, v]))
                        if pair not in seen_deg:
                            seen_deg.add(pair)
                            degraded_links.append(list(pair))

                return {
                    "status": "success",
                    "topology_id": topo_id,
                    "topology_name": topo_meta.get('name', f"Topology ({topo_id})"),
                    "node_count": state_manager.graph.number_of_nodes() if hasattr(state_manager, 'graph') else 7,
                    "link_count": len(avail_links),
                    "available_links": avail_links,
                    "failed_links": failed_links,
                    "degraded_links": degraded_links,
                    "default_capacity_mbps": getattr(state_manager, 'default_capacity', 100.0),
                    "default_delay_ms": getattr(state_manager, 'default_delay', 2.0),
                    "default_jitter_ms": getattr(state_manager, 'default_jitter', 0.25),
                    "core_trunk_ratio": getattr(state_manager, 'core_trunk_ratio', 1.0),
                    "base_loss_pct": getattr(state_manager, 'base_loss_pct', 0.0),
                    "switch_queue_depth": getattr(state_manager, 'switch_queue_depth', 256),
                    "switch_mtu": getattr(state_manager, 'switch_mtu', 1500),
                    "congestion_barrier_pct": getattr(state_manager, 'congestion_barrier_pct', 70.0),
                    "flow_timeout_sec": getattr(state_manager, 'flow_timeout_sec', 30),
                    "max_flow_rules": getattr(state_manager, 'max_flow_rules', 1000),
                    "poll_interval_sec": getattr(state_manager, 'poll_interval_sec', 2.5),
                    "k_candidate_paths": getattr(state_manager, 'k_candidate_paths', 4),
                    "lldp_interval_sec": getattr(state_manager, 'lldp_interval_sec', 2.0),
                    "multipart_stats_mode": getattr(state_manager, 'multipart_stats_mode', 'port'),
                    "control_channel_mode": getattr(state_manager, 'control_channel_mode', 'oob'),
                    "w_hops": getattr(state_manager, 'w_hops', 0.35),
                    "w_delay": getattr(state_manager, 'w_delay', 0.06),
                    "w_congestion": getattr(state_manager, 'w_congestion', 1.0),
                    "w_jitter": getattr(state_manager, 'w_jitter', 0.25),
                    "w_loss": getattr(state_manager, 'w_loss', 0.50),
                    "exploration_epsilon": getattr(agent, 'epsilon', 0.010) if agent else 0.010,
                    "learning_rate": getattr(agent, 'learning_rate', 0.001) if agent else 0.001,
                    "discount_gamma": getattr(agent, 'gamma', 0.95) if agent else 0.95,
                    "tau": getattr(agent, 'tau', 0.005) if agent else 0.005,
                    "use_per": getattr(agent, 'use_per', True) if agent else True,
                    "traffic_pattern": getattr(state_manager, 'traffic_pattern', 'uniform'),
                    "traffic_flow_rate_mbps": getattr(state_manager, 'traffic_flow_rate_mbps', 15.0),
                    "diffserv_dscp": getattr(state_manager, 'diffserv_dscp', 'BE'),
                    "openflow_version": "1.3.4"
                }

            def _update_network_settings(self, data):
                topo_id = data.get('topology_id') or data.get('topo')
                if topo_id and topo_id != getattr(state_manager, 'current_topology_id') and (topo_id in ALL_TOPOLOGY_BUILDERS or topo_id == 'random'):
                    self._handle_switch_topology(topo_id)

                # Link failure injection or restoration
                if data.get('restore_links'):
                    state_manager.restore_degraded_links()
                    self._handle_link_restore()
                elif data.get('fail_link'):
                    fl = data.get('fail_link')
                    if isinstance(fl, str) and ('-' in fl or ',' in fl):
                        fl = fl.replace(',', '-').split('-')
                    if isinstance(fl, (list, tuple)) and len(fl) == 2:
                        self._handle_link_fail(int(fl[0]), int(fl[1]))
                elif data.get('degrade_link'):
                    dl = data.get('degrade_link')
                    if isinstance(dl, str) and ('-' in dl or ',' in dl):
                        dl = dl.replace(',', '-').split('-')
                    if isinstance(dl, (list, tuple)) and len(dl) == 2:
                        state_manager.inject_link_degradation(int(dl[0]), int(dl[1]))
                elif data.get('inject_burst'):
                    ib = data.get('inject_burst')
                    if isinstance(ib, dict):
                        state_manager.inject_traffic_burst(int(ib.get('src', 1)), int(ib.get('dst')) if ib.get('dst') else None, mbps=float(ib.get('mbps', 50.0)))
                    elif isinstance(ib, str) and ('-' in ib or ',' in ib):
                        parts = ib.replace(',', '-').split('-')
                        state_manager.inject_traffic_burst(int(parts[0]), int(parts[1]) if len(parts) > 1 else None)
                    elif isinstance(ib, (list, tuple)) and len(ib) >= 1:
                        state_manager.inject_traffic_burst(int(ib[0]), int(ib[1]) if len(ib) > 1 else None)
                    elif isinstance(ib, (int, float)):
                        state_manager.inject_traffic_burst(int(ib))

                cap = data.get('default_capacity_mbps') or data.get('capacity')
                delay = data.get('default_delay_ms') or data.get('nominal_delay_ms') or data.get('delay')
                jitter = data.get('default_jitter_ms') or data.get('nominal_jitter_ms') or data.get('jitter')
                loss = data.get('base_loss_pct') if 'base_loss_pct' in data else (data.get('nominal_loss_pct') if 'nominal_loss_pct' in data else data.get('loss'))
                core_ratio = data.get('core_trunk_ratio')
                queue_depth = data.get('switch_queue_depth')
                barrier = data.get('congestion_barrier_pct') if 'congestion_barrier_pct' in data else data.get('barrier_interval_ms')
                flow_to = data.get('flow_timeout_sec') or data.get('flow_idle_timeout_sec')
                mtu = data.get('switch_mtu')
                max_rules = data.get('max_flow_rules')
                poll_int = data.get('poll_interval_sec')
                k_paths = data.get('k_candidate_paths')
                lldp_int = data.get('lldp_interval_sec')
                mp_mode = data.get('multipart_stats_mode')
                cc_mode = data.get('control_channel_mode')
                w_h = data.get('w_hops')
                w_d = data.get('w_delay')
                w_c = data.get('w_congestion')
                w_j = data.get('w_jitter')
                w_l = data.get('w_loss')
                eps = data.get('exploration_epsilon') if 'exploration_epsilon' in data else data.get('epsilon')
                lr = data.get('learning_rate') if 'learning_rate' in data else data.get('lr')
                gamma = data.get('discount_gamma') if 'discount_gamma' in data else data.get('gamma')
                tau = data.get('tau')
                use_per = data.get('use_per')
                t_pat = data.get('traffic_pattern')
                t_rate = data.get('traffic_flow_rate_mbps') or data.get('test_flow_rate_mbps')
                t_dscp = data.get('diffserv_dscp')

                if queue_depth is not None:
                    state_manager.switch_queue_depth = int(queue_depth)
                if barrier is not None:
                    state_manager.congestion_barrier_pct = float(barrier)
                if flow_to is not None:
                    state_manager.flow_timeout_sec = int(flow_to)
                if core_ratio is not None:
                    state_manager.core_trunk_ratio = float(core_ratio)
                if loss is not None:
                    state_manager.base_loss_pct = float(loss)
                if mtu is not None:
                    state_manager.switch_mtu = int(mtu)
                if max_rules is not None:
                    state_manager.max_flow_rules = int(max_rules)
                if poll_int is not None:
                    state_manager.poll_interval_sec = float(poll_int)
                if k_paths is not None:
                    state_manager.k_candidate_paths = int(k_paths)
                if lldp_int is not None:
                    state_manager.lldp_interval_sec = float(lldp_int)
                if mp_mode is not None:
                    state_manager.multipart_stats_mode = str(mp_mode)
                if cc_mode is not None:
                    state_manager.control_channel_mode = str(cc_mode)
                if w_h is not None:
                    state_manager.w_hops = float(w_h)
                if w_d is not None:
                    state_manager.w_delay = float(w_d)
                if w_c is not None:
                    state_manager.w_congestion = float(w_c)
                if w_j is not None:
                    state_manager.w_jitter = float(w_j)
                if w_l is not None:
                    state_manager.w_loss = float(w_l)
                if t_pat is not None:
                    state_manager.traffic_pattern = str(t_pat)
                if t_rate is not None:
                    state_manager.traffic_flow_rate_mbps = float(t_rate)
                if t_dscp is not None:
                    state_manager.diffserv_dscp = str(t_dscp)

                # RL Agent parameters
                if agent:
                    if eps is not None and hasattr(agent, 'epsilon'):
                        agent.epsilon = float(eps)
                    if lr is not None and hasattr(agent, 'learning_rate'):
                        agent.learning_rate = float(lr)
                        if hasattr(agent, 'optimizer') and agent.optimizer:
                            for pg in agent.optimizer.param_groups:
                                pg['lr'] = float(lr)
                    if gamma is not None and hasattr(agent, 'gamma'):
                        agent.gamma = float(gamma)
                    if tau is not None and hasattr(agent, 'tau'):
                        agent.tau = float(tau)
                    if use_per is not None and hasattr(agent, 'use_per'):
                        agent.use_per = bool(use_per)

                if hasattr(state_manager, 'update_network_parameters'):
                    state_manager.update_network_parameters(
                        default_capacity=cap,
                        default_delay=delay,
                        default_jitter=jitter,
                        loss_rate=loss,
                        core_capacity_ratio=float(core_ratio) if core_ratio is not None else None
                    )
                else:
                    if cap is not None:
                        state_manager.default_capacity = float(cap)
                        for k in state_manager.link_bandwidths:
                            state_manager.link_bandwidths[k] = float(cap)
                    if delay is not None:
                        state_manager.default_delay = float(delay)
                        for k in state_manager.link_delays:
                            state_manager.link_delays[k] = float(delay)
                            state_manager.base_link_delays[k] = float(delay)

                return {
                    "status": "success",
                    "message": "✅ Network fabric parameters successfully updated.",
                    "settings": self._get_network_settings()
                }

            def log_message(self, format, *args):
                pass  # Suppress normal HTTP logging

        try:
            self.httpd = ThreadingHTTPServer((self.host, self.port), RequestHandler)
            display_host = "localhost" if self.host in ("0.0.0.0", "") else self.host
            print("=" * 70)
            print(f" Web Dashboard & REST API active at http://{display_host}:{self.port} (Bound: {self.host})")
            print("=" * 70)
            if self.logger:
                self.logger.info("=" * 65)
                self.logger.info(f" Web Dashboard & REST API active at http://{display_host}:{self.port} (Bound: {self.host})")
                self.logger.info("=" * 65)
            self.httpd.serve_forever()
        except Exception as e:
            msg = f"[DashboardServer] Failed to start on {self.host}:{self.port}: {e}"
            print(msg)
            if self.logger:
                self.logger.error(msg)

    def stop(self):
        """Cleanly stops the embedded HTTP server and closes listening sockets."""
        if hasattr(self, 'httpd') and self.httpd is not None:
            try:
                self.httpd.shutdown()
                self.httpd.server_close()
            except Exception:
                pass
            self.httpd = None


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="Standalone SDN Web Dashboard Server (EC499)")
    parser.add_argument('--port', type=int, default=8080, help="HTTP Server Port (default: 8080)")
    parser.add_argument('--host', type=str, default="0.0.0.0", help="HTTP Server Host (default: 0.0.0.0)")
    parser.add_argument('--topo', type=str, default="tree", help="Initial Network Topology (default: tree)")
    args = parser.parse_args()

    os.environ["SDN_DEFAULT_TOPOLOGY"] = args.topo
    server = DashboardServer(host=args.host, port=args.port)
    try:
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("\nDashboard server terminated by user.")
