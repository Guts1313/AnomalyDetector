"""Capture live React-frontend screenshots for the research report.

Boots nothing itself — expects the Vite dev server on :5173 (proxying /api to
the FastAPI service on :8000, already seeded with demo traffic). Walks every
tab and writes PNGs into docs/screenshots/ that the Word report embeds.

    .venv/Scripts/python.exe -m scripts.capture_frontend
"""
from __future__ import annotations

import time
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://localhost:5173"
OUT = Path("docs/screenshots")
OUT.mkdir(parents=True, exist_ok=True)

VIEWPORT = {"width": 1480, "height": 1024}


def _tab(page, label: str) -> None:
    page.get_by_role("tab", name=label, exact=True).click()
    page.wait_for_timeout(1400)


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--force-color-profile=srgb"])
        page = browser.new_context(
            viewport=VIEWPORT, device_scale_factor=2
        ).new_page()

        page.goto(BASE, wait_until="networkidle")
        page.wait_for_timeout(2500)  # let Plotly + Orb settle

        # 1. Overview — KPIs, severity donut, attacks-by-class
        _tab(page, "Overview")
        page.screenshot(path=str(OUT / "10_fe_overview.png"), full_page=True)

        # 2. Alerts — severity-coloured audit table
        _tab(page, "Alerts")
        page.screenshot(path=str(OUT / "11_fe_alerts.png"), full_page=True)

        # 3. Manual scoring — drive a verdict so the card is populated
        _tab(page, "Manual scoring")
        try:
            page.get_by_role("button", name="Score flow").click()
            page.wait_for_timeout(1600)
        except Exception as exc:  # noqa: BLE001
            print(f"[!] manual score click skipped: {exc}")
        page.screenshot(path=str(OUT / "12_fe_manual_scoring.png"), full_page=True)

        # 4. Request examples — the attack/defend control plane
        _tab(page, "Request examples")
        page.wait_for_timeout(800)
        page.screenshot(path=str(OUT / "13_fe_examples.png"), full_page=True)

        # 4b. A focused crop of the first accordion (DDoS preset + Run on lab)
        try:
            acc = page.locator("details.accordion").first
            acc.screenshot(path=str(OUT / "14_fe_examples_ddos.png"))
        except Exception as exc:  # noqa: BLE001
            print(f"[!] accordion crop skipped: {exc}")

        # 5. About — active model + dataset disclosure
        _tab(page, "About")
        page.screenshot(path=str(OUT / "15_fe_about.png"), full_page=True)

        browser.close()
    print(f"[+] Screenshots written to {OUT}/")


if __name__ == "__main__":
    main()
