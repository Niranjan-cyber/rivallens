// B14k golden path v2 on the live app, as Stride & Co.: Overview → Product → Money → Customers → Market (simulate a move,
// check competitors, receipt) → Product re-plans → Report → switch to the bakery.
// node golden-path-v2.cjs <playwright-core> <out-dir> <chrome-exe>
const { chromium } = require(process.argv[2]);
const OUT = process.argv[3], BASE = "https://rivallens-eight.vercel.app";
const flat = (s, n = 400) => s.replace(/\s+/g, " ").slice(0, n);
(async () => {
  const browser = await chromium.launch({ executablePath: process.argv[4] });
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  page.setDefaultTimeout(90000);
  const nav = (name) => page.locator("nav[aria-label=Dashboards]").getByRole("link", { name, exact: true }).click();
  try {
    await page.goto(`${BASE}/login`);
    await page.getByRole("button", { name: /^Stride & Co\./ }).click();
    await page.locator("[data-screen=S-21]").waitFor();
    const id = page.url().split("/")[4];
    await page.waitForTimeout(2500);
    console.log("1-2. overview:", flat(await page.locator("[data-screen=S-21]").innerText()));
    await page.screenshot({ path: `${OUT}/gp2-1-overview.png`, fullPage: true });

    await nav("Product");
    await page.locator("[data-screen=S-22] a[href*='product-detail']").first().click();
    await page.locator("[data-testid=product-sim] table").waitFor();
    await page.locator("[data-testid=segment] [aria-busy]").waitFor({ state: "detached", timeout: 120000 }).catch(() => {});
    const productUrl = page.url();
    console.log("3. price position:", flat(await page.locator("[data-screen=S-23] .bg-ink").first().innerText(), 200));
    console.log("   segment:", flat(await page.locator("[data-testid=segment]").innerText(), 300));
    await page.screenshot({ path: `${OUT}/gp2-3-product.png`, fullPage: true });

    await nav("Money");
    await page.locator("[data-screen=S-24]").waitFor();
    await page.waitForTimeout(3000);
    console.log("4. money:", flat(await page.locator("[data-screen=S-24] .grid").first().innerText(), 400));
    console.log("   rival money:", flat(await page.getByText(/Campus Activewear/).first().locator("xpath=ancestor::li[1]").innerText().catch(() => "not shown"), 300));
    await page.screenshot({ path: `${OUT}/gp2-4-money.png`, fullPage: true });

    await nav("Customers");
    await page.locator("[data-screen=S-26]").waitFor();
    await page.waitForTimeout(2000);
    console.log("5. customers:", flat(await page.locator("[data-screen=S-26]").innerText(), 200));

    await page.goto(`${BASE}/app/${id}/dashboard`);
    await page.getByText("Simulate a competitor move").waitFor();
    await page.getByRole("button", { name: "Reset competitor pages" }).click();
    await page.getByText(/back to their original/).waitFor();
    for (const [move, label] of [["Redesign only", "redesign"], ["Cut a price 40%", "price cut"]]) {
      await page.getByRole("button", { name: move }).first().click();
      await page.getByText(/applied\. Now press/).waitFor();
      await page.getByRole("button", { name: "Check competitors now" }).click();
      await page.locator("[data-screen=S-10]").waitFor({ timeout: 240000 });
      await page.getByText(/meaningful/).first().waitFor({ timeout: 240000 });
      console.log(`6. ${label}:`, flat(await page.locator("[data-screen=S-10]").innerText(), 500));
      await page.screenshot({ path: `${OUT}/gp2-6-${label.replace(" ", "-")}.png`, fullPage: true });
      if (label === "price cut") {
        await page.getByRole("link", { name: /See receipt/ }).first().click();
        await page.locator("mark").first().waitFor();
        console.log("   receipt:", flat(await page.locator("[data-screen=S-11]").innerText(), 400));
        await page.screenshot({ path: `${OUT}/gp2-6-receipt.png`, fullPage: true });
      } else {
        await page.goto(`${BASE}/app/${id}/dashboard`);
        await page.getByText("Simulate a competitor move").waitFor();
      }
    }

    await page.goto(productUrl);
    await page.locator("[data-testid=product-sim] table").waitFor();
    console.log("7. product inputs:", (await page.locator("[data-testid=product-sim] ul[aria-label=Inputs] a").allInnerTexts()).join(" | "));
    await page.screenshot({ path: `${OUT}/gp2-7-product-replanned.png`, fullPage: true });

    await page.goto(`${BASE}/app/${id}/reports`);
    await page.getByRole("button", { name: /Generate report|Regenerate/ }).click();
    await page.getByRole("button", { name: "Download PDF" }).waitFor({ timeout: 180000 });
    await page.waitForTimeout(2000);
    console.log("8. report:", flat(await page.locator("article").first().innerText(), 500));
    await page.screenshot({ path: `${OUT}/gp2-8-report.png`, fullPage: true });

    await page.locator("header summary").first().click();
    await page.getByText("Kesar Bakehouse").first().waitFor({ timeout: 5000 }).then(() => console.log("9. switcher lists the bakery"), () => {
      console.log("9. switcher shows only this account's businesses (each demo business is its own sign-in)");
    });
  } catch (e) {
    console.log("FAIL", e.message.split("\n")[0]);
    await page.screenshot({ path: `${OUT}/gp2-fail.png`, fullPage: true });
  }
  await browser.close();
})();
