const fs = require("node:fs");
const path = require("node:path");
const os = require("node:os");
const assert = require("node:assert/strict");
const { chromium } = require(
  path.join(
    os.homedir(),
    ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright-core"
  )
);

const out = process.env.AUDIT05_OUT;
const run = process.env.AUDIT05_RUN_DIR;
const base = "http://127.0.0.1:" + process.env.AUDIT05_PORT;
const accounts = JSON.parse(fs.readFileSync(path.join(run, ".credentials.json"), "utf8"));
const fixture = JSON.parse(fs.readFileSync(path.join(out, "fixture.json"), "utf8"));

const report = {
  checks: [],
  observations: {},
  page_errors: [],
  screenshots: [],
  input: "Stage 05-N Chrome CT-COHERENCIA-UI, ADMIN surface, DEF-05M-01 visual proof, min_num=1 error focus, empty catalog, @media print",
};

function check(id, actual, expected) {
  assert.deepEqual(actual, expected, id);
  report.checks.push(id);
}

async function loginContext(browser, role, viewport = { width: 1366, height: 900 }) {
  const ctx = await browser.newContext({ locale: "es-PE", viewport });
  const page = await ctx.newPage();
  page.on("pageerror", (err) => report.page_errors.push({ role, message: err.message }));
  await page.goto(base);
  await page.locator("[name=email]").fill(accounts[role].email);
  await page.locator("[name=password]").fill(accounts[role].password);
  await page.locator('button[type="submit"]').click();
  await page.waitForURL(base + "/inicio/");
  return { ctx, page };
}

async function shot(page, filename) {
  await page.screenshot({ path: path.join(out, filename), fullPage: true });
  report.screenshots.push(filename);
}

async function runAudit(browser) {
  const whSession = await loginContext(browser, "warehouse");
  const wh = whSession.page;

  // 1. Real Chrome min_num=1 behavior: fill Card 1 (lots-1) only, leave Card 0 (lots-0) blank -> #initial-load-errors receives focus
  await wh.goto(base + "/inventario/carga-inicial/");
  await wh.locator("[name=product]").selectOption(fixture.products.elig1.id);
  await wh.locator('[name="lots-1-number"]').fill("L-CARD1-ONLY");
  await wh.locator('[name="lots-1-quantity"]').fill("5");
  await wh.locator('[name="lots-1-unit_cost"]').fill("2.50");
  await wh.locator('[name="lots-1-expiration_date"]').fill(fixture.future_45);
  await wh.getByRole("button", { name: "Confirmar existencias", exact: true }).click();
  await wh.waitForLoadState("domcontentloaded");

  const activeId = await wh.evaluate(() => document.activeElement?.id || "");
  const errSummaryText = await wh.locator("#initial-load-errors").innerText();
  const card1Errors = await wh.locator("#initial-load-errors li").allInnerTexts();
  check("card0_blank_focus_on_summary", activeId, "initial-load-errors");
  check("card0_blank_rejects_with_lots0_required", errSummaryText.includes("Lote 1"), true);
  report.observations.card0_blank_summary = card1Errors;
  await shot(wh, "05n-errors-focus.png");

  // 2. Load elig1 & elig2 properly so catalog has 0 eligible products -> inspect empty-state dropdown
  for (const [prodId, num] of [
    [fixture.products.elig1.id, "L-05N-E1"],
    [fixture.products.elig2.id, "L-05N-E2"],
  ]) {
    await wh.goto(base + "/inventario/carga-inicial/");
    await wh.locator("[name=product]").selectOption(prodId);
    await wh.locator('[name="lots-0-number"]').fill(num);
    await wh.locator('[name="lots-0-quantity"]').fill("10");
    await wh.locator('[name="lots-0-unit_cost"]').fill("3.2000");
    await wh.locator('[name="lots-0-expiration_date"]').fill(fixture.future_90);
    await wh.locator('[name="lots-1-number"]').fill("");
    await wh.locator('[name="lots-1-quantity"]').fill("");
    await wh.locator('[name="lots-1-unit_cost"]').fill("");
    await wh.locator('[name="lots-1-expiration_date"]').fill("");
    await wh.getByRole("button", { name: "Confirmar existencias", exact: true }).click();
    await wh.waitForURL(/\/inventario\/cargas\/.+\//);
  }
  const elig1LoadUrl = base + new URL(wh.url()).pathname.replace(/\/inventario\/cargas\/.+/, "");
  // Retrieve elig1 load URL by navigating back one product from stock_overview:
  await wh.goto(base + "/inventario/carga-inicial/");
  const emptyOpts = await wh.locator("[name=product] option").allInnerTexts();
  check("empty_catalog_only_placeholder_option", emptyOpts, ["Seleccione un producto"]);
  check("empty_form_sin_overflow", await wh.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), true);
  await shot(wh, "05n-empty-form.png");

  // 3. ADMIN creates positive PhysicalAdjustment new lot on elig1 via UI -> proves DEF-05M-01 visually on constancia!
  const adminSession = await loginContext(browser, "admin");
  const admin = adminSession.page;

  await admin.goto(base + "/inventario/stock/");
  const elig1LoadHref = await admin
    .locator("tbody tr", { hasText: fixture.products.elig1.name })
    .getByRole("link", { name: "Ver carga", exact: true })
    .getAttribute("href");
  const stockAdminLinks = await admin.locator(".form-actions a").allInnerTexts();
  check("admin_stock_has_adjustment_and_writeoff", stockAdminLinks.map((s) => s.trim()), ["Ajuste físico", "Registrar merma"]);
  check("admin_stock_desktop_sin_overflow", await admin.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), true);
  await shot(admin, "05n-admin-stock.png");

  // ADMIN @media print on stock_overview
  await admin.emulateMedia({ media: "print" });
  const printStockCheck = await admin.evaluate(() => {
    const hideSelectors = [".app-sidebar", ".app-topbar", ".app-footer", ".skip-link"];
    const allHidden = hideSelectors.every((s) => {
      const el = document.querySelector(s);
      return !el || getComputedStyle(el).display === "none";
    });
    return { allHidden, overflowOk: document.documentElement.scrollWidth <= window.innerWidth };
  });
  check("print_stock_overview_hides_chrome", printStockCheck, { allHidden: true, overflowOk: true });
  await shot(admin, "05n-print-stock.png");
  await admin.emulateMedia({ media: "screen" });

  // Create new lot via PhysicalAdjustment UI
  await admin.goto(base + "/inventario/ajustes/nuevo/");
  await admin.locator('select[name="producto"]').selectOption(fixture.products.elig1.id);
  await admin.getByRole("button", { name: "Registrar lote nuevo por ajuste", exact: true }).click();
  await admin.waitForURL(/\/inventario\/ajustes\/nuevo\/\?producto=/);
  await admin.locator('[name="delta"]').fill("5");
  await admin.locator('[name="number"]').fill("ADJ-NEW-05N");
  await admin.locator('[name="expiration_date"]').fill(fixture.future_90);
  await admin.locator('[name="reason"]').fill("Conteo físico positivo audit 05N");
  await admin.getByRole("button", { name: "Confirmar ajuste", exact: true }).click();
  await admin.waitForURL(/\/inventario\/ajustes\/.+\//);

  // ADMIN opens elig1 initial load constancia -> inspect DEF-05M-01 visual misclassification + print + role buttons
  await admin.goto(base + elig1LoadHref);
  const createdText = await admin.locator('[data-testid="inventory-load-created"]').innerText();
  const createdBtns = await admin.locator(".form-actions a").allInnerTexts();
  check("admin_created_only_ver_inventario_e_inicio", createdBtns.map((s) => s.trim()), ["Ver inventario", "Ir al inicio"]);
  check("def05m01_visible_legacy_heading", createdText.includes("Lotes vinculados sin fotografía original"), true);
  check("def05m01_visible_adj_lot_as_legacy", createdText.includes("ADJ-NEW-05N") && createdText.includes("Cantidad original no disponible"), true);
  await shot(admin, "05n-admin-created-def05m01.png");

  // ADMIN @media print on initial_load_created
  await admin.emulateMedia({ media: "print" });
  const printCreatedCheck = await admin.evaluate(() => {
    const hideSelectors = [".app-sidebar", ".app-topbar", ".app-footer", ".skip-link"];
    const allHidden = hideSelectors.every((s) => {
      const el = document.querySelector(s);
      return !el || getComputedStyle(el).display === "none";
    });
    const noPrintHidden = Array.from(document.querySelectorAll(".no-print")).every((el) => getComputedStyle(el).display === "none");
    return { allHidden, noPrintHidden, overflowOk: document.documentElement.scrollWidth <= window.innerWidth };
  });
  check("print_created_hides_chrome_and_noprint", printCreatedCheck, { allHidden: true, noPrintHidden: true, overflowOk: true });
  await shot(admin, "05n-print-created.png");
  await admin.emulateMedia({ media: "screen" });

  // 4. Kardex shows "Ajuste" for ADJ-NEW-05N & handles filter errors cleanly
  await admin.goto(base + `/inventario/productos/${fixture.products.elig1.id}/movimientos/`);
  const movText = await admin.locator("table.movements-table").innerText();
  check("kardex_identifies_ajuste_origen", movText.includes("ADJ-NEW-05N") && movText.includes("Ajuste"), true);
  await admin.goto(base + `/inventario/productos/${fixture.products.elig1.id}/movimientos/?desde=2026-11-01T00:00`);
  check("kardex_missing_hasta_error_visible", (await admin.locator(".panel-danger, .alert-danger").innerText()).includes("Complete Desde y Hasta"), true);

  // 5. Narrow viewport 390x844 check for ADMIN pages
  await admin.setViewportSize({ width: 390, height: 844 });
  await admin.goto(base + elig1LoadHref);
  check("admin_created_mobile_390_no_overflow", await admin.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), true);
  await admin.goto(base + "/inventario/stock/");
  check("admin_stock_mobile_390_no_overflow", await admin.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), true);

  check("cero_page_errors", report.page_errors.length, 0);
  await whSession.ctx.close();
  await adminSession.ctx.close();
}

(async () => {
  const browser = await chromium.launch({
    executablePath: "C:/Program Files/Google/Chrome/Application/chrome.exe",
    headless: true,
  });
  try {
    report.chrome = browser.version();
    await runAudit(browser);
  } catch (error) {
    report.error = error.message;
    process.exitCode = 1;
  } finally {
    fs.writeFileSync(path.join(out, "browser.json"), JSON.stringify(report, null, 2), "utf8");
    await browser.close();
  }
})();
