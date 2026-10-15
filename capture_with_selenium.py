#!/usr/bin/env python3
"""
Captures high-resolution, perfectly rendered screenshots of the SDN Web Dashboard
using Selenium WebDriver and Google Chrome.
"""

import os
import sys
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_DIR = Path(__file__).resolve().parent
PLOTS_DIR = BASE_DIR / "logs" / "plots"
CHROME_BIN = "/home/maher/.local/bin/google-chrome"
URL = "http://127.0.0.1:8089/?theme=light"

def main():
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    options = Options()
    options.binary_location = CHROME_BIN
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1650,1100')

    driver = webdriver.Chrome(options=options)
    driver.set_window_size(1650, 1100)

    try:
        print(f"[*] Navigating to {URL}...")
        driver.get(URL)

        # Wait for canvas to be present
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "topoCanvas")))
        time.sleep(1.5)

        # Trigger initial telemetry, prediction, and tournament matchup
        driver.execute_script("""
            if (typeof fetchTelemetry === 'function') fetchTelemetry();
            if (typeof runRoutePrediction === 'function') runRoutePrediction();
            if (typeof runVersusMatchup === 'function') runVersusMatchup();
        """)
        time.sleep(2.5)

        # 1. Capture Dashboard Overview (Top section with KPI cards & Topology Canvas)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1.0)
        p1 = PLOTS_DIR / "dashboard_topology_telemetry.png"
        driver.save_screenshot(str(p1))
        print(f"[+] Captured {p1.name} ({p1.stat().st_size:,} bytes)")

        # 2. Capture Protocol Tournament Section
        tournament_elem = driver.find_element(By.ID, "tournamentSection")
        driver.execute_script("arguments[0].scrollIntoView({ behavior: 'instant', block: 'start' });", tournament_elem)
        time.sleep(2.0)
        p2 = PLOTS_DIR / "dashboard_versus_tournament.png"
        tournament_elem.screenshot(str(p2))
        print(f"[+] Captured {p2.name} ({p2.stat().st_size:,} bytes)")

        # 3. Capture Model Architecture & Weights Inspector Modal
        driver.execute_script("""
            window.scrollTo(0, 0);
            if (typeof openModelInspectModal === 'function') openModelInspectModal();
        """)
        time.sleep(1.5)
        p3 = PLOTS_DIR / "dashboard_model_inspector.png"
        driver.save_screenshot(str(p3))
        print(f"[+] Captured {p3.name} ({p3.stat().st_size:,} bytes)")

        # 4. Capture Network Fabric Settings Modal
        driver.execute_script("""
            if (typeof closeModal === 'function') closeModal('modelInspectModal');
            if (typeof openNetworkSettingsModal === 'function') openNetworkSettingsModal();
        """)
        time.sleep(1.5)
        p4 = PLOTS_DIR / "dashboard_network_settings.png"
        driver.save_screenshot(str(p4))
        print(f"[+] Captured {p4.name} ({p4.stat().st_size:,} bytes)")

    finally:
        driver.quit()
        print("[+] Chrome WebDriver session finished successfully.")

if __name__ == '__main__':
    main()
