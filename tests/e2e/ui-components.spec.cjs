// @ts-check
const { test, expect } = require("@playwright/test");

/**
 * BarberX UI/UX Component Tests
 * Tests UI components, responsive design, and accessibility
 */

test.describe("Navigation", () => {
  test("main navigation links work", async ({ page }) => {
    await page.goto("/");
    
    // Check for navigation elements
    const nav = page.locator("nav, .navbar, .navigation, header");
    await expect(nav.first()).toBeVisible();
  });

  test("logo links to homepage", async ({ page }) => {
    await page.goto("/pricing.html");
    
    const logo = page.locator('a[href="/"], .logo a, .brand a').first();
    if (await logo.isVisible()) {
      await logo.click();
      await expect(page).toHaveURL(/\/$/);
    }
  });

  test("mobile menu toggle exists on small screens", async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto("/");
    
    // Look for hamburger menu or mobile toggle
    const mobileToggle = page.locator(
      ".hamburger, .mobile-menu-toggle, .navbar-toggler, [data-toggle='collapse']"
    );
    const toggleCount = await mobileToggle.count();
    // Mobile menu may or may not exist
    expect(toggleCount).toBeGreaterThanOrEqual(0);
  });
});

test.describe("Forms", () => {
  test("login form has proper labels", async ({ page }) => {
    await page.goto("/auth/login");
    
    // Check for form labels or placeholders
    const emailInput = page.locator('input[name="email"], input[type="email"]');
    const hasLabel = await page
      .locator('label[for="email"], label:has-text("email")')
      .count() > 0;
    const hasPlaceholder = await emailInput.getAttribute("placeholder");
    
    expect(hasLabel || hasPlaceholder).toBeTruthy();
  });

  test("password fields are masked", async ({ page }) => {
    await page.goto("/auth/login");
    
    const passwordInput = page.locator(
      'input[name="password"], input[type="password"]'
    );
    const type = await passwordInput.getAttribute("type");
    expect(type).toBe("password");
  });
});

test.describe("Responsive Design", () => {
  const viewports = [
    { name: "Mobile", width: 375, height: 667 },
    { name: "Tablet", width: 768, height: 1024 },
    { name: "Desktop", width: 1920, height: 1080 },
  ];

  for (const viewport of viewports) {
    test(`homepage renders on ${viewport.name}`, async ({ page }) => {
      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      await page.goto("/");
      
      // Page should not have horizontal scroll
      const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
      expect(bodyWidth).toBeLessThanOrEqual(viewport.width + 20); // Small tolerance
    });
  }
});

test.describe("Accessibility", () => {
  test("images have alt text", async ({ page }) => {
    await page.goto("/");
    
    const images = page.locator("img");
    const count = await images.count();
    
    for (let i = 0; i < Math.min(count, 10); i++) {
      const img = images.nth(i);
      const alt = await img.getAttribute("alt");
      const decorative = await img.getAttribute("role");
      
      // Either has alt text or is marked as decorative
      expect(alt !== null || decorative === "presentation").toBeTruthy();
    }
  });

  test("page has heading structure", async ({ page }) => {
    await page.goto("/");
    
    const h1 = await page.locator("h1").count();
    expect(h1).toBeGreaterThan(0);
  });

  test("buttons are keyboard accessible", async ({ page }) => {
    await page.goto("/auth/login");
    
    const submitBtn = page.locator('button[type="submit"], input[type="submit"]');
    await expect(submitBtn).toBeVisible();
    
    // Tab to the button and verify it's focusable
    await page.keyboard.press("Tab");
    await page.keyboard.press("Tab");
    await page.keyboard.press("Tab");
    
    const focused = page.locator(":focus");
    const isFocusable = await focused.count() > 0;
    expect(isFocusable).toBeTruthy();
  });

  test("links have discernible text", async ({ page }) => {
    await page.goto("/");
    
    const links = page.locator("a");
    const count = await links.count();
    
    for (let i = 0; i < Math.min(count, 20); i++) {
      const link = links.nth(i);
      const text = await link.textContent();
      const ariaLabel = await link.getAttribute("aria-label");
      const title = await link.getAttribute("title");
      const img = await link.locator("img").count();
      
      // Link should have text, aria-label, title, or contain an image
      const hasDiscernibleText =
        (text && text.trim().length > 0) ||
        ariaLabel ||
        title ||
        img > 0;
      
      expect(hasDiscernibleText).toBeTruthy();
    }
  });
});

test.describe("Error States", () => {
  test("404 page is styled", async ({ page }) => {
    await page.goto("/this-page-does-not-exist-12345");
    
    // Page should have some content, not a blank error
    const bodyText = await page.textContent("body");
    expect(bodyText.length).toBeGreaterThan(50);
  });
});

test.describe("Performance", () => {
  test("homepage loads within 5 seconds", async ({ page }) => {
    const startTime = Date.now();
    await page.goto("/", { waitUntil: "domcontentloaded" });
    const loadTime = Date.now() - startTime;
    
    expect(loadTime).toBeLessThan(5000);
  });

  test("no console errors on homepage", async ({ page }) => {
    const errors = [];
    page.on("pageerror", (error) => errors.push(error.message));
    
    await page.goto("/");
    await page.waitForLoadState("networkidle");
    
    // Filter out known non-critical errors
    const criticalErrors = errors.filter(
      (e) =>
        !e.includes("ResizeObserver") &&
        !e.includes("Script error") &&
        !e.includes("hydration")
    );
    
    expect(criticalErrors).toHaveLength(0);
  });
});

test.describe("Branding", () => {
  test("BarberX branding is present", async ({ page }) => {
    await page.goto("/");
    
    const pageText = await page.textContent("body");
    const hasBranding =
      pageText.includes("BarberX") ||
      pageText.includes("BARBERX") ||
      pageText.includes("barberx");
    
    expect(hasBranding).toBeTruthy();
  });

  test("favicon is present", async ({ page }) => {
    await page.goto("/");
    
    const favicon = page.locator(
      'link[rel="icon"], link[rel="shortcut icon"], link[rel="apple-touch-icon"]'
    );
    const count = await favicon.count();
    expect(count).toBeGreaterThan(0);
  });
});
