import path from "node:path"
import { expect, type Page, test } from "@playwright/test"

const fixtures = path.join(import.meta.dirname, "fixtures")

async function createBrand(page: Page, name: string) {
  await page.goto("/")
  await page.getByRole("button", { name: "New brand" }).first().click()
  await page.locator("#brand-name").fill(name)
  await page.getByRole("button", { name: "Create brand" }).click()
  await expect(page.getByText(`Working in ${name}.`)).toBeVisible()
}

test("complete MVP workflow with fake providers", async ({ page }) => {
  page.on("dialog", (dialog) => dialog.accept())
  const brandName = `E2E Atelier ${Date.now()}`

  await createBrand(page, brandName)

  // Brand import
  await page.goto("/brand/import")
  await page
    .locator("#brand-files")
    .setInputFiles([
      path.join(fixtures, "brand-book.pdf"),
      path.join(fixtures, "brand-hero.png"),
      path.join(fixtures, "brand-logo.svg"),
      path.join(fixtures, "serif.ttf"),
    ])
  await page.getByRole("button", { name: "Upload and process" }).click()
  await page.waitForURL(/\/brand\/imports\//)
  await expect(page.getByText("Import detail")).toBeVisible()

  // Brand intelligence and activation
  await page.getByRole("button", { name: "Analyze brand" }).click()
  await page.waitForURL(/\/brand\/profile/)
  await page.getByRole("button", { name: "Activate" }).first().click()
  await expect(page.getByText(/v1 · active/)).toBeVisible()

  // Virtual model
  await page.goto("/models/new")
  await page.locator("#model-name").fill("Aria")
  await page.getByRole("button", { name: "Create model" }).click()
  await page.waitForURL(/\/models\//)
  await page.getByRole("button", { name: "Generate previews" }).click()
  await expect(page.getByText("Canonical").first()).toBeVisible({
    timeout: 20000,
  })

  // Product
  await page.goto("/products/new")
  await page.locator("#product-name").fill("E2E Signet Ring")
  await page.getByRole("button", { name: "Create product" }).click()
  await page.waitForURL(/\/products\//)
  await page
    .locator("#source-image")
    .setInputFiles(path.join(fixtures, "brand-hero.png"))
  await page.getByRole("button", { name: "Upload", exact: true }).click()
  await expect(page.getByText("Primary")).toBeVisible()

  // Studio generation
  await page.goto("/studio")
  await page.locator("#product").click()
  await page.getByRole("option", { name: /E2E Signet Ring/ }).click()
  await page.getByRole("button", { name: "Generate image" }).click()
  await page.waitForURL(/\/studio\/generations\//)
  await expect(
    page.getByRole("button", { name: "Create content draft" }),
  ).toBeVisible({ timeout: 20000 })

  // Content draft and caption
  await page.getByRole("button", { name: "Create content draft" }).click()
  await page.waitForURL(/\/content\//)
  const contentUrl = page.url()
  await page.getByRole("button", { name: "Generate caption" }).click()
  await expect(page.locator("#caption")).not.toHaveValue("")
  await page.getByRole("button", { name: "Submit for approval" }).click()
  await page.getByRole("button", { name: "Approve" }).click()
  await expect(page.getByText(/Approved by Owner/)).toBeVisible()

  // Instagram connection
  await page.goto("/social")
  await page.locator("#account-id").fill("17841400000000000")
  await page.locator("#account-name").fill("e2e.atelier")
  await page.getByRole("button", { name: "Connect Instagram" }).click()
  await expect(page.getByText("connected", { exact: true })).toBeVisible()

  // Publish
  await page.goto(contentUrl)
  await page.getByRole("button", { name: "Publish to Instagram" }).click()
  await expect(page.getByText("Published successfully.")).toBeVisible({
    timeout: 20000,
  })
})

test("real model requires consent before default", async ({ page }) => {
  const brandName = `E2E Real ${Date.now()}`
  await createBrand(page, brandName)

  await page.goto("/models/new")
  await page.locator("#model-type").click()
  await page.getByRole("option", { name: "Real model" }).click()
  await page.locator("#model-name").fill("Noor")
  await page.getByRole("button", { name: "Create model" }).click()
  await page.waitForURL(/\/models\//)

  await page
    .locator("#reference-file")
    .setInputFiles(path.join(fixtures, "brand-hero.png"))
  await page.getByRole("button", { name: "Upload reference" }).click()
  await expect(page.getByText("Canonical").first()).toBeVisible()

  await expect(page.getByRole("button", { name: "Set default" })).toBeDisabled()
  await page.locator("#consent-check").click()
  await page.getByRole("button", { name: "Record consent" }).click()
  await expect(page.getByText("Consent recorded").first()).toBeVisible()
  await page.getByRole("button", { name: "Set default" }).click()
  await expect(page.getByText("Default", { exact: true })).toBeVisible()
})
