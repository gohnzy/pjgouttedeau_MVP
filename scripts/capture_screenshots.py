"""Capture les pages locales FastAPI et Streamlit pour le livrable."""
from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "docs" / "screenshots"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 1000})

        response = page.goto("http://127.0.0.1:8000/docs", wait_until="networkidle")
        if response is None or response.status != 200:
            raise RuntimeError("La page /docs n'a pas répondu en HTTP 200.")
        page.locator(".swagger-ui").wait_for(state="visible")
        page.screenshot(path=OUTPUT_DIR / "api-docs.png", full_page=True)

        response = page.goto("http://127.0.0.1:8501", wait_until="networkidle")
        if response is None or response.status != 200:
            raise RuntimeError("Streamlit n'a pas répondu en HTTP 200.")
        page.get_by_role("button", name="Estimer le risque").click()
        page.locator("[data-testid='stPlotlyChart']").first.wait_for(state="visible")
        page.screenshot(path=OUTPUT_DIR / "streamlit-desktop.png", full_page=True)

        page.set_viewport_size({"width": 390, "height": 844})
        page.reload(wait_until="networkidle")
        page.get_by_role("button", name="Estimer le risque").click()
        page.locator("[data-testid='stPlotlyChart']").first.wait_for(state="visible")
        page.screenshot(path=OUTPUT_DIR / "streamlit-mobile.png", full_page=True)
        browser.close()
    print(f"Captures créées dans {OUTPUT_DIR}")


if __name__ == "__main__":
    main()