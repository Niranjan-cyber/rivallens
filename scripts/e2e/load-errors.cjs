// Failed reads show what failed with Try again, never a fake empty state; Try again recovers.
// BASE=http://localhost:3000 node load-errors.cjs <playwright-core> <out-dir> <chrome-exe>
const { chromium } = require(process.argv[2]);
const OUT = process.argv[3], BASE = process.env.BASE ?? "https://rivallens-eight.vercel.app";
let failures = 0;
const check = (ok, what) => { console.log(`${ok ? "PASS" : "FAIL"} ${what}`); if (!ok) failures++; };
(async () => {
  const browser = await chromium.launch({ executablePath: process.argv[4] });
  const page = await (await browser.newContext({ viewport: { width: 1280, height: 900 } })).newPage();
  page.setDefaultTimeout(60000);
  await page.goto(`${BASE}/login`);
  await page.getByRole("button", { name: /^Stride & Co\./ }).click();
  await page.locator("[data-screen=S-21]").waitFor();
  const profileId = new URL(page.url()).pathname.split("/")[2];
  await page.goto(`${BASE}/app/${profileId}/product`);
  const productHref = await page.locator("[data-screen=S-22] a[href*='product-detail']").first().getAttribute("href");

  // [screen path, API path that fails, text expected once it recovers]
  const cases = [
    ["setup", /\/setup(\?|$)/, "Getting started"],
    ["finance", /\/money$/, "Revenue per month"],
    ["customers", /\/customers$/, "Mentions"],
    ["dashboard", /\/alerts\?/, "Recent checks"],
    [productHref.replace(`/app/${profileId}/`, ""), /\/comparison$/, "Price position"],
    [productHref.replace(`/app/${profileId}/`, ""), /\/simulation$/, "Price simulator for this product"],
  ];
  for (const [path, api, recovered] of cases) {
    const fail = (route) => (api.test(new URL(route.request().url()).pathname + new URL(route.request().url()).search)
      ? route.fulfill({ status: 500, contentType: "application/json", body: JSON.stringify({ error: { code: "test", message: "Test failure." } }) })
      : route.continue());
    await page.route("**/api/v1/**", fail);
    await page.goto(`${BASE}/app/${profileId}/${path}`);
    const alert = page.locator("div[role=alert]", { hasText: "Couldn't load" });
    const shown = await alert.waitFor({ timeout: 30000 }).then(() => true, () => false);
    check(shown, `${path} (${api}): failure named with Try again`);
    if (path === "dashboard") check(!(await page.getByText("No checks yet").count()), "dashboard: no fake 'No checks yet'");
    await page.screenshot({ path: `${OUT}/load-error-${path.split("?")[0]}-${cases.indexOf(cases.find((c) => c[1] === api))}.png`, fullPage: true });
    await page.unroute("**/api/v1/**", fail);
    if (shown) {
      await alert.getByRole("button", { name: "Try again" }).click();
      const gone = await alert.waitFor({ state: "detached", timeout: 60000 }).then(() => true, () => false);
      const ok = gone && await page.locator("section[data-screen]").getByText(recovered).first().waitFor({ timeout: 60000 }).then(() => true, () => false);
      check(ok, `${path}: Try again recovers`);
      if (!ok) await page.screenshot({ path: `${OUT}/load-error-recover-fail-${cases.indexOf(cases.find((c) => c[1] === api))}.png`, fullPage: true });
    }
  }
  await browser.close();
  console.log(failures ? `${failures} FAILED` : "ALL PASS");
  process.exit(failures ? 1 : 0);
})();
