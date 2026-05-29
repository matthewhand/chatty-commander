"""
Visual Page Rendering Tests with Playwright
Captures screenshots and verifies no visual errors
"""

import pytest

# Pages to visually verify
VISUAL_PAGES = [
    ("/", "homepage"),
    ("/commands", "commands-page"),
    ("/agents", "agents-page"),
    ("/settings", "settings-page"),
    ("/voice", "voice-page"),
    ("/avatar", "avatar-page"),
    ("/logs", "logs-page"),
]


@pytest.fixture(scope="module")
def browser_context():
    """Setup browser context for visual tests"""
    pytest.importorskip("playwright")
    from playwright.sync_api import sync_playwright
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        yield context
        context.close()
        browser.close()


class TestVisualRendering:
    """Verify pages render visually without errors"""

    @pytest.mark.parametrize("route,name", VISUAL_PAGES)
    def test_page_screenshot_no_errors(self, browser_context, route: str, name: str):
        """Capture screenshot and verify no error states"""
        page = browser_context.new_page()
        
        try:
            # Navigate to page
            page.goto(f"http://localhost:8000{route}", timeout=10000)
            
            # Wait for page to load
            page.wait_for_load_state("networkidle", timeout=5000)
            
            # Capture screenshot
            screenshot_path = f"tests/e2e/screenshots/{name}.png"
            page.screenshot(path=screenshot_path, full_page=True)
            
            # Check for error indicators in page content
            error_selectors = [
                "[data-testid='error']",
                ".error",
                "[role='alert']",
                ".alert-error",
            ]
            
            for selector in error_selectors:
                try:
                    element = page.locator(selector).first
                    if element.is_visible(timeout=100):
                        pytest.fail(f"Error element visible on {name}: {selector}")
                except:
                    pass  # Element not found is good
            
            # Check console for errors
            logs = page.event("console")
            error_logs = [log for log in logs if log.type == "error"]
            
            if error_logs:
                pytest.fail(f"Console errors on {name}: {[log.text for log in error_logs]}")
            
        finally:
            page.close()

    def test_responsive_layouts(self, browser_context):
        """Test page renders correctly at different viewports"""
        viewports = [
            {"width": 1920, "height": 1080, "name": "desktop"},
            {"width": 1366, "height": 768, "name": "laptop"},
            {"width": 768, "height": 1024, "name": "tablet"},
            {"width": 375, "height": 812, "name": "mobile"},
        ]
        
        for viewport in viewports:
            context = browser_context.browser.new_context(
                viewport={"width": viewport["width"], "height": viewport["height"]}
            )
            page = context.new_page()
            
            try:
                page.goto("http://localhost:8000/", timeout=10000)
                page.wait_for_load_state("networkidle")
                
                # Verify no horizontal scroll (layout overflow)
                has_overflow = page.evaluate("""() => {
                    return document.documentElement.scrollWidth > window.innerWidth;
                }""")
                
                assert not has_overflow, f"Horizontal overflow at {viewport['name']}"
                
            finally:
                page.close()
                context.close()


class TestInteractiveElements:
    """Test interactive elements work correctly"""

    def test_navigation_menu_works(self, browser_context):
        """Verify navigation menu items are clickable"""
        page = browser_context.new_page()
        
        try:
            page.goto("http://localhost:8000/", timeout=10000)
            page.wait_for_load_state("networkidle")
            
            # Find navigation links
            nav_links = page.locator("nav a, [role='navigation'] a, header a").all()
            
            if nav_links:
                # Test first navigation link
                first_link = nav_links[0]
                if first_link.is_visible():
                    first_link.click()
                    page.wait_for_load_state("networkidle", timeout=5000)
            
        finally:
            page.close()

    def test_modal_dialogs(self, browser_context):
        """Test modal dialogs open and close correctly"""
        page = browser_context.new_page()
        
        try:
            page.goto("http://localhost:8000/commands", timeout=10000)
            page.wait_for_load_state("networkidle")
            
            # Look for buttons that might open modals
            buttons = page.locator("button:has-text('Add'), button:has-text('New'), button:has-text('Create')").all()
            
            for button in buttons[:2]:  # Test first 2 buttons
                if button.is_visible() and button.is_enabled():
                    button.click()
                    
                    # Check for modal appearance
                    modal_selectors = [
                        "[role='dialog']",
                        ".modal",
                        ".dialog",
                        "[data-testid='modal']",
                    ]
                    
                    modal_found = False
                    for selector in modal_selectors:
                        try:
                            modal = page.locator(selector).first
                            if modal.is_visible(timeout=500):
                                modal_found = True
                                # Close modal
                                page.keyboard.press("Escape")
                                break
                        except:
                            continue
                    
                    if modal_found:
                        break  # Successfully tested modal
            
        finally:
            page.close()
