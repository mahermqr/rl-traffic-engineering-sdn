# `generate_docx_report.py`

> **File:** `generate_docx_report.py`  
> **Subsystem / Category:** 9. Publications, Documentation & Slide Generation  
> **Language:** `python`  
> **Lines of Code:** 436  
> **File Size:** 28.58 KB  

---

## Overview

Microsoft Word (.docx) comprehensive project report compiler with formatted tables, headings, and embedded figures.

### Architecture & Symbols
- **Classes:** None (Procedural / Script)
- **Key Functions:** `set_cell_background`, `set_cell_margins`, `add_styled_heading`, `add_body_p`, `add_figure_if_exists`, `style_table`, `build_dissertation_docx`

---

## Source Code

```python
#!/usr/bin/env python3
"""
Generates the authoritative Microsoft Word (.docx) dissertation report for:
Maher Abdulnasir Alqadhi (Student ID: 2210249576)
Reinforcement Learning for Adaptive Traffic Engineering in an SDN Network
University of Tripoli, Faculty of Engineering, Department of Computer Engineering
Supervisor: Dr. Suad El-Geder
"""

import os
import sys
from pathlib import Path
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

BASE_DIR = Path(__file__).resolve().parent
DOCS_DIR = BASE_DIR / "docs"
FIG_DIR = BASE_DIR / "report_artifacts" / "figures"
OUTPUT_DOCX_DOCS = DOCS_DIR / "Project_Report_EC499_Final.docx"
OUTPUT_DOCX_ARTIFACTS = BASE_DIR / "report_artifacts" / "Project_Report_EC499_Final.docx"

# Color constants
C_NAVY = RGBColor(30, 58, 138)      # #1E3A8A
C_EMERALD = RGBColor(16, 185, 129)  # #10B981
C_SLATE = RGBColor(71, 85, 105)     # #475569
C_CHARCOAL = RGBColor(30, 41, 59)   # #1E293B

HEX_NAVY = "1E3A8A"
HEX_LIGHT_BG = "F1F5F9"
HEX_BORDER = "CBD5E1"

def set_cell_background(cell, hex_color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
    tcPr.append(tcMar)

def add_styled_heading(doc, text, level):
    p = doc.add_heading(text, level=level)
    run = p.runs[0]
    if level == 1:
        run.font.color.rgb = C_NAVY
        run.font.size = Pt(18)
        run.font.bold = True
        p.paragraph_format.space_before = Pt(16)
        p.paragraph_format.space_after = Pt(6)
    elif level == 2:
        run.font.color.rgb = C_NAVY
        run.font.size = Pt(14)
        run.font.bold = True
        p.paragraph_format.space_before = Pt(12)
        p.paragraph_format.space_after = Pt(4)
    elif level == 3:
        run.font.color.rgb = C_SLATE
        run.font.size = Pt(12)
        run.font.bold = True
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(2)
    return p

def add_body_p(doc, text, bold_prefix=None, space_after=6):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.15
    if bold_prefix:
        r_pre = p.add_run(bold_prefix)
        r_pre.bold = True
        r_pre.font.color.rgb = C_CHARCOAL
        r_pre.font.size = Pt(10.5)
    r_body = p.add_run(text)
    r_body.font.color.rgb = C_CHARCOAL
    r_body.font.size = Pt(10.5)
    return p

def add_figure_if_exists(doc, filename, caption, width=Inches(6.2)):
    path = FIG_DIR / filename
    if path.exists():
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.paragraph_format.space_before = Pt(8)
        p_img.paragraph_format.space_after = Pt(2)
        run_img = p_img.add_run()
        run_img.add_picture(str(path), width=width)

        p_cap = doc.add_paragraph()
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap.paragraph_format.space_before = Pt(2)
        p_cap.paragraph_format.space_after = Pt(12)
        r_cap = p_cap.add_run(caption)
        r_cap.font.size = Pt(9.5)
        r_cap.font.italic = True
        r_cap.font.color.rgb = C_SLATE
    else:
        print(f"[Warning] Figure not found: {filename}")

def style_table(table, col_widths, headers, data_rows):
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    # Header row
    hdr_cells = table.rows[0].cells
    for i, h in enumerate(headers):
        hdr_cells[i].text = h
        set_cell_background(hdr_cells[i], HEX_NAVY)
        set_cell_margins(hdr_cells[i], top=120, bottom=120, left=120, right=120)
        p = hdr_cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for r in p.runs:
            r.font.bold = True
            r.font.color.rgb = RGBColor(255, 255, 255)
            r.font.size = Pt(9)
    # Data rows
    for r_idx, row in enumerate(data_rows):
        row_cells = table.add_row().cells
        bg_col = HEX_LIGHT_BG if r_idx % 2 == 1 else "FFFFFF"
        for c_idx, val in enumerate(row):
            row_cells[c_idx].text = str(val)
            set_cell_background(row_cells[c_idx], bg_col)
            set_cell_margins(row_cells[c_idx], top=80, bottom=80, left=100, right=100)
            p = row_cells[c_idx].paragraphs[0]
            if c_idx == 0:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            for r in p.runs:
                r.font.size = Pt(8.5)
                r.font.color.rgb = C_CHARCOAL
    # Set widths
    for row in table.rows:
        for idx, width in enumerate(col_widths):
            row.cells[idx].width = width

def build_dissertation_docx():
    print("[*] Generating Comprehensive Master Thesis Document (.docx)...")
    doc = Document()

    # Set page margins to 1 inch
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

    # =========================================================================
    # COVER / TITLE PAGE
    # =========================================================================
    p_inst = doc.add_paragraph()
    p_inst.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_inst.paragraph_format.space_before = Pt(24)
    p_inst.paragraph_format.space_after = Pt(4)
    r1 = p_inst.add_run("UNIVERSITY OF TRIPOLI\n")
    r1.font.bold = True
    r1.font.size = Pt(14)
    r1.font.color.rgb = C_NAVY
    r2 = p_inst.add_run("FACULTY OF ENGINEERING • DEPARTMENT OF COMPUTER ENGINEERING\n")
    r2.font.bold = True
    r2.font.size = Pt(11)
    r2.font.color.rgb = C_SLATE

    p_proj = doc.add_paragraph()
    p_proj.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_proj.paragraph_format.space_before = Pt(8)
    p_proj.paragraph_format.space_after = Pt(36)
    r_sub = p_proj.add_run("FINAL GRADUATION ENGINEERING DISSERTATION (EC499)")
    r_sub.font.bold = True
    r_sub.font.size = Pt(10.5)
    r_sub.font.color.rgb = C_EMERALD

    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(36)
    p_title.paragraph_format.space_after = Pt(24)
    r_t = p_title.add_run("Reinforcement Learning for Adaptive Traffic Engineering in an SDN Network")
    r_t.font.bold = True
    r_t.font.size = Pt(22)
    r_t.font.color.rgb = C_NAVY

    p_meta = doc.add_paragraph()
    p_meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_meta.paragraph_format.space_before = Pt(48)
    p_meta.paragraph_format.space_after = Pt(6)
    r_m1 = p_meta.add_run("Author:\n")
    r_m1.font.bold = True
    r_m1.font.size = Pt(11)
    r_m2 = p_meta.add_run("Maher Abdulnasir Alqadhi\n")
    r_m2.font.bold = True
    r_m2.font.size = Pt(14)
    r_m2.font.color.rgb = C_NAVY
    r_m3 = p_meta.add_run("Student Registration Number: 2210249576\n\n")
    r_m3.font.size = Pt(11)
    r_m3.font.color.rgb = C_SLATE

    r_s1 = p_meta.add_run("Project Supervisor:\n")
    r_s1.font.bold = True
    r_s1.font.size = Pt(11)
    r_s2 = p_meta.add_run("Dr. Suad El-Geder\n")
    r_s2.font.bold = True
    r_s2.font.size = Pt(13)
    r_s2.font.color.rgb = C_NAVY
    r_s3 = p_meta.add_run("Associate Professor of Computer Engineering\n\n")
    r_s3.font.size = Pt(11)
    r_s3.font.color.rgb = C_SLATE

    r_date = p_meta.add_run("October 2026")
    r_date.font.bold = True
    r_date.font.size = Pt(12)
    r_date.font.color.rgb = C_CHARCOAL

    doc.add_page_break()

    # =========================================================================
    # EXECUTIVE SUMMARY & ABSTRACT
    # =========================================================================
    add_styled_heading(doc, "Executive Summary & Abstract", level=1)

    add_body_p(doc,
        "Software-Defined Networking (SDN) centralizes control-plane intelligence, yet deployed routing systems frequently rely on static shortest-path algorithms such as Open Shortest Path First (OSPF) or equal-cost multi-path (ECMP). Under asymmetric multi-commodity traffic demands, static shortest-path forwarding persistently saturates primary core links while adjacent lateral paths remain severely underutilized, introducing localized buffer bloat, packet loss, and tail latency inflation.",
        bold_prefix="Problem Context: "
    )

    add_body_p(doc,
        "This dissertation presents the design, mathematical modeling, discrete-event validation, and carrier-grade implementation of an autonomous Traffic Engineering (TE) framework driven by Deep Reinforcement Learning (DRL). The control plane integrates a Ryu OpenFlow 1.3 controller, a NetworkX global topology representation, and a PyTorch Dueling Double Deep Q-Network (D3QN) augmented with Binary SumTree Prioritized Experience Replay (PER). Candidate loop-free paths are synthesized via Yen's k-shortest paths, evaluated via a continuous ten-dimensional state representation capturing hop count, bottleneck utilization, propagation latency, and network-wide load.",
        bold_prefix="Methodology & Architecture: "
    )

    add_body_p(doc,
        "Across standard benchmark fixtures (Hierarchical Tree, Fat-Tree Clos, Abilene US WAN, NSFNet, and Spine-Leaf) and two-way cluster bootstrap analyses with 95% confidence intervals, the reference learned policy achieves up to 51.7% bottleneck relief when compared against Dijkstra SPF. In multi-objective balance, the learned policy is competitive with rather than strictly superior to specialized heuristics (pure D3QN mean bottleneck of 30.9% vs. 29.3% for WSP and 29.5% for LLR), while maintaining balanced delay (13.7 ms) and high Jain's fairness (0.835).",
        bold_prefix="Empirical Findings: "
    )

    add_body_p(doc,
        "Architectural ablation across 20 retrained models confirms that dueling state-value/advantage streams drive the primary latency reduction (-512.8 ms), while target decoupling mitigates Q-value maximization bias. A three-factor hierarchical variance decomposition across 5 independent training seeds, 5 workload seeds, and 5 topologies indicates that topology graph structure mechanically accounts for 93.51% of total variance, while model weight initialization accounts for 0.73%. Furthermore, an agent trained strictly on synthetic random graphs transferred zero-shot to the five held-out benchmarks with an aggregate generalization degradation of only 6.9 pp. High availability testing validates sub-millisecond leader promotion and transparent 38 ms client failover with zero packet loss.",
        bold_prefix="Ablation, Robustness & High Availability: "
    )

    # Research Questions Box
    add_styled_heading(doc, "Formal Research Questions (RQ1 – RQ5)", level=2)
    add_body_p(doc, "Do architectural extensions (Double Q-learning, Dueling networks, and Prioritized Experience Replay) provide measurable, statistically significant advantages over plain DQN in multi-objective routing?", bold_prefix="RQ1 (Architectural Ablation): ")
    add_body_p(doc, "How stable is D3QN routing policy performance across different training seeds and workload seeds?", bold_prefix="RQ2 (Seed Stability & Variance): ")
    add_body_p(doc, "Can a D3QN policy trained exclusively on randomized synthetic graphs generalize zero-shot to unseen real-world benchmark topologies without retraining?", bold_prefix="RQ3 (Held-Out Zero-Shot Generalization): ")
    add_body_p(doc, "What is the optimality gap between D3QN routing decisions and the theoretical global optimum computed via exact Mixed-Integer Linear Programming (MILP)?", bold_prefix="RQ4 (Optimization Oracle Gap): ")
    add_body_p(doc, "Under what packet arrival dynamics (e.g., heavy-tailed Pareto bursts) does the analytical M/M/1/K queuing model break down, and how quickly does the SDN fast-failover mechanism recover?", bold_prefix="RQ5 (Packet Dynamics & Model Breakdown): ")

    doc.add_page_break()

    # =========================================================================
    # CHAPTER 3: SYSTEM MODELING & ANALYTICAL QUEUING
    # =========================================================================
    add_styled_heading(doc, "Chapter 3: System Modeling & Analytical Queuing Foundations", level=1)
    add_body_p(doc, "The network is modeled as a directed graph G = (V, E) where OpenFlow switches represent vertices |V| = N and directed transmission links represent edges |E| = M. Candidate path selection operates under the Unsplittable Multi-Commodity Flow (UMCF) integer model:")
    add_body_p(doc, "min sum(Phi(u_e)) + alpha * sum(Delay) + beta * sum(Jitter), subject to single-path binary allocation per commodity.")
    add_body_p(doc, "Queuing delay is initially derived using Kleinrock's independence approximation for an M/M/1/K finite buffer queue, where packet service rate mu_e = C_e / L_avg and packet loss probability follows the finite-capacity formula.")

    add_figure_if_exists(doc, "traffic_load_scaling_curves.png",
        "Figure 3.1: Analytical M/M/1/K load scaling curves showing non-linear queuing delay and packet loss cliff as load factor rho exceeds 0.85.")

    # =========================================================================
    # CHAPTER 4 & 5: D3QN ARCHITECTURE & CARRIER-GRADE CONTROL PLANE
    # =========================================================================
    add_styled_heading(doc, "Chapter 4 & 5: D3QN Architecture & Carrier-Grade SDN Control Plane", level=1)
    add_body_p(doc, "The intelligent routing engine employs a Dueling Double Deep Q-Network (D3QN) with a continuous 10-dimensional state vector capturing:")
    add_body_p(doc, "1. Normalized Hop Count; 2. Max Bottleneck Utilization; 3. Mean Link Utilization; 4. Total Propagation Delay; 5. Path Queuing Delay; 6. Estimated Jitter; 7. Residual Bandwidth Ratio; 8. Historical Flow Churn; 9. Link Failure Indicator; 10. Network-Wide Congestion Gradient.", bold_prefix="State Vector: ")
    add_body_p(doc, "State value V(s) and advantage stream A(s, a) are decoupled: Q(s, a) = V(s) + (A(s, a) - mean_a'(A(s, a'))). Double DQN target separation decouples action selection from action evaluation to eliminate positive maximization bias. Prioritized Experience Replay (PER) samples critical transitions using a Binary SumTree data structure with priority p_i = (|delta_i| + eps)^alpha.")

    add_body_p(doc, "To provide five-nines carrier-grade availability, an N+2 High Availability Multi-Controller Pool is implemented with one Active Master and two Hot-Standby controllers. Switches maintain persistent OpenFlow auxiliary channels. Under physical crash injection (SIGKILL), heartbeat timeouts trigger Raft-style leader election within 0.001 ms, and the standby assumes the master role within 37.96 ms with zero lost flow entries.", bold_prefix="High Availability Architecture: ")

    add_figure_if_exists(doc, "dashboard_upper_panoramic.png",
        "Figure 5.1: Panoramic telemetry console showing real-time topology layout, link saturation heatmaps, and routing decision streams.")

    add_figure_if_exists(doc, "ha_cluster_3node_modal.png",
        "Figure 5.2: Three-node High Availability cluster consensus modal illustrating leader promotion and synchronized state transfer.")

    # =========================================================================
    # CHAPTER 7: TRAINING DYNAMICS
    # =========================================================================
    add_styled_heading(doc, "Chapter 7: Training Dynamics & Policy Convergence", level=1)
    add_body_p(doc, "The D3QN routing policy was trained over 1,000 continuous episodes under non-stationary traffic churn. As exploration epsilon decays from 1.0 to 0.05, the Bellman loss stabilizes, and the episodic reward climbs from negative penalties to positive multi-objective rewards.")

    add_figure_if_exists(doc, "dqn_te_training_convergence.png",
        "Figure 7.1: D3QN training convergence progression over 1,000 episodes: (a) TD Loss; (b) Mean Reward; (c) Epsilon Decay; (d) Bottleneck Reduction.")

    doc.add_page_break()

    # =========================================================================
    # CHAPTER 8: EXPERIMENTAL EVALUATION & BENCHMARK TOURNAMENT
    # =========================================================================
    add_styled_heading(doc, "Chapter 8: Comprehensive Experimental Evaluation & Benchmark Tournament", level=1)
    add_body_p(doc, "The empirical evaluation subjected the reference D3QN agent and five baseline algorithms (Dijkstra SPF, OSPF RFC 2328, ECMP, WSP Widest-Path, and LLR Least-Loaded) to closed-loop dynamic traffic across five topologies:")

    # Table 8.1
    table_8_1_headers = ["Topology / Metric", "D3QN (Ours)", "WSP", "LLR", "ECMP", "Dijkstra SPF"]
    table_8_1_data = [
        ["Hierarchical Tree (7 Switches)", "", "", "", "", ""],
        ["  Bottleneck Util (%)", "43.9%", "44.1%", "44.9%", "41.3%", "42.1%"],
        ["  Mean Latency (ms)", "167.8 ms", "188.4 ms", "244.0 ms", "160.8 ms", "142.4 ms"],
        ["  Jain's Fairness", "0.58", "0.60", "0.60", "0.56", "0.55"],
        ["Fat-Tree Clos (20 Switches)", "", "", "", "", ""],
        ["  Bottleneck Util (%)", "28.9%", "23.3%", "23.3%", "52.7%", "94.7%"],
        ["  Mean Latency (ms)", "6.6 ms", "6.0 ms", "6.1 ms", "51.5 ms", "190.1 ms"],
        ["  Jain's Fairness", "0.70", "0.82", "0.82", "0.66", "0.87"],
        ["Abilene US WAN (12 Switches)", "", "", "", "", ""],
        ["  Bottleneck Util (%)", "32.0%", "31.5%", "31.6%", "32.7%", "33.1%"],
        ["  Mean Latency (ms)", "26.2 ms", "22.0 ms", "22.4 ms", "31.5 ms", "43.6 ms"],
        ["  Jain's Fairness", "0.68", "0.68", "0.68", "0.67", "0.66"],
        ["NSFNet Backbone (14 Switches)", "", "", "", "", ""],
        ["  Bottleneck Util (%)", "28.6%", "28.3%", "28.7%", "44.4%", "49.6%"],
        ["  Mean Latency (ms)", "19.7 ms", "17.6 ms", "19.4 ms", "191.7 ms", "224.6 ms"],
        ["  Jain's Fairness", "0.66", "0.65", "0.66", "0.61", "0.63"],
        ["Spine-Leaf Fabric (16 Switches)", "", "", "", "", ""],
        ["  Bottleneck Util (%)", "20.9%", "19.2%", "19.2%", "55.6%", "99.9%"],
        ["  Mean Latency (ms)", "2.5 ms", "2.5 ms", "2.5 ms", "23.6 ms", "145.5 ms"],
        ["  Jain's Fairness", "0.88", "0.91", "0.91", "0.68", "0.98"],
        ["Overall Grand Mean", "", "", "", "", ""],
        ["  Bottleneck Util (%)", "30.9%", "29.3%", "29.5%", "45.3%", "63.9%"],
        ["  Mean Latency (ms)", "44.5 ms", "47.3 ms", "58.9 ms", "91.8 ms", "149.2 ms"],
        ["  Jain's Fairness Index", "0.70", "0.73", "0.73", "0.64", "0.74"]
    ]
    t1 = doc.add_table(rows=1, cols=6)
    style_table(t1, [Inches(1.8), Inches(0.9), Inches(0.9), Inches(0.9), Inches(0.9), Inches(1.0)], table_8_1_headers, table_8_1_data)

    add_body_p(doc, "Table 8.1: Proposal benchmark tournament across 5 topologies and 6 routing algorithms (closed-loop dynamic traffic).")

    add_figure_if_exists(doc, "proposal_benchmarks_all_metrics.png",
        "Figure 8.1: Six-panel benchmark tournament comparison across all 5 topologies with star badges highlighting the winning policy per metric.")

    add_figure_if_exists(doc, "proposal_tournament_radar.png",
        "Figure 8.2: Multi-objective radar polygon summarizing normalized performance across bottleneck relief, delay, jitter, loss, and fairness.")

    add_figure_if_exists(doc, "routing_cdfs_latency_jitter.png",
        "Figure 8.3: Empirical cumulative distribution functions (CDFs) of end-to-end latency and jitter across 4,500 decisions, showing the 1,008 ms queue ceiling under stress.")

    add_figure_if_exists(doc, "multiseed_paired_effects.png",
        "Figure 8.4: Multi-seed paired difference distributions vs. baselines (95% CI). Note that pure D3QN is competitive with rather than superior to WSP on bottleneck (-1.891 pp).")

    add_figure_if_exists(doc, "policy_mode_ablation.png",
        "Figure 8.5: Comparative policy mode ablation across topologies: Pure D3QN vs. Safety-Enforced fallbacks.")

    add_figure_if_exists(doc, "stress_test_load_balancing.png",
        "Figure 8.6: Four-scenario stress testing: Normal traffic, Core Jamming, Bursty Avalanche, and Sudden Link Failure.")

    add_figure_if_exists(doc, "blind_topologies_stress_benchmark.png",
        "Figure 8.7: Blind transfer stress benchmark on unseen network topologies.")

    add_figure_if_exists(doc, "blind_topologies_radar.png",
        "Figure 8.8: Multi-objective radar polygon for blind topology transfer.")

    # Random Blind Topologies Table 8.8
    add_styled_heading(doc, "Zero-Shot Transfer on Random Graphs (Table 8.8)", level=2)
    t_rand_headers = ["Nodes (N)", "Edges", "SPF Util (%)", "D3QN Util (%)", "Relief (%)", "Delay Imprv (ms)", "Decisions/sec"]
    t_rand_data = [
        ["15", "60", "28.25%", "25.31%", "+2.93 pp", "4.25 ms", "1,109.1"],
        ["25", "100", "54.96%", "34.06%", "+20.90 pp", "13.41 ms", "645.4"],
        ["35", "140", "32.23%", "25.41%", "+6.82 pp", "7.61 ms", "529.5"]
    ]
    t2 = doc.add_table(rows=1, cols=7)
    style_table(t2, [Inches(0.9), Inches(0.8), Inches(1.0), Inches(1.0), Inches(1.0), Inches(1.1), Inches(1.0)], t_rand_headers, t_rand_data)

    add_figure_if_exists(doc, "random_blind_topologies_evaluation.png",
        "Figure 8.9: Recorded zero-shot transfer checks on dynamically generated random topologies at N = 15, 25, and 35 nodes.")

    doc.add_page_break()

    # =========================================================================
    # ABLATION & ROBUSTNESS STUDIES (RQ1 - RQ4)
    # =========================================================================
    add_styled_heading(doc, "Rigorous Ablation, Stability & Generalization Suites", level=1)

    # Architectural Ablation
    add_styled_heading(doc, "Architectural Ablation (RQ1)", level=2)
    add_body_p(doc, "To verify the individual contribution of Dueling networks, Double DQN targets, and Prioritized Experience Replay (PER), a 4-stage ablation study was conducted across 20 retrained models (5 training seeds x 4 variants, 500 closed-loop evaluations):")

    add_figure_if_exists(doc, "ablation_study_bootstrap.png",
        "Figure 8.10: Architectural ablation paired bootstrap effects vs. Full D3QN (95% CI): (a) Bottleneck relief; (b) Latency profile; (c) Win rate across 25 workloads.")

    # Model Seed Stability
    add_styled_heading(doc, "Model Seed Stability & Hierarchical Variance Decomposition (RQ2)", level=2)
    add_body_p(doc, "Evaluating 5 independent training seeds (Seeds 42, 101, 102, 103, 104) across 5 workload seeds and 5 topologies revealed that topology graph structure mechanically accounts for 93.51% of total variance, residual interaction accounts for 5.74%, model seed accounts for 0.73%, and workload churn accounts for 0.02%.")

    add_figure_if_exists(doc, "multiple_model_seeds_hierarchical.png",
        "Figure 8.11: Multi-seed stability evaluation: (a) Peak bottleneck utilization across 5 seeds; (b) Hierarchical variance decomposition confirming topology structure dominates variance.")

    # Held-Out Topologies
    add_styled_heading(doc, "Zero-Shot Held-Out Generalization (RQ3)", level=2)
    add_body_p(doc, "An agent trained strictly on synthetic Watts-Strogatz and Erdős-Rényi random graphs (completely excluding the 5 benchmark fixtures from its curriculum) was deployed zero-shot onto the benchmark topologies. The overall generalization gap was restricted to +6.9 pp bottleneck degradation, proving that the D3QN agent learns transferable representations of graph congestion dynamics.")

    add_figure_if_exists(doc, "held_out_topologies_generalization.png",
        "Figure 8.12: Zero-shot generalization on held-out topologies: (a) In-curriculum vs. Held-out agent utilization; (b) Percentage generalization gap across topologies.")

    # Optimization Oracle
    add_styled_heading(doc, "Optimization Oracle Gap Analysis (RQ4)", level=2)
    add_body_p(doc, "To establish theoretical bounds on routing performance, an exact Unsplittable Multi-Commodity Flow integer linear program was formulated and solved to global optimality using the HiGHS branch-and-cut solver. On Hierarchical Tree, D3QN achieves a peak link utilization of 78.74% (66.15% gap over the theoretical optimum alpha* = 47.39%), substantially outperforming static Dijkstra SPF (98.46% peak, 107.76% gap) and closing the distance to the theoretical lower bound by 41.6 percentage points. On Spine-Leaf, where the theoretical lower bound is alpha* = 10.06%, specialized load-aware heuristics operate within 14.27% - 15.76% gap, while single-path baselines operate at 30.66% (204.92% gap). On NSFNet (alpha* = 14.28%), D3QN operates within 44.89% of the theoretical optimum.")

    add_figure_if_exists(doc, "optimisation_oracle_gap.png",
        "Figure 8.13: Exact MILP HiGHS optimization oracle comparison: (a) Peak utilization vs. theoretical lower bound alpha*; (b) Percentage optimality gap across topologies.")

    # Multi-Seed Retrained Sensitivity Surface
    add_styled_heading(doc, "Multi-Seed Reward Retraining Sensitivity Grid", level=2)
    add_body_p(doc, "To verify hyperparameter robustness, a 12-cell grid across congestion penalty theta in {0.6, 0.7, 0.8} and relief weight w_relief in {1.0, 2.0, 4.0, 8.0} was evaluated by retraining 3 independent model seeds per cell (36 independently retrained models). Under-penalizing congestion (w_relief = 1.0) destabilizes latency (921 - 1,147 ms), while the nominal setting (theta = 0.70, w_relief = 4.0) achieves minimum packet loss (17.60% +/- 2.48%) and stable delay (653 ms).")

    add_figure_if_exists(doc, "reward_sensitivity_multiseed_surface.png",
        "Figure 8.14: Multi-seed reward sensitivity analysis (36 independently retrained models): (a) Bottleneck utilization; (b) Mean latency; (c) Packet loss rate across parameter grid.")

    # Queue Model Validation (RQ5)
    add_styled_heading(doc, "Packet-Level Dynamics & Discrete-Event Queue Breakdown (RQ5)", level=1)
    add_body_p(doc, "Discrete-event packet queue simulations comparing Poisson memoryless arrivals against heavy-tailed Pareto arrivals (shape alpha = 1.35) demonstrate that under self-similar bursty traffic, analytical M/M/1/K models underestimate queue buffer overflow by 4.2x. Under link failure, the OpenFlow fast-failover group table recovers forwarding in 14.2 ms with exactly 18 transient dropped packets.")

    add_figure_if_exists(doc, "queue_model_mm1k_validation.png",
        "Figure 8.15: Packet dynamics validation: (a) M/M/1/K analytical curve vs. Poisson and Pareto discrete-event simulation; (b) Transient SDN fast-failover drop window (14.2 ms).")

    doc.add_page_break()

    # =========================================================================
    # CHAPTER 10: CONCLUSION & FUTURE WORK
    # =========================================================================
    add_styled_heading(doc, "Chapter 10: Conclusion & Future Engineering Directions", level=1)
    add_body_p(doc, "This graduation project demonstrated that combining Deep Reinforcement Learning with Software-Defined Networking enables autonomous, adaptive traffic engineering that significantly mitigates core trunk congestion without requiring manual metric manipulation. Key achievements include:")
    add_body_p(doc, "1. Formulating adaptive traffic engineering as a mathematically sound MDP and training a D3QN agent with Prioritized Experience Replay;\n2. Demonstrating statistically robust bottleneck relief (up to 51.7% vs. SPF) across five benchmark topologies;\n3. Establishing that Dueling streams provide the dominant latency reduction and that weight initialization contributes less than 1% to performance variance;\n4. Validating zero-shot out-of-distribution transfer to held-out real-world and random graphs;\n5. Bounding the policy against an exact HiGHS MILP global optimization oracle;\n6. Certifying an N+2 high availability multi-controller cluster capable of sub-millisecond promotion and transparent 38 ms recovery.")

    add_body_p(doc, "Future work will investigate Graph Neural Network (GNN) state encoders for permutation-invariant action spaces, Multi-Agent Reinforcement Learning (MARL) for partitioned multi-domain WANs, and P4 hardware data plane integration for sub-microsecond in-band network telemetry.", bold_prefix="Future Directions: ")

    # Save to both destinations
    doc.save(str(OUTPUT_DOCX_DOCS))
    doc.save(str(OUTPUT_DOCX_ARTIFACTS))
    print(f"[✓] Successfully generated and saved Master Thesis DOCX:")
    print(f"    -> {OUTPUT_DOCX_DOCS}")
    print(f"    -> {OUTPUT_DOCX_ARTIFACTS}")

if __name__ == '__main__':
    build_dissertation_docx()
```
