// @ts-check
const { test, expect } = require("@playwright/test");

/**
 * BarberX Site Health & Core Functionality Tests
 * Tests all public pages and core site features
 */

test.describe("Site Health Checks", () => {
  test("homepage loads successfully", async ({ page }) => {
    const response = await page.goto("/");
    expect(response.status()).toBe(200);
    await expect(page).toHaveTitle(/BarberX/i);
  });

  test("health endpoint returns OK", async ({ page }) => {
    const response = await page.goto("/health");
    expect(response.status()).toBe(200);
    const content = await page.textContent("body");
    expect(content).toContain("ok");
  });

  test("detailed health check returns system status", async ({ page }) => {
    const response = await page.goto("/health-detailed");
    // May return 500 if some services are unavailable
    expect([200, 500]).toContain(response.status());
    if (response.status() === 200) {
      const json = await page.evaluate(() =>
        JSON.parse(document.body.textContent),
      );
      expect(json).toHaveProperty("status");
    }
  });

  test("404 page displays for invalid routes", async ({ page }) => {
    const response = await page.goto("/nonexistent-page-xyz");
    expect(response.status()).toBe(404);
  });
});

test.describe("Public Pages Load", () => {
  const publicPages = [
    { path: "/", name: "Homepage" },
    { path: "/auth/login", name: "Login" },
    { path: "/register", name: "Register" },
    { path: "/pricing", name: "Pricing" },
    { path: "/mission", name: "Mission" },
    { path: "/preview", name: "Preview" },
  ];

  for (const pageInfo of publicPages) {
    test(`${pageInfo.name} page loads (${pageInfo.path})`, async ({ page }) => {
      const response = await page.goto(pageInfo.path);
      // Allow 200 or 302 (redirect to login for some pages)
      expect([200, 302]).toContain(response.status());
    });
  }
});

test.describe("Static Assets", () => {
  test("CSS files load correctly", async ({ page }) => {
    await page.goto("/");
    // Check for inline styles or linked stylesheets
    const hasStyles = await page.evaluate(() => {
      const links = document.querySelectorAll('link[rel="stylesheet"]');
      const styleElements = document.querySelectorAll("style");
      return links.length > 0 || styleElements.length > 0;
    });
    expect(hasStyles).toBeTruthy();
  });

  test("JavaScript files load correctly", async ({ page }) => {
    await page.goto("/");
    // Check for no JS errors in console
    const errors = [];
    page.on("pageerror", (error) => errors.push(error.message));
    await page.waitForLoadState("networkidle");
    expect(errors.filter((e) => !e.includes("ResizeObserver"))).toHaveLength(0);
  });
});

test.describe("API Endpoints Health", () => {
  test("rate limit status endpoint", async ({ request }) => {
    const response = await request.get("/api/rate-limit/status");
    expect(response.ok()).toBeTruthy();
    const json = await response.json();
    // Response is wrapped in message object
    expect(json).toHaveProperty("message");
    expect(json.message).toHaveProperty("limit_per_minute");
    expect(json.message).toHaveProperty("remaining");
  });
});
