// Workstream 2 on the live app: the overview as a founder sees it on desktop and phone, on a first and a return visit.
// node overview.cjs <playwright-core> <out-dir> <chrome-exe> [email] [password]
const { chromium } = require(process.argv[2]);
const [, , , OUT, CHROME, EMAIL = "stride@rivallens.demo", PASSWORD = "RivalLens-demo-2026"] = process.argv;
const BASE = process.env.BASE ?? "https://rivallens-eight.vercel.app";
const flat = (s, n = 900) => s.replace(/\s+/g, " ").slice(0, n);
(async () => {
  const browser = await chromium.launch({ executablePath: CHROME });
  for (const [tag, viewport] of [["desktop", { width: 1280, height: 900 }], ["phone", { width: 390, height: 844 }]]) {
    const page = await (await browser.newContext({ viewport })).newPage();
    page.setDefaultTimeout(90000);
    await page.goto(`${BASE}/login`);
    await page.getByLabel("Email").fill(EMAIL);
    await page.getByLabel("Password").fill(PASSWORD);
    await page.getByRole("button", { name: "Log in" }).click();
    await page.waitForURL(/\/app/);
    await page.waitForTimeout(2500);
    const home = await page.locator("a[href*='/home']").first().getAttribute("href");
    await page.goto(BASE + home);
    await page.getByTestId("next-action").waitFor();
    const tiles = await page.locator("[data-status]").evaluateAll((els) => els.map((e) => e.dataset.status));
    console.log(`${tag} FIRST VISIT: since shown=${await page.getByTestId("since").count()} tiles=${tiles.join(",")}`);
    await page.reload();
    await page.getByTestId("since").waitFor();
    const wide = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
    console.log(`${tag} RETURN VISIT: ${flat(await page.getByTestId("since").innerText(), 200)} | horizontal scroll: ${wide}`);
    console.log(`${tag} TOP:`, flat(await page.locator("main").innerText(), 600));
    await page.screenshot({ path: `${OUT}/ws2-overview-${tag}.png`, fullPage: true });
  }
  await browser.close();
})();
