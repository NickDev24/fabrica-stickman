import { test, expect } from "@playwright/test";
test("onboarding shows office and panel", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText(/Fábrica Autónoma|Autonomous Factory/)).toBeVisible();
  await expect(page.getByLabel("panel")).toBeVisible();
});
