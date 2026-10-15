#!/usr/bin/env python3
"""
Captures high-resolution screenshots of the SDN Web Dashboard & Telemetry Console
using headless Google Chrome.
"""

import os
import sys
import time
import subprocess
import threading
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent
PLOTS_DIR = BASE_DIR / "logs" / "plots"
CHROME_BIN = "/home/maher/.local/bin/google-chrome"

# Ensure controller in sys.path
sys.path.insert(0, str(BASE_DIR / "controller"))
from web_dashboard import DashboardServer

def main():
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    port = 8089
    server = DashboardServer(host="127.0.0.1", port=port)
    print(f"[*] Dashboard server started on 127.0.0.1:{port}")
    time.sleep(1.5)

    targets = [
        ("dashboard_topology_telemetry.png", f"http://127.0.0.1:{port}/?theme=light", (1600, 1050), 3000),
        ("dashboard_versus_tournament.png", f"http://127.0.0.1:{port}/?theme=light&scroll=tournamentSection&plot=triad", (1600, 1100), 3500),
        ("dashboard_model_inspector.png", f"http://127.0.0.1:{port}/?theme=light&inspect", (1600, 1050), 3000),
        ("dashboard_network_settings.png", f"http://127.0.0.1:{port}/?theme=light&settings", (1600, 1050), 3000),
    ]

    for fname, url, (w, h), budget in targets:
        out_path = PLOTS_DIR / fname
        cmd = [
            CHROME_BIN,
            "--headless=new",
            "--disable-gpu",
            "--no-sandbox",
            f"--window-size={w},{h}",
            f"--virtual-time-budget={budget}",
            f"--screenshot={out_path}",
            url
        ]
        print(f"[*] Capturing {fname} with Chrome...")
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if out_path.exists() and out_path.stat().st_size > 0:
            print(f"    [+] Successfully captured {fname} ({out_path.stat().st_size:,} bytes)")
        else:
            print(f"    [-] Failed to capture {fname}. Stderr: {res.stderr}")

    server.stop()
    print("[+] Dashboard screenshot capture complete.")

if __name__ == '__main__':
    main()
