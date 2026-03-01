import asyncio
import os
from playwright.async_api import async_playwright

async def verify_websocket_connection():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        # Navigate to the dashboard - use env var for port to match dynamic WebSocket URL behavior
        port = os.environ.get('WEBUI_PORT', '8100')
        await page.goto(f"http://localhost:{port}/")

        # Wait for dashboard to load
        # Wait for "Dashboard" text to be visible
        await page.wait_for_selector('h2:has-text("Dashboard")', timeout=10000)

        # Wait for WebSocket connection indicator
        # We expect "Connected" which has class text-success
        # Use locator to target the element with specific text and class
        connected_indicator = page.locator('div.stat-value.text-success', has_text="Connected")
        await connected_indicator.wait_for(state="visible", timeout=10000)

        # Take screenshot
        await page.screenshot(path="verification/websocket_connected.png")
        print("Screenshot saved to verification/websocket_connected.png")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(verify_websocket_connection())
