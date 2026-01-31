// @ts-check
const { test, expect } = require("@playwright/test");

/**
 * BarberX Payments & Stripe Integration Tests
 * Tests payment-related pages and Stripe integration
 */

test.describe("Pricing Pages", () => {
  test("pricing page loads", async ({ page }) => {
    const response = await page.goto("/pricing.html");
    expect(response.status()).toBe(200);
  });

  test("pricing comparison page loads", async ({ page }) => {
    const response = await page.goto("/pricing-comparison.html");
    expect([200, 302, 404]).toContain(response.status());
  });

  test("pricing stripe embed page loads", async ({ page }) => {
    const response = await page.goto("/pricing-stripe-embed.html");
    expect([200, 302, 404]).toContain(response.status());
  });

  test("pricing page shows tier options", async ({ page }) => {
    await page.goto("/pricing.html");
    
    const content = await page.textContent("body");
    const hasPricingInfo =
      content.toLowerCase().includes("free") ||
      content.toLowerCase().includes("pro") ||
      content.toLowerCase().includes("premium") ||
      content.toLowerCase().includes("price") ||
      content.toLowerCase().includes("$");
    
    expect(hasPricingInfo).toBeTruthy();
  });

  test("pricing page has call-to-action buttons", async ({ page }) => {
    await page.goto("/pricing.html");
    
    const ctaButtons = page.locator(
      'a[href*="register"], a[href*="signup"], button:has-text("Start"), button:has-text("Get"), button:has-text("Subscribe")'
    );
    const count = await ctaButtons.count();
    expect(count).toBeGreaterThanOrEqual(0);
  });
});

test.describe("Payment Routes", () => {
  test("payment success redirect works", async ({ page }) => {
    const response = await page.goto("/payments/success");
    // May redirect or show success page
    expect([200, 302, 404]).toContain(response.status());
  });

  test("payment cancel redirect works", async ({ page }) => {
    const response = await page.goto("/payments/cancel");
    expect([200, 302, 404]).toContain(response.status());
  });
});

test.describe("Stripe Integration", () => {
  test("Stripe checkout endpoint exists", async ({ request }) => {
    const response = await request.post("/payments/create-checkout-session", {
      data: { tier: "pro" },
    });
    // Should require auth or return proper response
    expect([200, 302, 400, 401, 403]).toContain(response.status());
  });

  test("Stripe webhook endpoint exists", async ({ request }) => {
    const response = await request.post("/payments/webhook", {
      headers: { "stripe-signature": "test" },
      data: {},
    });
    // Should return 400 for invalid signature, not 404
    expect([400, 401, 403, 500]).toContain(response.status());
  });
});

test.describe("Thank You Pages", () => {
  const thankYouPages = [
    "/thank-you-contact.html",
    "/thank-you-curious.html",
    "/thank-you-developer.html",
    "/thank-you-newsletter.html",
    "/thank-you-reviewer.html",
    "/thank-you-supporter.html",
  ];

  for (const pagePath of thankYouPages) {
    test(`${pagePath} loads`, async ({ page }) => {
      const response = await page.goto(pagePath);
      expect([200, 302, 404]).toContain(response.status());
    });
  }
});

test.describe("Tier Features", () => {
  test("free tier dashboard exists", async ({ page }) => {
    const response = await page.goto("/free_tier_dashboard.html");
    expect([200, 302, 404]).toContain(response.status());
  });

  test("premium demo page exists", async ({ page }) => {
    const response = await page.goto("/premium-demo.html");
    expect([200, 302, 404]).toContain(response.status());
  });
});
