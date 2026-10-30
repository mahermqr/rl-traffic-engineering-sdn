#!/usr/bin/env python3
"""
Convert all codebase source files (.py, .sh) of EC499 project to Markdown (.md)
Generates:
1. Individual .md files in project_code_md/ mirroring folder hierarchy.
2. project_code_md/README.md indexing all individual markdown files.
3. Consolidated ALL_PROJECT_CODES.md containing the complete project code.
"""

import os
import sys
import ast
import re
import shutil

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "project_code_md")
WORKSPACE_ROOT = os.path.abspath(os.path.join(PROJECT_ROOT, ".."))

IGNORE_DIRS = {
    ".git", "__pycache__", "build", "dist",
    "adaptive_sdn_traffic_engineering.egg-info", ".idea", ".vscode",
    "report_artifacts", "project_code_md"
}

FILE_DESCRIPTIONS = {
    "__init__.py": "Top-level package initialization for the EC499 adaptive SDN traffic engineering framework.",
    "config.py": "Centralized system configuration defining network topology defaults, D3QN hyperparameters, OpenFlow polling intervals, queue parameters, reward weights, and path resolutions.",
    "agent/__init__.py": "Reinforcement learning package export exposing DQNRoutingAgent and PrioritizedReplayBuffer.",
    "agent/dqn_router.py": "Dueling Double Deep Q-Network (D3QN) routing agent implementation with prioritized experience replay, epsilon-greedy exploration, and target network synchronization in PyTorch.",
    "agent/prioritized_replay.py": "Prioritized Experience Replay (PER) buffer using a binary SumTree structure for O(log N) proportional priority updates and importance-sampling weight correction.",
    "controller/__init__.py": "SDN control plane package initialization for OpenFlow 1.3 Ryu applications.",
    "controller/main_controller.py": "Core OpenFlow 1.3 Ryu controller application handling switch registration, LLDP topology discovery, packet-in dispatch, and flow-table programming.",
    "controller/routing_module.py": "Dynamic routing engine bridging network telemetry with the DQN agent, computing candidate paths, and installing OpenFlow flow rules.",
    "controller/state_manager.py": "Real-time network telemetry engine collecting switch statistics, calculating link latency, jitter, loss, and maintaining the active topology graph.",
    "controller/ha_controller_pool.py": "High-Availability (HA) active-backup controller clustering engine with heartbeat monitoring, leader election, and sub-second failover recovery.",
    "controller/policy_selector.py": "Adaptive routing policy selector dynamically arbitrating between DQN routing, Shortest Path First (SPF), ECMP, and heuristics based on network health.",
    "controller/queue_model.py": "M/M/1/K finite-buffer queueing model utilities for theoretical delay estimation, buffer overflow modeling, and loss probability calculation.",
    "controller/traditional_routing.py": "Traditional routing algorithms baseline suite implementing Dijkstra SPF, Equal-Cost Multi-Path (ECMP), Widest-Path, and Hop-Count routing.",
    "controller/web_dashboard.py": "Interactive Flask & WebSocket real-time telemetry dashboard providing live panoramic topology visualization, performance graphs, and policy controls.",
    "topology/mininet_topo.py": "Mininet network topology builder constructing software-defined switches, host nodes, link bandwidth constraints, and propagation delays.",
    "topology/topology_library.py": "Comprehensive network topology library generating realistic backbones (NSFNET, GÉANT, Fattree, Grid, Mesh, Ring, and random graphs).",
    "topology/traffic_generator.sh": "Multi-profile synthetic traffic generation script orchestrating D-ITG, iperf, and Poisson packet streams across Mininet hosts.",
    "benchmark_evaluation.py": "Comprehensive benchmarking pipeline evaluating DQN performance against Dijkstra, ECMP, and heuristics under diverse traffic intensities.",
    "benchmark_routing_algorithms.py": "Algorithmic benchmark suite measuring route convergence time, latency CDFs, and throughput scaling across routing paradigms.",
    "run_benchmarks.py": "Lightweight CLI runner for executing algorithmic benchmark evaluations.",
    "evaluate_multiseed.py": "Multi-seed statistical significance evaluation calculating mean, standard deviation, and paired t-tests across multiple random initialization seeds.",
    "evaluate_random_blind_topology.py": "Zero-shot transfer learning evaluator testing DQN generalizability and performance on completely unseen random network topologies.",
    "stress_test_blind_topologies.py": "Heavy-load stress testing engine evaluating routing robustness and congestion avoidance on irregular blind topologies.",
    "stress_test_load_balancer.py": "Multi-path load balancing stress testing suite measuring traffic distribution fairness across parallel network links.",
    "ablate_reward_weights.py": "Multi-objective Pareto ablation study systematically analyzing the sensitivity of latency, loss, and utilization weights in the reward function.",
    "audit_dqn_agent_deep.py": "Deep diagnostic auditor analyzing Q-network weight distributions, gradient norms, TD-error convergence, and policy stability.",
    "run_multiseed_ablation_and_sweep.py": "Automated batch runner orchestrating multi-seed hyperparameter sweeps and Pareto frontier evaluations.",
    "experiment_phase1_suite.py": "Phase 1 numerical simulation testbed conducting synthetic traffic experiments and recording comparative telemetry.",
    "experiment_phase2_packet_validation.py": "Phase 2 live Mininet packet validation benchmark capturing real packet latency, jitter, and loss under controlled traffic loads.",
    "analyze_mininet_measured_trials.py": "Telemetry log parser aggregating measured packet trials, generating statistics, and computing confidence intervals.",
    "reproduce_mininet_packet_experiment.py": "Deterministic reproduction runner for replicating the Phase 2 Mininet experimental trials.",
    "simulate_live_traffic.py": "Dynamic traffic emulator generating time-varying Poisson arrival flows and bursty traffic patterns.",
    "test_suite.py": "Comprehensive unit and integration test suite verifying controller components, DQN agent, queue model, and routing mechanisms.",
    "test_dashboard_100_runs.py": "Endurance reliability test executing 100 consecutive dashboard simulation runs to verify memory stability and telemetry integrity.",
    "test_ha_controller_failover.py": "Automated HA controller failover validation script performing fault injection and measuring failover recovery time.",
    "reproduce_all.sh": "Master reproduction script automating the end-to-end execution of all experiments, benchmarks, and report figures.",
    "run_system.sh": "Production launcher script starting the Ryu OpenFlow controller, Mininet topology, and the web telemetry dashboard.",
    "run_tests.sh": "Automated test execution script running the complete pytest and unittest suites.",
    "run_ha_test.sh": "High availability failover demonstration script testing controller fault recovery scenarios.",
    "run_benchmarks.sh": "Benchmark execution script automating comparative algorithm evaluation runs.",
    "run_random_blind_test.sh": "Zero-shot blind topology transfer evaluation automation script.",
    "scripts/resolve_python.sh": "Environment resolution script locating the appropriate Python virtual environment and Ryu dependencies.",
    "scripts/ryu_manager_compat.py": "Compatibility wrapper resolving Ryu manager eventlet and Python execution differences.",
    "build_ali_style_thesis.py": "LaTeX thesis compiler compiling academic reports and formatting camera-ready graduation project manuscripts.",
    "build_html_slides.py": "HTML5 presentation deck generator producing interactive slides with CSS3 animations and embedded charts.",
    "build_mahermqr_handout.py": "Defense handout generator compiling a two-page summary brochure with embedded QR codes linking to project artifacts.",
    "generate_defense_deck.py": "Slide deck generator producing graduation defense presentation slides in PowerPoint (.pptx) and PDF formats.",
    "generate_docx_report.py": "Microsoft Word (.docx) comprehensive project report compiler with formatted tables, headings, and embedded figures.",
    "generate_detailed_plots.py": "Publication-quality figure generation script plotting latency CDFs, radar charts, and training convergence curves.",
    "generate_phase1_figures.py": "Comparative chart plotting script rendering Phase 1 benchmark results.",
    "package_submission.py": "Graduation submission packaging script assembling project zips, checksum manifests, and documentation trees."
}

CATEGORIES = [
    {
        "id": "agent",
        "name": "1. Reinforcement Learning (DQN) Agent",
        "desc": "Deep Q-Network routing models, Dueling architectures, and Prioritized Experience Replay (PER).",
        "matcher": lambda p: p.startswith("agent/")
    },
    {
        "id": "controller",
        "name": "2. SDN Controller Architecture & Modules",
        "desc": "Ryu OpenFlow 1.3 controller, dynamic routing modules, HA failover pool, queue models, and real-time dashboard.",
        "matcher": lambda p: p.startswith("controller/")
    },
    {
        "id": "topology",
        "name": "3. Network Topologies & Traffic Emulation",
        "desc": "Mininet network topologies, realistic topology library (NSFNET, GÉANT, etc.), and D-ITG traffic generators.",
        "matcher": lambda p: p.startswith("topology/")
    },
    {
        "id": "config",
        "name": "4. Project Configuration & Root Package",
        "desc": "Global hyperparameters, OpenFlow thresholds, network telemetry configurations, and package roots.",
        "matcher": lambda p: p in {"config.py", "__init__.py"}
    },
    {
        "id": "benchmarks",
        "name": "5. Benchmarking, Heuristics & Stress Testing",
        "desc": "Evaluation pipelines, shortest-path/ECMP heuristics comparison, reward weight ablation, and blind topology stress tests.",
        "matcher": lambda p: any(k in p for k in [
            "benchmark", "evaluate_", "stress_test", "ablate_reward",
            "audit_dqn", "run_multiseed"
        ]) and not p.endswith(".sh")
    },
    {
        "id": "experiments",
        "name": "6. Experimental Suites & Mininet Packet Validation",
        "desc": "Phase 1 synthetic benchmarks, Phase 2 Mininet packet-level validation, live traffic simulation, and data analysis.",
        "matcher": lambda p: any(k in p for k in [
            "experiment_", "analyze_mininet", "reproduce_mininet", "simulate_live"
        ])
    },
    {
        "id": "tests",
        "name": "7. Verification, Testing & High Availability",
        "desc": "Unit and integration test suites, HA controller failover validation, and 100-run endurance stress testing.",
        "matcher": lambda p: p.startswith("test_")
    },
    {
        "id": "scripts",
        "name": "8. Operational Automation & Shell Scripts",
        "desc": "Automated test runners, high availability verification scripts, runtime launchers, and Ryu wrappers.",
        "matcher": lambda p: p.endswith(".sh") or p.startswith("scripts/")
    },
    {
        "id": "reporting",
        "name": "9. Publications, Documentation & Slide Generation",
        "desc": "LaTeX thesis builders, PowerPoint/PDF slide deck generators, Matplotlib chart plotters, and submission packager.",
        "matcher": lambda p: any(k in p for k in [
            "build_ali", "build_html", "build_mahermqr", "generate_", "package_submission"
        ])
    }
]

def get_file_info(rel_path, abs_path):
    size = os.path.getsize(abs_path)
    with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    
    lines = content.splitlines()
    line_count = len(lines)
    is_python = rel_path.endswith(".py")
    is_shell = rel_path.endswith(".sh")
    
    classes = []
    functions = []
    
    if is_python:
        try:
            tree = ast.parse(content)
            classes = [node.name for node in tree.body if isinstance(node, ast.ClassDef)]
            functions = [node.name for node in tree.body if isinstance(node, ast.FunctionDef)]
        except Exception:
            pass

    docstring = FILE_DESCRIPTIONS.get(rel_path, "")
    if not docstring:
        comment_lines = []
        for line in lines[:25]:
            stripped = line.strip()
            if stripped.startswith("#"):
                comment_lines.append(stripped.lstrip("#!/ ").strip())
            elif stripped.startswith(('"""', "'''")):
                comment_lines.append(stripped.strip("\"'").strip())
            elif comment_lines and not stripped:
                break
        if comment_lines:
            docstring = " ".join([c for c in comment_lines if c and not c.startswith("coding:") and not c.startswith("usr/bin")])

    if not docstring:
        docstring = f"Source code implementation for {os.path.basename(rel_path)}."

    assigned_cat = CATEGORIES[-1]
    for cat in CATEGORIES:
        if cat["matcher"](rel_path):
            assigned_cat = cat
            break
            
    max_backticks = 3
    matches = re.findall(r"`{3,}", content)
    if matches:
        max_backticks = max(len(m) for m in matches) + 1
    fence = "`" * max_backticks

    return {
        "rel_path": rel_path,
        "abs_path": abs_path,
        "filename": os.path.basename(rel_path),
        "size": size,
        "line_count": line_count,
        "is_python": is_python,
        "is_shell": is_shell,
        "lang": "python" if is_python else ("bash" if is_shell else "text"),
        "docstring": docstring.strip(),
        "classes": classes,
        "functions": functions,
        "category": assigned_cat,
        "content": content,
        "fence": fence
    }

def collect_all_files():
    files = []
    for dirpath, dirnames, filenames in os.walk(PROJECT_ROOT):
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS and not d.startswith(".")]
        for f in filenames:
            if f.endswith(".py") or f.endswith(".sh"):
                abs_p = os.path.join(dirpath, f)
                rel_p = os.path.relpath(abs_p, PROJECT_ROOT)
                files.append(get_file_info(rel_p, abs_p))
    files.sort(key=lambda x: x["rel_path"])
    return files

def generate_individual_markdown(file_info):
    cat = file_info["category"]
    
    classes_str = ", ".join(f"`{c}`" for c in file_info["classes"]) if file_info["classes"] else "None (Procedural / Script)"
    functions_str = ", ".join(f"`{fn}`" for fn in file_info["functions"][:12]) if file_info["functions"] else "None (Module level / Declarative)"
    if len(file_info["functions"]) > 12:
        functions_str += f" *(and {len(file_info['functions']) - 12} more)*"

    md = []
    md.append(f"# `{file_info['rel_path']}`")
    md.append("")
    md.append(f"> **File:** `{file_info['rel_path']}`  ")
    md.append(f"> **Subsystem / Category:** {cat['name']}  ")
    md.append(f"> **Language:** `{file_info['lang']}`  ")
    md.append(f"> **Lines of Code:** {file_info['line_count']:,}  ")
    md.append(f"> **File Size:** {file_info['size'] / 1024:.2f} KB  ")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## Overview")
    md.append("")
    md.append(f"{file_info['docstring']}")
    md.append("")
    if file_info["is_python"]:
        md.append("### Architecture & Symbols")
        md.append(f"- **Classes:** {classes_str}")
        md.append(f"- **Key Functions:** {functions_str}")
        md.append("")
    md.append("---")
    md.append("")
    md.append("## Source Code")
    md.append("")
    md.append(f"{file_info['fence']}{file_info['lang']}")
    md.append(file_info["content"].rstrip())
    md.append(f"{file_info['fence']}")
    md.append("")
    
    return "\n".join(md)

def main():
    print("Collecting project code files...")
    all_files = collect_all_files()
    print(f"Total files collected: {len(all_files)}")
    
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    total_loc = sum(f["line_count"] for f in all_files)
    total_size = sum(f["size"] for f in all_files)
    
    created_individual = []
    
    for f in all_files:
        rel_p = f["rel_path"]
        md_content = generate_individual_markdown(f)
        
        stem, ext = os.path.splitext(rel_p)
        other_exists = any(o["rel_path"] != rel_p and os.path.splitext(o["rel_path"])[0] == stem for o in all_files)
        
        if other_exists:
            clean_name = f"{stem}_{ext.lstrip('.')}.md"
        else:
            clean_name = f"{stem}.md"
            
        out_path = os.path.join(OUTPUT_DIR, clean_name)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as fp:
            fp.write(md_content)
                
        f["out_md_rel"] = clean_name
        created_individual.append(out_path)
        
    print(f"Generated {len(created_individual)} individual Markdown files.")
    
    # Generate README.md
    readme_lines = [
        "# EC499: SDN Traffic Engineering with Reinforcement Learning — Codebase Documentation",
        "",
        "> **Project:** Reinforcement Learning for Adaptive Traffic Engineering in an SDN Network  ",
        "> **Student:** Maher Alqadhi (ID: 2210249576)  ",
        "> **Institution:** University of Tripoli — Faculty of Engineering — Department of Electrical & Electronic Engineering  ",
        f"> **Total Source Files:** {len(all_files)} files  ",
        f"> **Total Lines of Code:** {total_loc:,} lines  ",
        f"> **Total Codebase Size:** {total_size / 1024:.2f} KB ({total_size / (1024 * 1024):.2f} MB)  ",
        "",
        "---",
        "",
        "## Master Documents",
        "",
        "- [📖 **ALL_PROJECT_CODES.md**](./ALL_PROJECT_CODES.md) — Single consolidated Markdown document containing the entire codebase with Table of Contents and complete source codes.",
        "",
        "---",
        "",
        "## Subsystems & Architecture Modules",
        ""
    ]
    
    for cat in CATEGORIES:
        cat_files = [f for f in all_files if f["category"]["id"] == cat["id"]]
        if not cat_files:
            continue
        cat_loc = sum(f["line_count"] for f in cat_files)
        cat_kb = sum(f["size"] for f in cat_files) / 1024
        
        readme_lines.append(f"### {cat['name']}")
        readme_lines.append(f"*{cat['desc']}*  ")
        readme_lines.append(f"**Metrics:** {len(cat_files)} files | {cat_loc:,} lines | {cat_kb:.1f} KB")
        readme_lines.append("")
        readme_lines.append("| File | Language | Lines | Size | Description | Links |")
        readme_lines.append("| :--- | :---: | :---: | :---: | :--- | :---: |")
        for cf in cat_files:
            summary = cf["docstring"].replace("\n", " ").strip()
            if len(summary) > 95:
                summary = summary[:92] + "..."
            readme_lines.append(
                f"| [`{cf['rel_path']}`]({cf['out_md_rel']}) | `{cf['lang']}` | {cf['line_count']:,} | {cf['size']/1024:.1f} KB | {summary} | [View .md]({cf['out_md_rel']}) |"
            )
        readme_lines.append("")

    with open(os.path.join(OUTPUT_DIR, "README.md"), "w", encoding="utf-8") as fp:
        fp.write("\n".join(readme_lines) + "\n")
    print("Generated project_code_md/README.md")

    # Generate Consolidated ALL_PROJECT_CODES.md
    master_lines = [
        "# EC499: Reinforcement Learning for Adaptive Traffic Engineering in an SDN Network",
        "## Complete Project Source Code Repository (Unified Markdown Document)",
        "",
        "> **Project Title:** Reinforcement Learning for Adaptive Traffic Engineering in an SDN Network  ",
        "> **Author / Candidate:** Maher Alqadhi (Student ID: 2210249576)  ",
        "> **Academic Institution:** University of Tripoli — Faculty of Engineering  ",
        "> **Department:** Electrical & Electronic Engineering Department (Computer Engineering Branch)  ",
        "> **Course:** EC499 Graduation Project (Senior Design Thesis)  ",
        f"> **Total Source Files:** {len(all_files)} files  ",
        f"> **Total Codebase Lines:** {total_loc:,} lines of code  ",
        f"> **Total Source Volume:** {total_size / 1024:.2f} KB (~{total_size / (1024*1024):.2f} MB)  ",
        "",
        "---",
        "",
        "## Table of Contents",
        ""
    ]
    
    for cat in CATEGORIES:
        cat_files = [f for f in all_files if f["category"]["id"] == cat["id"]]
        if not cat_files:
            continue
        cat_anchor = re.sub(r"[^a-zA-Z0-9_-]", "", cat["name"].lower().replace(" ", "-"))
        master_lines.append(f"- **[{cat['name']}](#{cat_anchor})** ({len(cat_files)} files)")
        for cf in cat_files:
            gh_anchor = "file-" + re.sub(r"[^a-z0-9_-]", "", cf["rel_path"].lower().replace("/", "").replace(".", ""))
            master_lines.append(f"  - [{cf['rel_path']}](#{gh_anchor}) — *{cf['line_count']:,} lines, {cf['lang']}*")
    
    master_lines.append("")
    master_lines.append("---")
    master_lines.append("")
    master_lines.append("## Complete Codebase Inventory")
    master_lines.append("")
    master_lines.append("| # | Relative Path | Category | Language | Lines | Size (KB) | Key Symbols / Purpose |")
    master_lines.append("| :-: | :--- | :--- | :---: | :---: | :---: | :--- |")
    
    idx = 1
    for f in all_files:
        symbols = ""
        if f["classes"]:
            symbols = "Classes: " + ", ".join(f["classes"][:3])
        elif f["functions"]:
            symbols = "Funcs: " + ", ".join(f["functions"][:3])
        else:
            symbols = f["docstring"][:40] + "..." if len(f["docstring"]) > 40 else f["docstring"]
        symbols = symbols.replace("\n", " ").replace("|", "/")
        gh_anchor = "file-" + re.sub(r"[^a-z0-9_-]", "", f["rel_path"].lower().replace("/", "").replace(".", ""))
        master_lines.append(
            f"| {idx} | [{f['rel_path']}](#{gh_anchor}) | {f['category']['name'].split('.')[1].strip()} | `{f['lang']}` | {f['line_count']:,} | {f['size']/1024:.1f} | {symbols} |"
        )
        idx += 1
        
    master_lines.append("")
    master_lines.append("---")
    master_lines.append("")

    for cat in CATEGORIES:
        cat_files = [f for f in all_files if f["category"]["id"] == cat["id"]]
        if not cat_files:
            continue
        
        master_lines.append(f"# {cat['name']}")
        master_lines.append(f"> *{cat['desc']}*")
        master_lines.append("")
        
        for cf in cat_files:
            gh_anchor = "file-" + re.sub(r"[^a-z0-9_-]", "", cf["rel_path"].lower().replace("/", "").replace(".", ""))
            master_lines.append(f"<a id=\"{gh_anchor}\"></a>")
            master_lines.append(f"## File: `{cf['rel_path']}`")
            master_lines.append("")
            master_lines.append(f"- **Subsystem:** {cat['name']}")
            master_lines.append(f"- **Language:** `{cf['lang']}` | **Lines:** {cf['line_count']:,} | **Size:** {cf['size']/1024:.2f} KB")
            if cf["classes"]:
                master_lines.append(f"- **Classes:** " + ", ".join(f"`{c}`" for c in cf["classes"]))
            if cf["functions"]:
                fn_list = ", ".join(f"`{fn}`" for fn in cf["functions"][:10])
                if len(cf["functions"]) > 10:
                    fn_list += f" *(and {len(cf['functions']) - 10} more)*"
                master_lines.append(f"- **Functions:** {fn_list}")
            master_lines.append(f"- **Description:** {cf['docstring']}")
            master_lines.append(f"- [↑ Back to Table of Contents](#table-of-contents)")
            master_lines.append("")
            master_lines.append(f"{cf['fence']}{cf['lang']}")
            master_lines.append(cf["content"].rstrip())
            master_lines.append(f"{cf['fence']}")
            master_lines.append("")
            master_lines.append("---")
            master_lines.append("")

    master_content = "\n".join(master_lines) + "\n"
    
    p1 = os.path.join(OUTPUT_DIR, "ALL_PROJECT_CODES.md")
    p2 = os.path.join(PROJECT_ROOT, "ALL_PROJECT_CODES.md")
    p3 = os.path.join(WORKSPACE_ROOT, "ALL_PROJECT_CODES.md")
    
    with open(p1, "w", encoding="utf-8") as fp:
        fp.write(master_content)
    with open(p2, "w", encoding="utf-8") as fp:
        fp.write(master_content)
    with open(p3, "w", encoding="utf-8") as fp:
        fp.write(master_content)
        
    print(f"Generated master file at:")
    print(f"  - {p1} ({os.path.getsize(p1):,} bytes)")
    print(f"  - {p2} ({os.path.getsize(p2):,} bytes)")
    print(f"  - {p3} ({os.path.getsize(p3):,} bytes)")

if __name__ == "__main__":
    main()
