# `EC499report/package_submission.py`

> **File:** `EC499report/package_submission.py`  
> **Subsystem / Category:** 9. Publications, Documentation & Slide Generation  
> **Language:** `python`  
> **Lines of Code:** 411  
> **File Size:** 22.67 KB  

---

## Overview

Source code implementation for package_submission.py.

### Architecture & Symbols
- **Classes:** None (Procedural / Script)
- **Key Functions:** `compute_sha256`, `main`

---

## Source Code

````python
#!/usr/bin/env python3
"""
Packages the complete, authoritative EC499 graduation submission bundle for:
Maher Abdulnasir Alqadhi (Student ID: 2210249576)
Supervisor: Dr. Suad El-Geder
Department of Computer Engineering, University of Tripoli.

Creates a structured, timestamped, self-contained submission archive containing:
- Master thesis PDF & LaTeX sources
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

_curr = Path(__file__).resolve().parent
PROJECT_ROOT = _curr if (_curr / "agent").exists() else _curr.parent
REPORT_DIR = _curr
TESTS_DIR = PROJECT_ROOT / "EC499tests"

BASE_DIR = PROJECT_ROOT
DOCS_DIR = REPORT_DIR / "docs"
LOGS_DIR = PROJECT_ROOT / "logs"
PLOTS_DIR = LOGS_DIR / "plots"
MODELS_DIR = PROJECT_ROOT / "models"
CONTROLLER_DIR = PROJECT_ROOT / "controller"
AGENT_DIR = PROJECT_ROOT / "agent"
TOPOLOGY_DIR = PROJECT_ROOT / "topology"

BUNDLE_NAME = "Maher_Alqadhi_2210249576_EC499_Final_Graduation_Submission"
DIST_DIR = PROJECT_ROOT / "dist"
BUNDLE_ROOT = DIST_DIR / BUNDLE_NAME
ZIP_OUTPUT_DOCS = DOCS_DIR / f"{BUNDLE_NAME}.zip"
ZIP_OUTPUT_ROOT = PROJECT_ROOT / f"{BUNDLE_NAME}.zip"

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

    # 1. 01_Thesis_Document
    dir_thesis = BUNDLE_ROOT / "01_Thesis_Document"
    dir_thesis.mkdir(parents=True, exist_ok=True)
    master_pdf = PROJECT_ROOT.parent / "Project_Report_EC499_Final.pdf"
    report_artifacts_pdf = REPORT_DIR / "report_artifacts" / "main.pdf"
    if master_pdf.exists():
        shutil.copy2(master_pdf, dir_thesis / "Project_Report_EC499_Final.pdf")
        shutil.copy2(master_pdf, dir_thesis / "main.pdf")
    elif report_artifacts_pdf.exists():
        shutil.copy2(report_artifacts_pdf, dir_thesis / "Project_Report_EC499_Final.pdf")
        shutil.copy2(report_artifacts_pdf, dir_thesis / "main.pdf")

    master_tex = PROJECT_ROOT.parent / "Project_Report_EC499_Final.tex"
    if master_tex.exists():
        shutil.copy2(master_tex, dir_thesis / "Project_Report_EC499_Final.tex")
        shutil.copy2(master_tex, dir_thesis / "main.tex")
    elif (REPORT_DIR / "report_artifacts" / "main.tex").exists():
        shutil.copy2(REPORT_DIR / "report_artifacts" / "main.tex", dir_thesis / "main.tex")

    if (REPORT_DIR / "report_artifacts" / "references.bib").exists():
        shutil.copy2(REPORT_DIR / "report_artifacts" / "references.bib", dir_thesis / "references.bib")
    if (DOCS_DIR / "Project_Report_EC499_Monolithic.tex").exists():
        shutil.copy2(DOCS_DIR / "Project_Report_EC499_Monolithic.tex", dir_thesis / "Project_Report_EC499_Monolithic.tex")
    if (DOCS_DIR / "references.bib").exists() and not (dir_thesis / "references.bib").exists():
        shutil.copy2(DOCS_DIR / "references.bib", dir_thesis / "references.bib")
    if (DOCS_DIR / "chapters").exists():
        shutil.copytree(DOCS_DIR / "chapters", dir_thesis / "chapters")
    if (DOCS_DIR / "appendices").exists():
        shutil.copytree(DOCS_DIR / "appendices", dir_thesis / "appendices")
    docx_src = DOCS_DIR / "Project_Report_EC499_Final.docx"
    if not docx_src.exists():
        docx_src = PROJECT_ROOT.parent / "Project_Report_EC499_Final.docx"
    if docx_src.exists():
        shutil.copy2(docx_src, dir_thesis / "Project_Report_EC499_Final.docx")
    print("  [+] Staged 01_Thesis_Document (PDF, DOCX & Complete LaTeX Sources)")

    # 2. 02_Examination_Handout
    dir_handout = BUNDLE_ROOT / "02_Examination_Handout"
    dir_handout.mkdir(parents=True, exist_ok=True)
    for handout_name in ["mahermqr.pdf", "mahermqr.docx", "mahermqr.md", "mahermqr.tex"]:
        for h_dir in [DOCS_DIR, REPORT_DIR, PROJECT_ROOT.parent]:
            if (h_dir / handout_name).exists():
                shutil.copy2(h_dir / handout_name, dir_handout / handout_name)
                break
    print("  [+] Staged 02_Examination_Handout (PDF, DOCX, MD, TeX)")

    # 3. 03_Defense_Presentation
    dir_defense = BUNDLE_ROOT / "03_Defense_Presentation"
    dir_defense.mkdir(parents=True, exist_ok=True)
    slides_dir = PROJECT_ROOT.parent / "EC499sildes"
    if (slides_dir / "EC499_Defense_Slides.pdf").exists():
        shutil.copy2(slides_dir / "EC499_Defense_Slides.pdf", dir_defense / "EC499_Defense_Slides.pdf")
    if (slides_dir / "EC499_Final_Defense_Presentation.pptx").exists():
        shutil.copy2(slides_dir / "EC499_Final_Defense_Presentation.pptx", dir_defense / "EC499_Final_Defense_Presentation.pptx")
    if (slides_dir / "index.html").exists():
        shutil.copy2(slides_dir / "index.html", dir_defense / "EC499_Defense_Deck_Interactive.html")
    if (slides_dir / "slides.css").exists():
        shutil.copy2(slides_dir / "slides.css", dir_defense / "slides.css")
    if (slides_dir / "slides.js").exists():
        shutil.copy2(slides_dir / "slides.js", dir_defense / "slides.js")
    if (DOCS_DIR / "EC499_Graduation_Defense_Presentation.pptx").exists() and not (dir_defense / "EC499_Final_Defense_Presentation.pptx").exists():
        shutil.copy2(DOCS_DIR / "EC499_Graduation_Defense_Presentation.pptx", dir_defense / "EC499_Graduation_Defense_Presentation.pptx")
    if (DOCS_DIR / "EC499_Graduation_Defense_Slides.html").exists() and not (dir_defense / "EC499_Defense_Deck_Interactive.html").exists():
        shutil.copy2(DOCS_DIR / "EC499_Graduation_Defense_Slides.html", dir_defense / "EC499_Graduation_Defense_Slides.html")
    if (DOCS_DIR / "DEFENSE_CHEAT_SHEET.md").exists():
        shutil.copy2(DOCS_DIR / "DEFENSE_CHEAT_SHEET.md", dir_defense / "DEFENSE_CHEAT_SHEET.md")
    if (DOCS_DIR / "VIVA_DEFENSE_MASTER_GUIDE.md").exists():
        shutil.copy2(DOCS_DIR / "VIVA_DEFENSE_MASTER_GUIDE.md", dir_defense / "VIVA_DEFENSE_MASTER_GUIDE.md")
    print("  [+] Staged 03_Defense_Presentation (Vector PDF, PPTX Deck, Interactive HTML, Viva Guide)")

    # 4. 04_Source_Code
    dir_code = BUNDLE_ROOT / "04_Source_Code"
    dir_code.mkdir(parents=True, exist_ok=True)
    if CONTROLLER_DIR.exists():
        shutil.copytree(CONTROLLER_DIR, dir_code / "controller", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    if AGENT_DIR.exists():
        shutil.copytree(AGENT_DIR, dir_code / "agent", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    if TOPOLOGY_DIR.exists():
        shutil.copytree(TOPOLOGY_DIR, dir_code / "topology", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    report_builder_src = PROJECT_ROOT.parent / "report_builder"
    if report_builder_src.exists():
        shutil.copytree(report_builder_src, dir_code / "report_builder", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    scripts_dir = BASE_DIR / "scripts"
    if scripts_dir.exists():
        shutil.copytree(scripts_dir, dir_code / "scripts", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for script in [
        "config.py", "test_suite.py", "benchmark_evaluation.py",
        "benchmark_routing_algorithms.py", "stress_test_load_balancer.py",
        "stress_test_blind_topologies.py", "evaluate_random_blind_topology.py",
        "simulate_live_traffic.py", "audit_dqn_agent_deep.py",
        "ablate_reward_weights.py", "generate_detailed_plots.py",
        "experiment_phase1_suite.py", "experiment_phase2_packet_validation.py",
        "generate_phase1_figures.py", "reproduce_mininet_packet_experiment.py",
        "analyze_mininet_measured_trials.py",
        "reproduce_all.sh", "run_tests.sh", "run_benchmarks.sh", "run_benchmarks.py",
        "run_system.sh", "run_ha_test.sh", "run_random_blind_test.sh",
        "test_ha_controller_failover.py", "test_dashboard_100_runs.py",
        "requirements.txt", "pyproject.toml", "README.md", "LICENSE", "CITATION.cff",
    ]:
        p = PROJECT_ROOT / script
        if not p.exists():
            p = REPORT_DIR / script
        if not p.exists():
            p = TESTS_DIR / script
        if p.exists():
            shutil.copy2(p, dir_code / script)
    print("  [+] Staged 04_Source_Code (Controller, Agent, Topology, Report Builder, Tests, Tools)")

    # 5. 05_Trained_Models
    dir_models = BUNDLE_ROOT / "05_Trained_Models"
    dir_models.mkdir(parents=True, exist_ok=True)
    if (MODELS_DIR / "dqn_router.pth").exists():
        shutil.copy2(MODELS_DIR / "dqn_router.pth", dir_models / "dqn_router.pth")
    if MODELS_DIR.exists():
        for mf in MODELS_DIR.glob("*.pth"):
            shutil.copy2(mf, dir_models / mf.name)
    print("  [+] Staged 05_Trained_Models (PyTorch Neural Weights)")

    # 6. 06_Test_Reports
    dir_reports = BUNDLE_ROOT / "06_Test_Reports"
    dir_reports.mkdir(parents=True, exist_ok=True)
    matrix_dir = LOGS_DIR / "mininet_matrix"
    if matrix_dir.exists():
        shutil.copytree(matrix_dir, dir_reports / "mininet_matrix", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for log_name in ["training_metrics.csv", "evaluation_results.json", "routing_tournament_results.json", "pareto_sensitivity_ablation.json"]:
        p = LOGS_DIR / log_name
        if p.exists():
            shutil.copy2(p, dir_reports / log_name)
    artifacts_data_dir = REPORT_DIR / "report_artifacts" / "data"
    if artifacts_data_dir.exists():
        for data_file in artifacts_data_dir.glob("*.json"):
            shutil.copy2(data_file, dir_reports / data_file.name)
    dir_plots = dir_reports / "figures"
    dir_plots.mkdir(parents=True, exist_ok=True)
    for plot_file in PLOTS_DIR.glob("*.png"):
        shutil.copy2(plot_file, dir_plots / plot_file.name)
    if (DOCS_DIR / "figures").exists():
        for fig_file in (DOCS_DIR / "figures").glob("*.png"):
            shutil.copy2(fig_file, dir_plots / fig_file.name)
    artifacts_fig_dir = REPORT_DIR / "report_artifacts" / "figures"
    if artifacts_fig_dir.exists():
        for fig_file in artifacts_fig_dir.glob("*.png"):
            shutil.copy2(fig_file, dir_plots / fig_file.name)
    root_fig_dir = PROJECT_ROOT.parent / "figures"
    if root_fig_dir.exists():
        for fig_file in root_fig_dir.glob("*.png"):
            if not (dir_plots / fig_file.name).exists():
                shutil.copy2(fig_file, dir_plots / fig_file.name)
    demo_src = BASE_DIR.parent / "demo2026"
    if demo_src.exists():
        shutil.copytree(demo_src, dir_reports / "demo2026", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    print("  [+] Staged 06_Test_Reports (CSV Matrices, JSON Benchmarks, Figures, Demo Suite)")

    # 8. Generate README_GRADUATION_SUBMISSION.md
    readme_path = BUNDLE_ROOT / "README_GRADUATION_SUBMISSION.md"
    readme_content = f"""# EC499 Final Graduation Project Submission Dossier

**University of Tripoli &bull; Faculty of Engineering &bull; Department of Computer Engineering**  
**Project Title:** *Reinforcement Learning for Adaptive Traffic Engineering in an SDN Network*  
**Degree Candidate:** Maher Abdulnasir Alqadhi (Student ID: `2210249576`)  
**Project Supervisor:** Dr. Suad El-Geder  
**Submission Date:** Spring 2026  

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
├── 01_Thesis_Document/
│   ├── Project_Report_EC499_Final.pdf     <- Authoritative Master Thesis PDF (82 pages)
│   ├── Project_Report_EC499_Final.docx    <- Authoritative Master Thesis DOCX (Word Document)
│   ├── Project_Report_EC499_Final.tex     <- Monolithic LaTeX document (4,150+ lines)
│   ├── main.tex                           <- Clean Root LaTeX file
│   ├── references.bib                     <- Complete academic bibliography
│   ├── chapters/                          <- Thesis chapters (Modular LaTeX)
│   └── appendices/                        <- Technical appendices (Modular LaTeX)
│
├── 02_Examination_Handout/
│   ├── mahermqr.pdf                       <- 4-Page Examination Defense Handout PDF
│   ├── mahermqr.docx                      <- Editable Word Handout
│   ├── mahermqr.md                        <- Markdown Handout
│   └── mahermqr.tex                       <- LaTeX Source for Handout
│
├── 03_Defense_Presentation/
│   ├── EC499_Defense_Slides.pdf           <- Presentation Slides PDF
│   ├── EC499_Final_Defense_Presentation.pptx <- PowerPoint Presentation Deck
│   ├── EC499_Defense_Deck_Interactive.html <- Standalone Interactive HTML5 Deck
│   ├── slides.css                         <- Presentation Stylesheet
│   ├── slides.js                          <- Interactive Presentation Scripts
│   ├── DEFENSE_CHEAT_SHEET.md             <- 5-Minute Demo Runbook & Committee Q&As
│   └── VIVA_DEFENSE_MASTER_GUIDE.md       <- Complete Oral Examination Defense Guide
│
├── 04_Source_Code/                        <- Carrier-Grade Python 3.10+ Codebase
│   ├── controller/                        <- Ryu SDN controller, state manager, web dashboard
│   ├── agent/                             <- D3QN model and replay buffer
│   ├── topology/                          <- Network graphs and Mininet fabrics
│   ├── report_builder/                    <- Automated LaTeX report generation pipeline
│   ├── config.py                          <- Centralized runtime configuration
│   ├── benchmark_routing_algorithms.py    <- 6-Protocol Tournament Benchmark Runner
│   ├── stress_test_blind_topologies.py    <- Zero-Shot Generalization Test Runner
│   ├── ablate_reward_weights.py           <- Pareto Sensitivity Ablation Suite
│   ├── audit_dqn_agent_deep.py            <- Deep Mathematical & Policy Audit Suite
│   ├── run_tests.sh                       <- 42-Test Automated Unit & Integration Suite
│   └── requirements.txt                   <- Python Dependencies Manifest
│
├── 05_Trained_Models/
│   └── dqn_router.pth                     <- Optimized PyTorch Neural Network Weights
│
└── 06_Test_Reports/                       <- Validation Records, Benchmarks & Figures
    ├── mininet_matrix/                    <- Official Mininet Emulation Matrix
    ├── training_metrics.csv               <- D3QN Training Convergence Log
    ├── evaluation_results.json            <- Multi-topology evaluation records
    ├── routing_tournament_results.json    <- 6-protocol tournament benchmark records
    ├── pareto_sensitivity_ablation.json   <- Pareto weight sensitivity ablation records
    ├── figures/                           <- High-Resolution Publication Plots & UI Captures
    └── demo2026/                          <- Interactive Demo Suite & Scenarios
```

---

## 3. Quickstart & Verification Instructions

### A. Running the Automated Test Suite
```bash
cd 04_Source_Code
bash run_tests.sh
```
*Expected Result:* all tests complete with `OK`.

### B. Launching the Interactive Web Dashboard
```bash
cd 04_Source_Code
python3 controller/web_dashboard.py
```
Open **Google Chrome** to `http://localhost:8080`.

### C. Viewing Presentation Slides
- Open `03_Defense_Presentation/EC499_Defense_Deck_Interactive.html` in Google Chrome (press `F` for Fullscreen, `N` for Speaker Notes).
- Open `03_Defense_Presentation/EC499_Final_Defense_Presentation.pptx` in Microsoft PowerPoint.

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

    # Clean up uncompressed staging tree now that zip is complete
    if BUNDLE_ROOT.exists():
        shutil.rmtree(BUNDLE_ROOT)

    # Copy to root workspace and Downloads directory
    shutil.copy2(ZIP_OUTPUT_DOCS, ZIP_OUTPUT_ROOT)
    downloads_dir = Path("/home/maher/Downloads")
    downloads_zip = downloads_dir / f"{BUNDLE_NAME}.zip"
    shutil.copy2(ZIP_OUTPUT_DOCS, downloads_zip)
    root_workspace_zip = PROJECT_ROOT.parent / f"{BUNDLE_NAME}.zip"
    shutil.copy2(ZIP_OUTPUT_DOCS, root_workspace_zip)

    # Also copy DOCX and PDF directly to Downloads and workspace root for immediate access
    if (DOCS_DIR / "Project_Report_EC499_Final.docx").exists():
        shutil.copy2(DOCS_DIR / "Project_Report_EC499_Final.docx", downloads_dir / "Project_Report_EC499_Final.docx")
        shutil.copy2(DOCS_DIR / "Project_Report_EC499_Final.docx", PROJECT_ROOT.parent / "Project_Report_EC499_Final.docx")
    if (DOCS_DIR / "Project_Report_EC499_Final.pdf").exists():
        shutil.copy2(DOCS_DIR / "Project_Report_EC499_Final.pdf", downloads_dir / "Project_Report_EC499_Final.pdf")
        shutil.copy2(DOCS_DIR / "Project_Report_EC499_Final.pdf", PROJECT_ROOT.parent / "Project_Report_EC499_Final.pdf")

    # Generate Overleaf Ready Package with main.tex, references.bib, and all figures
    overleaf_zip = DOCS_DIR / "Overleaf_EC499_Ready_Package.zip"
    with zipfile.ZipFile(overleaf_zip, "w", zipfile.ZIP_DEFLATED) as oz:
        monolithic_tex = PROJECT_ROOT.parent / "Project_Report_EC499_Final.tex"
        if monolithic_tex.exists():
            oz.write(monolithic_tex, "main.tex")
        elif (REPORT_DIR / "report_artifacts" / "main.tex").exists():
            oz.write(REPORT_DIR / "report_artifacts" / "main.tex", "main.tex")
        if (REPORT_DIR / "report_artifacts" / "references.bib").exists():
            oz.write(REPORT_DIR / "report_artifacts" / "references.bib", "references.bib")
        fig_src = REPORT_DIR / "report_artifacts" / "figures"
        seen_figs = set()
        for fdir in [
            fig_src,
            PROJECT_ROOT.parent / "figures",
            PROJECT_ROOT / "logs" / "plots",
        ]:
            if fdir.exists():
                for f in fdir.glob("*"):
                    if f.is_file() and f.name not in seen_figs:
                        oz.write(f, f.name)
                        seen_figs.add(f.name)
    shutil.copy2(overleaf_zip, downloads_dir / "Overleaf_EC499_Ready_Package.zip")
    shutil.copy2(overleaf_zip, PROJECT_ROOT.parent / "Overleaf_EC499_Ready_Package.zip")

    zip_size_mb = ZIP_OUTPUT_DOCS.stat().st_size / (1024 * 1024)
    print(f"[+] Successfully generated Graduation Submission ZIP:")
    print(f"    - Docs Copy: {ZIP_OUTPUT_DOCS} ({zip_size_mb:.2f} MB)")
    print(f"    - Inner Root Copy: {ZIP_OUTPUT_ROOT} ({zip_size_mb:.2f} MB)")
    print(f"    - Workspace Root Copy: {root_workspace_zip} ({zip_size_mb:.2f} MB)")
    print(f"    - Downloads Copy: {downloads_zip} ({zip_size_mb:.2f} MB)")
    print(f"    - Overleaf ZIP: {overleaf_zip}")

if __name__ == "__main__":
    main()
````
