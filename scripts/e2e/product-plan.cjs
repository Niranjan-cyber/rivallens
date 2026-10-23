const { chromium } = require(process.argv[2]);
const OUT = process.argv[3], BASE = "https://rivallens-eight.vercel.app";
const { SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY } = process.env;
(async () => {
  const email = `b14b-test-${Date.now()}@example.com`, password = "Test-pass-1234";
  const admin = { apikey: SUPABASE_SERVICE_ROLE_KEY, Authorization: `Bearer ${SUPABASE_SERVICE_ROLE_KEY}`, "Content-Type": "application/json" };
  const u = await (await fetch(`${SUPABASE_URL}/auth/v1/admin/users`, { method: "POST", headers: admin, body: JSON.stringify({ email, password, email_confirm: true }) })).json();
  console.log("test user", u.id ? "created" : JSON.stringify(u));
  const browser = await chromium.launch({ executablePath: process.argv[4] });
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  page.setDefaultTimeout(90000);
  try {
    await page.goto(`${BASE}/login`);
    console.log("google button:", await page.getByRole("button", { name: /Continue with Google/ }).count());
    await page.getByLabel("Email").fill(email);
    await page.getByLabel("Password").fill(password);
    await page.locator("form").getByRole("button", { name: "Log in" }).click();
    await page.locator("[data-screen=S-20]").waitFor();
    console.log("1. new account lands on onboarding:", page.url());
    await page.screenshot({ path: `${OUT}/b14b-onboarding.png`, fullPage: true });
    await page.getByLabel("Business name").fill("Stride & Co.");
    await page.getByLabel("What kind of business is it?").selectOption("D2C brand");
    await page.getByLabel("City").fill("Pune");
    await page.getByLabel("What you do, in one line").fill("Running shoes for Indian roads, sold online");
    await page.getByLabel("Your main products (comma-separated)").fill("Stride Runner, Stride Trail, running socks");
    await page.getByRole("button", { name: "Next" }).click();
    await page.getByLabel("Funding stage (optional)").selectOption("Bootstrapped");
    await page.getByLabel(/Who are your customers/).fill("Recreational runners aged 22-40 in Indian metros");
    await page.getByRole("button", { name: "Draft my business card" }).click();
    await page.locator("[data-screen=S-05]").waitFor();
    console.log("2. card check, name =", await page.getByLabel(/^Name/).inputValue());
    for (let i = 0; i < 2; i++) await page.getByRole("button", { name: "Next" }).click();
    await page.getByRole("button", { name: "Finish" }).click();
    await page.locator("[data-screen=S-21]").waitFor();
    await page.getByText(/Stride Runner/).first().waitFor();
    console.log("3. overview:", (await page.locator("[data-screen=S-21]").innerText()).replace(/\s+/g, " ").slice(0, 400));
    await page.getByRole("link", { name: "Product" }).first().click();
    await page.locator("li", { hasText: "Stride Runner" }).getByText("Google product taxonomy").waitFor({ timeout: 120000 });
    const productUrl = BASE + await page.getByRole("link", { name: "Stride Runner" }).first().getAttribute("href");
    await page.getByRole("link", { name: "Finance" }).first().click();
    await page.locator("[data-screen=S-24]").waitFor();
    const FIX = "C:/Career/Hackathons/Pulzion HackNova/fixtures/demo/stride/";
    for (const f of ["orders-oct2025-sep2026.xlsx", "bank-statement-oct2025-sep2026.csv"]) {
      await page.getByLabel("File").setInputFiles(FIX + f);
      await page.getByRole("button", { name: /^Import \d+ rows/ }).click();
      await page.getByText(/^Imported \d+/).waitFor();
    }
    const setCash = async (c) => {
      await page.goto(productUrl.replace(/product-detail.*/, "finance"));
      await page.getByLabel("Cash in the bank today (₹)").fill(String(c));
      await page.getByRole("button", { name: "Save" }).first().click();
      await page.waitForTimeout(2500);
      console.log(`   money (cash ${c}):`, (await page.locator("[data-screen=S-24] .grid").first().innerText()).replace(/\s+/g, " "));
    };
    const plan = async (tag) => {
      await page.goto(productUrl);
      await page.getByText("Price position").waitFor();
      if (await page.getByLabel("Your price in rupees").count()) {  // product has no price yet
        await page.getByLabel("Your price in rupees").fill("1999");
        await page.getByRole("button", { name: "Save" }).click();
        await page.getByText(/is .* the median|at the median/).first().waitFor();
      }
      await page.locator("[data-testid=product-sim] table").waitFor();
      await page.locator("[data-testid=segment] [aria-busy]").waitFor({ state: "detached", timeout: 120000 });
      console.log(`${tag} inputs:`, (await page.locator("[data-testid=product-sim] ul[aria-label=Inputs] a").allInnerTexts()).join(" | "));
      console.log("   flags:", (await page.locator("[data-flag]").allInnerTexts()).join(" | ") || "none");
      console.log("   options:", (await page.locator("[data-testid=product-sim] tbody").innerText()).replace(/\s+/g, " "));
      console.log("   segment:", (await page.locator("[data-testid=segment]").innerText()).replace(/\s+/g, " ").slice(0, 600));
      await page.screenshot({ path: `${OUT}/b14i-${tag}.png`, fullPage: true });
    };
    await setCash(2716169);
    await plan("1-start");
    await setCash(20000);
    await plan("2-low-cash");
    await page.goto(productUrl.replace(/product-detail.*/, "customers"));
    await page.getByLabel("File").setInputFiles(process.env.NEG_CSV);
    await page.getByRole("button", { name: /^Import \d+ rows/ }).click();
    await page.getByText(/^Imported \d+ mentions\.$/).waitFor({ timeout: 240000 });
    await page.getByText(/\d+ negative/).first().waitFor({ timeout: 120000 });
    await plan("3-negative-reviews");
    const chip = page.locator("[data-testid=product-sim] a[data-source=customers]").first();
    console.log("   sentiment chip href:", await chip.getAttribute("href"));
  } catch (e) {
    console.log("FAIL", e.message.split("\n")[0]);
    await page.screenshot({ path: `${OUT}/b14i-fail.png`, fullPage: true });
  }
  await browser.close();
  await fetch(`${SUPABASE_URL}/auth/v1/admin/users/${u.id}`, { method: "DELETE", headers: admin });
  console.log("test user deleted");
})();
