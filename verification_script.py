from playwright.sync_api import sync_playwright

def run_cuj(page):
    page.goto("http://localhost:8100/commands")
    page.wait_for_timeout(1000)

    # Click the refresh button to trigger any loading states
    page.get_by_role("button", name="Refresh Commands").click()
    page.wait_for_timeout(1000)

    # Hover over the Export JSON button
    export_btn = page.locator('button', has_text="Export JSON")
    export_btn.hover()
    page.wait_for_timeout(1000)

    # Take screenshot at the key moment showing the tooltip
    page.screenshot(path="verification.png")
    page.wait_for_timeout(1000)

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            record_video_dir="videos"
        )
        page = context.new_page()
        try:
            run_cuj(page)
        finally:
            context.close()
            browser.close()
