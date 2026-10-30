# EC499: SDN Traffic Engineering with Reinforcement Learning — Codebase Documentation

> **Project:** Reinforcement Learning for Adaptive Traffic Engineering in an SDN Network  
> **Student:** Maher Alqadhi (ID: 2210249576)  
> **Institution:** University of Tripoli — Faculty of Engineering — Department of Electrical & Electronic Engineering  
> **Total Source Files:** 51 files  
> **Total Lines of Code:** 20,226 lines  
> **Total Codebase Size:** 1010.01 KB (0.99 MB)  

---

## Master Documents

- [📖 **ALL_PROJECT_CODES.md**](./ALL_PROJECT_CODES.md) — Single consolidated Markdown document containing the entire codebase with Table of Contents and complete source codes.

---

## Subsystems & Architecture Modules

### 1. Reinforcement Learning (DQN) Agent
*Deep Q-Network routing models, Dueling architectures, and Prioritized Experience Replay (PER).*  
**Metrics:** 3 files | 646 lines | 27.7 KB

| File | Language | Lines | Size | Description | Links |
| :--- | :---: | :---: | :---: | :--- | :---: |
| [`agent/__init__.py`](agent/__init__.md) | `python` | 18 | 0.4 KB | Reinforcement learning package export exposing DQNRoutingAgent and PrioritizedReplayBuffer. | [View .md](agent/__init__.md) |
| [`agent/dqn_router.py`](agent/dqn_router.md) | `python` | 404 | 19.0 KB | Dueling Double Deep Q-Network (D3QN) routing agent implementation with prioritized experienc... | [View .md](agent/dqn_router.md) |
| [`agent/prioritized_replay.py`](agent/prioritized_replay.md) | `python` | 224 | 8.3 KB | Prioritized Experience Replay (PER) buffer using a binary SumTree structure for O(log N) pro... | [View .md](agent/prioritized_replay.md) |

### 2. SDN Controller Architecture & Modules
*Ryu OpenFlow 1.3 controller, dynamic routing modules, HA failover pool, queue models, and real-time dashboard.*  
**Metrics:** 9 files | 4,398 lines | 212.8 KB

| File | Language | Lines | Size | Description | Links |
| :--- | :---: | :---: | :---: | :--- | :---: |
| [`controller/__init__.py`](controller/__init__.md) | `python` | 14 | 0.3 KB | SDN control plane package initialization for OpenFlow 1.3 Ryu applications. | [View .md](controller/__init__.md) |
| [`controller/ha_controller_pool.py`](controller/ha_controller_pool.md) | `python` | 355 | 13.6 KB | High-Availability (HA) active-backup controller clustering engine with heartbeat monitoring,... | [View .md](controller/ha_controller_pool.md) |
| [`controller/main_controller.py`](controller/main_controller.md) | `python` | 313 | 13.8 KB | Core OpenFlow 1.3 Ryu controller application handling switch registration, LLDP topology dis... | [View .md](controller/main_controller.md) |
| [`controller/policy_selector.py`](controller/policy_selector.md) | `python` | 83 | 3.3 KB | Adaptive routing policy selector dynamically arbitrating between DQN routing, Shortest Path ... | [View .md](controller/policy_selector.md) |
| [`controller/queue_model.py`](controller/queue_model.md) | `python` | 64 | 2.2 KB | M/M/1/K finite-buffer queueing model utilities for theoretical delay estimation, buffer over... | [View .md](controller/queue_model.md) |
| [`controller/routing_module.py`](controller/routing_module.md) | `python` | 501 | 22.4 KB | Dynamic routing engine bridging network telemetry with the DQN agent, computing candidate pa... | [View .md](controller/routing_module.md) |
| [`controller/state_manager.py`](controller/state_manager.md) | `python` | 1,036 | 48.1 KB | Real-time network telemetry engine collecting switch statistics, calculating link latency, j... | [View .md](controller/state_manager.md) |
| [`controller/traditional_routing.py`](controller/traditional_routing.md) | `python` | 237 | 8.8 KB | Traditional routing algorithms baseline suite implementing Dijkstra SPF, Equal-Cost Multi-Pa... | [View .md](controller/traditional_routing.md) |
| [`controller/web_dashboard.py`](controller/web_dashboard.md) | `python` | 1,795 | 100.3 KB | Interactive Flask & WebSocket real-time telemetry dashboard providing live panoramic topolog... | [View .md](controller/web_dashboard.md) |

### 3. Network Topologies & Traffic Emulation
*Mininet network topologies, realistic topology library (NSFNET, GÉANT, etc.), and D-ITG traffic generators.*  
**Metrics:** 3 files | 1,127 lines | 44.4 KB

| File | Language | Lines | Size | Description | Links |
| :--- | :---: | :---: | :---: | :--- | :---: |
| [`topology/mininet_topo.py`](topology/mininet_topo.md) | `python` | 281 | 12.1 KB | Mininet network topology builder constructing software-defined switches, host nodes, link ba... | [View .md](topology/mininet_topo.md) |
| [`topology/topology_library.py`](topology/topology_library.md) | `python` | 408 | 14.4 KB | Comprehensive network topology library generating realistic backbones (NSFNET, GÉANT, Fattre... | [View .md](topology/topology_library.md) |
| [`topology/traffic_generator.sh`](topology/traffic_generator.md) | `bash` | 438 | 18.0 KB | Multi-profile synthetic traffic generation script orchestrating D-ITG, iperf, and Poisson pa... | [View .md](topology/traffic_generator.md) |

### 4. Project Configuration & Root Package
*Global hyperparameters, OpenFlow thresholds, network telemetry configurations, and package roots.*  
**Metrics:** 2 files | 292 lines | 14.7 KB

| File | Language | Lines | Size | Description | Links |
| :--- | :---: | :---: | :---: | :--- | :---: |
| [`__init__.py`](__init__.md) | `python` | 7 | 0.1 KB | Top-level package initialization for the EC499 adaptive SDN traffic engineering framework. | [View .md](__init__.md) |
| [`config.py`](config.md) | `python` | 285 | 14.6 KB | Centralized system configuration defining network topology defaults, D3QN hyperparameters, O... | [View .md](config.md) |

### 5. Benchmarking, Heuristics & Stress Testing
*Evaluation pipelines, shortest-path/ECMP heuristics comparison, reward weight ablation, and blind topology stress tests.*  
**Metrics:** 10 files | 3,298 lines | 146.8 KB

| File | Language | Lines | Size | Description | Links |
| :--- | :---: | :---: | :---: | :--- | :---: |
| [`ablate_reward_weights.py`](ablate_reward_weights.md) | `python` | 206 | 8.8 KB | Multi-objective Pareto ablation study systematically analyzing the sensitivity of latency, l... | [View .md](ablate_reward_weights.md) |
| [`audit_dqn_agent_deep.py`](audit_dqn_agent_deep.md) | `python` | 328 | 14.6 KB | Deep diagnostic auditor analyzing Q-network weight distributions, gradient norms, TD-error c... | [View .md](audit_dqn_agent_deep.md) |
| [`benchmark_evaluation.py`](benchmark_evaluation.md) | `python` | 475 | 21.2 KB | Comprehensive benchmarking pipeline evaluating DQN performance against Dijkstra, ECMP, and h... | [View .md](benchmark_evaluation.md) |
| [`benchmark_routing_algorithms.py`](benchmark_routing_algorithms.md) | `python` | 336 | 14.9 KB | Algorithmic benchmark suite measuring route convergence time, latency CDFs, and throughput s... | [View .md](benchmark_routing_algorithms.md) |
| [`evaluate_multiseed.py`](evaluate_multiseed.md) | `python` | 278 | 12.0 KB | Multi-seed statistical significance evaluation calculating mean, standard deviation, and pai... | [View .md](evaluate_multiseed.md) |
| [`evaluate_random_blind_topology.py`](evaluate_random_blind_topology.md) | `python` | 385 | 16.4 KB | Zero-shot transfer learning evaluator testing DQN generalizability and performance on comple... | [View .md](evaluate_random_blind_topology.md) |
| [`run_benchmarks.py`](run_benchmarks_py.md) | `python` | 41 | 1.5 KB | Lightweight CLI runner for executing algorithmic benchmark evaluations. | [View .md](run_benchmarks_py.md) |
| [`run_multiseed_ablation_and_sweep.py`](run_multiseed_ablation_and_sweep.md) | `python` | 240 | 9.8 KB | Automated batch runner orchestrating multi-seed hyperparameter sweeps and Pareto frontier ev... | [View .md](run_multiseed_ablation_and_sweep.md) |
| [`stress_test_blind_topologies.py`](stress_test_blind_topologies.md) | `python` | 607 | 29.1 KB | Heavy-load stress testing engine evaluating routing robustness and congestion avoidance on i... | [View .md](stress_test_blind_topologies.md) |
| [`stress_test_load_balancer.py`](stress_test_load_balancer.md) | `python` | 402 | 18.4 KB | Multi-path load balancing stress testing suite measuring traffic distribution fairness acros... | [View .md](stress_test_load_balancer.md) |

### 6. Experimental Suites & Mininet Packet Validation
*Phase 1 synthetic benchmarks, Phase 2 Mininet packet-level validation, live traffic simulation, and data analysis.*  
**Metrics:** 5 files | 2,060 lines | 83.8 KB

| File | Language | Lines | Size | Description | Links |
| :--- | :---: | :---: | :---: | :--- | :---: |
| [`analyze_mininet_measured_trials.py`](analyze_mininet_measured_trials.md) | `python` | 183 | 7.1 KB | Telemetry log parser aggregating measured packet trials, generating statistics, and computin... | [View .md](analyze_mininet_measured_trials.md) |
| [`experiment_phase1_suite.py`](experiment_phase1_suite.md) | `python` | 876 | 35.6 KB | Phase 1 numerical simulation testbed conducting synthetic traffic experiments and recording ... | [View .md](experiment_phase1_suite.md) |
| [`experiment_phase2_packet_validation.py`](experiment_phase2_packet_validation.md) | `python` | 389 | 16.0 KB | Phase 2 live Mininet packet validation benchmark capturing real packet latency, jitter, and ... | [View .md](experiment_phase2_packet_validation.md) |
| [`reproduce_mininet_packet_experiment.py`](reproduce_mininet_packet_experiment.md) | `python` | 467 | 19.0 KB | Deterministic reproduction runner for replicating the Phase 2 Mininet experimental trials. | [View .md](reproduce_mininet_packet_experiment.md) |
| [`simulate_live_traffic.py`](simulate_live_traffic.md) | `python` | 145 | 6.1 KB | Dynamic traffic emulator generating time-varying Poisson arrival flows and bursty traffic pa... | [View .md](simulate_live_traffic.md) |

### 7. Verification, Testing & High Availability
*Unit and integration test suites, HA controller failover validation, and 100-run endurance stress testing.*  
**Metrics:** 3 files | 1,198 lines | 58.7 KB

| File | Language | Lines | Size | Description | Links |
| :--- | :---: | :---: | :---: | :--- | :---: |
| [`test_dashboard_100_runs.py`](test_dashboard_100_runs.md) | `python` | 311 | 19.8 KB | Endurance reliability test executing 100 consecutive dashboard simulation runs to verify mem... | [View .md](test_dashboard_100_runs.md) |
| [`test_ha_controller_failover.py`](test_ha_controller_failover.md) | `python` | 198 | 8.9 KB | Automated HA controller failover validation script performing fault injection and measuring ... | [View .md](test_ha_controller_failover.md) |
| [`test_suite.py`](test_suite.md) | `python` | 689 | 30.0 KB | Comprehensive unit and integration test suite verifying controller components, DQN agent, qu... | [View .md](test_suite.md) |

### 8. Operational Automation & Shell Scripts
*Automated test runners, high availability verification scripts, runtime launchers, and Ryu wrappers.*  
**Metrics:** 8 files | 406 lines | 16.0 KB

| File | Language | Lines | Size | Description | Links |
| :--- | :---: | :---: | :---: | :--- | :---: |
| [`reproduce_all.sh`](reproduce_all.md) | `bash` | 164 | 6.5 KB | Master reproduction script automating the end-to-end execution of all experiments, benchmark... | [View .md](reproduce_all.md) |
| [`run_benchmarks.sh`](run_benchmarks_sh.md) | `bash` | 21 | 0.9 KB | Benchmark execution script automating comparative algorithm evaluation runs. | [View .md](run_benchmarks_sh.md) |
| [`run_ha_test.sh`](run_ha_test.md) | `bash` | 13 | 0.5 KB | High availability failover demonstration script testing controller fault recovery scenarios. | [View .md](run_ha_test.md) |
| [`run_random_blind_test.sh`](run_random_blind_test.md) | `bash` | 35 | 1.5 KB | Zero-shot blind topology transfer evaluation automation script. | [View .md](run_random_blind_test.md) |
| [`run_system.sh`](run_system.md) | `bash` | 108 | 4.7 KB | Production launcher script starting the Ryu OpenFlow controller, Mininet topology, and the w... | [View .md](run_system.md) |
| [`run_tests.sh`](run_tests.md) | `bash` | 13 | 0.4 KB | Automated test execution script running the complete pytest and unittest suites. | [View .md](run_tests.md) |
| [`scripts/resolve_python.sh`](scripts/resolve_python.md) | `bash` | 37 | 1.0 KB | Environment resolution script locating the appropriate Python virtual environment and Ryu de... | [View .md](scripts/resolve_python.md) |
| [`scripts/ryu_manager_compat.py`](scripts/ryu_manager_compat.md) | `python` | 15 | 0.4 KB | Compatibility wrapper resolving Ryu manager eventlet and Python execution differences. | [View .md](scripts/ryu_manager_compat.md) |

### 9. Publications, Documentation & Slide Generation
*LaTeX thesis builders, PowerPoint/PDF slide deck generators, Matplotlib chart plotters, and submission packager.*  
**Metrics:** 8 files | 6,801 lines | 405.1 KB

| File | Language | Lines | Size | Description | Links |
| :--- | :---: | :---: | :---: | :--- | :---: |
| [`build_ali_style_thesis.py`](build_ali_style_thesis.md) | `python` | 1,525 | 103.5 KB | LaTeX thesis compiler compiling academic reports and formatting camera-ready graduation proj... | [View .md](build_ali_style_thesis.md) |
| [`build_html_slides.py`](build_html_slides.md) | `python` | 1,648 | 84.8 KB | HTML5 presentation deck generator producing interactive slides with CSS3 animations and embe... | [View .md](build_html_slides.md) |
| [`build_mahermqr_handout.py`](build_mahermqr_handout.md) | `python` | 721 | 50.9 KB | Defense handout generator compiling a two-page summary brochure with embedded QR codes linki... | [View .md](build_mahermqr_handout.md) |
| [`generate_defense_deck.py`](generate_defense_deck.md) | `python` | 888 | 57.1 KB | Slide deck generator producing graduation defense presentation slides in PowerPoint (.pptx) ... | [View .md](generate_defense_deck.md) |
| [`generate_detailed_plots.py`](generate_detailed_plots.md) | `python` | 792 | 39.7 KB | Publication-quality figure generation script plotting latency CDFs, radar charts, and traini... | [View .md](generate_detailed_plots.md) |
| [`generate_docx_report.py`](generate_docx_report.md) | `python` | 436 | 28.6 KB | Microsoft Word (.docx) comprehensive project report compiler with formatted tables, headings... | [View .md](generate_docx_report.md) |
| [`generate_phase1_figures.py`](generate_phase1_figures.md) | `python` | 439 | 21.2 KB | Comparative chart plotting script rendering Phase 1 benchmark results. | [View .md](generate_phase1_figures.md) |
| [`package_submission.py`](package_submission.md) | `python` | 352 | 19.3 KB | Graduation submission packaging script assembling project zips, checksum manifests, and docu... | [View .md](package_submission.md) |

