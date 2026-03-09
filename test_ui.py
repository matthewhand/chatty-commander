import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1280, "height": 900})
        await page.goto('http://localhost:8100/configuration')
        await page.wait_for_timeout(2000)
        await page.screenshot(path='/home/matthewh/.gemini/antigravity/brain/d0e1a5cd-2959-4f8a-b531-3fce7b7a8b4d/theme_override_test.png')
        await browser.close()

asyncio.run(run())
