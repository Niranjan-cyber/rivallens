// Improve slice 1: Excel CSVs preview, readable price input, Collect says what it found, simulator assumptions explain
// themselves and report what moved, and a check says plainly when nothing changed. Uses the Stride & Co. demo; nothing is
// imported or collected (those responses are faked), and the one assumption it sets is reset at the end.
// BASE=http://localhost:3000 node slice1-fixes.cjs <playwright-core> <out-dir> <chrome-exe>
const { chromium } = require(process.argv[2]);
const OUT = process.argv[3], BASE = process.env.BASE ?? "https://rivallens-eight.vercel.app";
let failures = 0;
const check = (ok, what) => { console.log(`${ok ? "PASS" : "FAIL"} ${what}`); if (!ok) failures++; };
const flat = (s, n = 300) => s.replace(/\s+/g, " ").slice(0, n);
(async () => {
  const browser = await chromium.launch({ executablePath: process.argv[4] });
  const page = await (await browser.newContext({ viewport: { width: 1280, height: 900 } })).newPage();
  page.setDefaultTimeout(60000);
  await page.goto(`${BASE}/login`);
  await page.getByRole("button", { name: /^Stride & Co\./ }).click();
  await page.locator("[data-screen=S-21]").waitFor();
  const pid = new URL(page.url()).pathname.split("/")[2];

  // 1. Finance: a Windows/Excel CSV (CRLF, quoted commas in the last column) previews instead of "couldn't read"
  await page.goto(`${BASE}/app/${pid}/finance`);
  const csv = ["date,type,amount,product,description", '2026-04-28,sale,58869,Stride Runner,"Online orders, 31 pairs"', "2026-04-29,expense,12000,,Rent",
    '2026-04-30,sale,9900,Running socks,"Marketplace, 33 pairs"', "2026-05-01,expense,5000,,Packaging (boxes)"].join("\r\n") + "\r\n";
  await page.locator("input[type=file]").first().setInputFiles({ name: "ledger.csv", mimeType: "text/csv", buffer: Buffer.from(csv) });
  const preview = page.getByText("First rows as we read them");
  check(await preview.waitFor({ timeout: 60000 }).then(() => true, () => false), "Finance: CRLF CSV with quoted commas previews");
  check(await page.locator("table").filter({ hasText: "Online orders, 31 pairs" }).count() > 0, "Finance: preview is a table with the full description");
  await page.screenshot({ path: `${OUT}/slice1-finance-preview.png`, fullPage: true });

  // 2. Getting started: a price typed in the dark next-step panel is dark on white (it was cream on white)
  await page.route("**/api/v1/profiles/*/setup*", async (route) => {
    const res = await route.fetch();
    const plan = await res.json();
    plan.next_action = { label: "Enter the price of Stride Runner", href: null, kind: "price", product_id: "00000000-0000-0000-0000-000000000000", product: "Stride Runner", unit: "one_time", key: "prices" };
    await route.fulfill({ response: res, json: plan });
  });
  await page.goto(`${BASE}/app/${pid}/setup`);
  const price = page.locator("[data-testid=next-action] input[type=number]");
  await price.fill("1999");
  const color = await price.evaluate((el) => getComputedStyle(el).color);
  check(color === "rgb(20, 20, 19)", `Setup: typed price is ink, not cream (${color})`);
  await page.screenshot({ path: `${OUT}/slice1-setup-price.png` });
  await page.unrouteAll({ behavior: "ignoreErrors" });

  // 3. Customers: Collect says what it read and why it found nothing (job faked, so demo mentions stay as they are)
  await page.route("**/api/v1/profiles/*/customers/collect", (r) => r.fulfill({ status: 202, json: { job_id: "fake-collect", status: "queued" } }));
  await page.route("**/api/v1/jobs/fake-collect", (r) => r.fulfill({ json: { id: "fake-collect", kind: "customers_collect", status: "done", steps: [], error: null,
    result: { own_site: 0, web: 0, pages: 0, pages_read: 0, searched: "Stride & Co.", web_results: 7, mentions: 0, themes: 0 } } }));
  await page.goto(`${BASE}/app/${pid}/customers`);
  await page.getByRole("button", { name: "Collect mentions" }).click();
  const note = page.locator("[data-testid=collect-note]");
  check(await note.waitFor({ timeout: 30000 }).then(() => true, () => false), "Customers: Collect reports its result");
  const noteText = (await note.innerText().catch(() => "")) || "";
  check(/No product page links saved/.test(noteText) && /7 results/.test(noteText), `Customers: says why 0 (${flat(noteText, 160)})`);
  check(await page.getByRole("button", { name: "Collect mentions" }).isEnabled(), "Customers: button usable again");
  await page.unrouteAll({ behavior: "ignoreErrors" });

  // 4. Product simulator: every assumption explains itself; conversion is marked as having no effect when calibrated; a change says what moved
  await page.goto(`${BASE}/app/${pid}/product`);
  await page.locator("[data-screen=S-22] a[href*='product-detail']").first().click();
  await page.locator("[data-testid=assumptions]").waitFor({ timeout: 90000 });
  await page.locator("[data-testid=assumptions] summary").click();
  const conv = page.getByRole("spinbutton", { name: "Conversion at market price" });
  check(await conv.isDisabled(), "Simulator: conversion disabled for a product calibrated to its sales");
  check(await page.getByText("No effect here: your sales already fix").count() > 0, "Simulator: says why conversion has no effect");
  check(await page.getByText("How strongly sales react to price").count() > 0, "Simulator: price sensitivity explained");
  const sens = page.getByRole("spinbutton", { name: "Price sensitivity" });
  await sens.fill("2.5");
  await sens.locator("xpath=following-sibling::button").click();
  const moved = page.locator("[data-testid=sim-changed]");
  check(await moved.waitFor({ timeout: 60000 }).then(() => true, () => false), "Simulator: a change says what moved");
  console.log("   ", flat(await moved.innerText().catch(() => ""), 200));
  await page.screenshot({ path: `${OUT}/slice1-simulator.png`, fullPage: true });
  await page.waitForTimeout(5000); // a late load used to put the old numbers back here
  const sensRow = page.locator("[data-testid=assumptions] li").filter({ hasText: "How strongly sales react" });
  check(await sens.inputValue() === "2.5" && (await sensRow.innerText()).includes("Yours"), "Simulator: the edit stays (no stale reload)");
  const reset = sensRow.getByRole("button", { name: "Reset" });
  const hasReset = await reset.waitFor({ timeout: 15000 }).then(() => true, () => false);
  check(hasReset, "Simulator: your own value offers Reset");
  if (!hasReset) await page.screenshot({ path: `${OUT}/slice1-no-reset.png`, fullPage: true });
  await reset.click({ timeout: 5000 }).catch(() => {}); // put the shared demo back
  await page.waitForTimeout(3000);
  check((await sensRow.innerText()).includes("Default") && await sens.inputValue() === "1.2", "Simulator: Reset puts the demo back to Default 1.2");

  // 5. Market: Stride's only check is its baseline (no 0/0 cards); StackNest's latest check leads with a plain verdict
  await page.goto(`${BASE}/app/${pid}/run`);
  await page.getByText("First check on").waitFor();
  check(await page.getByText("meaningful change").count() === 0, "Run: baseline shows no 0/0 count cards");
  await page.goto(`${BASE}/login`);
  await page.getByRole("button", { name: /^StackNest/ }).click();
  await page.locator("[data-screen=S-21]").waitFor();
  await page.goto(`${BASE}/app/${new URL(page.url()).pathname.split("/")[2]}/run`);
  const verdict = page.locator("[data-testid=run-verdict]");
  check(await verdict.waitFor({ timeout: 60000 }).then(() => true, () => false), "Run: verdict shown");
  console.log("   ", flat(await verdict.innerText().catch(() => ""), 240));
  await page.screenshot({ path: `${OUT}/slice1-run.png`, fullPage: true });

  await browser.close();
  console.log(failures ? `${failures} FAILED` : "ALL PASS");
  process.exit(failures ? 1 : 0);
})();
