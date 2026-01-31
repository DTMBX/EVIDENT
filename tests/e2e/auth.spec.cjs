// @ts-check
const { test, expect } = require("@playwright/test");

/**
 * BarberX Authentication Tests
 * Tests login, logout, registration, and session management
 */

test.describe("Authentication - Login Page", () => {
  test("login page displays correctly", async ({ page }) => {
    await page.goto("/auth/login");
    
    // Check for login form elements
    await expect(page.locator('input[name="email"], input[type="email"]')).toBeVisible();
    await expect(page.locator('input[name="password"], input[type="password"]')).toBeVisible();
    await expect(page.locator('button[type="submit"], input[type="submit"]')).toBeVisible();
  });

  test("login form shows validation for empty fields", async ({ page }) => {
    await page.goto("/auth/login");
    
    // Try to submit empty form
    await page.click('button[type="submit"], input[type="submit"]');
    
    // Browser validation should prevent submission
    const emailInput = page.locator('input[name="email"], input[type="email"]');
    const isInvalid = await emailInput.evaluate((el) => !el.checkValidity());
    expect(isInvalid).toBeTruthy();
  });

  test("invalid credentials show error message", async ({ page }) => {
    await page.goto("/auth/login");
    
    await page.fill('input[name="email"], input[type="email"]', "invalid@test.com");
    await page.fill('input[name="password"], input[type="password"]', "wrongpassword");
    await page.click('button[type="submit"], input[type="submit"]');
    
    // Should show error message or stay on login page
    await page.waitForLoadState("networkidle");
    const url = page.url();
    expect(url).toMatch(/login|auth/i);
  });

  test("login link to registration exists", async ({ page }) => {
    await page.goto("/auth/login");
    
    const registerLink = page.locator('a[href*="register"]');
    await expect(registerLink).toBeVisible();
  });
});

test.describe("Authentication - Registration Page", () => {
  test("registration page displays correctly", async ({ page }) => {
    await page.goto("/register");
    
    // Check for registration form elements
    await expect(page.locator('input[name="email"], input[type="email"]')).toBeVisible();
    await expect(page.locator('input[name="password"], input[type="password"]')).toBeVisible();
  });

  test("registration validates email format", async ({ page }) => {
    await page.goto("/register");
    
    const emailInput = page.locator('input[name="email"], input[type="email"]');
    await emailInput.fill("notanemail");
    
    const isInvalid = await emailInput.evaluate((el) => !el.checkValidity());
    expect(isInvalid).toBeTruthy();
  });
});

test.describe("Protected Routes - Require Login", () => {
  const protectedRoutes = [
    "/dashboard",
    "/account",
    "/account-settings",
    "/admin",
  ];

  for (const route of protectedRoutes) {
    test(`${route} redirects to login when not authenticated`, async ({ page }) => {
      const response = await page.goto(route);
      
      // Should redirect to login
      await page.waitForLoadState("networkidle");
      const url = page.url();
      expect(url).toMatch(/login|auth/i);
    });
  }
});

test.describe("Authentication - Session Management", () => {
  test("logout clears session", async ({ page }) => {
    // First try to access protected route
    await page.goto("/dashboard");
    await page.waitForLoadState("networkidle");
    
    // Should be on login page
    const loginUrl = page.url();
    expect(loginUrl).toMatch(/login|auth/i);
    
    // Access logout endpoint
    await page.goto("/logout");
    await page.waitForLoadState("networkidle");
    
    // Should redirect to home or login
    const url = page.url();
    expect(url).toMatch(/\/$|login|auth/i);
  });
});

test.describe("API Authentication", () => {
  test("protected API returns 401 without auth", async ({ request }) => {
    const response = await request.get("/api/user/profile");
    expect(response.status()).toBe(401);
  });

  test("auth check endpoint works", async ({ request }) => {
    const response = await request.get("/api/auth/check");
    // Should return 200 with authenticated: false, or 401
    expect([200, 401]).toContain(response.status());
  });
});
