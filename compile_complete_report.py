#!/usr/bin/env python3
"""
Compiles the complete 11-Chapter and 5-Appendix EC499 Graduation Report
into:
  1. A standalone, beautiful HTML document (docs/Project_Report_EC499.html)
  2. A comprehensive publication-grade PDF via Google Chrome (docs/Project_Report_EC499_Final.pdf)
"""

import os
import re
import sys
import base64
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DOCS_DIR = BASE_DIR / "docs"
CHAPS_DIR = DOCS_DIR / "chapters"
APPS_DIR = DOCS_DIR / "appendices"
PLOTS_DIR = BASE_DIR / "logs" / "plots"
HTML_OUTPUT = DOCS_DIR / "Project_Report_EC499.html"
PDF_OUTPUT = DOCS_DIR / "Project_Report_EC499_Final.pdf"
CHROME_BIN = "/home/maher/.local/bin/google-chrome"

def latex_to_html(tex_content):
    """Converts LaTeX content into semantic, cleanly styled HTML."""
    text = tex_content

    # Remove comments
    text = re.sub(r'(?<!\\)%.*$', '', text, flags=re.MULTILINE)

    # Convert sections and chapters
    text = re.sub(r'\\chapter\{([^}]+)\}', r'<h1 class="chapter-title">\1</h1>', text)
    text = re.sub(r'\\section\{([^}]+)\}', r'<h2 class="section-title">\1</h2>', text)
    text = re.sub(r'\\subsection\{([^}]+)\}', r'<h3 class="subsection-title">\1</h3>', text)
    text = re.sub(r'\\subsubsection\{([^}]+)\}', r'<h4 class="subsubsection-title">\1</h4>', text)

    # Convert text formatting
    text = re.sub(r'\\textbf\{([^}]+)\}', r'<strong>\1</strong>', text)
    text = re.sub(r'\\textit\{([^}]+)\}', r'<em>\1</em>', text)
    text = re.sub(r'\\emph\{([^}]+)\}', r'<em>\1</em>', text)
    text = re.sub(r'\\texttt\{([^}]+)\}', r'<code>\1</code>', text)
    text = re.sub(r'\\underline\{([^}]+)\}', r'<u>\1</u>', text)

    # Convert math blocks
    text = re.sub(r'\\begin\{equation\*?\}(.*?)\\end\{equation\*?\}', lambda m: f'<div class="math-block">$${m.group(1)}$$</div>', text, flags=re.DOTALL)
    text = re.sub(r'\\begin\{align\*?\}(.*?)\\end\{align\*?\}', lambda m: f'<div class="math-block">$$\\begin{{aligned}}{m.group(1)}\\end{{aligned}}$$</div>', text, flags=re.DOTALL)

    # Convert listings
    def replace_lstlisting(m):
        code = m.group(1).strip()
        code_esc = code.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        return f'<pre class="code-box"><code>{code_esc}</code></pre>'
    text = re.sub(r'\\begin\{lstlisting\}(?:\[.*?\])?(.*?)\\end\{lstlisting\}', replace_lstlisting, text, flags=re.DOTALL)

    # Convert itemize and enumerate
    text = re.sub(r'\\begin\{itemize\}', r'<ul class="academic-list">', text)
    text = re.sub(r'\\end\{itemize\}', r'</ul>', text)
    text = re.sub(r'\\begin\{enumerate\}', r'<ol class="academic-list">', text)
    text = re.sub(r'\\end\{enumerate\}', r'</ol>', text)
    text = re.sub(r'\\item\s+(.*?)(?=(\\item|</ul>|</ol>))', r'<li>\1</li>', text, flags=re.DOTALL)

    # Convert figures
    def replace_figure(m):
        body = m.group(1)
        cap_match = re.search(r'\\caption\{([^}]+)\}', body)
        caption = cap_match.group(1) if cap_match else ""
        img_match = re.search(r'\\includegraphics(?:\[.*?\])?\{([^}]+)\}', body)
        if img_match:
            img_rel = img_match.group(1).replace('../logs/plots/', '').replace('logs/plots/', '').replace('./plots/', '').strip()
            img_path = PLOTS_DIR / img_rel
            if img_path.exists():
                with open(img_path, 'rb') as f:
                    b64 = base64.b64encode(f.read()).decode('utf-8')
                return f'''
                <figure class="report-figure">
                    <img src="data:image/png;base64,{b64}" alt="{caption}">
                    <figcaption>{caption}</figcaption>
                </figure>
                '''
        return ""
    text = re.sub(r'\\begin\{figure\*?\}(?:\[.*?\])?(.*?)\\end\{figure\*?\}', replace_figure, text, flags=re.DOTALL)

    # Convert simple tables
    def replace_table(m):
        body = m.group(1)
        cap_match = re.search(r'\\caption\{([^}]+)\}', body)
        caption = cap_match.group(1) if cap_match else ""
        # Find tabular or tabularx
        tab_match = re.search(r'\\begin\{tabular(?:x)?\}\{.*?\}(.*?)\\end\{tabular(?:x)?\}', body, flags=re.DOTALL)
        if not tab_match:
            return ""
        tab_body = tab_match.group(1)
        # Parse rows
        rows = [r.strip() for r in tab_body.split(r'\\') if r.strip()]
        html_rows = []
        is_first = True
        for row in rows:
            row_clean = re.sub(r'\\(toprule|midrule|bottomrule|addlinespace|hline)', '', row).strip()
            if not row_clean:
                continue
            cells = [re.sub(r'\\textbf\{([^}]+)\}', r'<strong>\1</strong>', c.strip()) for c in row_clean.split('&')]
            cells = [re.sub(r'\\texttt\{([^}]+)\}', r'<code>\1</code>', c) for c in cells]
            cells = [re.sub(r'\\(small|footnotesize|scriptsize)', '', c).strip() for c in cells]
            if is_first:
                html_rows.append('<tr>' + ''.join(f'<th>{c}</th>' for c in cells) + '</tr>')
                is_first = False
            else:
                html_rows.append('<tr>' + ''.join(f'<td>{c}</td>' for c in cells) + '</tr>')

        cap_html = f'<div class="table-caption"><strong>Table:</strong> {caption}</div>' if caption else ""
        return f'<div class="table-container">{cap_html}<table class="academic-table">' + ''.join(html_rows) + '</table></div>'
    text = re.sub(r'\\begin\{table\*?\}(?:\[.*?\])?(.*?)\\end\{table\*?\}', replace_table, text, flags=re.DOTALL)

    # Clean leftover LaTeX macros
    text = re.sub(r'\\label\{[^}]+\}', '', text)
    text = re.sub(r'\\cite\{([^}]+)\}', r'[\1]', text)
    text = re.sub(r'\\ref\{([^}]+)\}', r'<strong>\1</strong>', text)
    text = re.sub(r'\\pagestyle\{[^}]+\}', '', text)
    text = re.sub(r'\\newpage|\\clearpage|\\pagebreak', r'<div class="page-break"></div>', text)
    text = re.sub(r'\\noindent', '', text)
    text = re.sub(r'\\vspace\{[^}]+\}', '', text)
    text = re.sub(r'\\hspace\{[^}]+\}', '', text)
    text = re.sub(r'\\small|\\footnotesize|\\scriptsize|\\large|\\Large', '', text)

    # Convert paragraphs
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    html_paragraphs = []
    for p in paragraphs:
        if p.startswith('<h') or p.startswith('<div') or p.startswith('<figure') or p.startswith('<ul') or p.startswith('<ol') or p.startswith('<pre') or p.startswith('<table'):
            html_paragraphs.append(p)
        else:
            html_paragraphs.append(f'<p class="academic-p">{p}</p>')

    return '\n'.join(html_paragraphs)

def main():
    print("[*] Compiling Master Thesis HTML & Publication PDF...")
    
    # Ordered Chapters
    chapters = [
        ("ch01_introduction.tex", "Chapter 1: Introduction & Research Motivation"),
        ("ch02_theoretical_foundations.tex", "Chapter 2: Theoretical Foundations of SDN & DRL"),
        ("ch03_mathematical_modeling.tex", "Chapter 3: Mathematical Modeling & Traffic Formulation"),
        ("ch04_system_architecture.tex", "Chapter 4: Closed-Loop Control Plane Architecture"),
        ("ch05_drl_agent_engineering.tex", "Chapter 5: DRL Agent Engineering & Prioritized Replay"),
        ("ch06_topologies_and_traffic.tex", "Chapter 6: Network Topologies & Synthetic Workloads"),
        ("ch07_benchmark_tournament.tex", "Chapter 7: Multi-Topology Benchmark Tournament Results"),
        ("ch08_stress_testing_generalization.tex", "Chapter 8: Stress Testing & Zero-Shot Generalization"),
        ("ch09_critical_discussion_defense_guide.tex", "Chapter 9: Critical Academic Discussion & Defense Guide"),
        ("ch10_verification_and_operations.tex", "Chapter 10: Software Quality Assurance, Test Suite & Platform Operations"),
        ("ch11_conclusion_future_work.tex", "Chapter 11: Conclusions, Ethical Reflections & Future Roadmap")
    ]

    appendices = [
        ("app_a_math_proofs.tex", "Appendix A: Mathematical Proofs & Convergence Theorems"),
        ("app_b_openflow_spec.tex", "Appendix B: OpenFlow 1.3 Protocol Message Specification & Pipeline"),
        ("app_c_config_reference.tex", "Appendix C: Global Configuration Parameter Reference"),
        ("app_d_code_listings.tex", "Appendix D: Complete Source Code Listings & Architecture Map"),
        ("app_e_user_manual.tex", "Appendix E: Complete User & Administrator Deployment Manual")
    ]

    body_html = ""

    for fname, title in chapters:
        fpath = CHAPS_DIR / fname
        if fpath.exists():
            print(f"[*] Processing {title} ({fpath.stat().st_size:,} bytes)...")
            raw = fpath.read_text(encoding='utf-8')
            conv = latex_to_html(raw)
            body_html += f'<section class="chapter-section"><div class="chapter-divider"></div>{conv}</section>'

    body_html += '<section class="appendices-start"><h1 class="chapter-title" style="margin-top:60px;">APPENDICES</h1></section>'

    for fname, title in appendices:
        fpath = APPS_DIR / fname
        if fpath.exists():
            print(f"[*] Processing {title} ({fpath.stat().st_size:,} bytes)...")
            raw = fpath.read_text(encoding='utf-8')
            conv = latex_to_html(raw)
            body_html += f'<section class="appendix-section"><div class="chapter-divider"></div>{conv}</section>'

    # Embed plot gallery
    all_plots = [
        ("proposal_benchmarks_all_metrics.png", "Figure 1: Full Metric Tournament Benchmarks across All 5 Topologies"),
        ("proposal_tournament_radar.png", "Figure 2: 6D Quality Radar Comparison across Routing Paradigms"),
        ("dqn_te_training_convergence.png", "Figure 3: Multi-Objective D3QN Training Loss & TD-Error Convergence"),
        ("routing_cdfs_latency_jitter.png", "Figure 4: Cumulative Distribution Functions (CDF) for End-to-End Latency & Jitter"),
        ("stress_test_load_balancing.png", "Figure 5: High-Intensity Stress Test Load Balancing & Congestion Relief"),
        ("blind_topologies_radar.png", "Figure 6: Zero-Shot Generalization Radar across Diverse Topologies"),
        ("blind_topologies_stress_benchmark.png", "Figure 7: Multi-Topology Blind Stress Benchmark (Zero-Shot Generalization)"),
        ("traffic_load_scaling_curves.png", "Figure 8: Network Scalability & Queuing Transition Curves under Escalating Traffic"),
        ("random_blind_topologies_evaluation.png", "Figure 9: Zero-Shot Blind Transfer Evaluation on Unseen Random Topologies (20-30 Nodes)"),
        ("dashboard_topology_telemetry.png", "Figure 10: Real-Time OpenFlow 1.3 Topology Fabric and Interactive Telemetry Console"),
        ("dashboard_versus_tournament.png", "Figure 11: Real-Time Algorithm Tournament and Multi-Metric Benchmarking Studio"),
        ("dashboard_model_inspector.png", "Figure 12: PyTorch D3QN Neural Network Architecture and Live Model Telemetry Inspector"),
        ("dashboard_network_settings.png", "Figure 13: Network Fabric Architecture Settings and Chaos Fault Injection Console")
    ]

    gallery_items = ""
    for img_name, cap in all_plots:
        ip = PLOTS_DIR / img_name
        if ip.exists():
            with open(ip, 'rb') as f:
                b64 = base64.b64encode(f.read()).decode('utf-8')
            gallery_items += f'''
            <div class="gallery-card">
                <img src="data:image/png;base64,{b64}" alt="{cap}" loading="lazy">
                <div class="gallery-caption">{cap}</div>
            </div>
            '''

    gallery_html = f'''
    <section class="plots-gallery-section">
        <h1 class="chapter-title">Empirical Benchmark Plot Studio & Figure Compendium</h1>
        <p class="academic-p">High-resolution scientific telemetry plots and interactive dashboard interfaces generated across multi-topology stress tournaments:</p>
        <div class="gallery-grid">
            {gallery_items}
        </div>
    </section>
    '''

    body_html += gallery_html

    full_html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EC499 Graduation Project Report: Reinforcement Learning for Adaptive Traffic Engineering in an SDN Network</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@500;700;800&family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;700&family=Lora:ital,wght@0,400;0,500;0,600;1,400&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
    <style>
        @page {{
            size: A4;
            margin: 22mm 18mm 24mm 22mm;
            @top-left {{
                content: "EC499 Final Project Report";
                font-family: 'Inter', sans-serif;
                font-size: 8pt;
                color: #64748b;
                border-bottom: 0.5pt solid #cbd5e1;
                padding-bottom: 4px;
            }}
            @top-right {{
                content: "Adaptive SDN Traffic Engineering with D3QN";
                font-family: 'Inter', sans-serif;
                font-size: 8pt;
                color: #64748b;
                border-bottom: 0.5pt solid #cbd5e1;
                padding-bottom: 4px;
            }}
            @bottom-center {{
                content: counter(page);
                font-family: 'Inter', sans-serif;
                font-size: 9pt;
                font-weight: 600;
                color: #334155;
            }}
        }}

        :root {{
            --font-display: 'Cinzel', Georgia, serif;
            --font-serif: 'Lora', Georgia, serif;
            --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            --font-mono: 'JetBrains Mono', Consolas, monospace;
            --text-color: #1e293b;
            --heading-color: #0f172a;
            --accent-color: #6d28d9;
            --border-color: #e2e8f0;
            --bg-light: #f8fafc;
        }}

        body {{
            font-family: var(--font-serif);
            font-size: 11pt;
            line-height: 1.65;
            color: var(--text-color);
            background-color: #ffffff;
            margin: 0;
            padding: 0;
            text-rendering: optimizeLegibility;
        }}

        .report-wrapper {{
            max-width: 900px;
            margin: 0 auto;
            padding: 40px 30px;
        }}

        /* Formal Cover Page */
        .cover-page {{
            text-align: center;
            padding: 60px 20px 80px 20px;
            page-break-after: always;
            border-bottom: 3px double #cbd5e1;
            margin-bottom: 40px;
        }}
        .university-header {{
            font-family: var(--font-display);
            font-size: 16pt;
            font-weight: 700;
            letter-spacing: 2px;
            text-transform: uppercase;
            color: #0f172a;
            margin-bottom: 6px;
        }}
        .faculty-header {{
            font-family: var(--font-sans);
            font-size: 11pt;
            font-weight: 500;
            color: #475569;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            margin-bottom: 40px;
        }}
        .thesis-badge {{
            display: inline-block;
            font-family: var(--font-mono);
            font-size: 9pt;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            background: #ede9fe;
            color: #5b21b6;
            padding: 5px 14px;
            border-radius: 20px;
            margin-bottom: 25px;
        }}
        .thesis-title {{
            font-family: var(--font-display);
            font-size: 23pt;
            font-weight: 800;
            line-height: 1.25;
            color: #0f172a;
            margin-bottom: 25px;
        }}
        .thesis-subtitle {{
            font-family: var(--font-sans);
            font-size: 12pt;
            color: #475569;
            max-width: 720px;
            margin: 0 auto 50px auto;
            line-height: 1.5;
        }}
        .author-box {{
            margin-top: 40px;
            font-family: var(--font-sans);
            border-top: 1px solid #e2e8f0;
            border-bottom: 1px solid #e2e8f0;
            padding: 24px 0;
            display: flex;
            justify-content: space-around;
            text-align: left;
        }}
        .author-col h4 {{
            margin: 0 0 6px 0;
            font-size: 9.5pt;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #64748b;
        }}
        .author-col p {{
            margin: 0 0 4px 0;
            font-size: 11pt;
            font-weight: 600;
            color: #0f172a;
        }}
        .author-col span {{
            font-size: 9.5pt;
            color: #64748b;
        }}
        .term-footer {{
            margin-top: 45px;
            font-family: var(--font-sans);
            font-size: 10pt;
            color: #64748b;
        }}

        /* Headings */
        h1.chapter-title {{
            font-family: var(--font-display);
            font-size: 18pt;
            font-weight: 700;
            color: #0f172a;
            border-bottom: 1.5pt solid #6d28d9;
            padding-bottom: 8px;
            margin-top: 50px;
            margin-bottom: 20px;
            page-break-before: always;
        }}
        h2.section-title {{
            font-family: var(--font-sans);
            font-size: 13.5pt;
            font-weight: 700;
            color: #1e1b4b;
            margin-top: 32px;
            margin-bottom: 12px;
            border-bottom: 0.5pt solid #cbd5e1;
            padding-bottom: 4px;
        }}
        h3.subsection-title {{
            font-family: var(--font-sans);
            font-size: 11.5pt;
            font-weight: 600;
            color: #4338ca;
            margin-top: 24px;
            margin-bottom: 8px;
        }}
        h4.subsubsection-title {{
            font-family: var(--font-sans);
            font-size: 10.5pt;
            font-weight: 600;
            color: #475569;
            margin-top: 16px;
            margin-bottom: 6px;
        }}

        /* Paragraphs & Text */
        p.academic-p {{
            text-align: justify;
            margin-bottom: 14px;
            text-indent: 1.5em;
        }}
        p.academic-p:first-of-type {{
            text-indent: 0;
        }}

        ul.academic-list, ol.academic-list {{
            margin: 12px 0 16px 24px;
            padding: 0;
        }}
        ul.academic-list li, ol.academic-list li {{
            margin-bottom: 6px;
            line-height: 1.55;
        }}

        /* Math Blocks */
        .math-block {{
            margin: 16px 0;
            padding: 10px 16px;
            background: #f8fafc;
            border-left: 3px solid #6d28d9;
            border-radius: 4px;
            overflow-x: auto;
            text-align: center;
        }}

        /* Tables */
        .table-container {{
            margin: 22px 0;
            page-break-inside: avoid;
        }}
        .table-caption {{
            font-family: var(--font-sans);
            font-size: 9.5pt;
            color: #334155;
            margin-bottom: 6px;
            text-align: left;
        }}
        table.academic-table {{
            width: 100%;
            border-collapse: collapse;
            font-family: var(--font-sans);
            font-size: 9pt;
            line-height: 1.45;
            margin-bottom: 8px;
        }}
        table.academic-table th {{
            background-color: #ede9fe;
            color: #4c1d95;
            font-weight: 700;
            text-align: left;
            padding: 8px 10px;
            border-top: 1.5pt solid #6d28d9;
            border-bottom: 1pt solid #cbd5e1;
        }}
        table.academic-table td {{
            padding: 6px 10px;
            border-bottom: 0.5pt solid #e2e8f0;
            color: #334155;
        }}
        table.academic-table tr:last-child td {{
            border-bottom: 1.5pt solid #6d28d9;
        }}
        table.academic-table tr:nth-child(even) {{
            background-color: #f8fafc;
        }}

        /* Figures */
        figure.report-figure {{
            margin: 24px 0;
            text-align: center;
            page-break-inside: avoid;
        }}
        figure.report-figure img {{
            max-width: 100%;
            height: auto;
            border-radius: 6px;
            border: 1px solid #cbd5e1;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        }}
        figure.report-figure figcaption {{
            font-family: var(--font-sans);
            font-size: 9pt;
            color: #475569;
            margin-top: 8px;
            font-weight: 500;
        }}

        /* Code Blocks */
        pre.code-box {{
            background-color: #0f172a;
            color: #e2e8f0;
            font-family: var(--font-mono);
            font-size: 8pt;
            line-height: 1.4;
            padding: 14px 18px;
            border-radius: 6px;
            overflow-x: auto;
            margin: 16px 0;
            page-break-inside: avoid;
        }}
        code {{
            font-family: var(--font-mono);
            font-size: 8.5pt;
            background: #ede9fe;
            color: #5b21b6;
            padding: 1px 4px;
            border-radius: 3px;
        }}
        pre.code-box code {{
            background: transparent;
            color: inherit;
            padding: 0;
        }}

        /* Gallery Grid */
        .plots-gallery-section {{
            margin-top: 50px;
            page-break-before: always;
        }}
        .gallery-grid {{
            display: grid;
            grid-template-columns: 1fr;
            gap: 24px;
            margin-top: 20px;
        }}
        .gallery-card {{
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 14px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
            page-break-inside: avoid;
            text-align: center;
        }}
        .gallery-card img {{
            max-width: 100%;
            height: auto;
            border-radius: 4px;
        }}
        .gallery-caption {{
            font-family: var(--font-sans);
            font-size: 9pt;
            font-weight: 600;
            color: #334155;
            margin-top: 8px;
        }}

        .page-break {{
            page-break-after: always;
        }}
        .chapter-divider {{
            height: 1px;
            background: #e2e8f0;
            margin: 30px 0;
        }}
    </style>
</head>
<body>

<div class="report-wrapper">

    <!-- Formal Cover Page -->
    <div class="cover-page">
        <div class="university-header">University of Tripoli</div>
        <div class="faculty-header">Faculty of Engineering &bull; Department of Computer Engineering</div>
        <div class="thesis-badge">EC499 Final Graduation Project Report</div>
        <h1 class="thesis-title">Reinforcement Learning for Adaptive Traffic Engineering in an SDN Network</h1>
        <p class="thesis-subtitle">
            A Closed-Loop Deep Reinforcement Learning Control Plane utilizing Dueling Double Deep Q-Networks (D3QN) and Prioritized Experience Replay for Real-Time Autonomous Congestion Mitigation and QoS Optimization.
        </p>
        <div class="author-box">
            <div class="author-col">
                <h4>Author</h4>
                <p>Maher Abdulnasir Alqadhi</p>
                <span>Student ID: 2210249576<br>ma.alqadhi@uot.edu.ly</span>
            </div>
            <div class="author-col">
                <h4>Project Supervisor</h4>
                <p>Dr. Suad El-Geder</p>
                <span>Associate Professor<br>Department of Computer Engineering</span>
            </div>
            <div class="author-col">
                <h4>Academic Evaluation</h4>
                <p>Degree of Bachelor of Science</p>
                <span>Computer Engineering<br>Academic Year 2025–2026</span>
            </div>
        </div>
        <div class="term-footer">
            Tripoli, Libya &bull; Spring 2026 &bull; Published under the MIT Open-Source License
        </div>
    </div>

    <!-- Master Document Content -->
    {body_html}

</div>

</body>
</html>
'''

    HTML_OUTPUT.write_text(full_html, encoding='utf-8')
    print(f"[+] Successfully generated standalone Master HTML Report: {HTML_OUTPUT} ({HTML_OUTPUT.stat().st_size:,} bytes)")

    # Export publication PDF with Google Chrome
    print(f"[*] Rendering Master Publication PDF via Google Chrome CLI to: {PDF_OUTPUT}...")
    cmd = [
        CHROME_BIN,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--no-pdf-header-footer",
        f"--print-to-pdf={PDF_OUTPUT}",
        str(HTML_OUTPUT)
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if PDF_OUTPUT.exists() and PDF_OUTPUT.stat().st_size > 0:
        print(f"[+] Successfully compiled Publication PDF via Google Chrome: {PDF_OUTPUT} ({PDF_OUTPUT.stat().st_size:,} bytes)")
    else:
        print(f"[-] Error rendering PDF with Google Chrome: {res.stderr}")

if __name__ == '__main__':
    main()
