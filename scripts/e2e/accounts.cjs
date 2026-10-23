const { chromium } = require(process.argv[2]);
const BASE = "https://rivallens-eight.vercel.app";
const { SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY } = process.env;
(async () => {
  const email = `b14a-live-${Date.now()}@example.com`, password = "Test-pass-1234";
  const browser = await chromium.launch({ executablePath: process.argv[4] });
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  page.setDefaultTimeout(90000);
  try {
    await page.goto(`${BASE}/login`);
    console.log("google button present:", await page.getByText("Continue with Google").count());
    await page.getByRole("tab", { name: "Create account" }).click();
    await page.getByLabel("Email").fill(email);
    await page.getByLabel("Password").fill(password);
    await page.locator("form").getByRole("button", { name: "Create account" }).click();
    await page.locator("[data-screen=S-20]").waitFor();
    console.log("1. created and signed in at once:", page.url());
    if (!(await page.getByRole("button", { name: "Log out" }).isVisible())) await page.locator("summary", { hasText: "All businesses" }).click();
    await page.getByRole("button", { name: "Log out" }).click();
    await page.waitForURL(/\/login/);
    await page.getByLabel("Email").fill(email);
    await page.getByLabel("Password").fill("wrong-password");
    await page.locator("form").getByRole("button", { name: "Log in" }).click();
    console.log("2. wrong password:", await page.locator("p[role=alert]").innerText());
    await page.getByLabel("Password").fill(password);
    await page.locator("form").getByRole("button", { name: "Log in" }).click();
    await page.locator("[data-screen=S-20]").waitFor();
    console.log("3. logged back in:", page.url());
    if (!(await page.getByRole("button", { name: "Log out" }).isVisible())) await page.locator("summary", { hasText: "All businesses" }).click();
    await page.getByRole("button", { name: "Log out" }).click();
    await page.waitForURL(/\/login/);
    await page.getByRole("tab", { name: "Create account" }).click();
    await page.getByLabel("Email").fill(email);
    await page.getByLabel("Password").fill(password);
    await page.locator("form").getByRole("button", { name: "Create account" }).click();
    console.log("4. same email again:", await page.locator("p[role=alert]").innerText());
  } catch (e) {
    console.log("FAIL", e.message.split("\n").slice(0, 4).join(" / "));
    await page.screenshot({ path: process.argv[3] + "/b14a-fail.png" });
  }
  await browser.close();
  const h = { apikey: SUPABASE_SERVICE_ROLE_KEY, Authorization: `Bearer ${SUPABASE_SERVICE_ROLE_KEY}` };
  const users = (await (await fetch(`${SUPABASE_URL}/auth/v1/admin/users?per_page=1000`, { headers: h })).json()).users;
  for (const u of users.filter((u) => u.email === email)) await fetch(`${SUPABASE_URL}/auth/v1/admin/users/${u.id}`, { method: "DELETE", headers: h });
  console.log("test user deleted");
})();
