"""Screenshot the styled HTML C4 diagrams, replacing the matplotlib versions.

Renders docs/c4_diagrams.html (dark background + grid + glass nodes) and writes
each .frame element to docs/screenshots/21_c4_context.png and 22_c4_container.png.

    python -m scripts.capture_c4
"""
from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "docs" / "c4_diagrams.html").as_uri()
OUT = ROOT / "docs" / "screenshots"


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--force-color-profile=srgb"])
        page = browser.new_context(device_scale_factor=2).new_page()
        page.goto(HTML, wait_until="networkidle")
        page.wait_for_timeout(1200)  # let the web font load
        page.locator("#context").screenshot(path=str(OUT / "21_c4_context.png"))
        page.locator("#container").screenshot(path=str(OUT / "22_c4_container.png"))
        browser.close()
    print("[+] Wrote styled C4 diagrams to", OUT)


if __name__ == "__main__":
    main()
