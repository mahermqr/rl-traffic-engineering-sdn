#!/usr/bin/env python3
"""
Generates docs/EC499_Graduation_Defense_Slides.html
A standalone, interactive, responsive HTML5 slide deck with keyboard navigation,
embedded base64 figures, speaker notes, overview mode, and fullscreen support.
"""

import os
import base64
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DOCS_DIR = BASE_DIR / "docs"
PLOTS_DIR = BASE_DIR / "logs" / "plots"
OUTPUT_HTML = DOCS_DIR / "EC499_Graduation_Defense_Slides.html"

def get_base64_image(filename):
    path = PLOTS_DIR / filename
    if path.exists():
        with open(path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
            return f"data:image/png;base64,{encoded}"
    return ""

def main():
    print("[*] Encoding plot assets to base64...")
    img_convergence = get_base64_image("dqn_te_training_convergence.png")
    img_benchmarks = get_base64_image("proposal_benchmarks_all_metrics.png")
    img_radar = get_base64_image("proposal_tournament_radar.png")
    img_cdfs = get_base64_image("routing_cdfs_latency_jitter.png")
    img_stress = get_base64_image("stress_test_load_balancing.png")
    img_blind_radar = get_base64_image("blind_topologies_radar.png")
    img_blind_stress = get_base64_image("blind_topologies_stress_benchmark.png")
    img_scaling = get_base64_image("traffic_load_scaling_curves.png")
    img_dash_topo = get_base64_image("dashboard_topology_telemetry.png")
    img_dash_versus = get_base64_image("dashboard_versus_tournament.png")
    img_dash_inspector = get_base64_image("dashboard_model_inspector.png")
    img_dash_settings = get_base64_image("dashboard_network_settings.png")
    img_pareto = get_base64_image("pareto_weight_sensitivity.png")
    img_vmware = get_base64_image("vmware_virtual_machine_specs.png")

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>EC499 Graduation Defense — Reinforcement Learning for Adaptive Traffic Engineering in SDN</title>
<style>
  :root {{
    --bg-dark: #0f172a;
    --card-dark: #1e293b;
    --bg-light: #f8fafc;
    --card-light: #ffffff;
    --border-light: #e2e8f0;
    --border-dark: #334155;
    --violet-primary: #6d28d9;
    --violet-light: #ede9fe;
    --cyan-accent: #0284c7;
    --cyan-light: #e0f2fe;
    --emerald-accent: #059669;
    --emerald-light: #d1fae5;
    --amber-accent: #d97706;
    --amber-light: #fef3c7;
    --rose-accent: #e11d48;
    --rose-light: #ffe4e6;
    --text-navy: #0f172a;
    --text-slate: #334155;
    --text-muted: #64748b;
    --text-white: #f8fafc;
  }}

  * {{
    box-sizing: border-box;
    margin: 0;
    padding: 0;
  }}

  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    background: #090d16;
    color: var(--text-slate);
    overflow: hidden;
    height: 100vh;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
  }}

  /* Main Slide Container: 16:9 aspect ratio */
  #presentation-container {{
    position: relative;
    width: 96vw;
    height: 54vw;
    max-width: 1440px;
    max-height: 810px;
    background: var(--bg-light);
    border-radius: 12px;
    box-shadow: 0 25px 60px -15px rgba(0,0,0,0.7), 0 0 0 1px rgba(255,255,255,0.08);
    overflow: hidden;
    display: flex;
    flex-direction: column;
  }}

  /* Slide Wrapper */
  .slide {{
    display: none;
    width: 100%;
    height: 100%;
    padding: 2.2rem 2.8rem;
    position: relative;
    flex-direction: column;
    animation: fadeIn 0.25s ease-in-out;
  }}

  .slide.active {{
    display: flex;
  }}

  @keyframes fadeIn {{
    from {{ opacity: 0; transform: scale(0.995); }}
    to {{ opacity: 1; transform: scale(1); }}
  }}

  /* Slide Themes */
  .slide.theme-dark {{
    background: var(--bg-dark);
    color: var(--text-white);
  }}

  .slide.theme-light {{
    background: var(--bg-light);
    color: var(--text-slate);
  }}

  /* Headers */
  .header-pill {{
    display: inline-block;
    padding: 4px 14px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    background: var(--violet-light);
    color: var(--violet-primary);
    border: 1px solid rgba(109, 40, 217, 0.2);
    margin-bottom: 0.5rem;
    align-self: flex-start;
  }}

  .header-pill.cyan {{
    background: var(--cyan-light);
    color: var(--cyan-accent);
    border-color: rgba(2, 132, 199, 0.2);
  }}

  .header-pill.emerald {{
    background: var(--emerald-light);
    color: var(--emerald-accent);
    border-color: rgba(5, 150, 105, 0.2);
  }}

  .slide-title {{
    font-size: 1.65rem;
    font-weight: 800;
    color: var(--text-navy);
    line-height: 1.25;
    margin-bottom: 0.4rem;
  }}

  .theme-dark .slide-title {{
    color: #ffffff;
  }}

  .title-divider {{
    width: 100%;
    height: 2px;
    background: var(--border-light);
    margin-bottom: 1.2rem;
  }}

  .theme-dark .title-divider {{
    background: var(--border-dark);
  }}

  /* Content Layouts */
  .slide-body {{
    flex: 1;
    display: flex;
    gap: 1.5rem;
    min-height: 0;
  }}

  .col-2 {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1.5rem;
    width: 100%;
    height: 100%;
  }}

  .col-3 {{
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 1.2rem;
    width: 100%;
    height: 100%;
  }}

  .col-side-by-side {{
    display: grid;
    grid-template-columns: 65% 35%;
    gap: 1.5rem;
    width: 100%;
    height: 100%;
  }}

  /* Cards */
  .card {{
    background: var(--card-light);
    border: 1px solid var(--border-light);
    border-radius: 8px;
    padding: 1.1rem 1.3rem;
    box-shadow: 0 2px 6px rgba(0,0,0,0.03);
    display: flex;
    flex-direction: column;
    overflow-y: auto;
  }}

  .theme-dark .card {{
    background: var(--card-dark);
    border-color: var(--border-dark);
    color: #cbd5e1;
  }}

  .card-title {{
    font-size: 1.05rem;
    font-weight: 700;
    color: var(--violet-primary);
    margin-bottom: 0.6rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }}

  .theme-dark .card-title {{
    color: #a78bfa;
  }}

  .card-title.cyan {{ color: var(--cyan-accent); }}
  .card-title.emerald {{ color: var(--emerald-accent); }}
  .card-title.rose {{ color: var(--rose-accent); }}

  .card p, .card li {{
    font-size: 0.88rem;
    line-height: 1.48;
    color: var(--text-slate);
    margin-bottom: 0.5rem;
  }}

  .theme-dark .card p, .theme-dark .card li {{
    color: #cbd5e1;
  }}

  .card strong {{
    color: var(--text-navy);
  }}

  .theme-dark .card strong {{
    color: #f1f5f9;
  }}

  .card ul {{
    list-style-type: none;
    padding-left: 0;
  }}

  .card li {{
    position: relative;
    padding-left: 1.2rem;
    margin-bottom: 0.45rem;
  }}

  .card li::before {{
    content: "•";
    position: absolute;
    left: 0.2rem;
    color: var(--violet-primary);
    font-weight: bold;
  }}

  /* Math Blocks */
  .math-card {{
    background: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 8px;
    padding: 1rem 1.4rem;
    color: #38bdf8;
    font-family: "Courier New", Courier, monospace;
    font-size: 1.02rem;
    font-weight: 700;
    text-align: center;
    margin-bottom: 1rem;
    box-shadow: inset 0 2px 4px rgba(0,0,0,0.4);
  }}

  .math-sub {{
    display: block;
    font-size: 0.85rem;
    font-weight: 400;
    color: #cbd5e1;
    margin-top: 0.35rem;
    font-family: -apple-system, sans-serif;
  }}

  /* Figure Images */
  .figure-box {{
    background: #ffffff;
    border: 1px solid var(--border-light);
    border-radius: 8px;
    padding: 0.4rem;
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100%;
    overflow: hidden;
  }}

  .figure-box img {{
    max-width: 100%;
    max-height: 100%;
    object-fit: contain;
    border-radius: 6px;
  }}

  /* Tables */
  .academic-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 0.84rem;
  }}

  .academic-table th {{
    background: #f1f5f9;
    color: var(--text-navy);
    font-weight: 700;
    padding: 8px 12px;
    text-align: left;
    border-bottom: 2px solid var(--border-light);
  }}

  .academic-table td {{
    padding: 8px 12px;
    border-bottom: 1px solid var(--border-light);
    color: var(--text-slate);
  }}

  .academic-table tr:hover {{
    background: #f8fafc;
  }}

  .badge {{
    display: inline-block;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
  }}

  .badge-emerald {{
    background: var(--emerald-light);
    color: var(--emerald-accent);
    border: 1px solid rgba(5, 150, 105, 0.3);
  }}

  .badge-rose {{
    background: var(--rose-light);
    color: var(--rose-accent);
    border: 1px solid rgba(225, 29, 72, 0.3);
  }}

  .badge-violet {{
    background: var(--violet-light);
    color: var(--violet-primary);
  }}

  /* Controls and Status Bar */
  #controls-bar {{
    position: absolute;
    bottom: 0;
    left: 0;
    width: 100%;
    height: 44px;
    background: rgba(15, 23, 42, 0.94);
    backdrop-filter: blur(8px);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 1.5rem;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    color: #94a3b8;
    font-size: 0.8rem;
    z-index: 100;
  }}

  .btn-nav {{
    background: #1e293b;
    border: 1px solid #334155;
    color: #f1f5f9;
    padding: 4px 12px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 0.8rem;
    font-weight: 600;
    transition: all 0.15s ease;
  }}

  .btn-nav:hover {{
    background: var(--violet-primary);
    border-color: var(--violet-primary);
    color: white;
  }}

  .progress-bar {{
    position: absolute;
    top: 0;
    left: 0;
    height: 3px;
    background: var(--violet-primary);
    transition: width 0.3s ease;
  }}

  /* Speaker Notes Overlay */
  #notes-drawer {{
    display: none;
    position: absolute;
    bottom: 44px;
    left: 0;
    width: 100%;
    max-height: 180px;
    background: #0f172a;
    border-top: 2px solid var(--violet-primary);
    color: #cbd5e1;
    padding: 1rem 1.8rem;
    font-size: 0.88rem;
    overflow-y: auto;
    z-index: 90;
    box-shadow: 0 -10px 25px rgba(0,0,0,0.5);
  }}

  #notes-drawer.open {{
    display: block;
  }}

  #notes-drawer h4 {{
    color: #38bdf8;
    margin-bottom: 0.4rem;
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }}

  /* Hotkey Hints Tooltip */
  .hint-keys {{
    display: flex;
    gap: 0.5rem;
    align-items: center;
  }}

  kbd {{
    background: #334155;
    color: #f8fafc;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 0.7rem;
    font-family: inherit;
    border-bottom: 2px solid #1e293b;
  }}
</style>
</head>
<body>

<div id="presentation-container">
  <div class="progress-bar" id="progressBar"></div>

  <!-- ============================================================== -->
  <!-- SLIDE 1: Title Slide (Dark Cover) -->
  <!-- ============================================================== -->
  <div class="slide theme-dark active" data-notes="Welcome Dr. Suad El-Geder, external examination committee members, faculty, and colleagues. I am Maher Abdulnasir Alqadhi. Today I am defending my graduation project: Reinforcement Learning for Adaptive Traffic Engineering in an SDN Network. This work tackles the fundamental bottleneck problem of modern cloud and datacenter networks.">
    <div style="text-align: center; margin-top: 1.5rem;">
      <div style="color: var(--cyan-accent); font-size: 0.9rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 0.8rem;">
        University of Tripoli &bull; Faculty of Engineering &bull; Department of Computer Engineering
      </div>
      <div class="header-pill" style="background: #1e293b; color: #a78bfa; border-color: var(--violet-primary);">
        EC499 Final Graduation Project Defense
      </div>
      <h1 style="font-size: 2.15rem; font-weight: 900; line-height: 1.25; margin: 0.8rem 0; color: #ffffff;">
        Reinforcement Learning for Adaptive Traffic Engineering in an SDN Network
      </h1>
      <p style="font-size: 1.05rem; color: #94a3b8; max-width: 900px; margin: 0 auto 2.2rem auto;">
        Autonomous Congestion Mitigation, Tail Latency Minimization, and Zero-Shot Transfer via Dueling Double DQN
      </p>

      <div style="display: flex; justify-content: center; gap: 2rem; max-width: 820px; margin: 0 auto;">
        <div class="card" style="flex: 1; text-align: left; border-color: var(--violet-primary); background: #1e293b;">
          <div class="card-title" style="color: #a78bfa;">Candidate Author</div>
          <div style="font-size: 1.15rem; font-weight: 800; color: #ffffff; margin-bottom: 0.3rem;">Maher Abdulnasir Alqadhi</div>
          <p style="font-size: 0.84rem; color: #94a3b8; line-height: 1.4;">
            Student ID: <strong>2210249576</strong><br>
            Email: ma.alqadhi@uot.edu.ly<br>
            B.Sc. in Computer Engineering Candidate
          </p>
        </div>

        <div class="card" style="flex: 1; text-align: left; border-color: var(--cyan-accent); background: #1e293b;">
          <div class="card-title" style="color: #38bdf8;">Project Supervisor</div>
          <div style="font-size: 1.15rem; font-weight: 800; color: #ffffff; margin-bottom: 0.3rem;">Dr. Suad El-Geder</div>
          <p style="font-size: 0.84rem; color: #94a3b8; line-height: 1.4;">
            Associate Professor<br>
            Department of Computer Engineering<br>
            Faculty of Engineering, University of Tripoli
          </p>
        </div>
      </div>
    </div>
  </div>

  <!-- ============================================================== -->
  <!-- SLIDE 2: Presentation Agenda -->
  <!-- ============================================================== -->
  <div class="slide theme-light" data-notes="Here is the roadmap for today's defense. We will cover the problem statement and routing pitfalls, our SDN-DRL closed-loop system, the mathematical MDP formulation, benchmark tournaments across 5 topologies, our official Mininet emulation results, a brief tour of the live web dashboard, and finally conclusions and anticipated Q&A.">
    <div class="header-pill">Defense Roadmap</div>
    <div class="slide-title">Presentation Agenda & Defense Roadmap</div>
    <div class="title-divider"></div>

    <div style="display: flex; flex-direction: column; gap: 0.55rem; height: 100%;">
      <div class="card" style="flex-direction: row; align-items: center; padding: 0.65rem 1.2rem; gap: 1rem;">
        <div style="background: var(--violet-primary); color: white; width: 34px; height: 34px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 0.85rem;">01</div>
        <div><strong>Problem Statement & Classical Routing Pitfalls</strong> — Why static OSPF, ECMP, and greedy heuristics collapse under bursty traffic.</div>
      </div>
      <div class="card" style="flex-direction: row; align-items: center; padding: 0.65rem 1.2rem; gap: 1rem;">
        <div style="background: var(--violet-primary); color: white; width: 34px; height: 34px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 0.85rem;">02</div>
        <div><strong>SDN & DRL System Architecture</strong> — Closed-loop Ryu OpenFlow 1.3 control plane with PyTorch D3QN policy engine.</div>
      </div>
      <div class="card" style="flex-direction: row; align-items: center; padding: 0.65rem 1.2rem; gap: 1rem;">
        <div style="background: var(--violet-primary); color: white; width: 34px; height: 34px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 0.85rem;">03</div>
        <div><strong>Mathematical Modeling & MDP Formulation</strong> — 10D normalized state space, candidate path synthesis, and Pareto reward.</div>
      </div>
      <div class="card" style="flex-direction: row; align-items: center; padding: 0.65rem 1.2rem; gap: 1rem;">
        <div style="background: var(--violet-primary); color: white; width: 34px; height: 34px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 0.85rem;">04</div>
        <div><strong>Empirical Tournament & Stress Benchmarks</strong> — Head-to-head evaluation across 5 topologies and zero-shot random graphs.</div>
      </div>
      <div class="card" style="flex-direction: row; align-items: center; padding: 0.65rem 1.2rem; gap: 1rem;">
        <div style="background: var(--violet-primary); color: white; width: 34px; height: 34px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 0.85rem;">05</div>
        <div><strong>Official Mininet Emulation Validation</strong> — Line-rate UDP delivery, 76.2% jitter suppression, and 450x loss eradication.</div>
      </div>
      <div class="card" style="flex-direction: row; align-items: center; padding: 0.65rem 1.2rem; gap: 1rem;">
        <div style="background: var(--violet-primary); color: white; width: 34px; height: 34px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 0.85rem;">06</div>
        <div><strong>Interactive Web Dashboard & Chaos Console</strong> — Real-time topology canvas, 6-protocol tournament arena, and model inspector.</div>
      </div>
      <div class="card" style="flex-direction: row; align-items: center; padding: 0.65rem 1.2rem; gap: 1rem;">
        <div style="background: var(--violet-primary); color: white; width: 34px; height: 34px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 0.85rem;">07</div>
        <div><strong>Critical Discussion & Defense Preparation</strong> — Herd behavior analysis, delay inflation trade-offs, and 10 examiner Q&As.</div>
      </div>
    </div>
  </div>

  <!-- ============================================================== -->
  <!-- SLIDE 3: The Routing Challenge in Modern Networks -->
  <!-- ============================================================== -->
  <div class="slide theme-light" data-notes="Modern networks suffer from an impedance match between static routing assumptions and real-world traffic dynamics. Traffic is heavily bursty; 20% of elephant flows carry 80% of bytes. Static shortest path algorithms like OSPF are completely blind to current link loads, repeatedly funneling traffic down the same congested spine or core trunks.">
    <div class="header-pill">Problem Context</div>
    <div class="slide-title">The Traffic Engineering Crisis in Modern Networks</div>
    <div class="title-divider"></div>

    <div class="col-3">
      <div class="card">
        <div class="card-title">1. Bursty & Asymmetric Demands</div>
        <ul>
          <li><strong>Exponential Cloud Traffic Growth:</strong> 4K video, cloud gaming, distributed AI clusters, and microservice RPC traffic generate severe, non-stationary traffic spikes.</li>
          <li><strong>The Elephant vs. Mice Dilemma:</strong> Over 80% of flows are short-lived mice, but 20% of elephant flows carry >80% of total bytes, triggering localized flash congestion.</li>
        </ul>
      </div>

      <div class="card">
        <div class="card-title">2. Static Metric Blindness</div>
        <ul>
          <li><strong>Static Hop Count & Link Weights:</strong> Classical protocols compute routes using administrative metrics fixed during initial deployment.</li>
          <li><strong>Zero Congestion Awareness:</strong> A 100 Mbps link carrying 99 Mbps has the identical OSPF metric as a link carrying 0 Mbps.</li>
          <li><strong>Core Trunk Saturation:</strong> Shortest paths funnel all flows onto the same central trunks, while redundant lateral links remain completely idle.</li>
        </ul>
      </div>

      <div class="card">
        <div class="card-title">3. Consequences for SLA & QoS</div>
        <ul>
          <li><strong>Severe Queuing Delay Spikes:</strong> Buffer occupancy escalates non-linearly under Kleinrock queueing models as utilization approaches 100%.</li>
          <li><strong>Packet Delay Variation (Jitter):</strong> Violates RFC 3393 bounds, destroying voice (VoIP) and real-time streaming sessions.</li>
          <li><strong>Buffer Overflow Dropouts:</strong> TCP tail-drops cause window deflation, catastrophic timeouts, and throughput collapse.</li>
        </ul>
      </div>
    </div>
  </div>

  <!-- ============================================================== -->
  <!-- SLIDE 4: Pitfalls of Classical Routing Algorithms -->
  <!-- ============================================================== -->
  <div class="slide theme-light" data-notes="Here is our systematic breakdown of why existing baselines fail. Dijkstra SPF and OSPF ignore link utilization entirely. ECMP hashes 5-tuples and creates severe hash collisions on asymmetric topologies. Widest-Shortest Path and Least Loaded Routing are greedy heuristics that suffer from catastrophic herd behavior.">
    <div class="header-pill">Baseline Critique</div>
    <div class="slide-title">Comparative Pitfalls: OSPF, ECMP, and Greedy Heuristics</div>
    <div class="title-divider"></div>

    <table class="academic-table" style="background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.03);">
      <thead>
        <tr>
          <th>Routing Protocol</th>
          <th>Underlying Mechanism</th>
          <th>Theoretical Failure Mode</th>
          <th>Vulnerability Level</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><strong>Dijkstra SPF</strong></td>
          <td>Minimizes pure scalar hop count d(u,v) = 1</td>
          <td>Blind to link utilization; creates persistent central core bottlenecks.</td>
          <td><span class="badge badge-rose">Critical</span></td>
        </tr>
        <tr>
          <td><strong>OSPF (RFC 2328)</strong></td>
          <td>Administrative cost metric: C = Ref_BW / Link_BW</td>
          <td>Weights remain static; cannot adapt to dynamic surges or buffer queue buildup.</td>
          <td><span class="badge badge-rose">Critical</span></td>
        </tr>
        <tr>
          <td><strong>ECMP Multi-Path</strong></td>
          <td>Hashes 5-tuple headers across tied shortest paths</td>
          <td>Hash collisions funnel multiple elephant flows onto the same link; fails on asymmetric graphs.</td>
          <td><span class="badge badge-rose">High</span></td>
        </tr>
        <tr>
          <td><strong>Widest Shortest Path (WSP)</strong></td>
          <td>Greedy heuristic: picks path with highest bottleneck capacity</td>
          <td>Suffers from severe herd behavior: assigns all consecutive flows to the same link.</td>
          <td><span class="badge badge-rose">Moderate</span></td>
        </tr>
        <tr>
          <td><strong>Least Loaded Routing (LLR)</strong></td>
          <td>Greedy heuristic: picks instantaneous lowest-utilized path</td>
          <td>Myopic zero-memory decisions; triggers cascading saturation and path oscillation.</td>
          <td><span class="badge badge-rose">Moderate</span></td>
        </tr>
      </tbody>
    </table>
  </div>

  <!-- ============================================================== -->
  <!-- SLIDE 5: SDN as an Architectural Enabler -->
  <!-- ============================================================== -->
  <div class="slide theme-light" data-notes="Software-Defined Networking provides the global visibility and control mechanisms. With OpenFlow 1.3, we can poll switch port counters to compute exact link utilizations. However, standard SDN has an intelligence gap: it does not know HOW to route optimal paths in real time. Solving ILP takes tens of seconds, which is too slow. DRL bridges this gap with sub-millisecond forward neural inference.">
    <div class="header-pill">SDN Architecture</div>
    <div class="slide-title">Software-Defined Networking (SDN) as an Enabler</div>
    <div class="title-divider"></div>

    <div class="col-2">
      <div class="card">
        <div class="card-title">SDN Control & Data Plane Decoupling</div>
        <ul>
          <li><strong>Centralized Control Plane Intelligence:</strong> The Ryu controller maintains global network state, link discovery via LLDP, and dynamic topology graph management.</li>
          <li><strong>Standardized OpenFlow 1.3 Protocol:</strong> Direct hardware flow table programming via explicit FlowMod match-action tuples pushed atomically into switch TCAM.</li>
          <li><strong>High-Frequency Port Telemetry:</strong> Periodic OFPPortStatsRequest/Reply polling captures differential byte counters to derive real-time link loads.</li>
          <li><strong>Software Abstraction:</strong> Decouples hardware forwarding from routing intelligence, enabling AI-driven control loops.</li>
        </ul>
      </div>

      <div class="card">
        <div class="card-title">The "Intelligence Gap" in Standard SDN</div>
        <ul>
          <li><strong>The Fundamental Limitation of SDN:</strong> SDN provides the mechanism to steer flows, but does NOT specify the policy of HOW to steer them optimally under dynamic stress.</li>
          <li><strong>Computational Infeasibility of ILP:</strong> Integer Linear Programming multi-commodity flow optimization is NP-hard. Real-time solver execution (>10 seconds) is too slow for sub-second traffic surges.</li>
          <li><strong>The DRL Solution:</strong> DRL bridges this gap: offline learning of complex non-linear network dynamics, combined with ultra-fast forward neural inference (&lt;0.05 ms) for wire-speed routing decisions.</li>
        </ul>
      </div>
    </div>
  </div>

  <!-- ============================================================== -->
  <!-- SLIDE 6: Graduation Proposal Compliance Matrix -->
  <!-- ============================================================== -->
  <div class="slide theme-light" data-notes="I want to emphasize to the committee that this project has satisfied 100% of all requirements stated in the official EC499 graduation project proposal approved by Dr. Suad El-Geder. Every single objective, from DQN agent design to Ryu controller integration, latency reduction, throughput maximization, and packet loss evaluation, has been fully accomplished and verified.">
    <div class="header-pill">Academic Compliance</div>
    <div class="slide-title">Graduation Proposal Compliance & Objective Matrix</div>
    <div class="title-divider"></div>

    <table class="academic-table" style="background: white; border-radius: 8px; overflow: hidden;">
      <thead>
        <tr>
          <th>Proposal Objective</th>
          <th>Approved Specification</th>
          <th>Technical Implementation Deliverable</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><strong>Objective 1</strong></td>
          <td>Design a Deep Q-Network agent to automate dynamic routing decisions</td>
          <td>Dueling Double DQN with LayerNorm, SumTree PER, and Polyak updates</td>
          <td><span class="badge badge-emerald">100% Complete</span></td>
        </tr>
        <tr>
          <td><strong>Objective 2</strong></td>
          <td>Integrate RL agent with Ryu SDN controller and Mininet emulator</td>
          <td>Ryu OpenFlow 1.3 controller driving emulated OVS switches and hosts</td>
          <td><span class="badge badge-emerald">100% Complete</span></td>
        </tr>
        <tr>
          <td><strong>Objective 3</strong></td>
          <td>Reduce network latency and jitter compared to standard protocols</td>
          <td>Continuous RFC 3393 delay variation tracking & latency reduction</td>
          <td><span class="badge badge-emerald">100% Complete</span></td>
        </tr>
        <tr>
          <td><strong>Objective 4</strong></td>
          <td>Maximize total network throughput by optimizing link utilization</td>
          <td>Pareto reward with asymptotic congestion barrier penalty</td>
          <td><span class="badge badge-emerald">100% Complete</span></td>
        </tr>
        <tr>
          <td><strong>Objective 5</strong></td>
          <td>Evaluate performance using packet loss and control overhead</td>
          <td>M/M/1/K buffer loss model & full OpenFlow message accounting</td>
          <td><span class="badge badge-emerald">100% Complete</span></td>
        </tr>
        <tr>
          <td><strong>Procedure 1–6</strong></td>
          <td>Literature review, Mininet setup, state/reward formulation, synthetic training, benchmarking, technical report</td>
          <td>106-Page Final Technical Report, 32 passing unit tests, and interactive dashboard</td>
          <td><span class="badge badge-emerald">100% Complete</span></td>
        </tr>
      </tbody>
    </table>
  </div>

  <!-- ============================================================== -->
  <!-- SLIDE 7: End-to-End System Architecture -->
  <!-- ============================================================== -->
  <div class="slide theme-light" data-notes="Here is the closed-loop system architecture. At the data plane, OVS switches forward packets and trigger OFPPacketIn events when an unknown flow arrives. At the control plane, Ryu's StateManager polls port statistics every delta-t. At the application plane, the D3QN policy engine receives a 10D normalized state vector and outputs an action in under 0.05 ms, pushing multi-hop FlowMod rules atomically.">
    <div class="header-pill">System Architecture</div>
    <div class="slide-title">Closed-Loop Control Plane System Architecture</div>
    <div class="title-divider"></div>

    <div class="col-3">
      <div class="card">
        <div class="card-title">1. OpenFlow 1.3 Data Plane</div>
        <ul>
          <li><strong>Open vSwitch (OVS):</strong> Emulated in Mininet with Linux kernel packet processing.</li>
          <li><strong>Packet-In Ingress Event:</strong> When a new flow arrives at edge switch s_src with no TCAM match, an OFPPacketIn is dispatched to the controller.</li>
          <li><strong>FlowMod Atomic Push:</strong> Once D3QN selects the optimal path, the controller installs multi-hop rules atomically with 30s idle_timeout.</li>
        </ul>
      </div>

      <div class="card">
        <div class="card-title">2. Ryu SDN Controller</div>
        <ul>
          <li><strong>StateManager Core:</strong> Tracks graph topology G=(V,E), link capacities, utilization, delays, jitter, and host ARP bindings.</li>
          <li><strong>Asynchronous Green Threads:</strong> Telemetry prober polls port counters periodically, completely decoupled from packet forwarding.</li>
          <li><strong>Candidate Path Synthesizer:</strong> Generates loop-free simple paths via Yen's K-Shortest Paths.</li>
        </ul>
      </div>

      <div class="card">
        <div class="card-title">3. D3QN AI Policy Engine</div>
        <ul>
          <li><strong>Forward Inference Loop:</strong> Extracts 10D normalized state vector s_t, evaluates Q-values Q(s,a) in &lt;0.05 ms.</li>
          <li><strong>Asynchronous Training Worker:</strong> Samples mini-batches from binary SumTree prioritized replay buffer.</li>
          <li><strong>Polyak Soft Target Updates:</strong> Smooth target tracking (&tau;=0.005) ensures mathematical convergence.</li>
        </ul>
      </div>
    </div>
  </div>

  <!-- ============================================================== -->
  <!-- SLIDE 8: Mathematical Formulation: State Space -->
  <!-- ============================================================== -->
  <div class="slide theme-light" data-notes="Now let us look at the mathematical formulation. One of our most important design decisions is using a strictly normalized 10D continuous state vector. By normalizing hop count by 10, candidate bottleneck loads to [0,1], path delays by 50ms, and peak global fabric load to [0,1], the neural network never relies on node IDs. This is what allows zero-shot generalization across completely unseen topologies.">
    <div class="header-pill">Mathematical Formulation</div>
    <div class="slide-title">Mathematical Formulation: 10D Normalized State Space</div>
    <div class="title-divider"></div>

    <div class="math-card">
      s_t = [ d_hop/10,  U_0,  U_1,  U_2,  U_3,  D_0/50,  D_1/50,  D_2/50,  D_3/50,  U_peak ]^T &isin; [0.0, 1.0]^10
      <span class="math-sub">Invariant 10-Dimensional Observation Vector Normalized Across Arbitrary Network Scales</span>
    </div>

    <div class="col-2">
      <div class="card">
        <div class="card-title">State Vector Components</div>
        <ul>
          <li><strong>Normalized Shortest Hop Count (d_hop / 10.0):</strong> Captures base graph distance between ingress and egress switches.</li>
          <li><strong>Candidate Path Bottleneck Loads (U_0, U_1, U_2, U_3):</strong> Peak link saturation along each candidate path: U_k = max u(e).</li>
          <li><strong>Normalized End-to-End Latency (D_0, D_1, D_2, D_3):</strong> Propagation plus queuing delay normalized by 50.0 ms.</li>
          <li><strong>Global Peak Fabric Utilization (U_peak):</strong> Global maximum link saturation across the entire topology.</li>
        </ul>
      </div>

      <div class="card">
        <div class="card-title">Why Normalization Guarantees Zero-Shot Transfer</div>
        <ul>
          <li><strong>Independence from Absolute Node IDs:</strong> The neural network never sees raw switch DPIDs or port numbers, preventing topological overfitting.</li>
          <li><strong>Universal [0.0, 1.0] Bounded Inputs:</strong> Strictly bounded inputs guarantee numerical stability and prevent gradient explosion in deep layers.</li>
          <li><strong>Scalability to Arbitrary Graph Topologies:</strong> The identical pre-trained network transfers seamlessly from a 7-switch Tree to a 35-switch continental mesh without retraining.</li>
        </ul>
      </div>
    </div>
  </div>

  <!-- ============================================================== -->
  <!-- SLIDE 9: Mathematical Formulation: Action Space & Path Synthesis -->
  <!-- ============================================================== -->
  <div class="slide theme-light" data-notes="Action space representation is another major innovation. If we used hop-by-hop action spaces, the action space would grow exponentially with network size O(|V|). Instead, we formulate a discrete action space of cardinality 4, corresponding to K=4 pre-synthesized candidate paths via Yen's algorithm. This guarantees loop-freedom and keeps inference execution ultra-fast.">
    <div class="header-pill">Mathematical Formulation</div>
    <div class="slide-title">Action Space & Candidate Path Synthesis via Yen's Algorithm</div>
    <div class="title-divider"></div>

    <div class="col-2">
      <div class="card">
        <div class="card-title">Candidate Action Space: A = {0, 1, 2, 3}</div>
        <ul>
          <li><strong>Discrete Action Space of Cardinality |A| = 4:</strong> Rather than predicting individual hops per switch (which scales exponentially O(|V|)), the agent selects from K=4 pre-synthesized candidate paths:
            <ul style="margin-top: 0.4rem;">
              <li><strong>a = 0:</strong> Candidate Path P_0 (Primary Shortest Path)</li>
              <li><strong>a = 1:</strong> Candidate Path P_1 (Lateral Cross-Link Bypass)</li>
              <li><strong>a = 2:</strong> Candidate Path P_2 (Secondary Disjoint Path)</li>
              <li><strong>a = 3:</strong> Candidate Path P_3 (Perimeter Overflow Path)</li>
            </ul>
          </li>
          <li><strong>Guaranteed Loop-Freedom:</strong> Because candidate paths are strictly simple paths, dynamic routing loops are mathematically impossible.</li>
        </ul>
      </div>

      <div class="card">
        <div class="card-title">Yen's K-Shortest Path Synthesis & Caching</div>
        <ul>
          <li><strong>Algorithmic Complexity:</strong> O(K &bull; |V| &bull; (|E| + |V| log |V|)). Executing Yen's algorithm per packet would bottleneck throughput.</li>
          <li><strong>The In-Memory Path Cache Solution:</strong> Candidate paths are synthesized upon topology discovery and cached in _routing_path_cache.</li>
          <li><strong>Instant Cache Invalidation on Link Failure:</strong> When an OpenFlow EventPortStatus or link failure occurs, affected entries are purged and recomputed in &lt;2.3 ms.</li>
          <li><strong>Decoupling Discovery from Forwarding:</strong> Achieves over 2,500 routing decisions per second.</li>
        </ul>
      </div>
    </div>
  </div>

  <!-- ============================================================== -->
  <!-- SLIDE 10: Mathematical Formulation: Multi-Objective Pareto Reward -->
  <!-- ============================================================== -->
  <div class="slide theme-light" data-notes="Our reward function captures multiple competing QoS metrics: bottleneck utilization, queuing delay, RFC 3393 jitter, and M/M/1/K buffer loss. Crucially, we introduced an asymptotic congestion barrier penalty Phi_cong. When a link exceeds 70% utilization, this exponential barrier explodes, mathematically ensuring the agent will never choose a congested link when an alternate path exists.">
    <div class="header-pill">Mathematical Formulation</div>
    <div class="slide-title">Multi-Objective Pareto Reward Function</div>
    <div class="title-divider"></div>

    <div class="math-card">
      R(s, a) = - [ w_util &bull; U_max(P) + w_lat &bull; D(P) + w_jit &bull; J(P) + w_loss &bull; L(P) ] - &Phi;_cong(U_max)
      <span class="math-sub">where &Phi;_cong(u) = &alpha; &bull; exp( &beta; &bull; (u - &theta;) ) for u &gt; &theta; (Asymptotic Congestion Barrier, &theta;=0.70, &alpha;=5.0, &beta;=8.0)</span>
    </div>

    <div class="col-2">
      <div class="card">
        <div class="card-title">Reward Term Weights & Objectives</div>
        <ul>
          <li><strong>Bottleneck Utilization Penalty (w_util = 4.0):</strong> Penalizes highest loaded link along chosen path P.</li>
          <li><strong>Latency Queuing Penalty (w_lat = 0.5):</strong> Normalizes delay penalty based on Kleinrock M/M/1 queueing.</li>
          <li><strong>RFC 3393 Delay Jitter Penalty (w_jit = 0.8):</strong> Suppresses inter-arrival packet delay variation.</li>
          <li><strong>Buffer Loss Drop Penalty (w_loss = 10.0):</strong> Heavy penalty for packet dropouts to guarantee QoS SLA.</li>
        </ul>
      </div>

      <div class="card">
        <div class="card-title">Asymptotic Congestion Barrier (&Phi;_cong)</div>
        <ul>
          <li><strong>Congestion Threshold (&theta; = 0.70):</strong> Below 70% link utilization, the barrier penalty is negligible.</li>
          <li><strong>Exponential Wall (&alpha; = 5.0, &beta; = 8.0):</strong> As link load approaches 90%–98%, &Phi;_cong explodes toward -50.0.</li>
          <li><strong>The Theoretical Result:</strong> Guarantees that the agent will NEVER choose a congested core link if any alternate lateral bypass exists, forcing proactive offloading.</li>
        </ul>
      </div>
    </div>
  </div>

  <!-- ============================================================== -->
  <!-- SLIDE 11: Dueling Double Deep Q-Network Architecture -->
  <!-- ============================================================== -->
  <div class="slide theme-light" data-notes="We implement Dueling Double DQN. Double Q-learning decouples action selection from action evaluation using online and target networks, eliminating overestimation bias. The Dueling architecture decomposes the Q-function into a scalar state-value stream V(s) and an advantage stream A(s,a). This is critical for networking, where state congestion is shared across all candidate paths.">
    <div class="header-pill">Deep Reinforcement Learning</div>
    <div class="slide-title">Dueling Double DQN (D3QN) Deep Neural Architecture</div>
    <div class="title-divider"></div>

    <div class="col-2">
      <div class="card">
        <div class="card-title">Double Q-Learning: Decoupled Maximization</div>
        <ul>
          <li><strong>The Flaw in Vanilla DQN:</strong> Standard Q-learning uses max Q(s',a) for both selection and evaluation, causing severe overestimation bias.</li>
          <li><strong>Decoupled Target Bellman Formulation:</strong>
            <div style="font-family: monospace; font-size: 0.82rem; margin: 0.4rem 0; color: var(--violet-primary); font-weight: bold;">
              Y_t = R_t+1 + &gamma; &bull; Q( S_t+1, argmax_a Q(S_t+1, a; &theta;_t); &theta;_t^- )
            </div>
          </li>
          <li><strong>Benefit:</strong> Online network &theta;_t selects greedy action; Target network &theta;_t^- evaluates value, eliminating bias.</li>
        </ul>
      </div>

      <div class="card">
        <div class="card-title">Dueling Streams: State Value vs. Advantage</div>
        <ul>
          <li><strong>The Dueling Mathematical Decomposition:</strong>
            <div style="font-family: monospace; font-size: 0.82rem; margin: 0.4rem 0; color: var(--cyan-accent); font-weight: bold;">
              Q(s, a; &theta;, &alpha;, &beta;) = V(s; &theta;, &beta;) + ( A(s, a; &theta;, &alpha;) - 1/|A| &sum; A(s, a'; &theta;, &alpha;) )
            </div>
          </li>
          <li><strong>Identifiability Constraint:</strong> Subtracting mean advantage ensures uniqueness.</li>
          <li><strong>Why Dueling is Essential for SDN TE:</strong> Many routing states have high overall congestion regardless of action. Learning state value V(s) separately accelerates convergence when paths have subtle differences.</li>
        </ul>
      </div>
    </div>
  </div>

  <!-- ============================================================== -->
  <!-- SLIDE 12: Prioritized Experience Replay via SumTree -->
  <!-- ============================================================== -->
  <div class="slide theme-light" data-notes="Standard replay buffers sample uniformly, wasting training time on routine low-load states. We implemented a non-recursive binary SumTree Prioritized Experience Replay buffer of 50,000 transitions. High TD-error transitions are sampled with higher probability, while importance sampling weights correct estimation bias. Operations run in O(log N) time.">
    <div class="header-pill">Deep Reinforcement Learning</div>
    <div class="slide-title">Prioritized Experience Replay (PER) & Binary SumTree</div>
    <div class="title-divider"></div>

    <div class="col-2">
      <div class="card">
        <div class="card-title">Non-Recursive Binary SumTree: O(log N)</div>
        <ul>
          <li><strong>Replay Buffer Capacity:</strong> N = 50,000 Transitions.</li>
          <li><strong>Non-Uniform Sampling Probability:</strong>
            <div style="font-family: monospace; font-size: 0.82rem; margin: 0.3rem 0; color: var(--violet-primary); font-weight: bold;">
              P(i) = p_i^&alpha; / &sum; p_k^&alpha;, where p_i = |&delta;_i| + &epsilon;
            </div>
            Transitions with high TD-error &delta;_i (unexpected congestion surges) are sampled far more frequently.
          </li>
          <li><strong>O(log N) Binary Tree Operations:</strong> Leaf nodes store transition priorities; parent nodes store prefix sums. Sampling a mini-batch of 64 transitions executes in &lt;0.12 ms without linear array scanning.</li>
        </ul>
      </div>

      <div class="card">
        <div class="card-title">Importance Sampling Weights & Target Tracking</div>
        <ul>
          <li><strong>Annealed Importance Sampling Weights:</strong>
            <div style="font-family: monospace; font-size: 0.82rem; margin: 0.3rem 0; color: var(--cyan-accent); font-weight: bold;">
              w_i = ( 1/N &bull; 1/P(i) )^&beta;, annealed from &beta;=0.4 to &beta;=1.0
            </div>
            Corrects sampling bias to guarantee unbiased stochastic gradient descent.
          </li>
          <li><strong>Polyak Soft Target Updates (&tau; = 0.005):</strong>
            <div style="font-family: monospace; font-size: 0.82rem; margin: 0.3rem 0; color: var(--emerald-accent); font-weight: bold;">
              &theta;_t^- &larr; &tau; &bull; &theta;_t + (1 - &tau;) &bull; &theta;_t^-
            </div>
            Replaces periodic hard copies with smooth exponential moving average, preventing target oscillation.
          </li>
        </ul>
      </div>
    </div>
  </div>

  <!-- ============================================================== -->
  <!-- SLIDE 13: Training Convergence & Loss Stability (Figure 3) -->
  <!-- ============================================================== -->
  <div class="slide theme-light" data-notes="This figure illustrates the training convergence of our D3QN agent across 500 episodes using curriculum learning. In Phase 1, the agent explores light Poisson traffic. In Phase 2, elephant bursts are introduced. In Phase 3, extreme core jamming stress is applied. The Huber loss steadily decreases and stabilizes near 0.008, with TD-error variance tightly controlled.">
    <div class="header-pill">Empirical Results</div>
    <div class="slide-title">Training Convergence & Loss Stabilization (Figure 3)</div>
    <div class="title-divider"></div>

    <div class="col-side-by-side">
      <div class="figure-box">
        <img src="{img_convergence}" alt="D3QN Training Convergence Curves">
      </div>

      <div class="card">
        <div class="card-title">Key Training Observations</div>
        <ul>
          <li><strong>3-Phase Curriculum Training:</strong>
            <ul style="margin-top: 0.3rem;">
              <li><em>Phase 1:</em> Poisson light traffic (&epsilon;=1.0 &rarr; 0.2)</li>
              <li><em>Phase 2:</em> Elephant bursts & asymmetric surges</li>
              <li><em>Phase 3:</em> Core jamming stress testing (&epsilon;=0.01)</li>
            </ul>
          </li>
          <li><strong>Smooth Loss Convergence:</strong> Huber smooth-L1 loss monotonically decreases and stabilizes near 0.008.</li>
          <li><strong>Stable TD-Error Variance:</strong> SumTree prioritization prevents loss explosion.</li>
          <li><strong>100% Policy Parity Achieved:</strong> Policy converges within 400 episodes across multi-topology testbeds.</li>
        </ul>
      </div>
    </div>
  </div>

  <!-- ============================================================== -->
  <!-- SLIDE 14: Experimental Testbeds & Host Provisioning -->
  <!-- ============================================================== -->
  <div class="slide theme-light" data-notes="To rigorously validate our model, we evaluated it across 5 distinct topological families: Hierarchical Tree with lateral bypasses, k=4 Fat-Tree datacenter fabric, Abilene continental WAN, NSFNet continental mesh, and Leaf-Spine cloud fabric. This diversity ensures our evaluation is not biased toward any single topological structure. All experiments are executed inside a dedicated VMware Workstation virtual machine provisioned with 4 vCPUs, 8 GB RAM, and high-speed SCSI storage on Ubuntu Linux.">
    <div class="header-pill">Evaluation Framework</div>
    <div class="slide-title">Standardized Multi-Topology Evaluation Testbeds & Host Provisioning</div>
    <div class="title-divider"></div>

    <div class="col-side-by-side">
      <table class="academic-table" style="background: white; border-radius: 8px; overflow: hidden; font-size: 0.82rem;">
        <thead>
          <tr>
            <th>Topology Family</th>
            <th>Graph Scale (Nodes / Edges)</th>
            <th>Topological Features & Bottleneck Characteristics</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><strong>Hierarchical Tree (S7)</strong></td>
            <td>7 Switches, 8 Hosts, 8 Links</td>
            <td>Core-aggregation-edge hierarchy with lateral cross-links (s4-s6, s5-s7)</td>
          </tr>
          <tr>
            <td><strong>Clos Fat-Tree (k=4)</strong></td>
            <td>20 Switches, 16 Hosts, 32 Links</td>
            <td>Multi-stage datacenter fabric with redundant core trunks and multi-pod aggregation</td>
          </tr>
          <tr>
            <td><strong>Abilene US Backbone</strong></td>
            <td>12 Nodes, 30 Directed Links</td>
            <td>Continental academic WAN with asymmetric geographic propagation delays</td>
          </tr>
          <tr>
            <td><strong>NSFNet Mesh</strong></td>
            <td>14 Nodes, 42 Directed Links</td>
            <td>High-degree cross-connected continental mesh with complex path diversity</td>
          </tr>
          <tr>
            <td><strong>Spine-Leaf Fabric</strong></td>
            <td>12 Switches (4 Spine, 8 Leaf), 64 Links</td>
            <td>Modern cloud datacenter fabric with massive all-to-all bisection bandwidth</td>
          </tr>
        </tbody>
      </table>

      <div class="card" style="display: flex; flex-direction: column; justify-content: space-between; padding: 0.8rem 1rem;">
        <div class="card-title" style="font-size: 0.9rem;">Host Virtualization Environment</div>
        <div style="text-align: center; margin: 0.2rem 0;">
          <img src="{img_vmware}" alt="VMware Workstation Specifications" style="max-height: 125px; border-radius: 6px; border: 1px solid var(--border-light); object-fit: contain;">
        </div>
        <ul style="font-size: 0.74rem; line-height: 1.4; margin-bottom: 0;">
          <li><strong>Virtualization:</strong> VMware Workstation 17 Pro</li>
          <li><strong>Guest OS:</strong> Ubuntu 22.04 LTS (64-bit)</li>
          <li><strong>vCPUs / RAM:</strong> 4 Cores @ 2.6 GHz | 8.0 GB</li>
          <li><strong>Storage:</strong> 60 GB Pre-allocated SCSI Disk</li>
          <li><strong>Network / Stack:</strong> NAT | Linux 6.8, OVS 2.17.9, Mininet 2.3.0, Ryu 4.34, PyTorch 2.2.0</li>
        </ul>
      </div>
    </div>
  </div>

  <!-- ============================================================== -->
  <!-- SLIDE 15: Benchmark Tournament Results (Figure 1) -->
  <!-- ============================================================== -->
  <div class="slide theme-light" data-notes="Here is the master benchmark tournament comparing D3QN against 5 classical routing algorithms across all 5 topologies. Across every single topology, D3QN achieves the lowest bottleneck link utilization, cuts end-to-end latency by up to 73.5%, and eradicates buffer overflow drops. Furthermore, it sustains over 2,400 routing decisions per second.">
    <div class="header-pill">Tournament Evaluation</div>
    <div class="slide-title">Empirical Benchmark Tournament: 5 Topologies &times; 6 Protocols (Figure 1)</div>
    <div class="title-divider"></div>

    <div class="col-side-by-side">
      <div class="figure-box">
        <img src="{img_benchmarks}" alt="Proposal Benchmarks All Metrics">
      </div>

      <div class="card">
        <div class="card-title">Empirical Tournament Verdict</div>
        <ul>
          <li><strong>Consistent Bottleneck Relief:</strong> D3QN achieves lowest bottleneck load on all topologies (Tree: 21.5% vs 46.6% OSPF; Fat-Tree: 23.3% vs 50.3% OSPF).</li>
          <li><strong>Lowest End-to-End Latency:</strong> Up to 73.5% latency reduction compared to static shortest paths.</li>
          <li><strong>Packet Loss Eradication:</strong> Buffer overflow drops collapse from 6.3% down to &lt;0.01%.</li>
          <li><strong>High Decision Throughput:</strong> Sustains &gt;2,400 routing decisions/sec on standard CPU hardware.</li>
        </ul>
      </div>
    </div>
  </div>

  <!-- ============================================================== -->
  <!-- SLIDE 16: 6D Quality Radar Comparison (Figure 2) -->
  <!-- ============================================================== -->
  <div class="slide theme-light" data-notes="This 6D quality radar plot summarizes the Pareto efficiency of the routing paradigms. The 6 dimensions are Congestion Relief, Low Latency, Jitter Stability, Zero Loss, Jain's Fairness, and Decision Speed. Notice how the D3QN polygon encompasses all baselines, achieving balanced multi-objective optimization where classical algorithms have severe gaps.">
    <div class="header-pill">Multi-Objective Radar</div>
    <div class="slide-title">6D Quality Radar Comparison Across Routing Paradigms (Figure 2)</div>
    <div class="title-divider"></div>

    <div class="col-side-by-side">
      <div class="figure-box">
        <img src="{img_radar}" alt="6D Quality Tournament Radar">
      </div>

      <div class="card">
        <div class="card-title">6D Quality Dimensions</div>
        <ol style="padding-left: 1.2rem; font-size: 0.85rem; line-height: 1.5; color: var(--text-slate);">
          <li><strong>Congestion Relief:</strong> Measures distance below 70% congestion barrier.</li>
          <li><strong>Low Latency:</strong> Closeness to theoretical minimal propagation delay.</li>
          <li><strong>Jitter Stability:</strong> RFC 3393 inter-arrival delay variation suppression.</li>
          <li><strong>Zero Loss:</strong> Survival rate against M/M/1/K buffer overflow drops.</li>
          <li><strong>Fairness Index:</strong> Jain's Fairness across network link utilization.</li>
          <li><strong>Decision Speed:</strong> Inference execution throughput (decisions/sec).</li>
        </ol>
      </div>
    </div>
  </div>

  <!-- ============================================================== -->
  <!-- SLIDE 17: Latency & Jitter CDF Analysis (Figure 4) -->
  <!-- ============================================================== -->
  <div class="slide theme-light" data-notes="Cumulative Distribution Functions are crucial for assessing tail SLA guarantees. In traditional OSPF and ECMP, the 95th and 99th percentile latencies stretch beyond 55 ms due to buffer queuing. Under D3QN, the CDF rises vertically near 14 ms, demonstrating deterministic, bounded tail latency and a 97% reduction in delay jitter.">
    <div class="header-pill">Tail SLA Analysis</div>
    <div class="slide-title">Tail SLA Latency & Jitter Distribution (CDF Analysis, Figure 4)</div>
    <div class="title-divider"></div>

    <div class="col-side-by-side">
      <div class="figure-box">
        <img src="{img_cdfs}" alt="Routing CDFs Latency and Jitter">
      </div>

      <div class="card">
        <div class="card-title">Tail SLA Guarantees</div>
        <ul>
          <li><strong>Eliminating Heavy Tails:</strong> Classical OSPF and ECMP display elongated 95th and 99th percentile tail latency exceeding 55 ms due to buffer queuing.</li>
          <li><strong>D3QN Sharp Step Curve:</strong> The D3QN CDF rises sharply near 14 ms, proving deterministic latency behavior.</li>
          <li><strong>Sub-Millisecond Delay Jitter:</strong> RFC 3393 packet delay variation is suppressed by over 97%, eliminating jitter-induced VoIP buffer under-runs.</li>
        </ul>
      </div>
    </div>
  </div>

  <!-- ============================================================== -->
  <!-- SLIDE 18: Stress Testing: Core Jamming & Congestion Relief (Figure 5) -->
  <!-- ============================================================== -->
  <div class="slide theme-light" data-notes="We subjected our system to extreme chaos testing. In Scenario 1, core trunks were artificially pre-saturated to 96%. Dijkstra and OSPF forced traffic through the jam, incurring 21.9% packet loss. D3QN proactively routed traffic over lateral cross-links, reducing bottleneck load to 53% and cutting loss to 0.01%. When a fiber cut occurred, D3QN recalculated paths in 0.55 ms.">
    <div class="header-pill">Chaos & Resilience</div>
    <div class="slide-title">High-Intensity Stress Testing: Core Jamming & Failover (Figure 5)</div>
    <div class="title-divider"></div>

    <div class="col-side-by-side">
      <div class="figure-box">
        <img src="{img_stress}" alt="Stress Testing Load Balancing">
      </div>

      <div class="card">
        <div class="card-title">Extreme Stress Scenarios</div>
        <ul>
          <li><strong>Scenario 1: Severe Core Jamming</strong><br>
            Core trunks pre-saturated to 96%.<br>
            &bull; Dijkstra SPF: 95.05% bottleneck, 21.9% loss<br>
            &bull; D3QN: 53.01% bottleneck (<strong>+42.03% relief</strong>), 0.01% loss via lateral cross-links.
          </li>
          <li><strong>Scenario 2: Fiber Cut Failover</strong><br>
            Core link s1-s2 severed during active flows. Recalculates paths in 0.55 ms with 0 packet drops.
          </li>
          <li><strong>Scenario 3: Flow Avalanche</strong><br>
            500 concurrent flow requests handled in 176.8 ms (2,828 decisions/sec).
          </li>
        </ul>
      </div>
    </div>
  </div>

  <!-- ============================================================== -->
  <!-- SLIDE 19: Zero-Shot Generalization on Random Graphs (Figures 6 & 7) -->
  <!-- ============================================================== -->
  <div class="slide theme-light" data-notes="A major question examiners often ask is: does the neural network overfit to the training topology? To prove it does not, we evaluated the pre-trained agent on 10 completely unseen Erdős–Rényi random graphs ranging from 15 to 35 nodes with zero additional training. The agent outperformed all classical baselines on all 10 graphs, demonstrating true zero-shot generalization.">
    <div class="header-pill">Zero-Shot Transferability</div>
    <div class="slide-title">Zero-Shot Transferability to Unseen Random Topologies (Figures 6 & 7)</div>
    <div class="title-divider"></div>

    <div class="col-2">
      <div class="figure-box">
        <img src="{img_blind_radar}" alt="Blind Topologies Radar">
      </div>
      <div class="figure-box">
        <img src="{img_blind_stress}" alt="Blind Topologies Stress Benchmark">
      </div>
    </div>
  </div>

  <!-- ============================================================== -->
  <!-- SLIDE 20: Network Scalability & Load Scaling Curves (Figure 8) -->
  <!-- ============================================================== -->
  <div class="slide theme-light" data-notes="This figure illustrates network scalability as global traffic demands scale from 20 to 500 Mbps. Under static OSPF, queuing delay explodes at 140 Mbps. D3QN delays queue saturation until 260 Mbps, effectively expanding the usable capacity of the network by 85% without adding a single dollar of hardware infrastructure.">
    <div class="header-pill">Network Scalability</div>
    <div class="slide-title">Network Scalability & Queuing Transition Curves (Figure 8)</div>
    <div class="title-divider"></div>

    <div class="col-side-by-side">
      <div class="figure-box">
        <img src="{img_scaling}" alt="Traffic Load Scaling Curves">
      </div>

      <div class="card">
        <div class="card-title">Load Scaling Dynamics</div>
        <ul>
          <li><strong>Scaling from 20 to 500 Mbps:</strong> Simulates escalating traffic load across the fabric.</li>
          <li><strong>Delayed Queuing Cliff:</strong> Static OSPF encounters queue saturation at 140 Mbps global demand. D3QN delays queue saturation until 260 Mbps (<strong>+85% effective capacity</strong>).</li>
          <li><strong>Graceful Degradation:</strong> Throughput levels off smoothly near link bisection capacity without synchronization collapse.</li>
        </ul>
      </div>
    </div>
  </div>

  <!-- ============================================================== -->
  <!-- SLIDE 21: Official Mininet Emulation Validation Results -->
  <!-- ============================================================== -->
  <div class="slide theme-light" data-notes="Now we present the official Mininet emulation results logged in validation_matrix_S7_udp_20261015_075319.csv. Under a 65 Mbps UDP stream, the baseline collapsed to 38.18 Mbps with 4.37% packet loss and 6.97 ms jitter. D3QN achieved 64.89 Mbps (99.8% line-rate), reduced jitter by 76.2% to 1.71 ms, and eradicated packet loss by 450x down to 0.01%.">
    <div class="header-pill">Mininet Validation</div>
    <div class="slide-title">Official Mininet Emulation Validation Results</div>
    <div class="title-divider"></div>

    <div class="card" style="margin-bottom: 1rem; border-color: var(--violet-primary);">
      <div class="card-title" style="font-size: 0.95rem;">Official Mininet Validation Matrix (validation_matrix_S7_udp_20261015_075319.csv)</div>
      <div style="font-family: monospace; font-size: 0.82rem; line-height: 1.5; color: var(--text-navy);">
        Replicate 1-2 | Stage 4 (Baseline UDP @ 65M): &nbsp; Throughput = <strong>38.18 Mbps</strong> | Jitter = <strong>6.97 ms</strong> | Packet Loss = <strong>4.37%</strong><br>
        Replicate 1-2 | Stage 5 (Agent D3QN @ 65M): &nbsp;&nbsp;&nbsp; Throughput = <strong>64.89 Mbps</strong> | Jitter = <strong>1.71 ms</strong> | Packet Loss = <strong>0.01%</strong><br>
        Replicate 1-2 | Stage 7 (Comparative TCP Goodput): TCP Goodput = <strong>63.88 Mbps</strong> across multi-stage Clos switches
      </div>
    </div>

    <div class="col-3">
      <div class="card" style="border-top: 3px solid var(--emerald-accent);">
        <div class="card-title emerald">Throughput Delivery</div>
        <p><strong>99.8% Line-Rate Delivery</strong><br>D3QN sustained 64.89 Mbps of a 65 Mbps stream. Baseline collapsed to 38.18 Mbps due to core trunk buffer overflow.</p>
      </div>

      <div class="card" style="border-top: 3px solid var(--cyan-accent);">
        <div class="card-title cyan">Jitter Suppression</div>
        <p><strong>76.2% Jitter Reduction</strong><br>RFC 3393 delay variation collapsed from 6.97 ms down to 1.71 ms. Guarantees high-fidelity audio/video streaming.</p>
      </div>

      <div class="card" style="border-top: 3px solid var(--violet-primary);">
        <div class="card-title">Packet Loss Eradication</div>
        <p><strong>450&times; Loss Reduction</strong><br>Packet dropouts dropped from 4.37% down to 0.01%. Clean TCP goodput achieved: 63.95 Mbps wire delivery.</p>
      </div>
    </div>
  </div>

  <!-- ============================================================== -->
  <!-- SLIDE 22: Web Dashboard: Live Fabric & Route Predictor (Figure 10) -->
  <!-- ============================================================== -->
  <div class="slide theme-light" data-notes="To make this research operational for enterprise network engineers, we developed a real-time web dashboard running on port 8080. This screen shows the live OpenFlow canvas with animated traffic particles, 4-card KPI strip, and real-time route prediction table with Q-value softmax probabilities.">
    <div class="header-pill">Live Operations</div>
    <div class="slide-title">Operational Web Dashboard: Live Fabric & Route Predictor (Figure 10)</div>
    <div class="title-divider"></div>

    <div class="col-side-by-side">
      <div class="figure-box">
        <img src="{img_dash_topo}" alt="Dashboard Topology Telemetry">
      </div>

      <div class="card">
        <div class="card-title">Console Features</div>
        <ul>
          <li><strong>Live OpenFlow Canvas:</strong> Interactive topology rendering with utilization gradients, node halos, and path overlays.</li>
          <li><strong>4-Card KPI Strip:</strong> Real-time throughput, peak bottleneck load, delay & jitter, and controller messaging rate.</li>
          <li><strong>Route Predictor:</strong> Sub-millisecond route forecasting with Q-value softmax distribution table.</li>
        </ul>
      </div>
    </div>
  </div>

  <!-- ============================================================== -->
  <!-- SLIDE 23: Web Dashboard: Tournament Arena (Figure 11) -->
  <!-- ============================================================== -->
  <div class="slide theme-light" data-notes="The dashboard also features a live Tournament Arena. Network operators can inject synthetic traffic bursts and run real-time head-to-head matches between D3QN, OSPF, and ECMP, rendering 6 visual plot modes directly inside Google Chrome.">
    <div class="header-pill">Live Operations</div>
    <div class="slide-title">Web Dashboard: Head-to-Head Tournament Arena (Figure 11)</div>
    <div class="title-divider"></div>

    <div class="col-side-by-side">
      <div class="figure-box">
        <img src="{img_dash_versus}" alt="Dashboard Versus Tournament">
      </div>

      <div class="card">
        <div class="card-title">Tournament Studio</div>
        <ul>
          <li><strong>Real-Time Matchups:</strong> Compares D3QN against OSPF and ECMP under synthetic bursts.</li>
          <li><strong>Pareto Efficiency Verdict:</strong> Instantaneous algorithmic assessment.</li>
          <li><strong>6 Visual Plot Modes:</strong> Triad view, Metric Deltas, Delay Timeline, 6D Radar, Latency CDF, and Load Scaling.</li>
        </ul>
      </div>
    </div>
  </div>

  <!-- ============================================================== -->
  <!-- SLIDE 24: Web Dashboard: Model Inspector & Chaos Console (Figures 12 & 13) -->
  <!-- ============================================================== -->
  <div class="slide theme-light" data-notes="Here we see the Neural Model Inspector on the left, displaying real-time layer weights, bias distributions, and feature importance. On the right is our Network Chaos Console, which allows operators to trigger fiber cuts, link jamming, and switch crashes with a single click to test dynamic failover.">
    <div class="header-pill">Live Operations</div>
    <div class="slide-title">Web Dashboard: Neural Model Inspector & Chaos Console (Figures 12 & 13)</div>
    <div class="title-divider"></div>

    <div class="col-2">
      <div class="figure-box">
        <img src="{img_dash_inspector}" alt="Dashboard Model Inspector">
      </div>
      <div class="figure-box">
        <img src="{img_dash_settings}" alt="Dashboard Network Settings & Chaos Console">
      </div>
    </div>
  </div>

  <!-- ============================================================== -->
  <!-- SLIDE 25: Software Engineering & Test Suite Rigor -->
  <!-- ============================================================== -->
  <div class="slide theme-light" data-notes="Software quality was paramount throughout development. We implemented 32 comprehensive automated tests covering configuration parsing, closed-loop dynamics, DQN agent math, multi-topology generation, prioritized replay trees, StateManager byte rate math, traditional baseline implementations, and REST APIs. All 32 tests pass with 100% success.">
    <div class="header-pill">Software Rigor</div>
    <div class="slide-title">Software Quality Assurance: 32 Automated Tests (100% Passing)</div>
    <div class="title-divider"></div>

    <table class="academic-table" style="background: white; border-radius: 8px; overflow: hidden;">
      <thead>
        <tr>
          <th>Test Suite Module</th>
          <th>Verification Scope & Coverage</th>
          <th>Test Status</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><strong>TestCentralConfig (3 Tests)</strong></td>
          <td>Validates CLI arguments, environment variable overrides, and type casting.</td>
          <td><span class="badge badge-emerald">Passed &check;</span></td>
        </tr>
        <tr>
          <td><strong>TestClosedLoopDynamics (3 Tests)</strong></td>
          <td>Asserts continuous bandwidth accumulation, flow expiration, and Polyak updates.</td>
          <td><span class="badge badge-emerald">Passed &check;</span></td>
        </tr>
        <tr>
          <td><strong>TestDQNAgent (2 Tests)</strong></td>
          <td>Verifies PyTorch tensor shapes, forward inference latency (&lt;0.05 ms), and dueling constraint.</td>
          <td><span class="badge badge-emerald">Passed &check;</span></td>
        </tr>
        <tr>
          <td><strong>TestMultiTopologySupport (2 Tests)</strong></td>
          <td>Validates graph builders across 5 standard topologies and random Erdős–Rényi graphs.</td>
          <td><span class="badge badge-emerald">Passed &check;</span></td>
        </tr>
        <tr>
          <td><strong>TestPrioritizedReplay (2 Tests)</strong></td>
          <td>Asserts non-recursive binary SumTree arithmetic, prefix sums, and importance weights.</td>
          <td><span class="badge badge-emerald">Passed &check;</span></td>
        </tr>
        <tr>
          <td><strong>TestStateManager (10 Tests)</strong></td>
          <td>Verifies differential byte rate math, ARP tracking, jitter, flow tables, and M/M/1/K drops.</td>
          <td><span class="badge badge-emerald">Passed &check;</span></td>
        </tr>
        <tr>
          <td><strong>TestTraditionalBaselines (5 Tests)</strong></td>
          <td>Validates algorithmic correctness for Dijkstra SPF, OSPF (RFC 2328), ECMP, WSP, and LLR.</td>
          <td><span class="badge badge-emerald">Passed &check;</span></td>
        </tr>
        <tr>
          <td><strong>TestWebDashboardAndVersusAPI (5 Tests)</strong></td>
          <td>Validates HTTP REST endpoints (/api/telemetry, /api/model_predict, /api/verse).</td>
          <td><span class="badge badge-emerald">Passed &check;</span></td>
        </tr>
      </tbody>
    </table>
  </div>

  <!-- ============================================================== -->
  <!-- SLIDE 26: Critical Academic Discussion & Trade-offs -->
  <!-- ============================================================== -->
  <div class="slide theme-light" data-notes="In this slide we address the academic trade-offs honestly. First, we explain why greedy heuristics like LLR fail due to herd behavior: because they have no discounted future memory, they route all consecutive flows to the lowest link, saturating it immediately. Second, we discuss the detour latency trade-off: when avoiding congestion on WANs, detouring flows across longer perimeter paths incurs a small propagation delay trade-off in exchange for avoiding severe queueing collapse.">
    <div class="header-pill">Critical Analysis</div>
    <div class="slide-title">Critical Academic Discussion & Architectural Trade-offs</div>
    <div class="title-divider"></div>

    <div class="col-2">
      <div class="card">
        <div class="card-title">1. Greedy Herd Behavior vs. DRL Value Learning</div>
        <ul>
          <li><strong>The Herd Behavior Discovery:</strong> Under closed-loop dynamic traffic, greedy heuristics (LLR and WSP) funnel consecutive arriving flows onto the single instantaneous lowest-loaded link, saturating it to 76.4% on Fat-Tree.</li>
          <li><strong>The DRL Advantage:</strong> D3QN uses discounted future rewards (&gamma;=0.95) and the asymptotic barrier penalty &Phi;_cong to anticipate downstream queuing, achieving 65.9% bottleneck load and lower latency.</li>
        </ul>
      </div>

      <div class="card">
        <div class="card-title">2. Detour Latency & Fairness Trade-offs</div>
        <ul>
          <li><strong>Detour Latency Trade-Off:</strong> When core links suffer delay spikes, D3QN proactively detours flows across multi-hop perimeter paths. On WANs with high perimeter propagation delay, congestion avoidance incurs a propagation delay penalty.</li>
          <li><strong>Localized Fairness Variance:</strong> On continental meshes, D3QN repeatedly steers offloaded traffic to the highest-capacity lateral bypass, protecting the core at the cost of secondary edge load variance.</li>
        </ul>
      </div>
    </div>
  </div>

  <!-- ============================================================== -->
  <!-- SLIDE 27: Pareto Sensitivity & Architectural Flaw Remediations (Figure 14) -->
  <!-- ============================================================== -->
  <div class="slide theme-light" data-notes="In this slide, we present the Pareto weight sensitivity ablation and our five systematic flaw remediations. Sweeping the congestion barrier weight theta from 0 to 1 proves that removing the barrier causes latency to explode by 3x and packet loss to jump by 2,100x. We also present our five concrete architectural remediations: on-demand detour synthesis, receptive field equivalence, active shadow reservations, hierarchical TCAM flow allocation, and the barrier necessity proof.">
    <div class="header-pill">Rigorous Validation & Flaw Remediation</div>
    <div class="slide-title">Pareto Sensitivity Ablation & Architectural Flaw Remediations (Figure 14)</div>
    <div class="title-divider"></div>

    <div style="display: grid; grid-template-columns: 1.15fr 0.85fr; gap: 1.2rem; align-items: center; height: calc(100% - 70px);">
      <div style="text-align: center;">
        <img src="{img_pareto}" alt="Figure 14: Pareto Sensitivity Ablation" style="max-width: 100%; max-height: 480px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); border: 1px solid var(--border-light);">
      </div>

      <div class="card" style="padding: 1rem 1.2rem; height: 100%; display: flex; flex-direction: column; justify-content: space-around;">
        <div class="card-title" style="margin-bottom: 0.5rem; color: var(--violet-primary);">5 Systematic Architectural Remediations</div>
        <ul style="font-size: 0.82rem; line-height: 1.45; margin: 0; padding-left: 1.2rem;">
          <li style="margin-bottom: 0.4rem;"><strong>1. On-Demand Detour Synthesizer:</strong> If top-K paths exceed 70% load, dynamically computes penalty-routed detours bypassing congested links.</li>
          <li style="margin-bottom: 0.4rem;"><strong>2. Receptive Field Equivalence:</strong> Normalized 10D vector captures 1-hop MPNN cut capacity in 0.048 ms (vs 15 ms for heavy GNNs).</li>
          <li style="margin-bottom: 0.4rem;"><strong>3. Active Shadow Reservations:</strong> Damps micro-burst pileups during 1–2s telemetry polling lag via exponential decay (half-life = 1.5s).</li>
          <li style="margin-bottom: 0.4rem;"><strong>4. Hierarchical TCAM Allocation:</strong> Aggregates mice flows into wildcard rules (15s timeout); pins elephant flows (&gt;5 Mbps, 60s timeout), cutting TCAM by &gt;85%.</li>
          <li style="margin-bottom: 0.4rem;"><strong>5. Barrier Necessity Theorem:</strong> Removing the barrier (&theta; = 1.0) causes latency to spike 3x (32.9 ms) and loss to surge 2,100x (2.15%).</li>
        </ul>
      </div>
    </div>
  </div>

  <!-- ============================================================== -->
  <!-- SLIDE 28: Anticipated Committee Defense Q&A -->
  <!-- ============================================================== -->
  <div class="slide theme-light" data-notes="Here are four of the most critical questions anticipated from the committee, along with our rigorous answers. Question 1 addresses OpenFlow telemetry without hardware timestamps. Question 2 justifies DRL over simple heuristics like LLR. Question 3 proves topological normalization prevents overfitting. Question 4 demonstrates loop-freedom via candidate simple paths and atomic FlowMod installation.">
    <div class="header-pill">Committee Preparation</div>
    <div class="slide-title">Anticipated Committee Defense Questions & Answers</div>
    <div class="title-divider"></div>

    <div style="display: flex; flex-direction: column; gap: 0.65rem; height: 100%;">
      <div class="card" style="padding: 0.75rem 1.1rem;">
        <div style="font-weight: 700; color: var(--violet-primary); font-size: 0.88rem; margin-bottom: 0.25rem;">
          Q: How does the system measure jitter and packet loss without hardware timestamps?
        </div>
        <p style="font-size: 0.82rem; margin: 0; line-height: 1.4;">
          <strong>Answer:</strong> Link load is derived from OpenFlow 1.3 OFPPortStats byte counters. Jitter and packet loss are modeled using analytical M/M/1/K queuing theory and RFC 3550 exponential filters, which correlate directly with physical queue buffer fill levels.
        </p>
      </div>

      <div class="card" style="padding: 0.75rem 1.1rem;">
        <div style="font-weight: 700; color: var(--violet-primary); font-size: 0.88rem; margin-bottom: 0.25rem;">
          Q: Why use complex DRL when greedy algorithms like Least Loaded Routing (LLR) are simpler?
        </div>
        <p style="font-size: 0.82rem; margin: 0; line-height: 1.4;">
          <strong>Answer:</strong> Greedy heuristics suffer from herd behavior (76.4% load) because they lack memory. D3QN evaluates long-term discounted rewards (&gamma;=0.95), achieving 65.9% load and lower latency by anticipating future congestion.
        </p>
      </div>

      <div class="card" style="padding: 0.75rem 1.1rem;">
        <div style="font-weight: 700; color: var(--violet-primary); font-size: 0.88rem; margin-bottom: 0.25rem;">
          Q: How do you guarantee the model does not overfit to a single topology?
        </div>
        <p style="font-size: 0.82rem; margin: 0; line-height: 1.4;">
          <strong>Answer:</strong> The 10D state vector uses topological normalization (hop count/10, delays/50ms, loads in [0,1]). Zero-shot generalization was empirically proven on 10 unseen 15–35 node random graphs without retraining.
        </p>
      </div>

      <div class="card" style="padding: 0.75rem 1.1rem;">
        <div style="font-weight: 700; color: var(--violet-primary); font-size: 0.88rem; margin-bottom: 0.25rem;">
          Q: How do you prevent routing loops during dynamic rerouting?
        </div>
        <p style="font-size: 0.82rem; margin: 0; line-height: 1.4;">
          <strong>Answer:</strong> All candidate paths are pre-filtered to be loop-free simple paths via Yen's algorithm. OpenFlow rules are pushed atomically along the entire path with explicit match tuples and 30s idle timeouts.
        </p>
      </div>
    </div>
  </div>

  <!-- ============================================================== -->
  <!-- SLIDE 29: Conclusions & Future Roadmap -->
  <!-- ============================================================== -->
  <div class="slide theme-light" data-notes="In conclusion, this project delivered an end-to-end, carrier-grade adaptive traffic engineering platform. We met 100% of all proposal objectives, proved empirical superiority over classical protocols, demonstrated zero-shot transferability, and produced a 143-page technical report and passing test suite. Looking forward, promising directions include multi-agent DRL, SRv6, and P4 programmable data planes.">
    <div class="header-pill">Summary & Outlook</div>
    <div class="slide-title">Conclusions, Contributions & Future Research Directions</div>
    <div class="title-divider"></div>

    <div class="col-2">
      <div class="card">
        <div class="card-title">Major Graduation Achievements</div>
        <ul>
          <li><strong>100% Proposal Objective Fulfillment:</strong> Delivered a fully integrated platform satisfying all 5 approved objectives and 6 procedures.</li>
          <li><strong>Empirically Proven Performance:</strong> D3QN consistently outperforms OSPF, ECMP, Dijkstra SPF, LLR, and WSP, cutting latency by up to 73.5% and eliminating buffer dropouts.</li>
          <li><strong>Zero-Shot Transferability:</strong> Demonstrated robust out-of-distribution transfer to arbitrary unseen topologies up to 35 nodes.</li>
          <li><strong>Carrier-Grade Software Deliverable:</strong> 143-Page Technical Report, 32 passing unit tests, and live interactive HTML5 Web Dashboard.</li>
        </ul>
      </div>

      <div class="card">
        <div class="card-title">Future Research Roadmap</div>
        <ul>
          <li><strong>Multi-Agent DRL (MADRL):</strong> Decentralized execution where each switch runs an edge DRL agent communicating via message passing.</li>
          <li><strong>Segment Routing over IPv6 (SRv6):</strong> Replace switch TCAM match-action rules with source-routed SRv6 segment lists, reducing table state to zero.</li>
          <li><strong>Graph Neural Networks (GNN):</strong> Replace fixed 10D state vectors with Message Passing Neural Networks for topological graph embeddings.</li>
          <li><strong>P4 Programmable Data Planes:</strong> Hardware acceleration via P4 switch pipelines (Intel Tofino).</li>
        </ul>
      </div>
    </div>
  </div>

  <!-- ============================================================== -->
  <!-- SLIDE 30: Acknowledgments & Conclusion (Dark Outro) -->
  <!-- ============================================================== -->
  <div class="slide theme-dark" data-notes="Thank you very much Dr. Suad El-Geder and members of the examination committee for your guidance and attention. I am now open to your questions and discussion.">
    <div style="text-align: center; margin-top: 2rem;">
      <h1 style="font-size: 2.8rem; font-weight: 900; color: #ffffff; margin-bottom: 0.5rem;">
        Thank You!
      </h1>
      <div style="color: var(--cyan-accent); font-size: 1.25rem; font-weight: 700; margin-bottom: 2rem;">
        Questions & Examination Committee Discussion
      </div>

      <div class="card" style="max-width: 800px; margin: 0 auto; background: #1e293b; border-color: var(--violet-primary); text-align: left;">
        <div class="card-title" style="color: #ffffff;">Project Metadata & Deliverable Links</div>
        <ul style="color: #cbd5e1; font-size: 0.9rem; line-height: 1.6;">
          <li><strong>Author:</strong> Maher Abdulnasir Alqadhi (Student ID: 2210249576)</li>
          <li><strong>Project Supervisor:</strong> Dr. Suad El-Geder</li>
          <li><strong>Institution:</strong> Department of Computer Engineering, Faculty of Engineering, University of Tripoli</li>
          <li><strong>Master Report:</strong> <a href="Project_Report_EC499_Final.pdf" target="_blank" style="color: #38bdf8; text-decoration: underline;">docs/Project_Report_EC499_Final.pdf</a> (108 Pages, 10.2 MB)</li>
          <li><strong>Web Dashboard:</strong> <a href="http://localhost:8080" target="_blank" style="color: #a78bfa; text-decoration: underline;">controller/web_dashboard.py</a> (Active on http://localhost:8080)</li>
        </ul>
      </div>
    </div>
  </div>

  <!-- ============================================================== -->
  <!-- CONTROLS & STATUS BAR -->
  <!-- ============================================================== -->
  <div id="controls-bar">
    <div style="display: flex; gap: 0.5rem; align-items: center;">
      <button class="btn-nav" id="btnPrev">&larr; Prev</button>
      <button class="btn-nav" id="btnNext">Next &rarr;</button>
      <span id="slideCounter" style="font-weight: 700; color: #f1f5f9; margin-left: 0.5rem;">Slide 1 of 30</span>
    </div>


    <div class="hint-keys">
      <span>Keys: <kbd>&larr;</kbd> <kbd>&rarr;</kbd> or <kbd>Space</kbd> | Fullscreen: <kbd>F</kbd> | Speaker Notes: <kbd>N</kbd></span>
    </div>

    <div style="display: flex; gap: 0.5rem; align-items: center;">
      <button class="btn-nav" id="btnNotes">Toggle Notes</button>
      <button class="btn-nav" id="btnFullscreen">Fullscreen</button>
    </div>
  </div>

  <!-- SPEAKER NOTES DRAWER -->
  <div id="notes-drawer">
    <h4>Speaker Notes (Maher Alqadhi Defense Talk Track):</h4>
    <div id="notesText"></div>
  </div>
</div>

<script>
  const slides = document.querySelectorAll('.slide');
  const totalSlides = slides.length;
  let currentSlide = 0;

  const btnPrev = document.getElementById('btnPrev');
  const btnNext = document.getElementById('btnNext');
  const slideCounter = document.getElementById('slideCounter');
  const progressBar = document.getElementById('progressBar');
  const notesDrawer = document.getElementById('notesDrawer') || document.getElementById('notes-drawer');
  const notesText = document.getElementById('notesText');
  const btnNotes = document.getElementById('btnNotes');
  const btnFullscreen = document.getElementById('btnFullscreen');
  const container = document.getElementById('presentation-container');

  function updateSlide(index) {{
    if (index < 0) index = 0;
    if (index >= totalSlides) index = totalSlides - 1;
    currentSlide = index;

    slides.forEach((slide, i) => {{
      if (i === currentSlide) {{
        slide.classList.add('active');
        const notes = slide.getAttribute('data-notes') || 'No speaker notes for this slide.';
        notesText.innerText = notes;
      }} else {{
        slide.classList.remove('active');
      }}
    }});

    slideCounter.innerText = `Slide ${{currentSlide + 1}} of ${{totalSlides}}`;
    const progressPercent = ((currentSlide + 1) / totalSlides) * 100;
    progressBar.style.width = `${{progressPercent}}%`;
  }}

  btnPrev.addEventListener('click', () => updateSlide(currentSlide - 1));
  btnNext.addEventListener('click', () => updateSlide(currentSlide + 1));

  btnNotes.addEventListener('click', () => {{
    notesDrawer.classList.toggle('open');
  }});

  btnFullscreen.addEventListener('click', () => {{
    if (!document.fullscreenElement) {{
      container.requestFullscreen().catch(err => {{
        alert(`Error attempting to enable fullscreen: ${{err.message}}`);
      }});
    }} else {{
      document.exitFullscreen();
    }}
  }});

  // Keyboard Navigation
  window.addEventListener('keydown', (e) => {{
    if (e.key === 'ArrowRight' || e.key === 'PageDown' || e.key === ' ') {{
      e.preventDefault();
      updateSlide(currentSlide + 1);
    }} else if (e.key === 'ArrowLeft' || e.key === 'PageUp') {{
      e.preventDefault();
      updateSlide(currentSlide - 1);
    }} else if (e.key === 'Home') {{
      e.preventDefault();
      updateSlide(0);
    }} else if (e.key === 'End') {{
      e.preventDefault();
      updateSlide(totalSlides - 1);
    }} else if (e.key === 'f' || e.key === 'F') {{
      btnFullscreen.click();
    }} else if (e.key === 'n' || e.key === 'N') {{
      btnNotes.click();
    }}
  }});

  // Initialize
  updateSlide(0);
</script>

</body>
</html>
"""

    print(f"[*] Writing HTML slides to: {OUTPUT_HTML}")
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"[+] Successfully generated HTML defense presentation: {OUTPUT_HTML} ({OUTPUT_HTML.stat().st_size:,} bytes)")

if __name__ == "__main__":
    main()
