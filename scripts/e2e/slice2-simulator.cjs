// Improve slice 2: one simulator per product (/simulator lists them), a grid that visibly runs (values decode into place,
// then the best price is highlighted), "Run simulation again", and "What if I charge ₹X?". Read-only on the Stride demo.
// BASE=http://localhost:3000 node slice2-simulator.cjs <playwright-core> <out-dir> <chrome-exe>
const { chromium } = require(process.argv[2]);
const OUT = process.argv[3], BASE = process.env.BASE ?? "https://rivallens-eight.vercel.app";
let failures = 0;
const check = (ok, what) => { console.log(`${ok ? "PASS" : "FAIL"} ${what}`); if (!ok) failures++; };
(async () => {
  const browser = await chromium.launch({ executablePath: process.argv[4] });
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await ctx.newPage();
  page.setDefaultTimeout(60000);
  await page.goto(`${BASE}/login`);
  await page.getByRole("button", { name: /^Stride & Co\./ }).click();
  await page.locator("[data-screen=S-21]").waitFor();
  const pid = new URL(page.url()).pathname.split("/")[2];

  // 1. /simulator is a list of products, each with its recommended price, opening that product's simulator
  await page.goto(`${BASE}/app/${pid}/simulator`);
  const cards = page.locator("[data-testid=sim-products] li");
  await cards.first().waitFor();
  await page.getByText("recommended").first().waitFor({ timeout: 90000 });
  check(await cards.count() >= 2, `Simulator page lists products (${await cards.count()})`);
  check(!(await page.locator("[data-screen=S-14]").innerText()).includes("/month"), "Simulator page: no /month assumed for shoes");
  await page.screenshot({ path: `${OUT}/slice2-simulator-list.png`, fullPage: true });
  await cards.first().getByRole("link").click();
  await page.locator("[data-screen=S-23]").waitFor();
  check(page.url().includes("product-detail?id="), "Simulator page opens the product's simulator");

  // 2. The grid visibly runs: status says what is being tested, cells scramble, then settle on the real values
  const status = page.locator("[data-testid=sim-status]");
  const grid = page.locator("[data-testid=sim-grid]");
  await grid.waitFor({ timeout: 90000 });
  const run = page.locator("[data-testid=sim-run]");
  await page.waitForFunction(() => !document.querySelector("[data-testid=sim-run]")?.hasAttribute("disabled"));
  const settled = await grid.locator("tbody").innerText();
  await run.click();
  const during = await status.innerText();
  await page.waitForTimeout(250);
  const mid = await grid.locator("tbody").innerText();
  check(/Testing \d+ prices × 3 levels of price sensitivity/.test(during), `Run: status while running ("${during}")`);
  check(mid !== settled, "Run: values scramble while running");
  await page.screenshot({ path: `${OUT}/slice2-running.png` });
  await page.waitForFunction(() => !document.querySelector("[data-testid=sim-run]")?.hasAttribute("disabled"), null, { timeout: 15000 });
  check(await grid.locator("tbody").innerText() === settled, "Run: settles on exactly the computed values");
  check(/scenarios run\. Best: ₹/.test(await status.innerText()), `Run: says how many scenarios and the best price (${await status.innerText()})`);
  check(await grid.locator("tr.bg-white", { hasText: "Recommended" }).count() === 1, "Run: recommended row highlighted after it finishes");
  check(await grid.locator("thead").getByText(/less price-sensitive \(0\.8\)/).count() === 1 && await grid.locator("thead").getByText(/More price-sensitive \(1\.8\)/).count() === 1,
    "Grid columns name the price sensitivity they assume (not worst/best, which swap below the market price)");

  // 3. What if I charge ₹X? adds one computed row; removing it takes it away
  await page.getByLabel("What if I charge").fill("2299");
  await page.getByRole("button", { name: "Test this price" }).click();
  const testRow = grid.locator("tr", { hasText: "₹2,299" });
  check(await testRow.waitFor({ timeout: 60000 }).then(() => true, () => false), "Test price: ₹2,299 row appears");
  await page.waitForFunction(() => !document.querySelector("[data-testid=sim-run]")?.hasAttribute("disabled"), null, { timeout: 15000 });
  check((await testRow.innerText()).includes("your test price") || (await testRow.innerText()).includes("Recommended"), `Test price: labelled (${(await testRow.innerText()).replace(/\s+/g, " ").slice(0, 90)})`);
  await page.screenshot({ path: `${OUT}/slice2-test-price.png`, fullPage: true });
  await page.getByRole("button", { name: /Remove ₹2,299/ }).click();
  check(await testRow.waitFor({ state: "detached", timeout: 60000 }).then(() => true, () => false), "Test price: removed");

  // 4. Reduced motion: no scrambling, values shown at once
  const calm = await browser.newContext({ viewport: { width: 1280, height: 900 }, reducedMotion: "reduce", storageState: await ctx.storageState() });
  const p2 = await calm.newPage();
  await p2.goto(page.url());
  await p2.locator("[data-testid=sim-grid]").waitFor({ timeout: 90000 });
  const first = await p2.locator("[data-testid=sim-grid] tbody").innerText();
  await p2.waitForTimeout(1500);
  check(first === await p2.locator("[data-testid=sim-grid] tbody").innerText() && !/₹0\b/.test(first), "Reduced motion: final values immediately");

  // 5. Market: the simulator card no longer shows a business-wide "/month" price
  await page.goto(`${BASE}/app/${pid}/dashboard`);
  const card = page.getByRole("link", { name: /Price simulator/ });
  check(await card.waitFor().then(() => true, () => false) && !(await card.innerText()).includes("/month"), "Market: simulator card points to the per-product simulators");

  await browser.close();
  console.log(failures ? `${failures} FAILED` : "ALL PASS");
  process.exit(failures ? 1 : 0);
})();
