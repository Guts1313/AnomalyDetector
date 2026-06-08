"""Screenshot each epic of the styled user-stories HTML for the TDD.

    python -m scripts.capture_user_stories
"""
from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "additional-docs" / "user_stories.html").as_uri()
OUT = ROOT / "additional-docs" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)

EPICS = ["epic-a", "epic-b", "epic-c", "epic-d", "epic-e", "epic-f"]


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--force-color-profile=srgb"])
        page = browser.new_context(device_scale_factor=2).new_page()
        page.goto(HTML, wait_until="networkidle")
        page.wait_for_timeout(1200)  # web font
        for eid in EPICS:
            page.locator(f"#{eid}").screenshot(path=str(OUT / f"us_{eid.replace('-', '_')}.png"))
        browser.close()
    print("[+] User-story epic screenshots written to", OUT)


if __name__ == "__main__":
    main()
