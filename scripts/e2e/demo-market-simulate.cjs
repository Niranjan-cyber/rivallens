const { chromium } = require(process.argv[2]);
const OUT = process.argv[3], BASE = "https://rivallens-eight.vercel.app";
(async () => {
  const browser = await chromium.launch({ executablePath: process.argv[4] });
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  page.setDefaultTimeout(120000);
  try {
    await page.goto(`${BASE}/login`);
    console.log("header Demo Lab link:", await page.getByRole("link", { name: "Demo Lab" }).count());
    await page.getByRole("button", { name: /demo account/i }).click();
    await page.getByText("Cloud deployment, Pune").first().waitFor();
    const href = await page.locator("main ul li a", { hasText: "StackNest" }).first().getAttribute("href");
    const id = href.split("/")[2];
    await page.goto(`${BASE}/app/${id}/dashboard`);
    await page.getByText("Simulate a competitor move").waitFor();
    await page.getByRole("button", { name: "Reset competitor pages" }).click();
    await page.getByText(/back to their original/).waitFor();
    for (const [move, label] of [["Redesign only", "redesign"], ["Cut Pro price 40%", "price cut"]]) {
      await page.getByRole("button", { name: move }).first().click();
      await page.getByText(/applied\. Now press/).waitFor();
      await page.getByRole("button", { name: "Check competitors now" }).click();
      await page.locator("[data-screen=S-10]").waitFor({ timeout: 180000 });
      await page.getByText(/meaningful/).first().waitFor();
      console.log(`${label}:`, (await page.locator("[data-screen=S-10]").innerText()).replace(/\s+/g, " ").slice(0, 160));
      await page.goto(`${BASE}/app/${id}/dashboard`);
      await page.getByText("Simulate a competitor move").waitFor();
    }
    await page.getByRole("button", { name: /Find news|Refresh/ }).click();
    await page.getByRole("button", { name: /^(Find news|Refresh)$/ }).waitFor();
    await page.waitForTimeout(1500);
    console.log("news:", (await page.locator("li", { has: page.locator("a[target=_blank]") }).allInnerTexts()).slice(0, 4).map((t) => t.split("\n")[0].slice(0, 90)));
    console.log("categories:", (await page.getByText("Your categories now").count()) ? "shown" : "none (StackNest has no products yet)");
    await page.screenshot({ path: `${OUT}/b14h-market.png`, fullPage: true });
  } catch (e) {
    console.log("FAIL", e.message.split("\n").slice(0, 3).join(" / "));
    await page.screenshot({ path: `${OUT}/b14h-fail.png`, fullPage: true });
  }
  await browser.close();
})();
