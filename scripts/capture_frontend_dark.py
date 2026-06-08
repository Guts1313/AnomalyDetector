"""Capture dark-theme React-frontend screenshots for the research report.

Forces the FE into its dark theme by seeding localStorage before the app boots
(the theme provider reads `ad.theme`). Expects the Vite dev server on :5173.

    python -m scripts.capture_frontend_dark
"""
from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://localhost:5173"
OUT = Path("docs/screenshots")
VIEWPORT = {"width": 1480, "height": 1040}


def _tab(page, label: str) -> None:
    page.get_by_role("tab", name=label, exact=True).click()
    page.wait_for_timeout(1400)


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--force-color-profile=srgb"])
        ctx = browser.new_context(viewport=VIEWPORT, device_scale_factor=2)
        ctx.add_init_script("window.localStorage.setItem('ad.theme','dark')")
        page = ctx.new_page()
        page.goto(BASE, wait_until="networkidle")
        page.wait_for_timeout(2600)  # Plotly + Orb settle

        _tab(page, "Overview")
        page.screenshot(path=str(OUT / "30_fe_overview_dark.png"), full_page=True)

        _tab(page, "Alerts")
        page.screenshot(path=str(OUT / "31_fe_alerts_dark.png"))  # viewport crop

        _tab(page, "Manual scoring")
        try:
            page.get_by_role("button", name="Score flow").click()
            page.wait_for_timeout(1600)
        except Exception as exc:  # noqa: BLE001
            print(f"[!] manual score skipped: {exc}")
        page.screenshot(path=str(OUT / "32_fe_manual_dark.png"), full_page=True)

        _tab(page, "Request examples")
        page.wait_for_timeout(700)
        page.screenshot(path=str(OUT / "33_fe_examples_dark.png"), full_page=True)

        browser.close()
    print("[+] Dark-theme screenshots written to", OUT)


if __name__ == "__main__":
    main()
