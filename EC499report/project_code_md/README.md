# EC499: SDN Traffic Engineering with Reinforcement Learning — Codebase Documentation

> **Project:** Reinforcement Learning for Adaptive Traffic Engineering in Software-Defined Network  
> **Student:** Maher Alqadhi (ID: 2210249576)  
> **Institution:** University of Tripoli — Faculty of Engineering — Department of Computer Engineering  
> **Total Source Files:** 79 files  
> **Total Lines of Code:** 28,394 lines  
> **Total Codebase Size:** 1486.44 KB (1.45 MB)  

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
**Metrics:** 9 files | 4,895 lines | 239.3 KB

| File | Language | Lines | Size | Description | Links |
| :--- | :---: | :---: | :---: | :--- | :---: |
| [`controller/__init__.py`](controller/__init__.md) | `python` | 14 | 0.3 KB | SDN control plane package initialization for OpenFlow 1.3 Ryu applications. | [View .md](controller/__init__.md) |
| [`controller/ha_controller_pool.py`](controller/ha_controller_pool.md) | `python` | 456 | 18.6 KB | High-Availability (HA) active-backup controller clustering engine with heartbeat monitoring,... | [View .md](controller/ha_controller_pool.md) |
| [`controller/main_controller.py`](controller/main_controller.md) | `python` | 320 | 14.0 KB | Core OpenFlow 1.3 Ryu controller application handling switch registration, LLDP topology dis... | [View .md](controller/main_controller.md) |
| [`controller/policy_selector.py`](controller/policy_selector.md) | `python` | 83 | 3.3 KB | Adaptive routing policy selector dynamically arbitrating between DQN routing, Shortest Path ... | [View .md](controller/policy_selector.md) |
| [`controller/queue_model.py`](controller/queue_model.md) | `python` | 64 | 2.2 KB | M/M/1/K finite-buffer queueing model utilities for theoretical delay estimation, buffer over... | [View .md](controller/queue_model.md) |
| [`controller/routing_module.py`](controller/routing_module.md) | `python` | 501 | 22.4 KB | Dynamic routing engine bridging network telemetry with the DQN agent, computing candidate pa... | [View .md](controller/routing_module.md) |
| [`controller/state_manager.py`](controller/state_manager.md) | `python` | 1,061 | 49.2 KB | Real-time network telemetry engine collecting switch statistics, calculating link latency, j... | [View .md](controller/state_manager.md) |
| [`controller/traditional_routing.py`](controller/traditional_routing.md) | `python` | 237 | 8.8 KB | Traditional routing algorithms baseline suite implementing Dijkstra SPF, Equal-Cost Multi-Pa... | [View .md](controller/traditional_routing.md) |
| [`controller/web_dashboard.py`](controller/web_dashboard.md) | `python` | 2,159 | 120.5 KB | Interactive Flask & WebSocket real-time telemetry dashboard providing live panoramic topolog... | [View .md](controller/web_dashboard.md) |

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
**Metrics:** 2 files | 302 lines | 15.1 KB

| File | Language | Lines | Size | Description | Links |
| :--- | :---: | :---: | :---: | :--- | :---: |
| [`__init__.py`](__init__.md) | `python` | 7 | 0.1 KB | Top-level package initialization for the EC499 adaptive SDN traffic engineering framework. | [View .md](__init__.md) |
| [`config.py`](config.md) | `python` | 295 | 15.0 KB | Centralized system configuration defining network topology defaults, D3QN hyperparameters, O... | [View .md](config.md) |

### 5. Benchmarking, Heuristics & Stress Testing
*Evaluation pipelines, shortest-path/ECMP heuristics comparison, reward weight ablation, and blind topology stress tests.*  
**Metrics:** 10 files | 3,319 lines | 147.7 KB

| File | Language | Lines | Size | Description | Links |
| :--- | :---: | :---: | :---: | :--- | :---: |
| [`EC499tests/ablate_reward_weights.py`](EC499tests/ablate_reward_weights.md) | `python` | 212 | 8.9 KB | Source code implementation for ablate_reward_weights.py. | [View .md](EC499tests/ablate_reward_weights.md) |
| [`EC499tests/audit_dqn_agent_deep.py`](EC499tests/audit_dqn_agent_deep.md) | `python` | 329 | 14.7 KB | Source code implementation for audit_dqn_agent_deep.py. | [View .md](EC499tests/audit_dqn_agent_deep.md) |
| [`EC499tests/benchmark_evaluation.py`](EC499tests/benchmark_evaluation.md) | `python` | 476 | 21.3 KB | Source code implementation for benchmark_evaluation.py. | [View .md](EC499tests/benchmark_evaluation.md) |
| [`EC499tests/benchmark_routing_algorithms.py`](EC499tests/benchmark_routing_algorithms.md) | `python` | 338 | 15.0 KB | Source code implementation for benchmark_routing_algorithms.py. | [View .md](EC499tests/benchmark_routing_algorithms.md) |
| [`EC499tests/evaluate_multiseed.py`](EC499tests/evaluate_multiseed.md) | `python` | 278 | 12.0 KB | Repeated-seed statistical evaluation for the EC499 routing tournament. | [View .md](EC499tests/evaluate_multiseed.md) |
| [`EC499tests/evaluate_random_blind_topology.py`](EC499tests/evaluate_random_blind_topology.md) | `python` | 386 | 16.5 KB | Source code implementation for evaluate_random_blind_topology.py. | [View .md](EC499tests/evaluate_random_blind_topology.md) |
| [`EC499tests/run_benchmarks.py`](EC499tests/run_benchmarks_py.md) | `python` | 41 | 1.5 KB | Typed orchestration entry point for all benchmark suites. | [View .md](EC499tests/run_benchmarks_py.md) |
| [`EC499tests/run_multiseed_ablation_and_sweep.py`](EC499tests/run_multiseed_ablation_and_sweep.md) | `python` | 247 | 10.0 KB | Source code implementation for run_multiseed_ablation_and_sweep.py. | [View .md](EC499tests/run_multiseed_ablation_and_sweep.md) |
| [`EC499tests/stress_test_blind_topologies.py`](EC499tests/stress_test_blind_topologies.md) | `python` | 608 | 29.2 KB | Source code implementation for stress_test_blind_topologies.py. | [View .md](EC499tests/stress_test_blind_topologies.md) |
| [`EC499tests/stress_test_load_balancer.py`](EC499tests/stress_test_load_balancer.md) | `python` | 404 | 18.6 KB | Source code implementation for stress_test_load_balancer.py. | [View .md](EC499tests/stress_test_load_balancer.md) |

### 6. Experimental Suites & Mininet Packet Validation
*Phase 1 synthetic benchmarks, Phase 2 Mininet packet-level validation, live traffic simulation, and data analysis.*  
**Metrics:** 5 files | 2,131 lines | 88.0 KB

| File | Language | Lines | Size | Description | Links |
| :--- | :---: | :---: | :---: | :--- | :---: |
| [`EC499tests/analyze_mininet_measured_trials.py`](EC499tests/analyze_mininet_measured_trials.md) | `python` | 185 | 7.3 KB | Analyze measured Mininet trials without manufacturing missing observations. | [View .md](EC499tests/analyze_mininet_measured_trials.md) |
| [`EC499tests/experiment_phase1_suite.py`](EC499tests/experiment_phase1_suite.md) | `python` | 877 | 35.7 KB | Source code implementation for experiment_phase1_suite.py. | [View .md](EC499tests/experiment_phase1_suite.md) |
| [`EC499tests/experiment_phase2_packet_validation.py`](EC499tests/experiment_phase2_packet_validation.md) | `python` | 390 | 16.2 KB | Source code implementation for experiment_phase2_packet_validation.py. | [View .md](EC499tests/experiment_phase2_packet_validation.md) |
| [`EC499tests/reproduce_mininet_packet_experiment.py`](EC499tests/reproduce_mininet_packet_experiment.md) | `python` | 534 | 22.8 KB | Run auditable Mininet/OVS traffic-engineering trials. | [View .md](EC499tests/reproduce_mininet_packet_experiment.md) |
| [`simulate_live_traffic.py`](simulate_live_traffic.md) | `python` | 145 | 6.1 KB | Dynamic traffic emulator generating time-varying Poisson arrival flows and bursty traffic pa... | [View .md](simulate_live_traffic.md) |

### 8. Operational Automation & Shell Scripts
*Automated test runners, high availability verification scripts, runtime launchers, and Ryu wrappers.*  
**Metrics:** 19 files | 1,211 lines | 53.8 KB

| File | Language | Lines | Size | Description | Links |
| :--- | :---: | :---: | :---: | :--- | :---: |
| [`EC499report/reproduce_all.sh`](EC499report/reproduce_all.md) | `bash` | 171 | 6.8 KB | ============================================================================== Master Reprod... | [View .md](EC499report/reproduce_all.md) |
| [`EC499sildes/run_slides.sh`](EC499sildes/run_slides.md) | `bash` | 56 | 2.5 KB | ============================================================================== EC499 Final D... | [View .md](EC499sildes/run_slides.md) |
| [`EC499tests/run_benchmarks.sh`](EC499tests/run_benchmarks_sh.md) | `bash` | 24 | 1.1 KB | ============================================================================== Run All Routi... | [View .md](EC499tests/run_benchmarks_sh.md) |
| [`EC499tests/run_e2e_tests.sh`](EC499tests/run_e2e_tests.md) | `bash` | 20 | 0.8 KB | ============================================================================== Run 4-Tier Op... | [View .md](EC499tests/run_e2e_tests.md) |
| [`EC499tests/run_ha_test.sh`](EC499tests/run_ha_test.md) | `bash` | 16 | 0.6 KB | ============================================================================== Run High Avai... | [View .md](EC499tests/run_ha_test.md) |
| [`EC499tests/run_mininet_analysis.sh`](EC499tests/run_mininet_analysis.md) | `bash` | 15 | 0.6 KB | Analyze an existing measured Mininet run using a Python with Matplotlib. | [View .md](EC499tests/run_mininet_analysis.md) |
| [`EC499tests/run_mininet_experiment.sh`](EC499tests/run_mininet_experiment.md) | `bash` | 52 | 2.2 KB | Run auditable packet-level Mininet/OVS trials.  Requires Linux root privileges. | [View .md](EC499tests/run_mininet_experiment.md) |
| [`EC499tests/run_random_blind_test.sh`](EC499tests/run_random_blind_test.md) | `bash` | 40 | 1.8 KB | ============================================================================== Autonomous Ze... | [View .md](EC499tests/run_random_blind_test.md) |
| [`EC499tests/run_tests.sh`](EC499tests/run_tests.md) | `bash` | 16 | 0.6 KB | ============================================================================== Run Unit and ... | [View .md](EC499tests/run_tests.md) |
| [`reproduce_all.sh`](reproduce_all.md) | `bash` | 23 | 0.7 KB | Master reproduction script automating the end-to-end execution of all experiments, benchmark... | [View .md](reproduce_all.md) |
| [`run_benchmarks.sh`](run_benchmarks.md) | `bash` | 15 | 0.5 KB | Benchmark execution script automating comparative algorithm evaluation runs. | [View .md](run_benchmarks.md) |
| [`run_ha_test.sh`](run_ha_test.md) | `bash` | 15 | 0.5 KB | High availability failover demonstration script testing controller fault recovery scenarios. | [View .md](run_ha_test.md) |
| [`run_random_blind_test.sh`](run_random_blind_test.md) | `bash` | 15 | 0.5 KB | Zero-shot blind topology transfer evaluation automation script. | [View .md](run_random_blind_test.md) |
| [`run_system.sh`](run_system.md) | `bash` | 108 | 4.7 KB | Production launcher script starting the Ryu OpenFlow controller, Mininet topology, and the w... | [View .md](run_system.md) |
| [`run_tests.sh`](run_tests.md) | `bash` | 15 | 0.5 KB | Automated test execution script running the complete pytest and unittest suites. | [View .md](run_tests.md) |
| [`scripts/convert_codebase_to_markdown.py`](scripts/convert_codebase_to_markdown.md) | `python` | 466 | 24.7 KB | Source code implementation for convert_codebase_to_markdown.py. | [View .md](scripts/convert_codebase_to_markdown.md) |
| [`scripts/resolve_python.sh`](scripts/resolve_python.md) | `bash` | 39 | 1.1 KB | Environment resolution script locating the appropriate Python virtual environment and Ryu de... | [View .md](scripts/resolve_python.md) |
| [`scripts/ryu_manager_compat.py`](scripts/ryu_manager_compat.md) | `python` | 15 | 0.4 KB | Compatibility wrapper resolving Ryu manager eventlet and Python execution differences. | [View .md](scripts/ryu_manager_compat.md) |
| [`status.sh`](status.md) | `bash` | 90 | 3.2 KB | Source code implementation for status.sh. | [View .md](status.md) |

### 9. Publications, Documentation & Slide Generation
*LaTeX thesis builders, PowerPoint/PDF slide deck generators, Matplotlib chart plotters, and submission packager.*  
**Metrics:** 28 files | 14,763 lines | 870.4 KB

| File | Language | Lines | Size | Description | Links |
| :--- | :---: | :---: | :---: | :--- | :---: |
| [`EC499report/build_ali_style_thesis.py`](EC499report/build_ali_style_thesis.md) | `python` | 1,525 | 103.5 KB | Source code implementation for build_ali_style_thesis.py. | [View .md](EC499report/build_ali_style_thesis.md) |
| [`EC499report/build_html_slides.py`](EC499report/build_html_slides.md) | `python` | 1,649 | 84.9 KB | Source code implementation for build_html_slides.py. | [View .md](EC499report/build_html_slides.md) |
| [`EC499report/build_mahermqr_handout.py`](EC499report/build_mahermqr_handout.md) | `python` | 888 | 58.7 KB | Source code implementation for build_mahermqr_handout.py. | [View .md](EC499report/build_mahermqr_handout.md) |
| [`EC499report/generate_defense_deck.py`](EC499report/generate_defense_deck.md) | `python` | 914 | 58.2 KB | Source code implementation for generate_defense_deck.py. | [View .md](EC499report/generate_defense_deck.md) |
| [`EC499report/generate_detailed_plots.py`](EC499report/generate_detailed_plots.md) | `python` | 796 | 39.9 KB | Source code implementation for generate_detailed_plots.py. | [View .md](EC499report/generate_detailed_plots.md) |
| [`EC499report/generate_docx_report.py`](EC499report/generate_docx_report.md) | `python` | 433 | 28.4 KB | Source code implementation for generate_docx_report.py. | [View .md](EC499report/generate_docx_report.md) |
| [`EC499report/generate_phase1_figures.py`](EC499report/generate_phase1_figures.md) | `python` | 441 | 21.3 KB | Source code implementation for generate_phase1_figures.py. | [View .md](EC499report/generate_phase1_figures.md) |
| [`EC499report/package_submission.py`](EC499report/package_submission.md) | `python` | 411 | 22.7 KB | Source code implementation for package_submission.py. | [View .md](EC499report/package_submission.md) |
| [`EC499report/report_builder/build_report.py`](EC499report/report_builder/build_report.md) | `python` | 69 | 3.7 KB | Ensure path is included | [View .md](EC499report/report_builder/build_report.md) |
| [`EC499report/report_builder/p01_preamble.py`](EC499report/report_builder/p01_preamble.md) | `python` | 370 | 16.9 KB | Preliminary pages and LaTeX preamble | [View .md](EC499report/report_builder/p01_preamble.md) |
| [`EC499report/report_builder/p02_ch1_intro.py`](EC499report/report_builder/p02_ch1_intro.md) | `python` | 79 | 6.9 KB | Chapter 1: Introduction | [View .md](EC499report/report_builder/p02_ch1_intro.md) |
| [`EC499report/report_builder/p03_ch2_background.py`](EC499report/report_builder/p03_ch2_background.md) | `python` | 150 | 13.7 KB | Chapter 2: Background | [View .md](EC499report/report_builder/p03_ch2_background.md) |
| [`EC499report/report_builder/p04_ch3_related.py`](EC499report/report_builder/p04_ch3_related.md) | `python` | 73 | 7.1 KB | Chapter 3: Related Work | [View .md](EC499report/report_builder/p04_ch3_related.md) |
| [`EC499report/report_builder/p05_ch4_design_exp.py`](EC499report/report_builder/p05_ch4_design_exp.md) | `python` | 782 | 50.9 KB | Chapter 4: The Proposed System (Part 1 - Design and Experiments) | [View .md](EC499report/report_builder/p05_ch4_design_exp.md) |
| [`EC499report/report_builder/p06_ch4_eval_results.py`](EC499report/report_builder/p06_ch4_eval_results.md) | `python` | 431 | 38.8 KB | Chapter 4: The Proposed System (Part 2 - Testing & Evaluation, Results & Discussion) | [View .md](EC499report/report_builder/p06_ch4_eval_results.md) |
| [`EC499report/report_builder/p07_ch5_conclusion.py`](EC499report/report_builder/p07_ch5_conclusion.md) | `python` | 23 | 2.9 KB | Chapter 5: Conclusion | [View .md](EC499report/report_builder/p07_ch5_conclusion.md) |
| [`EC499report/report_builder/p08_ch6_future_work.py`](EC499report/report_builder/p08_ch6_future_work.md) | `python` | 27 | 2.9 KB | Chapter 6: Future Work | [View .md](EC499report/report_builder/p08_ch6_future_work.md) |
| [`EC499report/report_builder/p09_references_appendices.py`](EC499report/report_builder/p09_references_appendices.md) | `python` | 526 | 35.1 KB | References and Appendices | [View .md](EC499report/report_builder/p09_references_appendices.md) |
| [`EC499sildes/build_html_presentation.py`](EC499sildes/build_html_presentation.md) | `python` | 737 | 52.0 KB | Source code implementation for build_html_presentation.py. | [View .md](EC499sildes/build_html_presentation.md) |
| [`EC499sildes/build_slides.py`](EC499sildes/build_slides.md) | `python` | 670 | 47.3 KB | Source code implementation for build_slides.py. | [View .md](EC499sildes/build_slides.md) |
| [`EC499tests/stress_ha_cluster_deep.py`](EC499tests/stress_ha_cluster_deep.md) | `python` | 293 | 12.2 KB | Source code implementation for stress_ha_cluster_deep.py. | [View .md](EC499tests/stress_ha_cluster_deep.md) |
| [`EC499tests/test_adversarial_d3qn_challenger.py`](EC499tests/test_adversarial_d3qn_challenger.md) | `python` | 620 | 29.2 KB | Source code implementation for test_adversarial_d3qn_challenger.py. | [View .md](EC499tests/test_adversarial_d3qn_challenger.md) |
| [`EC499tests/test_challenger2_api_ha.py`](EC499tests/test_challenger2_api_ha.md) | `python` | 273 | 11.4 KB | Source code implementation for test_challenger2_api_ha.py. | [View .md](EC499tests/test_challenger2_api_ha.md) |
| [`EC499tests/test_dashboard_100_runs.py`](EC499tests/test_dashboard_100_runs.md) | `python` | 313 | 19.9 KB | Source code implementation for test_dashboard_100_runs.py. | [View .md](EC499tests/test_dashboard_100_runs.md) |
| [`EC499tests/test_e2e_opaque_box.py`](EC499tests/test_e2e_opaque_box.md) | `python` | 829 | 36.5 KB | Source code implementation for test_e2e_opaque_box.py. | [View .md](EC499tests/test_e2e_opaque_box.md) |
| [`EC499tests/test_ha_adversarial_suite.py`](EC499tests/test_ha_adversarial_suite.md) | `python` | 538 | 25.4 KB | Source code implementation for test_ha_adversarial_suite.py. | [View .md](EC499tests/test_ha_adversarial_suite.md) |
| [`EC499tests/test_ha_controller_failover.py`](EC499tests/test_ha_controller_failover.md) | `python` | 199 | 9.0 KB | Source code implementation for test_ha_controller_failover.py. | [View .md](EC499tests/test_ha_controller_failover.md) |
| [`EC499tests/test_suite.py`](EC499tests/test_suite.md) | `python` | 704 | 30.8 KB | Source code implementation for test_suite.py. | [View .md](EC499tests/test_suite.md) |

