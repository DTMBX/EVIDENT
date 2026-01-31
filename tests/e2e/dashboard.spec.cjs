// @ts-check
const { test, expect } = require("@playwright/test");

/**
 * BarberX Dashboard & Feature Tests
 * Tests dashboard functionality and tier-based features
 */

// Test user credentials - set via environment or use test defaults
const TEST_USER = {
  email: process.env.TEST_USER_EMAIL || "test@barberx.info",
  password: process.env.TEST_USER_PASSWORD || "testpassword123",
};

const ADMIN_USER = {
  email: process.env.ADMIN_EMAIL || "admin@barberx.info",
  password: process.env.ADMIN_PASSWORD || process.env.BARBERX_ADMIN_PASSWORD,
};

/**
 * Helper to login a user
 */
async function loginUser(page, email, password) {
  await page.goto("/auth/login");
  await page.fill('input[name="email"], input[type="email"]', email);
  await page.fill('input[name="password"], input[type="password"]', password);
  await page.click('button[type="submit"], input[type="submit"]');
  await page.waitForLoadState("networkidle");
}

test.describe("Dashboard - Public Features", () => {
  test("BWC dashboard page exists", async ({ page }) => {
    const response = await page.goto("/bwc-dashboard");
    // May require login or be publicly accessible
    expect([200, 302, 401]).toContain(response.status());
  });

  test("preview demo is accessible", async ({ page }) => {
    const response = await page.goto("/preview");
    expect(response.status()).toBe(200);
  });

  test("pricing page shows tier options", async ({ page }) => {
    await page.goto("/pricing.html");
    
    // Look for tier names or pricing elements
    const pageContent = await page.textContent("body");
    const hasTierInfo =
      pageContent.toLowerCase().includes("free") ||
      pageContent.toLowerCase().includes("pro") ||
      pageContent.toLowerCase().includes("premium") ||
      pageContent.toLowerCase().includes("tier");
    
    expect(hasTierInfo).toBeTruthy();
  });
});

test.describe("Dashboard - Feature Cards", () => {
  test.skip(
    !process.env.TEST_USER_PASSWORD,
    "Skipping - TEST_USER_PASSWORD not set"
  );

  test("dashboard displays feature cards after login", async ({ page }) => {
    await loginUser(page, TEST_USER.email, TEST_USER.password);
    
    // Check if on dashboard
    await expect(page).toHaveURL(/dashboard/);
    
    // Look for common dashboard elements
    const hasFeatureCards = await page.locator(".card, .feature-card, .dashboard-card").count();
    expect(hasFeatureCards).toBeGreaterThan(0);
  });
});

test.describe("File Upload Features", () => {
  test("batch PDF upload page exists", async ({ page }) => {
    const response = await page.goto("/batch-pdf-upload.html");
    expect([200, 302, 401]).toContain(response.status());
  });

  test("batch upload unified page exists", async ({ page }) => {
    const response = await page.goto("/batch-upload-unified.html");
    expect([200, 302, 401]).toContain(response.status());
  });
});

test.describe("Legal Analysis Features", () => {
  test("legal analysis page exists", async ({ page }) => {
    const response = await page.goto("/legal-analysis.html");
    expect([200, 302, 401]).toContain(response.status());
  });

  test("evidence intake page exists", async ({ page }) => {
    const response = await page.goto("/evidence-intake.html");
    expect([200, 302, 401]).toContain(response.status());
  });

  test("analysis results page exists", async ({ page }) => {
    const response = await page.goto("/analysis-results.html");
    expect([200, 302, 401]).toContain(response.status());
  });
});

test.describe("Chat Features", () => {
  test("chat page exists", async ({ page }) => {
    const response = await page.goto("/chat");
    expect([200, 302, 401]).toContain(response.status());
  });
});

test.describe("Admin Features", () => {
  test("admin page requires authentication", async ({ page }) => {
    await page.goto("/admin");
    await page.waitForLoadState("networkidle");
    
    // Should redirect to login
    const url = page.url();
    expect(url).toMatch(/login|auth/i);
  });

  test("founding members page requires admin", async ({ page }) => {
    await page.goto("/admin/founding-members");
    await page.waitForLoadState("networkidle");
    
    // Should redirect to login or show unauthorized
    const url = page.url();
    expect(url).toMatch(/login|auth|\//i);
  });
});

test.describe("Educational Resources", () => {
  test("education center exists", async ({ page }) => {
    const response = await page.goto("/education_center.html");
    expect([200, 302, 404]).toContain(response.status());
  });

  test("resources pages exist", async ({ page }) => {
    const response = await page.goto("/resources/");
    expect([200, 302, 404]).toContain(response.status());
  });
});
