// Milestone "first useful insight", on the live app: a brand-new founder (not a demo account) signs up, describes a real-market
// business, follows Getting started (prices, competitors, like-for-like products, first check) and reads findings and a next step;
// then refresh, log out and log in, and the state is still there. node first-insight.cjs <playwright-core> <out-dir> <chrome-exe>
const { chromium } = require(process.argv[2]);
const OUT = process.argv[3], BASE = process.env.BASE ?? "https://rivallens-eight.vercel.app";
const flat = (s, n = 900) => s.replace(/\s+/g, " ").slice(0, n);
const email = `founder-${Date.now()}@rivallens.test`, password = "Founder-test-2026";
// A different business: BIZ="name|kind|city|what you do|products, comma-separated|customers|price1,price2" (defaults: a coffee roaster)
const [NAME, KIND, CITY, WHAT, PRODUCTS, WHO, PRICES] = (process.env.BIZ ?? "Hillcrest Roasters|D2C brand|Bengaluru|Specialty coffee beans and South Indian filter coffee powder, roasted in Bengaluru and sold online|Filter coffee powder, Cold brew coffee bags|Home coffee drinkers aged 25-45 in Indian metros|450,650").split("|");
(async () => {
  const browser = await chromium.launch({ executablePath: process.argv[4] });
  const page = await (await browser.newContext({ viewport: { width: 1280, height: 900 } })).newPage();
  page.setDefaultTimeout(90000);
  const shot = (n) => page.screenshot({ path: `${OUT}/${n}.png`, fullPage: true });
  const steps = async () => (await page.locator("[data-step]").evaluateAll((els) => els.map((e) => `${e.dataset.step}:${e.dataset.status}`))).join(" ");
  const next = page.getByTestId("next-action");
  // Click the next step's button, then wait until the plan moves on (job finished and the plan reloaded).
  async function doNext(fill) {
    const label = flat(await next.locator("p").nth(1).innerText(), 120);
    if (fill) await next.locator("input").fill(fill);
    await next.getByRole("button").first().click();
    await page.waitForFunction((l) => {
      const n = document.querySelector("[data-testid=next-action]");
      return n && !n.innerText.includes("Working") && !n.innerText.includes("Saving") && !n.innerText.includes(l);
    }, label, { timeout: 360000 }).catch(() => console.log("  (next step unchanged after", label, ")"));
    console.log(`DID "${label}" →`, await steps());
  }
  try {
    await page.goto(`${BASE}/login`);
    await page.getByRole("tab", { name: "Create account" }).click();
    await page.getByLabel("Name").fill("Asha");
    await page.getByLabel("Email").fill(email);
    await page.getByLabel("Password").fill(password);
    await page.getByRole("button", { name: "Create account" }).click();
    await page.locator("[data-screen=S-20]").waitFor();
    console.log("1 SIGNED UP", email);
    await page.getByLabel("Business name").fill(NAME);
    await page.getByLabel("What kind of business is it?").selectOption(KIND);
    await page.getByLabel("City").fill(CITY);
    await page.getByLabel("What you do, in one line").fill(WHAT);
    await page.getByLabel(/Your main products/).fill(PRODUCTS);
    await page.getByRole("button", { name: "Next" }).click();
    await page.getByLabel(/Who are your customers/).fill(WHO);
    await page.getByRole("button", { name: "Draft my business card" }).click();
    await page.locator("[data-screen=S-05]").waitFor();
    await page.getByRole("button", { name: "Next" }).click();
    await page.getByRole("button", { name: "Finish" }).click();
    await page.locator("[data-screen=S-27]").waitFor();
    const setupUrl = page.url();
    await page.waitForFunction(() => document.querySelectorAll("[data-step]").length >= 7);
    await page.waitForTimeout(8000); // products are classified on a background thread
    await page.reload();
    await next.waitFor();
    console.log("2 SETUP", setupUrl, "\n ", await steps(), "\n  NEXT:", flat(await next.innerText(), 300));
    await shot("first-insight-setup-start");

    let priced = 0;
    for (let i = 0; i < 8; i++) {
      const kind = flat(await next.innerText(), 200);
      if (/Add the price/.test(kind)) await doNext(PRICES.split(",")[priced++ % 2]);
      else if (/Find competitors|Find products like|Start watching/.test(kind)) await doNext();
      else break;
    }
    await page.reload();
    await next.waitFor();
    const before = await steps();
    console.log("3 AFTER SETUP\n ", before, "\n  NEXT:", flat(await next.innerText(), 300));
    console.log("  STEPS TEXT:", flat(await page.locator("ol").last().innerText(), 1500));
    console.log("  FOUND:", flat(await page.locator("main").innerText().then((t) => t.split("What we found")[1] ?? ""), 1200));
    await shot("first-insight-setup-done");

    await page.goto(setupUrl.replace(/setup$/, "home"));
    await next.waitFor();
    console.log("4 OVERVIEW:", flat(await page.locator("main").innerText(), 900));
    await shot("first-insight-overview");

    await page.locator("summary", { hasText: "▾" }).click();
    await page.getByRole("button", { name: "Log out" }).click();
    await page.waitForURL(/\/login/);
    await page.getByLabel("Email").fill(email);
    await page.getByLabel("Password").fill(password);
    await page.getByRole("button", { name: "Log in" }).click();
    await page.waitForURL(/\/app/);
    await page.goto(setupUrl);
    await next.waitFor();
    const after = await steps();
    console.log("5 AFTER LOGOUT+LOGIN", after === before ? "SAME" : `CHANGED: ${after}`);
  } catch (e) {
    console.log("FAILED", e.message.split("\n")[0]);
    await shot("first-insight-failed");
  }
  await browser.close();
})();
