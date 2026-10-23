// B14j: sign in as each demo business from the login page and read every dashboard.
// node demo-businesses.cjs <playwright-core> <out-dir> <chrome-exe> [business names…]
const { chromium } = require(process.argv[2]);
const OUT = process.argv[3], BASE = "https://rivallens-eight.vercel.app";
const NAMES = process.argv.slice(5).length ? process.argv.slice(5) : ["Stride & Co.", "Kesar Bakehouse", "StackNest", "QuickKart"];
const flat = (s, n = 500) => s.replace(/\s+/g, " ").slice(0, n);
(async () => {
  const browser = await chromium.launch({ executablePath: process.argv[4] });
  for (const name of NAMES) {
    const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 } });
    const page = await ctx.newPage();
    page.setDefaultTimeout(60000);
    const tag = name.split(/\W/)[0].toLowerCase();
    try {
      await page.goto(`${BASE}/login`);
      await page.getByRole("button", { name: new RegExp(`^${name.replace(/[.&]/g, "\\$&")}`) }).click();
      await page.locator("[data-screen=S-21]").waitFor();
      await page.waitForTimeout(2500);
      console.log(`\n== ${name}\nOVERVIEW:`, flat(await page.locator("[data-screen=S-21]").innerText(), 700));
      await page.screenshot({ path: `${OUT}/b14j-${tag}-overview.png`, fullPage: true });
      for (const [nav, screen, len] of [["Product", "S-22", 500], ["Money", "S-24", 700], ["Market", "S-09", 700], ["Customers", "S-26", 500]]) {
        await page.locator("nav[aria-label=Dashboards]").getByRole("link", { name: nav, exact: true }).click();
        await page.locator(`[data-screen=${screen}]`).waitFor();
        await page.waitForTimeout(3500);
        console.log(`${nav.toUpperCase()}:`, flat(await page.locator(`[data-screen=${screen}]`).innerText(), len));
        await page.screenshot({ path: `${OUT}/b14j-${tag}-${nav.toLowerCase()}.png`, fullPage: true });
      }
      await page.locator("nav[aria-label=Dashboards]").getByRole("link", { name: "Product", exact: true }).click();
      await page.locator("[data-screen=S-22] a[href*='product-detail']").first().click();
      await page.locator("[data-screen=S-23]").waitFor();
      await page.locator("[data-testid=product-sim] table, [data-testid=product-sim] p.mt-2").first().waitFor({ timeout: 90000 }).catch(() => {});
      await page.locator("[data-testid=segment] [aria-busy]").waitFor({ state: "detached", timeout: 120000 }).catch(() => {});
      console.log("PRODUCT DETAIL:", flat(await page.locator("[data-screen=S-23]").innerText(), 900));
      await page.screenshot({ path: `${OUT}/b14j-${tag}-product-detail.png`, fullPage: true });
    } catch (e) {
      console.log(name, "FAIL", e.message.split("\n")[0]);
      await page.screenshot({ path: `${OUT}/b14j-${tag}-fail.png`, fullPage: true });
    }
    await ctx.close();
  }
  await browser.close();
})();
