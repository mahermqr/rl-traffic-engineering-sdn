# Reinforcement Learning for Adaptive Traffic Engineering in an SDN Network (EC499)

**Course**: EC499 — Graduation Project in Computer Engineering
**Institution**: Department of Computer Engineering, Faculty of Engineering, University of Tripoli
**Student**: Maher Abdulnasir Alqadhi (ID: 2210249576, `ma.alqadhi@uot.edu.ly`)
**Supervisor**: Dr. Suad El-Geder
**Term**: Spring 2026

---

## Project Overview

This repository contains the complete implementation and benchmark suite for the graduation project: **Reinforcement Learning for Adaptive Traffic Engineering in an SDN Network**.

Traditional IP routing protocols (such as OSPF, Dijkstra SPF, or ECMP) route traffic using static hop counts or fixed administrative weights. Under dynamic traffic surges, this causes severe core switch bottlenecks, high queuing delays, packet jitter, and buffer overflow loss.

This platform integrates a **Dueling Double Deep Q-Network (D3QN)** with **Prioritized Experience Replay (PER)** into a **Ryu OpenFlow 1.3 SDN Controller** to adaptively optimize unicast traffic engineering. The agent continuously senses network link loads, delays, and packet rates, dynamically steering traffic over underutilized lateral cross-links to maximize throughput, minimize latency, suppress jitter, and eliminate packet loss.

---

## Fulfillment of Graduation Project Proposal

| Proposal Item | Approved Specification | Implementation Detail |
|---|---|---|
| **Objective 1** | Design a Deep Q-Network (DQN) agent to automate dynamic routing decisions | Dueling Double Deep Q-Network (`agent/dqn_router.py`) with Layer Normalization and Prioritized Experience Replay (`agent/prioritized_replay.py`) |
| **Objective 2** | Integrate RL agent with Ryu SDN controller using Mininet emulator | Ryu OpenFlow 1.3 controller (`controller/main_controller.py`) controlling Mininet fabrics (`topology/mininet_topo.py`) |
| **Objective 3** | Reduce network latency and jitter compared to standard routing protocols | Real-time tracking of path latency and RFC 3393 packet delay variation (`controller/state_manager.py`) |
| **Objective 4** | Maximize total network throughput by optimizing link utilization levels | Asymptotic barrier reward penalty preventing core bottlenecks; verified by Jain's Fairness Index |
| **Objective 5** | Evaluate performance using packet loss and control overhead metrics | M/M/1/K buffer overflow loss model and OpenFlow message accounting (`OFPPacketIn`, `OFPFlowMod`, decision latency) |
| **Procedure 4** | Train DQN agent using synthetic traffic patterns to simulate load | Poisson burst generator, elephant flows, and core jamming stress tests (`topology/traffic_generator.sh`) |
| **Procedure 5** | Benchmark RL agent against OSPF and greedy routing baselines | Automated tournament benchmark (`benchmark_routing_algorithms.py`) comparing DQN against OSPF (RFC 2328), Dijkstra SPF, ECMP, WSP, and LLR |
| **Procedure 6** | Document findings and prepare final technical report and source code | Graduation thesis, defense decks, automated tests (`test_suite.py`), and reproducible plotting tools |

---

## Head-to-Head Benchmark Summary across 5 Topologies

> Historical snapshot from the checked-in result files. Run `./run_benchmarks.sh --seed 42`
> after changing the model, queue model, or policy mode; do not treat these values as current
> until the JSON artifacts have been regenerated.

Evaluated under **closed-loop dynamic flow accumulation and lifecycle stepping** across **Hierarchical Tree**, **Fat-Tree ($k=4$)**, **Abilene US Backbone**, **NSFNet Continental Mesh**, and **Spine-Leaf Fabrics**:

| Metric | OSPF (RFC 2328) | Dijkstra SPF | ECMP | Greedy LLR | DQN Traffic Engineering (Ours) | Net Advantage |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Bottleneck Link Load** | 33.3% – 86.7% | 33.1% – 86.7% | 32.7% – 55.3% | 19.2% – 32.5% | **24.5% – 34.9%** | **Massive -39.9% peak relief on Fat-Tree & -62.2% on Spine-Leaf** |
| **Fat-Tree Bottleneck** | 65.5% | 65.5% | 50.3% | 23.6% | **25.6%** | **39.9% lower bottleneck than Dijkstra SPF** |
| **Spine-Leaf Bottleneck**| 86.7% | 86.7% | 55.3% | 19.2% | **24.5%** | **62.2% lower bottleneck than Dijkstra SPF** |
| **Fat-Tree Latency** | 164.0 ms | 164.0 ms | 101.3 ms | 7.72 ms | **9.15 ms** | **Lowest latency across dynamic algorithms (-154.9 ms savings)** |
| **Spine-Leaf Latency** | 195.3 ms | 195.3 ms | 118.2 ms | 2.75 ms | **3.16 ms** | **192.1 ms latency savings vs Dijkstra SPF** |
| **Packet Loss Rate** | 1.2% – 13.5% | 0.95% – 13.5% | 0.93% – 8.00% | 0.01% – 3.17% | **0.01% – 2.04%** | **0.01% loss on Fat-Tree & Spine-Leaf fabrics** |
| **Offload Rate** | 0.0% (Static) | 0.0% (Base) | 2.0% – 74.7% | 8.7% – 100.0% | **10.0% – 100.0%** | **Active anti-congestion steering across all multi-core fabrics** |
| **Decision Latency** | 0.07 – 0.20 ms | 0.01 ms | 0.01 – 0.02 ms | 0.01 ms | **0.33 – 0.34 ms** | **> 2,900 Decisions/Second** |

---

## Project Structure

```
.
├── agent/
│   ├── dqn_router.py                   # Dueling Double Deep Q-Network (D3QN) with LayerNorm
│   ├── prioritized_replay.py           # SumTree Prioritized Experience Replay (PER) buffer
│   └── __init__.py                     # Package exports
│
├── controller/
│   ├── main_controller.py              # Ryu OpenFlow 1.3 application & control overhead monitor
│   ├── routing_module.py               # Unicast traffic engineering & hierarchical TCAM allocation
│   ├── state_manager.py                # Telemetry engine with shadow reservations & on-demand detours
│   ├── traditional_routing.py          # Baselines: OSPF RFC 2328, Dijkstra SPF, ECMP, WSP, LLR
│   ├── web_dashboard.py                # Embedded REST API server (port 8080)
│   └── static/index.html               # Real-time topology canvas web UI
│
├── topology/
│   ├── mininet_topo.py                 # Mininet topologies (Tree, Fat-Tree) with OpenFlow 1.3 switches
│   ├── topology_library.py             # Multi-topology generator (Tree, Fat-Tree, Abilene, NSFNet, Spine-Leaf)
│   └── traffic_generator.sh            # Synthetic traffic generator (iperf background, elephant & bursts)
│
├── models/
│   └── dqn_router.pth                  # Trained PyTorch Double DQN weights
│
├── logs/
│   ├── routing_tournament_results.json # Quantitative benchmark tournament results
│   ├── blind_topologies_stress_results.json # 5-topology stress testing results
│   ├── stress_test_results.json        # Load balancer stress test results
│   ├── pareto_sensitivity_ablation.json # Pareto weight sensitivity ablation data
│   ├── evaluation_results.json         # DQN training convergence summary
│   ├── training_metrics.csv            # Episode-by-episode training metric records
│   └── plots/                          # 14 publication-grade figures
│       ├── proposal_benchmarks_all_metrics.png     # Figure 1: 6-panel all-metrics comparison
│       ├── proposal_tournament_radar.png           # Figure 2: 6D quality radar comparison
│       ├── dqn_te_training_convergence.png        # Figure 3: Training convergence dashboard
│       ├── routing_cdfs_latency_jitter.png         # Figure 4: Latency & jitter CDFs
│       ├── stress_test_load_balancing.png          # Figure 5: Load balancing stress comparison
│       ├── blind_topologies_radar.png              # Figure 6: Blind topology radar
│       ├── blind_topologies_stress_benchmark.png   # Figure 7: Blind stress benchmark
│       ├── traffic_load_scaling_curves.png         # Figure 8: Queuing transition load curves
│       ├── random_blind_topologies_evaluation.png  # Figure 9: 10 random topologies zero-shot
│       ├── dashboard_topology_telemetry.png        # Figure 10: Live fabric dashboard
│       ├── dashboard_versus_tournament.png         # Figure 11: Head-to-head tournament arena
│       ├── dashboard_model_inspector.png           # Figure 12: Neural model inspector
│       ├── dashboard_network_settings.png          # Figure 13: Network chaos & settings console
│       └── pareto_weight_sensitivity.png           # Figure 14: Pareto sensitivity ablation
│
├── docs/
│   ├── Project_Report_EC499_Final.pdf  # 143-Page Official Graduation Project Master Thesis
│   ├── Project_Report_EC499_Monolithic.tex # Monolithic LaTeX document (11 chapters + 5 appendices)
│   ├── EC499_Graduation_Defense_Presentation.pptx # 30-Slide Defense PowerPoint Presentation
│   ├── EC499_Graduation_Defense_Slides.html       # 30-Slide Interactive Standalone HTML5 Deck
│   ├── DEFENSE_CHEAT_SHEET.md          # Examiner Q&A and defense cheat sheet
│   ├── USER_MANUAL.md                  # Comprehensive dashboard user & operations manual
│   └── chapters/                       # Modular LaTeX source chapters (ch01–ch11)
│
├── test_suite.py                       # Unit & integration test suite (32 tests, 100% passing)
├── ablate_reward_weights.py            # Formal Pareto reward sensitivity ablation suite
├── benchmark_routing_algorithms.py     # 5-topology head-to-head tournament benchmark
├── benchmark_evaluation.py             # 3-phase curriculum DQN training script
├── evaluate_random_blind_topology.py   # Zero-shot random dynamic topology evaluation
├── stress_test_blind_topologies.py     # Multi-topology high-intensity stress suite
├── stress_test_load_balancer.py        # Core jamming and avalanche stress suite
├── simulate_live_traffic.py            # Live traffic driver and simulation runner
├── generate_defense_deck.py            # Generates official 30-slide PPTX presentation
├── build_html_slides.py                # Generates standalone 30-slide HTML5 presentation
├── package_submission.py               # Official graduation package archive builder
├── run_system.sh                       # One-command system launcher
├── run_benchmarks.sh                   # One-command tournament benchmark runner
├── run_tests.sh                        # One-command test suite executor
├── run_random_blind_test.sh            # Quick launcher for zero-shot testing
├── CITATION.cff                        # Academic citation metadata
├── requirements.txt                    # Python package dependencies
└── LICENSE                             # MIT Open-Source License
```

---

## Architectural Design Notes

To satisfy the highest standards of IEEE transaction reviewers and academic examiners, the platform incorporates five rigorous architectural remediations:

1. **Load-Aware Candidate Generation (`controller/state_manager.py`)**:
   - The topology-only simple-path cache is separated from a load-aware Dijkstra candidate that is recomputed for every decision. A bypass is selected only when the active graph actually contains one.
2. **Fixed-Width State Vector (`controller/state_manager.py`)**:
   - The normalized vector summarizes candidate bottlenecks and delays and now follows `RL_STATE_SIZE`. It is a compact engineered representation, not a graph-neural-network equivalent.
3. **Active Closed-Loop Shadow Bandwidth Reservations (`controller/state_manager.py`)**:
   - Records immediate reservations on selected path links with configurable exponential decay to reduce repeated decisions based on stale polling data.
4. **Hierarchical TCAM Flow Table Allocation (`controller/routing_module.py`)**:
   - Mice and elephant flows use distinct priorities and configurable idle timeouts. Current rules match the IPv4 source/destination pair; transport-protocol and port matching is not yet implemented.
5. **Pareto Multi-Objective Sensitivity Ablation (`ablate_reward_weights.py`)**:
   - A deterministic multi-topology sensitivity run compares six objective-weight configurations. It evaluates path choices directly and is explicitly not presented as D3QN retraining.

---

## Quick Start & Verification

Use Python 3.9–3.11 for the live Ryu controller (Ryu 4.34 is not compatible with Python 3.12+), create a virtual environment, and install `requirements.txt`.

### 1. Run Unit & Integration Tests
```bash
./run_tests.sh
# Or with active virtual environment:
python3 test_suite.py -v
```

### 2. Run Head-to-Head Routing Tournament Benchmark (5 Topologies)
```bash
./run_benchmarks.sh
# Or with active virtual environment:
python3 benchmark_routing_algorithms.py
```

### 3. Run Pareto Sensitivity Ablation Suite
```bash
python3 ablate_reward_weights.py
```

### 4. Run Multi-Topology Stress Testing Suite
```bash
python3 stress_test_blind_topologies.py
```

### 5. Zero-Shot Blind Random Topology Test
```bash
./run_random_blind_test.sh
# Or with active virtual environment:
python3 evaluate_random_blind_topology.py --nodes 20 --flows 200
```

### 6. Train Deep Q-Network Agent
```bash
python3 benchmark_evaluation.py --episodes 1000
```

### 7. Launch Ryu Controller, Live Traffic Simulation, and Web Dashboard
```bash
./run_system.sh
```

### 8. Access Interactive Telemetry Web Dashboard
Open your browser at:
```
http://localhost:8080
```
(Configurable via `SDN_REST_PORT` or `--port`)

---

## Centralized Configuration System (Zero Hardcoding)

All runtime parameters, model paths, SDN endpoints, and reinforcement learning hyperparameters are managed by `config.py` following strict precedence:
1. **CLI Arguments** (highest priority, e.g. `--model-path`, `--rest-port`, `--episodes`)
2. **Environment Variables** (e.g. `SDN_*`, `RL_*`, `TORCH_DEVICE`)
3. **Optional `config.json`** file in the project directory
4. **Sensible Production Defaults** (lowest priority)

### Key Environment Variables

| Variable | Default | Description |
|:---|:---:|:---|
| `SDN_MODEL_PATH` | `models/dqn_router.pth` | Path to PyTorch trained D3QN weights |
| `SDN_LOGS_DIR` | `logs/` | Output directory for metrics, logs, and JSON summaries |
| `SDN_PLOTS_DIR` | `logs/plots/` | Directory where publication figures are generated |
| `SDN_CONTROLLER_IP` | `127.0.0.1` | Ryu OpenFlow controller host address |
| `SDN_CONTROLLER_PORT` | `6633` | OpenFlow switch-controller listening port |
| `SDN_REST_HOST` | `127.0.0.1` | Dashboard server bind address |
| `SDN_REST_PORT` | `8080` | Dashboard server HTTP port |
| `SDN_POLL_INTERVAL` | `3.0` | OpenFlow statistics polling period (seconds) |
| `SDN_DEFAULT_TOPOLOGY` | `tree` | Default network fabric (`tree`, `fattree`, `abilene`, `nsfnet`, `spineleaf`) |
| `RL_LR` | `0.001` | Adam optimizer learning rate |
| `RL_BATCH_SIZE` | `32` | Experience replay mini-batch sample size |
| `RL_MEMORY_SIZE` | `5000` | Prioritized experience replay buffer capacity |
| `RL_POLICY_MODE` | `pure` | `pure` DQN evaluation or explicitly labelled `safety` post-processing |
| `SDN_API_TOKEN` | empty | Optional bearer/API-key required for state-changing POST requests |
| `TORCH_DEVICE` | Auto (`cuda` / `cpu`) | PyTorch compute accelerator device |


---

## Citation

If you use this work in your research or project, please cite:

```bibtex
@misc{alqadhi2026sdnrl,
  author = {Maher Abdulnasir Alqadhi and Dr. Suad El-Geder},
  title = {Reinforcement Learning for Adaptive Traffic Engineering in an SDN Network},
  year = {2026},
  publisher = {Department of Computer Engineering, Faculty of Engineering, University of Tripoli},
  howpublished = {\url{https://github.com/maheralqadhi/EC499-SDN-Adaptive-TE-RL}}
}
```
