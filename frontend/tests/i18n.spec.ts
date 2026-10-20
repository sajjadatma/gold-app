import { expect, test } from "@playwright/test"

test("switches to Farsi, applies RTL, and persists the choice", async ({
  page,
}) => {
  await page.goto("/")
  await expect(page.getByRole("heading", { name: /Hi,/ })).toBeVisible()

  await page.getByRole("button", { name: "Language" }).click()
  await page.getByRole("menuitem", { name: "فارسی" }).click()

  await expect(page.locator("html")).toHaveAttribute("dir", "rtl")
  await expect(page.locator("html")).toHaveAttribute("lang", "fa")
  await expect(page.getByRole("link", { name: "داشبورد" })).toBeVisible()
  await expect(page.getByRole("heading", { name: /سلام،/ })).toBeVisible()
  await page.evaluate(() => document.fonts.ready)
  const farsiFont = await page.evaluate(
    () => getComputedStyle(document.body).fontFamily,
  )
  expect(farsiFont).toContain("Vazirmatn")
  expect(
    await page.evaluate(() => document.fonts.check("16px Vazirmatn")),
  ).toBe(true)

  await page.reload()
  await expect(page.locator("html")).toHaveAttribute("dir", "rtl")
  await expect(page.getByRole("link", { name: "داشبورد" })).toBeVisible()

  await page.getByRole("link", { name: "ورود برند" }).click()
  await expect(
    page.getByRole("heading", { name: "ورود دارایی‌های برند" }),
  ).toBeVisible()
  await page.getByRole("link", { name: "شبکه اجتماعی" }).click()
  await expect(page.getByRole("heading", { name: "اینستاگرام" })).toBeVisible()
  await page.getByRole("link", { name: "تیم" }).click()
  await expect(page.getByRole("heading", { name: "تیم" })).toBeVisible()

  await page.getByRole("button", { name: "زبان" }).click()
  await page.getByRole("menuitem", { name: "English" }).click()
  await expect(page.locator("html")).toHaveAttribute("dir", "ltr")
  await expect(page.getByRole("link", { name: "Dashboard" })).toBeVisible()
  const englishFont = await page.evaluate(
    () => getComputedStyle(document.body).fontFamily,
  )
  expect(englishFont).not.toContain("Vazirmatn")
})
