// Workstream 4 on the live app: change an assumption, see the decision and its risks change, and the saved scenarios explain why.
// Runs on the Stride demo and resets what it changes. node simulator.cjs <playwright-core> <out-dir> <chrome-exe>
const { chromium } = require(process.argv[2]);
const [, , , OUT, CHROME] = process.argv;
const BASE = process.env.BASE ?? "https://rivallens-eight.vercel.app";
const flat = (s, n = 500) => s.replace(/\s+/g, " ").slice(0, n);
(async () => {
  const browser = await chromium.launch({ executablePath: CHROME });
  const page = await (await browser.newContext({ viewport: { width: 1280, height: 900 } })).newPage();
  page.setDefaultTimeout(90000);
  try {
    await page.goto(`${BASE}/login`);
    await page.getByRole("button", { name: /^Stride & Co\./ }).click();
    await page.locator("[data-screen=S-21]").waitFor();
    await page.goto(page.url().replace(/home$/, "product"));
    await page.getByRole("link", { name: "Compare" }).first().click();
    const sim = page.getByTestId("product-sim");
    await sim.locator("table").waitFor();
    const rec = async () => flat(await sim.locator("tr.bg-white").innerText(), 160);
    console.log("BEFORE:", await rec());
    console.log("REASON:", flat(await sim.locator("p.text-\\[13px\\]").first().innerText(), 200));
    console.log("SENSITIVITY:", flat(await page.getByTestId("sensitivity").innerText(), 700));
    await sim.getByRole("button", { name: "Save this scenario" }).click();
    await page.waitForTimeout(4000);

    await page.getByTestId("assumptions").locator("summary").click();
    const row = page.getByTestId("assumptions").locator("li", { hasText: "Price sensitivity" }).first();
    await row.getByRole("spinbutton").fill("1.6");
    await row.getByRole("button", { name: "Set" }).click();
    await page.waitForFunction(() => document.querySelector("[data-testid=assumptions]")?.textContent?.includes("Yours"), null, { timeout: 60000 });
    console.log("AFTER price sensitivity 1.6:", await rec());
    console.log("FLAGS:", flat(await sim.locator("[role=note]").allInnerTexts().then((t) => t.join(" | ")), 300) || "none");
    await sim.getByRole("button", { name: "Save this scenario" }).click();
    await page.waitForTimeout(4000);
    console.log("LATEST SCENARIO:", flat(await page.getByTestId("scenarios").locator("li").first().innerText(), 400));
    await page.screenshot({ path: `${OUT}/ws4-simulator.png`, fullPage: true });

    await row.getByRole("button", { name: "Reset" }).click();
    await page.waitForTimeout(5000);
    console.log("RESET:", await rec());
  } catch (e) {
    console.log("FAILED", e.message.split("\n")[0]);
    await page.screenshot({ path: `${OUT}/ws4-simulator-failed.png`, fullPage: true });
  }
  await browser.close();
})();
