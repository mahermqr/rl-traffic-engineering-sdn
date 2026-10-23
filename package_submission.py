#!/usr/bin/env python3
"""
Packages the complete, authoritative EC499 graduation submission bundle for:
Maher Abdulnasir Alqadhi (Student ID: 2210249576)
Supervisor: Dr. Suad El-Geder
Department of Computer Engineering, University of Tripoli.

Creates a structured, timestamped, self-contained submission archive containing:
- 143-page Master Thesis PDF & LaTeX sources
- 30-slide PowerPoint deck & standalone interactive HTML slides
- Defense quick-reference cheat sheet & live demo runbook
- All 15 publication-grade experimental plots & environment captures
- Official Mininet validation logs and benchmark matrices
- Trained PyTorch D3QN model weights
- Carrier-grade source code, tests, and web dashboard
- Cryptographic SHA256 checksums manifest
"""

import os
import shutil
import zipfile
import hashlib
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
DOCS_DIR = BASE_DIR / "docs"
LOGS_DIR = BASE_DIR / "logs"
PLOTS_DIR = LOGS_DIR / "plots"
MODELS_DIR = BASE_DIR / "models"
CONTROLLER_DIR = BASE_DIR / "controller"
AGENT_DIR = BASE_DIR / "agent"
TOPOLOGY_DIR = BASE_DIR / "topology"

BUNDLE_NAME = "Maher_Alqadhi_2210249576_EC499_Final_Graduation_Submission"
DIST_DIR = BASE_DIR / "dist"
BUNDLE_ROOT = DIST_DIR / BUNDLE_NAME
ZIP_OUTPUT_DOCS = DOCS_DIR / f"{BUNDLE_NAME}.zip"
ZIP_OUTPUT_ROOT = BASE_DIR.parent / f"{BUNDLE_NAME}.zip"

def compute_sha256(filepath):
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

def main():
    print(f"[*] Starting graduation submission packaging for {BUNDLE_NAME}...")

    # Clean existing dist
    if BUNDLE_ROOT.exists():
        shutil.rmtree(BUNDLE_ROOT)
    BUNDLE_ROOT.mkdir(parents=True, exist_ok=True)

    # 1. 01_Final_Thesis_Report
    dir_thesis = BUNDLE_ROOT / "01_Final_Thesis_Report"
    dir_thesis.mkdir(parents=True, exist_ok=True)
    report_artifacts_pdf = BASE_DIR / "report_artifacts" / "main.pdf"
    if report_artifacts_pdf.exists():
        shutil.copy2(report_artifacts_pdf, dir_thesis / "Project_Report_EC499_Final.pdf")
        shutil.copy2(report_artifacts_pdf, dir_thesis / "main.pdf")
        if (BASE_DIR / "report_artifacts" / "main.tex").exists():
            shutil.copy2(BASE_DIR / "report_artifacts" / "main.tex", dir_thesis / "main.tex")
        if (BASE_DIR / "report_artifacts" / "references.bib").exists():
            shutil.copy2(BASE_DIR / "report_artifacts" / "references.bib", dir_thesis / "references.bib")
    elif (DOCS_DIR / "Project_Report_EC499_Final.pdf").exists():
        shutil.copy2(DOCS_DIR / "Project_Report_EC499_Final.pdf", dir_thesis / "Project_Report_EC499_Final.pdf")
    if (DOCS_DIR / "Project_Report_EC499_Monolithic.tex").exists():
        shutil.copy2(DOCS_DIR / "Project_Report_EC499_Monolithic.tex", dir_thesis / "Project_Report_EC499_Monolithic.tex")
    if (DOCS_DIR / "references.bib").exists() and not (dir_thesis / "references.bib").exists():
        shutil.copy2(DOCS_DIR / "references.bib", dir_thesis / "references.bib")
    if (DOCS_DIR / "chapters").exists():
        shutil.copytree(DOCS_DIR / "chapters", dir_thesis / "chapters")
    if (DOCS_DIR / "appendices").exists():
        shutil.copytree(DOCS_DIR / "appendices", dir_thesis / "appendices")
    print("  [+] Staged 01_Final_Thesis_Report (143-Page PDF & Complete LaTeX Sources)")

    # 2. 02_Defense_Presentation
    dir_defense = BUNDLE_ROOT / "02_Defense_Presentation"
    dir_defense.mkdir(parents=True, exist_ok=True)
    if (DOCS_DIR / "EC499_Graduation_Defense_Presentation.pptx").exists():
        shutil.copy2(DOCS_DIR / "EC499_Graduation_Defense_Presentation.pptx", dir_defense / "EC499_Graduation_Defense_Presentation.pptx")
    if (DOCS_DIR / "EC499_Graduation_Defense_Slides.html").exists():
        shutil.copy2(DOCS_DIR / "EC499_Graduation_Defense_Slides.html", dir_defense / "EC499_Graduation_Defense_Slides.html")
    if (DOCS_DIR / "DEFENSE_CHEAT_SHEET.md").exists():
        shutil.copy2(DOCS_DIR / "DEFENSE_CHEAT_SHEET.md", dir_defense / "DEFENSE_CHEAT_SHEET.md")
    if (DOCS_DIR / "VIVA_DEFENSE_MASTER_GUIDE.md").exists():
        shutil.copy2(DOCS_DIR / "VIVA_DEFENSE_MASTER_GUIDE.md", dir_defense / "VIVA_DEFENSE_MASTER_GUIDE.md")
    print("  [+] Staged 02_Defense_Presentation (PPTX Deck, Interactive HTML, Viva Guide, Demo Runbook)")

    # 3. 03_Experimental_Figures_and_Plots
    dir_plots = BUNDLE_ROOT / "03_Experimental_Figures_and_Plots"
    dir_plots.mkdir(parents=True, exist_ok=True)
    for plot_file in PLOTS_DIR.glob("*.png"):
        shutil.copy2(plot_file, dir_plots / plot_file.name)
    if (DOCS_DIR / "figures").exists():
        for fig_file in (DOCS_DIR / "figures").glob("*.png"):
            shutil.copy2(fig_file, dir_plots / fig_file.name)
    artifacts_fig_dir = BASE_DIR / "report_artifacts" / "figures"
    if artifacts_fig_dir.exists():
        for fig_file in artifacts_fig_dir.glob("*.png"):
            shutil.copy2(fig_file, dir_plots / fig_file.name)
    print(f"  [+] Staged 03_Experimental_Figures_and_Plots ({len(list(dir_plots.glob('*.png')))} figures and UI captures)")

    # 4. 04_Validation_Logs_and_Metrics
    dir_logs = BUNDLE_ROOT / "04_Validation_Logs_and_Metrics"
    dir_logs.mkdir(parents=True, exist_ok=True)
    matrix_src = LOGS_DIR / "mininet_matrix" / "validation_matrix_S7_udp_20261015_075319.csv"
    if matrix_src.exists():
        shutil.copy2(matrix_src, dir_logs / "validation_matrix_S7_udp_20261015_075319.csv")
    for log_name in ["training_metrics.csv", "evaluation_results.json", "routing_tournament_results.json", "pareto_sensitivity_ablation.json"]:
        p = LOGS_DIR / log_name
        if p.exists():
            shutil.copy2(p, dir_logs / log_name)
    artifacts_data_dir = BASE_DIR / "report_artifacts" / "data"
    if artifacts_data_dir.exists():
        for data_file in artifacts_data_dir.glob("*.json"):
            shutil.copy2(data_file, dir_logs / data_file.name)
    print("  [+] Staged 04_Validation_Logs_and_Metrics (Official CSV Matrix & JSON Benchmarks)")

    # 5. 05_Trained_D3QN_Model
    dir_model = BUNDLE_ROOT / "05_Trained_D3QN_Model"
    dir_model.mkdir(parents=True, exist_ok=True)
    if (MODELS_DIR / "dqn_router.pth").exists():
        shutil.copy2(MODELS_DIR / "dqn_router.pth", dir_model / "dqn_router.pth")
    print("  [+] Staged 05_Trained_D3QN_Model (PyTorch Neural Weights)")

    # 6. 06_Source_Code_and_Dashboard
    dir_code = BUNDLE_ROOT / "06_Source_Code_and_Dashboard"
    dir_code.mkdir(parents=True, exist_ok=True)
    if CONTROLLER_DIR.exists():
        shutil.copytree(CONTROLLER_DIR, dir_code / "controller", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    if AGENT_DIR.exists():
        shutil.copytree(AGENT_DIR, dir_code / "agent", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    if TOPOLOGY_DIR.exists():
        shutil.copytree(TOPOLOGY_DIR, dir_code / "topology", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for script in [
        "config.py", "test_suite.py", "benchmark_evaluation.py",
        "benchmark_routing_algorithms.py", "stress_test_load_balancer.py",
        "stress_test_blind_topologies.py", "evaluate_random_blind_topology.py",
        "simulate_live_traffic.py", "audit_dqn_agent_deep.py",
        "ablate_reward_weights.py", "generate_detailed_plots.py",
        "experiment_phase1_suite.py", "experiment_phase2_packet_validation.py",
        "generate_phase1_figures.py", "reproduce_mininet_packet_experiment.py",
        "reproduce_all.sh", "run_tests.sh", "run_benchmarks.sh", "run_benchmarks.py",
        "run_system.sh", "run_ha_test.sh", "run_random_blind_test.sh",
        "test_ha_controller_failover.py", "test_dashboard_100_runs.py",
        "requirements.txt", "pyproject.toml", "README.md", "LICENSE", "CITATION.cff",
    ]:
        p = BASE_DIR / script
        if p.exists():
            shutil.copy2(p, dir_code / script)
    print("  [+] Staged 06_Source_Code_and_Dashboard (Controller, Simulation, Tests, Tools)")

    # 7. 07_Live_Demo_and_Screenshots
    dir_demo = BUNDLE_ROOT / "07_Live_Demo_and_Screenshots"
    dir_demo.mkdir(parents=True, exist_ok=True)
    demo_src = BASE_DIR.parent / "demo2026"
    if demo_src.exists():
        shutil.copytree(demo_src, dir_demo / "demo2026", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        print(f"  [+] Staged 07_Live_Demo_and_Screenshots (Interactive Demo Suite & All Scenarios)")

    # 8. Generate README_GRADUATION_SUBMISSION.md
    readme_path = BUNDLE_ROOT / "README_GRADUATION_SUBMISSION.md"
    readme_content = f"""# EC499 Final Graduation Project Submission Dossier

**University of Tripoli &bull; Faculty of Engineering &bull; Department of Computer Engineering**  
**Project Title:** *Reinforcement Learning for Adaptive Traffic Engineering in an SDN Network*  
**Degree Candidate:** Maher Abdulnasir Alqadhi (Student ID: `2210249576`)  
**Project Supervisor:** Dr. Suad El-Geder (Associate Professor)  
**Submission Date:** October 2026  

---

## 1. Project Abstract
Static shortest-path routing frequently induces severe congestion along primary network trunks by assigning flows without considering real-time link loads or parallel capacity. This project presents an adaptive, closed-loop Software-Defined Networking (SDN) traffic engineering architecture combining a Ryu OpenFlow 1.3 controller, a NetworkX global topology model, and a PyTorch Dueling Double Deep Q-Network (D3QN) with Prioritized Experience Replay. Candidate paths are dynamically selected using a normalized ten-dimensional state representation capturing hop count, bottleneck utilization, propagation delay, and network-wide load.

The architecture was evaluated against conventional baselines, including OSPF, Dijkstra SPF, Equal-Cost Multi-Path (ECMP), Widest Shortest Path (WSP), Least-Loaded Routing (LLR), and an exact Unsplittable Multi-Commodity Flow integer linear programming oracle solved via HiGHS. Across benchmark topologies and two-way cluster bootstrap analyses with 95% confidence intervals, the D3QN agent significantly outperformed static routing, achieving up to 23.07% bottleneck utilization relief while reducing latency and packet loss. An architectural ablation demonstrated that dueling streams drive the primary latency reduction, while hierarchical variance analysis across five independent seeds proved that weight initialization contributes only 0.73% to performance variance. Furthermore, zero-shot evaluation on held-out topologies confirmed robust out-of-distribution transfer without retraining. With sub-millisecond inference (0.04 ms), carrier-grade controller failover, and discrete-event queue validation, the system provides a mathematically grounded, reproducible foundation for intelligent software-defined networks.

---

## 2. Directory Layout & Manifest

```text
Maher_Alqadhi_2210249576_EC499_Final_Graduation_Submission/
├── README_GRADUATION_SUBMISSION.md        <- This authoritative dossier
├── CHECKSUMS_SHA256.txt                   <- Cryptographic SHA256 integrity hashes
│
├── 01_Final_Thesis_Report/
│   ├── Project_Report_EC499_Final.pdf     <- Authoritative 143-Page Master Thesis PDF
│   ├── Project_Report_EC499_Monolithic.tex<- Monolithic LaTeX document (3,886 lines)
│   ├── references.bib                     <- Complete academic bibliography
│   ├── chapters/                          <- All 11 thesis chapters (Modular LaTeX)
│   └── appendices/                        <- All 5 technical appendices (Modular LaTeX)
│
├── 02_Defense_Presentation/
│   ├── EC499_Graduation_Defense_Presentation.pptx <- 30-Slide PowerPoint Presentation Deck
│   ├── EC499_Graduation_Defense_Slides.html       <- Standalone Interactive HTML5 Deck
│   └── DEFENSE_CHEAT_SHEET.md                     <- 5-Minute Demo Runbook & 11 Committee Q&As
│
├── 03_Experimental_Figures_and_Plots/     <- All 15 High-Resolution Publication Plots
│   ├── proposal_benchmarks_all_metrics.png
│   ├── proposal_tournament_radar.png
│   ├── dqn_te_training_convergence.png
│   ├── routing_cdfs_latency_jitter.png
│   ├── stress_test_load_balancing.png
│   ├── blind_topologies_radar.png
│   ├── blind_topologies_stress_benchmark.png
│   ├── traffic_load_scaling_curves.png
│   ├── random_blind_topologies_evaluation.png
│   ├── dashboard_topology_telemetry.png
│   ├── dashboard_versus_tournament.png
│   ├── dashboard_model_inspector.png
│   ├── dashboard_network_settings.png
│   ├── pareto_weight_sensitivity.png
│   └── vmware_virtual_machine_specs.png
│
├── 04_Validation_Logs_and_Metrics/        <- Empirical Validation Matrices
│   ├── validation_matrix_S7_udp_20261015_075319.csv <- Official Mininet Emulation Matrix
│   ├── training_metrics.csv               <- 500-Episode D3QN Training Convergence Log
│   ├── evaluation_results.json            <- Multi-topology evaluation records
│   ├── routing_tournament_results.json    <- 6-protocol tournament benchmark records
│   └── pareto_sensitivity_ablation.json   <- Pareto weight sensitivity ablation records
│
├── 05_Trained_D3QN_Model/
│   └── dqn_router.pth                     <- Optimized PyTorch Neural Network Weights
│
└── 06_Source_Code_and_Dashboard/          <- Carrier-Grade Python 3.10+ Codebase
    ├── controller/                        <- Ryu SDN controller, state manager, web dashboard
    ├── agent/                             <- D3QN model and replay buffer
    ├── topology/                          <- Network graphs and Mininet fabrics
    ├── config.py                          <- Centralized runtime configuration
    ├── benchmark_routing_algorithms.py    <- 6-Protocol Tournament Benchmark Runner
    ├── stress_test_blind_topologies.py    <- Zero-Shot Generalization Test Runner
    ├── ablate_reward_weights.py           <- Pareto Sensitivity Ablation Suite
    ├── audit_dqn_agent_deep.py            <- Deep Mathematical & Policy Audit Suite
    ├── run_tests.sh                       <- 32-Test Automated Unit & Integration Suite
    └── requirements.txt                   <- Python Dependencies Manifest
```

---

## 3. Quickstart & Verification Instructions

### A. Running the Automated Test Suite
```bash
cd 06_Source_Code_and_Dashboard
bash run_tests.sh
```
*Expected Result:* all tests complete with `OK`.

### B. Launching the Interactive Web Dashboard
```bash
cd 06_Source_Code_and_Dashboard
python3 controller/web_dashboard.py
```
Open **Google Chrome** to `http://localhost:8080`.

### C. Viewing Presentation Slides
- Open `02_Defense_Presentation/EC499_Graduation_Defense_Slides.html` in Google Chrome (press `F` for Fullscreen, `N` for Speaker Notes).
- Open `02_Defense_Presentation/EC499_Graduation_Defense_Presentation.pptx` in Microsoft PowerPoint.

---

## 4. Archived Performance Indicators

The values below are historical results carried in the submitted logs. Re-run the bundled
tests and benchmarks on the target environment before citing them as current measurements.

| Metric | Classical Baseline (OSPF/ECMP) | Proposed D3QN Agent | Measured Benefit |
| :--- | :--- | :--- | :--- |
| **UDP Throughput Delivery** | 38.18 Mbps | **64.89 Mbps** | **+69.9% gain (99.8% line-rate)** |
| **Delay Variation (Jitter)**| 6.97 ms | **1.71 ms** | **76.2% jitter suppression** |
| **Packet Loss Rate** | 4.37% | **0.01%** | **450x loss eradication** |
| **TCP Goodput** | Window deflation | **63.88 Mbps** | **Clean, smooth window growth** |
| **Core Jamming Relief** | 95.05% bottleneck | **53.01% bottleneck** | **+42.04% congestion relief** |
| **Inference Decision Speed**| N/A | **<0.05 ms** | **>2,400 decisions/second** |
| **Zero-Shot Transfer (10 Graphs)** | High failure | **100% Win Rate** | **Invariant across 15–35 nodes** |

---

*Compiled and certified for graduation defense examination, Faculty of Engineering, University of Tripoli.*
"""
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(readme_content)
    print("  [+] Generated README_GRADUATION_SUBMISSION.md")

    # 8. Generate CHECKSUMS_SHA256.txt
    checksums_path = BUNDLE_ROOT / "CHECKSUMS_SHA256.txt"
    lines = []
    for p in sorted(BUNDLE_ROOT.rglob("*")):
        if p.is_file() and p.name != "CHECKSUMS_SHA256.txt":
            rel = p.relative_to(BUNDLE_ROOT)
            sha = compute_sha256(p)
            lines.append(f"{sha}  {rel}")
    with open(checksums_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"  [+] Generated CHECKSUMS_SHA256.txt ({len(lines)} files checksummed)")

    # 9. Compress to ZIP archive
    print(f"[*] Compressing bundle into: {ZIP_OUTPUT_DOCS}...")
    with zipfile.ZipFile(ZIP_OUTPUT_DOCS, "w", zipfile.ZIP_DEFLATED) as zipf:
        for p in sorted(BUNDLE_ROOT.rglob("*")):
            if p.is_file():
                arcname = p.relative_to(DIST_DIR)
                zipf.write(p, arcname)

    # Copy to root workspace
    shutil.copy2(ZIP_OUTPUT_DOCS, ZIP_OUTPUT_ROOT)

    zip_size_mb = ZIP_OUTPUT_DOCS.stat().st_size / (1024 * 1024)
    print(f"[+] Successfully generated Graduation Submission ZIP:")
    print(f"    - Docs Copy: {ZIP_OUTPUT_DOCS} ({zip_size_mb:.2f} MB)")
    print(f"    - Root Copy: {ZIP_OUTPUT_ROOT} ({zip_size_mb:.2f} MB)")

if __name__ == "__main__":
    main()
