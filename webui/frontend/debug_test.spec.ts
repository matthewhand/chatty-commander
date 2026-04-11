import { test, expect } from "@playwright/test";

test("debug configuration link", async ({ page }) => {
    page.on('console', msg => console.log(`BROWSER LOG: ${msg.text()}`));
    await page.goto("/");
    await page.waitForTimeout(2000);

    // Dump page HTML to see what's rendering
    const html = await page.content();
    console.log("HTML length:", html.length);
    console.log(html.substring(0, 1000));

    const configLinks = await page.locator("text=Configuration").count();
    console.log(`Found ${configLinks} elements matching 'text=Configuration'`);
});
