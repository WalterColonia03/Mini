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

const out = process.env.AUDIT06B_OUT;
const run = process.env.AUDIT06B_RUN_DIR;
const base = "http://127.0.0.1:" + process.env.AUDIT06B_PORT;
const creds = JSON.parse(fs.readFileSync(path.join(run, ".credentials.json"), "utf8"));
const fixture = JSON.parse(fs.readFileSync(path.join(out, "browser-fixture.json"), "utf8"));

const report = {
  checks: [],
  page_errors: [],
  screenshots: [],
  a11y_metrics: {},
  layout_metrics: {},
};

function check(id, cond, extra = undefined) {
  assert.ok(cond, id + (extra !== undefined ? `: ${JSON.stringify(extra)}` : ""));
  report.checks.push(id);
}

async function tabUntilFocused(page, predicateFn, maxTabs = 80) {
  for (let i = 0; i < maxTabs; i++) {
    await page.keyboard.press("Tab");
    const matched = await page.evaluate(predicateFn);
    if (matched) return true;
  }
  return false;
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  try {
    // 1. Desktop 1366x900 Keyboard-Only & Accessibility Audit as ALMACENERO
    const ctx = await browser.newContext({ locale: "es-PE", viewport: { width: 1366, height: 900 } });
    const page = await ctx.newPage();
    page.on("pageerror", (e) => report.page_errors.push(e.message));

    await page.goto(base);
    await page.locator("[name=email]").fill(creds.wh.email);
    await page.locator("[name=password]").fill(creds.wh.password);
    await page.locator('button[type="submit"]').click();
    await page.waitForURL(/\/inicio\//);

    // Check skip link & keyboard nav from /inicio/ to /inventario/entrada/
    const skipFirstFocus = await tabUntilFocused(
      page,
      () => document.activeElement && document.activeElement.classList.contains("skip-link"),
      5
    );
    check("KBD-01-SKIP-LINK-REACHABLE", skipFirstFocus);

    const reachedEntryNav = await tabUntilFocused(
      page,
      () =>
        document.activeElement &&
        document.activeElement.tagName === "A" &&
        document.activeElement.getAttribute("href") === "/inventario/entrada/",
      60
    );
    check("KBD-02-NAV-TO-STOCK-ENTRY-BY-TAB", reachedEntryNav);
    await page.keyboard.press("Enter");
    await page.waitForURL(/\/inventario\/entrada\//);

    // Inspect DOM Accessibility on /inventario/entrada/
    const entryA11y = await page.evaluate(() => {
      const visibleControls = Array.from(document.querySelectorAll("select, input:not([type=hidden]), textarea, button[type=submit]"));
      const unlabeled = visibleControls
        .filter((el) => el.tagName !== "BUTTON")
        .filter((el) => !el.id || !document.querySelector(`label[for="${el.id}"]`))
        .map((el) => el.name || el.id || el.tagName);
      const headings = Array.from(document.querySelectorAll("h1, h2, h3")).map((h) => ({
        tag: h.tagName,
        text: h.textContent.trim(),
      }));
      const selectOptCount = document.querySelector("#id_product")?.options.length || 0;
      const hasSkipLink = Boolean(document.querySelector("a.skip-link"));
      const mainEl = document.querySelector("main#contenido-principal");
      return {
        lang: document.documentElement.lang,
        hasSkipLink,
        hasMainTarget: Boolean(mainEl),
        unlabeledCount: unlabeled.length,
        unlabeled,
        headings,
        selectOptCount,
      };
    });
    report.a11y_metrics.stock_entry = entryA11y;
    check("A11Y-01-LANG-ES-MAIN-SKIP", entryA11y.lang && entryA11y.hasSkipLink && entryA11y.hasMainTarget, entryA11y);
    check("A11Y-02-ALL-CONTROLS-LABELED", entryA11y.unlabeledCount === 0, entryA11y.unlabeled);

    // Keyboard-only error submit (empty Lote 1) and inspect focus after re-render
    const reachedSubmit = await tabUntilFocused(
      page,
      () => document.activeElement && document.activeElement.tagName === "BUTTON" && document.activeElement.textContent.includes("Confirmar entrada"),
      60
    );
    check("KBD-03-TAB-TO-SUBMIT", reachedSubmit);
    await page.keyboard.press("Enter");
    await page.waitForLoadState("networkidle");

    const errorFocusInfo = await page.evaluate(() => ({
      activeTag: document.activeElement ? document.activeElement.tagName : null,
      activeId: document.activeElement ? document.activeElement.id : null,
      hasTopErrorSummary: Boolean(document.querySelector("#stock-entry-errors")),
      alertCount: document.querySelectorAll('[role="alert"]').length,
    }));
    report.a11y_metrics.after_error_submit = errorFocusInfo;
    check("A11Y-03-ERRORS-ALERT-ROLE-PRESENT", errorFocusInfo.alertCount >= 1, errorFocusInfo);

    // Fill form purely using keyboard focus transitions + typing
    await page.locator("#id_product").focus();
    await page.locator("#id_product").selectOption(fixture.product_id);
    await page.keyboard.press("Tab");
    await page.locator("#id_supplier").selectOption(fixture.supplier_homonym_id);
    await page.keyboard.press("Tab");
    await page.keyboard.type("KBD-LOTE-01");
    await page.keyboard.press("Tab");
    await page.keyboard.type("5");
    await page.keyboard.press("Tab");
    await page.keyboard.type("6.5000");
    await page.keyboard.press("Tab");
    await page.locator("#id_lots-0-expiration_date").fill(fixture.future_date);
    const submitAgain = await tabUntilFocused(
      page,
      () => document.activeElement && document.activeElement.tagName === "BUTTON" && document.activeElement.textContent.includes("Confirmar entrada"),
      40
    );
    check("KBD-04-TAB-AFTER-FILL-TO-SUBMIT", submitAgain);
    await page.keyboard.press("Enter");
    await page.waitForURL(/\/inventario\/recepciones\//);

    const receiptText = await page.locator("main").innerText();
    check("KBD-05-CREATED-RECEIPT-R1", receiptText.includes("R-00000001") && receiptText.includes("KBD-LOTE-01") && receiptText.includes(fixture.supplier_homonym_ruc));

    // Navigate from StockReceipt to Kardex via keyboard ("Ver movimientos")
    const reachedMov = await tabUntilFocused(
      page,
      () => document.activeElement && document.activeElement.tagName === "A" && document.activeElement.textContent.includes("Ver movimientos"),
      20
    );
    check("KBD-06-TAB-TO-MOVEMENTS", reachedMov);
    await page.keyboard.press("Enter");
    await page.waitForURL(/\/movimientos\//);

    const kardexDom = await page.evaluate((ruc) => {
      const text = document.body.innerText;
      const backBtn = document.querySelector('a[href="/inventario/stock/"]');
      const recLink = document.querySelector('a[href*="/inventario/recepciones/"]');
      return {
        hasCorrelative: text.includes("R-00000001"),
        hasLot: text.includes("KBD-LOTE-01"),
        hasSupplierName: text.includes("Distribuidora Central SAC"),
        showsSupplierRuc: text.includes(ruc),
        hasVerRecepcionLink: Boolean(recLink),
        backBtnClasses: backBtn ? Array.from(backBtn.classList) : [],
      };
    }, fixture.supplier_homonym_ruc);
    report.a11y_metrics.kardex_cross = kardexDom;
    check("KARDEX-01-TRACE-TO-RECEIPT", kardexDom.hasCorrelative && kardexDom.hasLot && kardexDom.hasVerRecepcionLink, kardexDom);

    const kShot = path.join(out, "01-kardex-desde-recepcion.png");
    await page.screenshot({ path: kShot, fullPage: true });
    report.screenshots.push("01-kardex-desde-recepcion.png");

    // 2. Mobile 390x844 Layout Audit on /inventario/entrada/ and /movimientos/
    const mCtx = await browser.newContext({ locale: "es-PE", viewport: { width: 390, height: 844 } });
    const mPage = await mCtx.newPage();
    mPage.on("pageerror", (e) => report.page_errors.push(e.message));
    await mPage.goto(base);
    await mPage.locator("[name=email]").fill(creds.wh.email);
    await mPage.locator("[name=password]").fill(creds.wh.password);
    await mPage.locator('button[type="submit"]').click();
    await mPage.waitForURL(/\/inicio\//);

    await mPage.goto(base + `/inventario/productos/${fixture.product_id}/movimientos/`);
    const mKardexMetrics = await mPage.evaluate(() => ({
      docOverflow: document.documentElement.scrollWidth - window.innerWidth,
      tableWrapOverflow: (document.querySelector(".table-wrap")?.scrollWidth || 0) - (document.querySelector(".table-wrap")?.clientWidth || 0),
    }));
    report.layout_metrics.mobile_kardex = mKardexMetrics;
    const mShot = path.join(out, "02-kardex-movil-390x844.png");
    await mPage.screenshot({ path: mShot, fullPage: true });
    report.screenshots.push("02-kardex-movil-390x844.png");

    await mCtx.close();
    await ctx.close();
    check("CERO-PAGE-ERRORS", report.page_errors.length === 0, report.page_errors);
    fs.writeFileSync(path.join(out, "browser-deep.json"), JSON.stringify(report, null, 2), "utf8");
  } finally {
    await browser.close();
  }
})();
