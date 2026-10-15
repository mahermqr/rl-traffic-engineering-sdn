#!/usr/bin/env python3
"""
Export Script for EC499 Final Project Report
Converts Project_Report_EC499.md into:
  1. A standalone, high-res HTML report with print-optimized CSS (docs/Project_Report_EC499.html)
  2. A formal multi-page PDF report with cover page, tables, and figures (docs/Project_Report_EC499_Exported.pdf)
"""

import os
import re
import sys
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent
DOCS_DIR = BASE_DIR / "docs"
PLOTS_DIR = BASE_DIR / "logs" / "plots"
MD_PATH = DOCS_DIR / "Project_Report_EC499.md"
HTML_OUTPUT = DOCS_DIR / "Project_Report_EC499.html"
PDF_OUTPUT = DOCS_DIR / "Project_Report_EC499_Exported.pdf"

def generate_html_report():
    print(f"[*] Reading Markdown from {MD_PATH}...")
    with open(MD_PATH, "r", encoding="utf-8") as f:
        md_text = f.read()

    # Convert Markdown to HTML using markdown-it-py if available, or regex-based converter
    try:
        from markdown_it import MarkdownIt
        md = MarkdownIt('gfm-like', {'html': True, 'linkify': True})
        html_body = md.render(md_text)
    except ImportError:
        import html
        # Basic fallback
        html_body = f"<pre>{html.escape(md_text)}</pre>"

    # Embed plot images into the HTML
    plot_images = [
        ("proposal_benchmarks_all_metrics.png", "Figure 1: Full Metric Tournament Benchmarks across All 5 Topologies"),
        ("proposal_tournament_radar.png", "Figure 2: 6D Quality Radar Comparison across Routing Paradigms"),
        ("dqn_te_training_convergence.png", "Figure 3: Multi-Objective D3QN Training Loss & TD-Error Convergence"),
        ("routing_cdfs_latency_jitter.png", "Figure 4: Cumulative Distribution Functions (CDF) for End-to-End Latency & Jitter"),
        ("stress_test_load_balancing.png", "Figure 5: High-Intensity Stress Test Load Balancing & Congestion Relief"),
        ("blind_topologies_radar.png", "Figure 6: Zero-Shot Generalization Radar across Diverse Topologies")
    ]

    plots_gallery_html = '<section class="plots-gallery"><h2>Empirical Plot Studio & Visual Benchmark Gallery</h2><div class="gallery-grid">'
    for img_name, caption in plot_images:
        img_path = PLOTS_DIR / img_name
        rel_path = f"../logs/plots/{img_name}"
        if img_path.exists():
            plots_gallery_html += f'''
            <div class="gallery-item">
                <img src="{rel_path}" alt="{caption}" loading="lazy">
                <div class="caption">{caption}</div>
            </div>
            '''
    plots_gallery_html += '</div></section>'

    # Append plots gallery before references or at the end
    if "## 12. References" in html_body:
        html_body = html_body.replace("<h2>12. References</h2>", f"{plots_gallery_html}<h2>12. References</h2>")
    else:
        html_body += plots_gallery_html

    full_html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EC499 Final Project Report: Reinforcement Learning for Adaptive Traffic Engineering in an SDN Network</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-body: #0d1117;
            --bg-card: #161b22;
            --border-color: #30363d;
            --text-main: #c9d1d9;
            --text-heading: #f0f6fc;
            --text-muted: #8b949e;
            --accent: #8b5cf6;
            --accent-glow: rgba(139, 92, 246, 0.25);
            --accent-cyan: #38bdf8;
            --accent-emerald: #10b981;
            --accent-rose: #f43f5e;
            --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            --font-mono: 'JetBrains Mono', monospace;
        }}

        @media (prefers-color-scheme: light) {{
            :root {{
                --bg-body: #ffffff;
                --bg-card: #f8fafc;
                --border-color: #e2e8f0;
                --text-main: #334155;
                --text-heading: #0f172a;
                --text-muted: #64748b;
                --accent: #7c3aed;
                --accent-glow: rgba(124, 58, 237, 0.15);
            }}
        }}

        body {{
            font-family: var(--font-sans);
            background-color: var(--bg-body);
            color: var(--text-main);
            line-height: 1.7;
            margin: 0;
            padding: 0;
            -webkit-font-smoothing: antialiased;
        }}

        .report-container {{
            max-width: 960px;
            margin: 40px auto;
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 50px 65px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.35);
        }}

        .print-btn-bar {{
            position: sticky;
            top: 20px;
            z-index: 100;
            display: flex;
            justify-content: flex-end;
            margin-bottom: 25px;
            gap: 12px;
        }}

        .btn-action {{
            background: var(--accent);
            color: #ffffff;
            border: none;
            padding: 8px 18px;
            border-radius: 8px;
            font-weight: 600;
            font-size: 0.9rem;
            cursor: pointer;
            box-shadow: 0 4px 14px var(--accent-glow);
            transition: all 0.2s ease;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }}

        .btn-action:hover {{
            opacity: 0.92;
            transform: translateY(-1px);
        }}

        h1, h2, h3, h4, h5, h6 {{
            color: var(--text-heading);
            font-weight: 700;
            margin-top: 1.8em;
            margin-bottom: 0.6em;
            line-height: 1.3;
        }}

        h1 {{
            font-size: 2.2rem;
            border-bottom: 2px solid var(--border-color);
            padding-bottom: 16px;
            margin-top: 0;
            color: var(--accent);
        }}

        h2 {{
            font-size: 1.55rem;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 8px;
            color: var(--accent-cyan);
        }}

        h3 {{
            font-size: 1.25rem;
        }}

        p, li {{
            font-size: 1rem;
        }}

        code {{
            font-family: var(--font-mono);
            background: rgba(139, 92, 246, 0.12);
            color: var(--accent);
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.88em;
        }}

        pre {{
            background: #090d13;
            border: 1px solid var(--border-color);
            border-radius: 10px;
            padding: 16px 20px;
            overflow-x: auto;
            font-family: var(--font-mono);
            font-size: 0.85rem;
            color: #e6edf3;
        }}

        pre code {{
            background: transparent;
            color: inherit;
            padding: 0;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 24px 0;
            font-size: 0.9rem;
            background: rgba(0, 0, 0, 0.15);
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid var(--border-color);
        }}

        th, td {{
            padding: 10px 14px;
            text-align: left;
            border-bottom: 1px solid var(--border-color);
        }}

        th {{
            background: rgba(139, 92, 246, 0.15);
            color: var(--text-heading);
            font-weight: 700;
            text-transform: uppercase;
            font-size: 0.78rem;
            letter-spacing: 0.05em;
        }}

        tr:last-child td {{
            border-bottom: none;
        }}

        tr:hover td {{
            background: rgba(255, 255, 255, 0.02);
        }}

        blockquote {{
            border-left: 4px solid var(--accent);
            margin: 20px 0;
            padding: 10px 20px;
            background: rgba(139, 92, 246, 0.05);
            border-radius: 0 8px 8px 0;
            color: var(--text-main);
        }}

        hr {{
            border: none;
            border-top: 1px solid var(--border-color);
            margin: 40px 0;
        }}

        .gallery-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin: 25px 0;
        }}

        .gallery-item {{
            background: rgba(0, 0, 0, 0.2);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 12px;
            text-align: center;
        }}

        .gallery-item img {{
            width: 100%;
            height: auto;
            border-radius: 8px;
            display: block;
        }}

        .gallery-item .caption {{
            font-size: 0.8rem;
            color: var(--text-muted);
            margin-top: 8px;
            font-weight: 500;
        }}

        @media print {{
            body {{
                background: #ffffff;
                color: #000000;
            }}
            .print-btn-bar {{
                display: none;
            }}
            .report-container {{
                max-width: 100%;
                margin: 0;
                padding: 0;
                border: none;
                box-shadow: none;
            }}
            h1, h2, h3 {{
                page-break-after: avoid;
            }}
            table, pre, .gallery-item {{
                page-break-inside: avoid;
            }}
        }}
    </style>
</head>
<body>
    <div class="report-container">
        <div class="print-btn-bar">
            <button class="btn-action" onclick="window.print()">🖨️ Print / Save to PDF</button>
            <a class="btn-action" href="Project_Report_EC499.pdf" download style="background:var(--accent-emerald);">📥 Download Compiled PDF</a>
        </div>
        {html_body}
    </div>
</body>
</html>
'''
    with open(HTML_OUTPUT, "w", encoding="utf-8") as f:
        f.write(full_html)
    print(f"[+] Successfully exported HTML report to: {HTML_OUTPUT}")

def generate_pdf_report():
    print(f"[*] Compiling PDF report to {PDF_OUTPUT} via ReportLab...")
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, PageBreak, KeepTogether, HRFlowable
        )
        from reportlab.pdfgen import canvas

        class NumberedCanvas(canvas.Canvas):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self._saved_page_states = []

            def showPage(self):
                self._saved_page_states.append(dict(self.__dict__))
                self._startPage()

            def save(self):
                num_pages = len(self._saved_page_states)
                for state in self._saved_page_states:
                    self.__dict__.update(state)
                    self.draw_page_number(num_pages)
                    super().showPage()
                super().save()

            def draw_page_number(self, page_count):
                if self._pageNumber == 1:
                    return  # Suppress on cover page
                self.saveState()
                self.setFont("Helvetica", 9)
                self.setFillColor(colors.HexColor("#64748b"))
                # Header
                self.drawString(54, 750, "EC499 Graduation Project Report: Reinforcement Learning for Adaptive SDN TE")
                self.setStrokeColor(colors.HexColor("#cbd5e1"))
                self.setLineWidth(0.5)
                self.line(54, 742, 558, 742)
                # Footer
                self.line(54, 45, 558, 45)
                self.drawString(54, 32, "Department of Computer Engineering • University of Tripoli")
                page_str = f"Page {self._pageNumber} of {page_count}"
                self.drawRightString(558, 32, page_str)
                self.restoreState()

        doc = SimpleDocTemplate(
            str(PDF_OUTPUT),
            pagesize=letter,
            leftMargin=54,
            rightMargin=54,
            topMargin=54,
            bottomMargin=54
        )

        styles = getSampleStyleSheet()
        normal = styles["Normal"]
        normal.textColor = colors.HexColor("#1e293b")
        normal.fontSize = 10
        normal.leading = 14

        title_style = ParagraphStyle(
            "CoverTitle",
            parent=normal,
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=26,
            textColor=colors.HexColor("#6d28d9"),
            alignment=1,
            spaceAfter=15
        )

        sub_style = ParagraphStyle(
            "CoverSub",
            parent=normal,
            fontName="Helvetica",
            fontSize=11,
            leading=16,
            textColor=colors.HexColor("#475569"),
            alignment=1,
            spaceAfter=30
        )

        h1_style = ParagraphStyle(
            "ReportH1",
            parent=normal,
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=18,
            textColor=colors.HexColor("#0f172a"),
            spaceBefore=18,
            spaceAfter=8,
            keepWithNext=True
        )

        h2_style = ParagraphStyle(
            "ReportH2",
            parent=normal,
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            textColor=colors.HexColor("#7c3aed"),
            spaceBefore=14,
            spaceAfter=6,
            keepWithNext=True
        )

        meta_style = ParagraphStyle(
            "CoverMeta",
            parent=normal,
            fontSize=10,
            leading=15,
            textColor=colors.HexColor("#334155")
        )

        story = []

        # Cover Page
        story.append(Spacer(1, 40))
        story.append(Paragraph("University of Tripoli • Faculty of Engineering", sub_style))
        story.append(Paragraph("Department of Computer Engineering", sub_style))
        story.append(Spacer(1, 20))
        story.append(Paragraph("Reinforcement Learning for Adaptive Traffic Engineering in an SDN Network", title_style))
        story.append(Paragraph("Final Graduation Technical Project Report (EC499)", sub_style))
        story.append(Spacer(1, 40))

        meta_table_data = [
            [Paragraph("<b>Student Author:</b>", meta_style), Paragraph("Maher Abdulnasir Alqadhi (ID: 2210249576)", meta_style)],
            [Paragraph("<b>Supervisor:</b>", meta_style), Paragraph("Dr. Suad El-Geder", meta_style)],
            [Paragraph("<b>Degree Program:</b>", meta_style), Paragraph("Bachelor of Science in Computer Engineering", meta_style)],
            [Paragraph("<b>Academic Term:</b>", meta_style), Paragraph("Spring 2026", meta_style)],
            [Paragraph("<b>Repository:</b>", meta_style), Paragraph("github.com/maheralqadhi/EC499-SDN-Adaptive-TE-RL", meta_style)],
            [Paragraph("<b>Platform Status:</b>", meta_style), Paragraph("Production Verified (32/32 Unit Tests, 15/15 Dashboard Tests)", meta_style)]
        ]
        t_meta = Table(meta_table_data, colWidths=[130, 360])
        t_meta.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#e2e8f0")),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('LEFTPADDING', (0,0), (-1,-1), 10),
            ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ]))
        story.append(t_meta)
        story.append(Spacer(1, 50))

        # Add Executive Summary on Cover
        abstract_box = [
            [Paragraph("<b>Executive Abstract:</b> Traditional IP routing protocols (OSPF, ECMP, Dijkstra) forward traffic based on static metrics, creating severe core congestion during burst surges. This project engineers and evaluates an autonomous Deep Reinforcement Learning (D3QN) platform with Prioritized Experience Replay on an OpenFlow 1.3 Ryu SDN controller. Benchmarked against 5 classic protocols across 5 topologies and unseen random graphs, D3QN achieves up to <b>+26.2% congestion relief</b>, cuts latency by <b>73.5%</b>, and suppresses jitter by <b>>97%</b> with sub-millisecond inference.", meta_style)]
        ]
        t_abs = Table(abstract_box, colWidths=[490])
        t_abs.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#ede9fe")),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#c4b5fd")),
            ('TOPPADDING', (0,0), (-1,-1), 10),
            ('BOTTOMPADDING', (0,0), (-1,-1), 10),
            ('LEFTPADDING', (0,0), (-1,-1), 12),
            ('RIGHTPADDING', (0,0), (-1,-1), 12),
        ]))
        story.append(t_abs)
        story.append(PageBreak())

        # Read markdown sections and render
        with open(MD_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()

        in_table = False
        table_lines = []

        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue

            # Skip top frontmatter
            if line_str.startswith("# Project Final Technical Report") or line_str.startswith("**Project Title**") or line_str.startswith("**Degree**") or line_str.startswith("**Department**") or line_str.startswith("**Institution**") or line_str.startswith("**Author**") or line_str.startswith("**Project Supervisor**") or line_str.startswith("**Academic Term**") or line_str.startswith("**Repository**") or line_str.startswith("**License**"):
                continue

            if line_str.startswith("|"):
                in_table = True
                table_lines.append(line_str)
                continue
            elif in_table:
                in_table = False
                # Parse markdown table
                if len(table_lines) >= 3:
                    rows = []
                    for tl in table_lines:
                        if re.match(r'^\|[\s\-:]+\|$', tl):
                            continue # skip separator
                        cells = [c.strip() for c in tl.split("|")[1:-1]]
                        rows.append([Paragraph(re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', c), meta_style) for c in cells])
                    if rows:
                        col_w = 500 / len(rows[0])
                        t = Table(rows, colWidths=[col_w] * len(rows[0]))
                        t.setStyle(TableStyle([
                            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#ede9fe")),
                            ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor("#4c1d95")),
                            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
                            ('TOPPADDING', (0,0), (-1,-1), 4),
                            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                        ]))
                        story.append(Spacer(1, 6))
                        story.append(t)
                        story.append(Spacer(1, 8))
                table_lines = []

            if line_str.startswith("## "):
                story.append(Spacer(1, 10))
                story.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#cbd5e1"), spaceAfter=10))
                story.append(Paragraph(line_str[3:], h1_style))
            elif line_str.startswith("### "):
                story.append(Paragraph(line_str[4:], h2_style))
            elif line_str.startswith("#### "):
                story.append(Paragraph(f"<b>{line_str[5:]}</b>", meta_style))
            elif line_str.startswith("- ") or line_str.startswith("* "):
                clean_bullet = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line_str[2:])
                story.append(Paragraph(f"• {clean_bullet}", normal))
            elif re.match(r'^\d+\.\s', line_str):
                clean_num = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line_str)
                story.append(Paragraph(clean_num, normal))
            elif line_str.startswith("```"):
                continue
            else:
                clean_p = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line_str)
                clean_p = re.sub(r'`(.*?)`', r'<font face="Courier" color="#6d28d9">\1</font>', clean_p)
                story.append(Paragraph(clean_p, normal))
                story.append(Spacer(1, 4))

        # Add Embedded Plots at the end
        story.append(PageBreak())
        story.append(Paragraph("Empirical Plot Studio & Benchmark Gallery", h1_style))
        story.append(Paragraph("High-resolution telemetry plots generated across multi-topology stress tournaments:", normal))
        story.append(Spacer(1, 10))

        plot_files = [
            ("proposal_benchmarks_all_metrics.png", "Figure 1: Benchmark Matrix Across All 5 Topologies"),
            ("proposal_tournament_radar.png", "Figure 2: 6D Quality Radar Comparison (D3QN vs Baselines)"),
            ("dqn_te_training_convergence.png", "Figure 3: Multi-Objective D3QN Training Loss & TD-Error"),
            ("routing_cdfs_latency_jitter.png", "Figure 4: Latency & Jitter Cumulative Distribution Functions (CDF)"),
            ("stress_test_load_balancing.png", "Figure 5: High-Intensity Stress Test Congestion Relief"),
            ("blind_topologies_radar.png", "Figure 6: Zero-Shot Generalization Radar Across Diverse Topologies")
        ]

        for pf, cap in plot_files:
            p_path = PLOTS_DIR / pf
            if p_path.exists():
                story.append(KeepTogether([
                    RLImage(str(p_path), width=480, height=270),
                    Spacer(1, 4),
                    Paragraph(f"<b>{cap}</b>", ParagraphStyle("Caption", parent=normal, fontSize=8.5, alignment=1, textColor=colors.HexColor("#475569"))),
                    Spacer(1, 14)
                ]))

        doc.build(story, canvasmaker=NumberedCanvas)
        print(f"[+] Successfully exported PDF report to: {PDF_OUTPUT}")
    except Exception as e:
        print(f"[-] PDF compilation error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    generate_html_report()
    generate_pdf_report()
