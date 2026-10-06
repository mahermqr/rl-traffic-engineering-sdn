# 📘 Synapse SDN Console — User Manual & Operations Guide
### Reinforcement Learning for Adaptive Traffic Engineering in Software-Defined Networks (EC499)

---

## 📑 Table of Contents
1. [Introduction & System Overview](#1-introduction--system-overview)
2. [Quick Start & Launching the Platform](#2-quick-start--launching-the-platform)
3. [Console Interface & Layout Tour](#3-console-interface--layout-tour)
4. [Interactive Operational Workflows](#4-interactive-operational-workflows)
   - [Workflow A: Real-Time D3QN Route Prediction & Inspection](#workflow-a-real-time-d3qn-route-prediction--inspection)
   - [Workflow B: Protocol Tournament & Benchmark Versus Engine](#workflow-b-protocol-tournament--benchmark-versus-engine)
   - [Workflow C: Chaos Engineering & Fault Injection Simulator](#workflow-c-chaos-engineering--fault-injection-simulator)
   - [Workflow D: Network Fabric & Subsystem Configuration (5 Tabs)](#workflow-d-network-fabric--subsystem-configuration-5-tabs)
   - [Workflow E: 1-Click Interactive Demonstration Scenarios](#workflow-e-1-click-interactive-demonstration-scenarios)
5. [REST API Reference Manual](#5-rest-api-reference-manual)
6. [Automated Testing & Verification](#6-automated-testing--verification)
7. [Troubleshooting & Operational FAQs](#7-troubleshooting--operational-faqs)

---

## 1. Introduction & System Overview

**Synapse** is a carrier-grade Software-Defined Networking (SDN) Traffic Engineering platform powered by a **Dueling Double Deep Q-Network (D3QN)** with **Prioritized Experience Replay (PER)**.

### Core Architecture Components:
1. **Ryu OpenFlow 1.3 Controller (`controller/main_controller.py`)**:
   - Manages OpenFlow switch handshakes, flow table updates (`OFPFlowMod`), packet ingress processing (`OFPPacketIn`), and periodic port/flow multi-part statistics harvesting.
2. **Global Network State Manager (`controller/state_manager.py`)**:
   - Maintains a live NetworkX topology graph, tracking link capacities, utilization, RFC 3393 delay variation (jitter), analytical $M/M/1/K$ packet loss, and host locations.
3. **D3QN Neural Routing Engine (`agent/dqn_router.py`)**:
   - Evaluates a 10-dimensional network state vector for any source-destination switch pair.
   - Decouples state value $V(s)$ from path advantages $A(s, a)$ to dynamically select the optimal route among $K$-candidate shortest paths.
4. **Interactive Synapse Web Console (`controller/web_dashboard.py` + `controller/static/index.html`)**:
   - A dual-theme (Light/Dark) dashboard delivering real-time telemetry, interactive HTML5 canvas topology rendering, protocol tournament benchmarking, and live chaos injection.

```
       ┌────────────────────────────────────────────────────────┐
       │             Synapse Web Dashboard (Port 8080)          │
       │   HTML5 Canvas Graph  •  Chart.js  •  Versus Engine    │
       └───────────────────────────┬────────────────────────────┘
                                   │ REST API / JSON Telemetry
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │               Ryu OpenFlow 1.3 Controller              │
       │           State Manager  •  OpenFlow Handlers          │
       └─────────────────────┬────────────────────┬─────────────┘
                             │                    │
              Decision Query │                    │ OpenFlow 1.3
                             ▼                    ▼
       ┌───────────────────────────┐    ┌───────────────────────┐
       │     D3QN Neural Engine    │    │      SDN Switches     │
       │  Dueling DQN + Polyak PER │    │  Mininet / OVS Fabric │
       └───────────────────────────┘    └───────────────────────┘
```

---

## 2. Quick Start & Launching the Platform

### Prerequisites
* Linux OS (Ubuntu 20.04/22.04 or compatible).
* Python 3.8+ virtual environment (`~/ec499_env` or `./venv`).
* Dependencies installed from `requirements.txt`:
  ```bash
  pip install -r requirements.txt
  ```

### Platform Launch Commands

Start the unified SDN controller, telemetry engine, and dashboard with a single command:

```bash
./run_system.sh
```

### What Happens at Startup:
1. Automatically detects virtual environments (`ec499_env`, `.venv`, `venv`).
2. Starts the **Ryu OpenFlow 1.3 Controller** on port `6633`.
3. Launches the **Synapse Web Dashboard HTTP Server** on `http://localhost:8080`.
4. If run without `sudo`, starts the **Autonomous Simulation Driver** (`simulate_live_traffic.py`) to inject realistic dynamic workloads and drive the live telemetry charts.
5. If run with `sudo`, launches the full **Mininet physical network emulation**.

### Environment Variables & Custom Options

You can override defaults before launching:

```bash
# Example: Change dashboard port, controller port, and default topology
SDN_REST_PORT=9090 SDN_CONTROLLER_PORT=6653 SDN_DEFAULT_TOPOLOGY=fattree ./run_system.sh
```

| Variable | Default | Description |
|:---|:---:|:---|
| `SDN_REST_PORT` | `8080` | Web Dashboard & REST API port |
| `SDN_REST_HOST` | `0.0.0.0` | Bind IP for the web console |
| `SDN_CONTROLLER_PORT` | `6633` | OpenFlow TCP listening port |
| `SDN_DEFAULT_TOPOLOGY` | `tree` | Initial fabric (`tree`, `fattree`, `abilene`, `nsfnet`, `spineleaf`) |

---

## 3. Console Interface & Layout Tour

Navigate your browser to **`http://localhost:8080`**.

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│ 🧠 SYNAPSE   [🌳 Tree ▼]   [⚡ Burst] [💥 Cut] [🔄 Restore]  [☀️ Light] [⚙️] [❓]  │
├──────────────────────────────────────────────────────────────────────────────────┤
│ [ 148.5 Mbps ]  [ 16.4% Peak ]  [ 1.8 ms Lat ]  [ 0.25 ms Jit ]  [ 0.0% Loss ]   │
├────────────────────────────────────────┬─────────────────────────────────────────┤
│                                        │  🧠 D3QN Route Predictor               │
│                                        │  Src: [s4]  Dst: [s7]  Rate: [25.0]     │
│       INTERACTIVE FABRIC CANVAS        │  [🚀 Compute Route]  [🔍 Inspect Agent] │
│                                        ├─────────────────────────────────────────┤
│  • Spring-physics nodes (draggable)    │  📊 Live Telemetry Stream               │
│  • Link color: Green → Yellow → Red    │  • Bottleneck Utilization (60s)         │
│  • Animated flow particles             │  • Mean Latency & RFC 3393 Jitter       │
│  • Fullscreen, Zoom In/Out, Fit-view   │  • Control Plane Overhead (FlowMods)    │
│                                        │  • Dynamic Active Flows Table           │
├────────────────────────────────────────┴─────────────────────────────────────────┤
│  ⚔️ Protocol Tournament / Versus Engine (D3QN vs OSPF vs ECMP vs WSP vs LLR)     │
│  • Multi-Metric Leaderboard  • Radar Chart  • Latency CDFs  • Load Scaling Curves │
└──────────────────────────────────────────────────────────────────────────────────┘
```

### 1. Top Navigation Bar:
* **Fabric Selector**: Switch between `Hierarchical Tree`, `Fat-Tree k=4`, `Abilene WAN`, `NSFNet`, `Spine-Leaf`, or `Random Mesh`.
* **Quick Chaos Toolbar**: Instant buttons for `⚡ Surge`, `💥 Cut`, and `🔄 Restore`.
* **Theme Toggle**: 1-click switch between **Light Mode** (Modern Clean) and **Dark Mode** (Cyberpunk Console).
* **Settings Gear (`⚙️`)**: Opens the 5-category Network Architecture modal.
* **Guide Button (`❓`)**: Opens the built-in reference documentation modal.

### 2. Live KPI Telemetry Ribbon:
* **Aggregated Throughput (Mbps)**: Current sum of all active unicast traffic flows.
* **Bottleneck Utilization (%)**: Maximum single-link saturation level across the fabric.
* **Mean Fabric Latency (ms)**: End-to-end propagation and queuing delay.
* **Mean Jitter (ms)**: RFC 3393 packet delay variation.
* **Packet Loss Rate (%)**: Congestion and bit-error loss.
* **Active Unicast Flows**: Count of tracked dynamic flows.

### 3. Canvas View Controls:
* **Zoom In (`+`)** / **Zoom Out (`-`)**: Scale the network graph.
* **Fit View (`⛶`)**: Auto-centers and scales the network inside the view window.
* **Full Screen Mode**: Expands the topology canvas to true 100vw/100vh display.
* **Interactive Drag**: Click and drag any switch node to reposition it.

---

## 4. Interactive Operational Workflows

### Workflow A: Real-Time D3QN Route Prediction & Inspection

1. Locate the **🧠 D3QN Neural Route Predictor** panel in the right sidebar.
2. Select your **Ingress Switch** (e.g., `s4`) and **Egress Switch** (e.g., `s7`).
3. Set the **Traffic Demand** slider (e.g., `25.0 Mbps`).
4. Click **🚀 Compute Route**.
5. **Observing Results**:
   * The chosen optimal path highlights in vibrant color on the canvas with animated packet particles.
   * The **Candidate Path Pool ($K=4$)** table displays all evaluated paths, their predicted Q-values, hop counts, latencies, and bottleneck capacities.
   * Model inference latency is displayed (typically $< 0.8$ ms).
6. Click **🔍 Inspect Agent** to open the Neural Network modal showing:
   * Total model weights count (26,501 parameters).
   * LayerNorm activation features and Q-value decoupling streams.
   * Active exploration rate ($\epsilon$) and execution device (`cpu` or `cuda`).

---

### Workflow B: Protocol Tournament & Benchmark Versus Engine

Benchmark D3QN against 5 industry-standard routing algorithms under identical network workloads.

1. Scroll down to the **⚔️ Protocol Tournament / Versus Engine** section.
2. Select the **Target Fabric** (e.g., `Fat-Tree Clos Fabric (k=4)` or `Abilene WAN`).
3. Check the **Competing Protocols** you want to benchmark:
   - `D3QN (Ours)` (Deep Reinforcement Learning)
   - `OSPF (RFC 2328)` (Open Shortest Path First)
   - `ECMP (RFC 2992)` (Equal-Cost Multi-Path)
   - `WSP Widest Path` (Widest-Shortest Path)
   - `LLR Least Loaded` (Least-Loaded Dynamic Routing)
   - `Dijkstra SPF` (Shortest Path First)
4. Choose the **Traffic Pattern**:
   - `Jam (Core Saturation)`: High load designed to choke core links.
   - `Bursts (Elephant & Mice)`: Sudden multi-hop flow surges.
   - `Uniform Random`: Balanced traffic across all edge nodes.
   - `Hotspot Server`: Concentrated traffic targeting high-capacity pods.
5. Select the **Active Flow Count** (e.g., `15` or `30` flows) and click **⚔️ Run Tournament Matchup**.
6. **Reviewing Tournament Outputs**:
   - **Verdict Banner**: Clear statistical declaration of the winner and percentage advantages.
   - **Multi-Objective Leaderboard**: Side-by-side comparison of Bottleneck Load, Latency, Jitter, Packet Loss, Jain's Fairness Index, and QoS SLA Score.
   - **Multi-Metric Radar Chart**: Spider plot showing multi-objective trade-offs.
   - **Latency CDF Distribution**: Empirical Cumulative Distribution Function comparing tail latencies.
   - **Load Scaling Curves**: Performance curves as network utilization scales from 20% to 100%.
   - **Export Report**: Click **📋 Copy Markdown** or **💾 Export JSON** to export thesis-ready benchmark tables.

---

### Workflow C: Chaos Engineering & Fault Injection Simulator

Stress-test D3QN's autonomous self-healing and rerouting capabilities:

1. **Fiber Cut (Physical Link Severance)**:
   - In the quick toolbar or Settings modal, click **💥 Sever Link** (e.g., `s1 ⚡ s2`).
   - The link visually turns dashed red on the canvas.
   - Run a route prediction through `s1` $\to$ `s2`. D3QN automatically reroutes packets around the broken link with zero packet drops.
2. **Optical Brownout (Degraded Link Throttling)**:
   - Click **⚠️ Brownout Link** on a targeted edge (e.g., `s2 ~ s4`).
   - The link capacity is throttled to 10% and latency spikes by 5×.
   - D3QN detects the degradation and shifts high-bandwidth flows to alternative paths.
3. **Flash Congestion Burst**:
   - Click **⚡ Flash Burst** to inject a sudden 50–75 Mbps traffic surge into Switch 1.
   - Observe link utilization color change to amber/red and queue depths adjust.
4. **Self-Healing Recovery**:
   - Click **🔄 Restore All** to re-establish all links to 100% operational baseline capacity.

---

### Workflow D: Network Fabric & Subsystem Configuration (5 Tabs)

Click the **⚙️ Settings** icon in the navigation bar to open the **Network Architecture Modal**:

#### Tab 1: 🌐 Fabric Architecture & Physical Parameters
* **Fabric Topology**: Switch active topology between `tree`, `fattree`, `abilene`, `nsfnet`, `spineleaf`, and `random`.
* **Switch MTU**: Toggle between Standard Ethernet (`1500 B`) and Jumbo Frames (`9000 B`).
* **Switch Queue Depth**: Adjust buffer depth from `64` to `1024 pkts`.
* **Link Capacities**: Set nominal bandwidth (`50`, `100`, `500`, `1000 Mbps`).
* **Core Trunk Multiplier**: Configure core backbone oversubscription (`1.0×`, `2.0×`, `5.0×`, `10.0×`).
* **Propagation Latency ($t_{prop}$)**: Slide from `0.5 ms` to `25.0 ms`.
* **Delay Variation (Jitter)**: Set baseline jitter from `0.05 ms` to `2.0 ms`.
* **Physical Packet Loss**: Configure baseline bit-error loss from `0.0%` to `5.0%`.

#### Tab 2: 💥 Faults & Chaos Testing
* Select specific links from the dropdown list.
* Perform targeted cuts, throttles, and flash bursts on individual switch pairs.
* View live status of severed and degraded links.

#### Tab 3: 🧠 D3QN Agent Hyperparameters
* **Multi-Objective Reward Weights**:
  - Hop Count Weight ($\alpha$): `0.0` – `1.0`
  - Queuing Delay Weight ($\beta$): `0.0` – `0.20`
  - Congestion Multiplier ($\gamma$): `0.2×` – `3.0×`
  - Jitter Stability Weight ($\delta$): `0.0` – `1.0`
  - Packet Loss Penalty ($\epsilon$): `0.0` – `2.0`
  - Congestion Barrier Threshold ($\theta_{cong}$): `50%` – `95%`
* **Learning Hyperparameters**:
  - Learning Rate ($\eta$): `0.0001` (conservative) to `0.005` (aggressive).
  - Exploration Epsilon ($\epsilon$): `0.001` to `0.200`.
  - Discount Factor ($\gamma$): `0.80` to `0.99`.
  - Replay Buffer: Toggle between Prioritized Experience Replay (PER) and Uniform Random Replay.

#### Tab 4: 📡 OpenFlow 1.3 Control Plane
* **Flow Rule Timeout**: Set idle/hard timeout between `10s` and `180s`.
* **Max Flow Rules per Switch**: Configure TCAM table capacity (`500` to `4,000` rules).
* **Telemetry Polling Interval ($T_{poll}$)**: Set frequency (`1.0s`, `2.5s`, `5.0s`).
* **Candidate Path Pool ($K$)**: Select between $K=2$, $K=4$, or $K=6$ paths.
* **LLDP Discovery Interval**: Configure topology sensing frequency (`1.0s` to `5.0s`).
* **Control Plane Channel**: Choose between Dedicated Out-of-Band (`oob`) and In-Band (`inband`).

#### Tab 5: 🚦 Traffic Generation & QoS Profiles
* **Workload Pattern**: Choose `Uniform Random`, `Data Center Hotspot`, `Pareto Burst`, or `Diurnal Cyclical`.
* **Flow Bandwidth Rate**: Select default flow rates (`5.0`, `15.0`, `30.0`, `50.0 Mbps`).
* **DiffServ DSCP Marking**: Set QoS class:
  - `BE` (Best Effort - RFC 2474 Default)
  - `AF41` (Assured Forwarding - Low Drop Priority)
  - `EF` (Expedited Forwarding - Ultra-Low Latency)
* **Instant Unicast Flow Injection**: Click **🚀 Inject Instant Test Flow** to dispatch a live flow between edge switches.

Click **💾 Save & Apply Settings** to apply all updates instantly.

---

### Workflow E: 1-Click Interactive Demonstration Scenarios

Under the **1-Click Interactive Scenarios** toolbar on the dashboard:
* **🔥 Core Link Jamming**: Saturates core switches to 96% load to demonstrate D3QN's autonomous lateral offloading.
* **⚡ Fiber Cut**: Simulates an instant physical fiber cut on the core backbone.
* **📉 Brownout**: Throttles link capacity to 10% and spikes jitter.
* **🏆 Launch 6-Protocol Tournament**: Kicks off a 6-algorithm tournament matchup and scrolls down to the live leaderboard.
* **↺ Restore Nominal Baseline**: Restores all links, clears simulated bursts, and resets the fabric to proposal defaults.

---

## 5. REST API Reference Manual

The platform exposes a full REST API for programmatic control and telemetry integration.

### Core Endpoints

#### 1. System Health
* **Endpoint**: `GET /api/health`
* **Response**:
  ```json
  {
    "status": "healthy",
    "topology": "tree",
    "nodes": 7,
    "links": 16,
    "flows": 4
  }
  ```

#### 2. Unified Telemetry Bundle
* **Endpoint**: `GET /api/telemetry?topo=tree`
* **Description**: Returns complete topology graph, performance KPIs, RL agent info, and control overhead in a single gzip-compressed payload.

#### 3. Real-Time D3QN Route Inference
* **Endpoint**: `GET /api/model_predict?src=4&dst=7&demand=25.0`
* **Response**:
  ```json
  {
    "status": "success",
    "src": 4,
    "dst": 7,
    "demand_mbps": 25.0,
    "chosen_path": [4, 2, 5, 7],
    "candidate_paths": [[4, 2, 5, 7], [4, 6, 3, 7], [4, 2, 1, 3, 7]],
    "inference_time_ms": 0.52,
    "path_metrics": {
      "bottleneck_util": 0.25,
      "estimated_latency_ms": 4.5,
      "hops": 3
    }
  }
  ```

#### 4. Protocol Tournament Execution
* **Endpoint**: `GET /api/verse?topo=fattree&protocols=dqn,ospf,ecmp,wsp&pattern=jam&flows=15`
* **Response**: Contains multi-protocol leaderboard, comparative metrics, radar chart datasets, and empirical CDFs.

#### 5. Fault Injection Endpoints
* **Sever Link**: `POST /api/simulate/link_fail?u=1&v=2`
* **Throttle Link**: `POST /api/simulate/link_degrade?u=2&v=4`
* **Traffic Burst**: `POST /api/simulate/inject_burst?u=1&mbps=50.0`
* **Restore All Links**: `POST /api/simulate/link_restore`
* **Reset Simulation**: `POST /api/simulate/reset`

#### 6. Dynamic Flow Allocation
* **Endpoint**: `POST /api/simulate/apply_flow`
* **Payload**:
  ```json
  {
    "src": 4,
    "dst": 7,
    "demand": 25.0,
    "duration": 30.0
  }
  ```

#### 7. Network Settings Configuration
* **Get Settings**: `GET /api/network_settings`
* **Update Settings**: `POST /api/network_settings`
* **Sample Payload**:
  ```json
  {
    "default_capacity_mbps": 500.0,
    "default_delay_ms": 3.5,
    "core_trunk_ratio": 2.0,
    "switch_mtu": 9000,
    "w_hops": 0.40,
    "w_congestion": 1.5,
    "learning_rate": 0.0005,
    "traffic_pattern": "pareto"
  }
  ```

---

## 6. Automated Testing & Verification

The project includes an exhaustive 64-test automated test suite across 3 test runners:

```bash
# 1. Comprehensive Network Settings Test Suite (17 Tests)
# Validates all 5 modal categories, parameter synonyms, and baseline resets
python test_all_network_settings.py

# 2. Headless Dashboard & API Test Suite (15 Tests)
# Validates HTML asset delivery, live telemetry, D3QN prediction, and tournament APIs
python test_dashboard_headless.py

# 3. Unit & Integration Test Suite (32 Tests)
# Validates agent math, SumTree PER, Polyak updates, baselines, and state manager
python test_suite.py
```

All 64 tests pass with **100% success rate**.

---

## 7. Troubleshooting & Operational FAQs

### Q1: The web dashboard fails to bind to port 8080 (`Address already in use`).
* **Cause**: Another service or previous instance of Ryu/dashboard is holding port 8080.
* **Fix**: Run `./run_system.sh` with a custom port:
  ```bash
  SDN_REST_PORT=8090 ./run_system.sh
  ```
  Or kill the existing process:
  ```bash
  fuser -k 8080/tcp
  ```

### Q2: What is the difference between Mininet physical emulation and Autonomous mode?
* When launched with `sudo`, `./run_system.sh` starts Mininet with Open vSwitch software switches and virtual host veth pairs.
* When launched without `sudo`, the system starts the autonomous simulation driver (`simulate_live_traffic.py`). Both modes connect to the identical Ryu OpenFlow controller and web dashboard.

### Q3: How do I restore the system to its initial baseline?
* In the web console, click **↺ Restore Baseline** in the quick actions toolbar, or send a request to:
  ```bash
  python -c "import urllib.request; urllib.request.urlopen(urllib.request.Request('http://localhost:8080/api/simulate/reset', method='POST'))"
  ```

### Q4: How do I export tournament charts for papers or presentations?
1. Execute a tournament under the **Versus Engine** tab.
2. Click **📋 Copy Markdown** to copy the formatted GitHub/IEEE markdown table.
3. Pre-rendered high-resolution figures are saved in the `logs/plots/` directory:
   - `logs/plots/proposal_tournament_radar.png` (Multi-Metric Radar Comparison)
   - `logs/plots/routing_cdfs_latency_jitter.png` (Latency & Jitter CDFs)
   - `logs/plots/traffic_load_scaling_curves.png` (Load Scaling Curves)
   - `logs/plots/proposal_benchmarks_all_metrics.png` (Comparative Bar Charts)

---

*Synapse Adaptive SDN Platform — Developed for EC499 Final Project.*
