/**
 * Stage 01-F Chrome Playwright verification:
 * - Own isolated server HMAC proof
 * - 1366x768 live 254/257 keyboard truncation (without redaction) + Tab navigation + logout
 * - 390x844 mobile viewport layout, error visibility, zero horizontal overflow
 * - 01-F-ADMIN-PERIMETRO-01: locked staff & superuser bypassing public RN-17 lock via /admin/login/ into /inicio/ & /admin/identity/account/
 */
const fs = require("node:fs");
const path = require("node:path");
const os = require("node:os");
const crypto = require("node:crypto");
const assert = require("node:assert/strict");
const { chromium } = require(
  path.join(
    os.homedir(),
    ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright-core"
  )
);

const ROOT = path.resolve(__dirname, "../../..");
const DATA = path.join(ROOT, "auditoria_por_etapas/resultados/datos/01-F-20261114");
const OUT = path.join(ROOT, "auditoria_por_etapas/resultados/evidencias/01-F-20261114");
const NAV_DIR = path.join(OUT, "navegador");
fs.mkdirSync(NAV_DIR, { recursive: true });

const PORT = process.env.AUDIT01F_PORT || "8782";
const BASE = `http://127.0.0.1:${PORT}`;
const CREDS = JSON.parse(fs.readFileSync(path.join(DATA, ".credentials.json"), "utf8"));
const KEY = fs.readFileSync(path.join(DATA, ".django-key"), "utf8").trim();

const manifest = {
  base_url: BASE,
  executed_at_utc: new Date().toISOString(),
  checks: [],
  screenshots: [],
  page_errors: [],
  console_errors: [],
  failed_responses: [],
};

function recordCheck(id, ok, details = {}) {
  assert.equal(ok, true, `Failed check ${id}: ${JSON.stringify(details)}`);
  manifest.checks.push({ id, ok, ...details });
}

async function shot(page, filename) {
  const full = path.join(NAV_DIR, filename);
  await page.screenshot({ path: full, fullPage: true });
  manifest.screenshots.push(`navegador/${filename}`);
}

async function submitPublicLogin(page, email, password) {
  await page.locator('[name="email"]').fill(email);
  await page.locator('[name="password"]').fill(password);
  await Promise.all([
    page.waitForLoadState("networkidle"),
    page.locator('button[type="submit"]').click(),
  ]);
  const errorText = await page.locator('[data-testid="login-error"]').textContent().catch(() => "");
  return {
    url: page.url(),
    errorText: (errorText || "").trim(),
  };
}

async function attachDiagnostics(ctx, label) {
  ctx.on("page", (p) => {
    p.on("pageerror", (e) => manifest.page_errors.push({ label, message: e.message }));
    p.on("console", (msg) => {
      if (msg.type() === "error") {
        manifest.console_errors.push({ label, text: msg.text() });
      }
    });
    p.on("response", (res) => {
      if (res.status() >= 400) {
        manifest.failed_responses.push({
          label,
          status: res.status(),
          path: new URL(res.url()).pathname,
        });
      }
    });
  });
}

(async () => {
  const browser = await chromium.launch({
    executablePath: "C:/Program Files/Google/Chrome/Application/chrome.exe",
    headless: true,
  });
  manifest.chrome_version = browser.version();
  try {
    // 1. Desktop 1366x768: HMAC proof + live 254/257 typing + Tab order + login + logout
    const ctx1 = await browser.newContext({ locale: "es-PE", viewport: { width: 1366, height: 768 } });
    await attachDiagnostics(ctx1, "desktop-254");
    const page1 = await ctx1.newPage();

    const nonce = crypto.randomBytes(24).toString("hex");
    const proofResp = await page1.request.get(BASE + "/", { headers: { "X-Audit01f-Challenge": nonce } });
    const expectedProof = crypto.createHmac("sha256", KEY).update(nonce).digest("hex");
    recordCheck("C01_HMAC_SERVER_PROOF", proofResp.headers()["x-audit01f-proof"] === expectedProof, {
      status: proofResp.status(),
    });

    await page1.goto(BASE + "/", { waitUntil: "networkidle" });
    const cssRespDesktop = await page1.request.get(BASE + "/static/identity/app.css");
    const focusInfo = await page1.evaluate(() => ({
      activeName: document.activeElement?.getAttribute("name"),
      maxlength: document.querySelector('[name="email"]')?.getAttribute("maxlength"),
      autocompleteEmail: document.querySelector('[name="email"]')?.getAttribute("autocomplete"),
      autocompletePw: document.querySelector('[name="password"]')?.getAttribute("autocomplete"),
      overflow: document.documentElement.scrollWidth > window.innerWidth,
      csrfPresent: !!document.querySelector('input[name="csrfmiddlewaretoken"]')?.value,
      stylesheetsCount: document.styleSheets.length,
      cardBorderRadius: getComputedStyle(document.querySelector(".login-card")).borderRadius,
    }));
    recordCheck(
      "C01B_DESKTOP_STYLESHEET_LOADED",
      cssRespDesktop.status() === 200 &&
        (cssRespDesktop.headers()["content-type"] || "").includes("text/css") &&
        focusInfo.stylesheetsCount >= 1 &&
        parseFloat(focusInfo.cardBorderRadius || "0") > 0,
      {
        cssStatus: cssRespDesktop.status(),
        contentType: cssRespDesktop.headers()["content-type"],
        stylesheetsCount: focusInfo.stylesheetsCount,
        cardBorderRadius: focusInfo.cardBorderRadius,
      }
    );
    recordCheck(
      "C02_LOGIN_DOM_ATTRIBUTES",
      focusInfo.activeName === "email" &&
        focusInfo.maxlength === "254" &&
        focusInfo.autocompleteEmail === "username" &&
        focusInfo.autocompletePw === "current-password" &&
        !focusInfo.overflow &&
        focusInfo.csrfPresent,
      focusInfo
    );

    // Type 257 characters (254 valid + 3 extra) cleanly via keyboard events so HTML maxlength=254 clips to exact 254
    const email254 = CREDS.email254.email;
    await page1.locator('[name="email"]').pressSequentially(email254 + "xyz", { delay: 0 });
    const typedState = await page1.evaluate(() => {
      const el = document.querySelector('[name="email"]');
      return { length: el.value.length, endsWithInvalid: el.value.endsWith("@ejemplo.invalid") };
    });
    recordCheck(
      "C03_LIVE_254_TRUNCATION_WITHOUT_REDACTION",
      typedState.length === 254 && typedState.endsWithInvalid,
      typedState
    );

    await page1.keyboard.press("Tab");
    const pwFocused = await page1.evaluate(() => document.activeElement?.getAttribute("name") === "password");
    await page1.locator('[name="password"]').fill(CREDS.email254.password);
    await page1.keyboard.press("Tab");
    const btnFocused = await page1.evaluate(
      () => document.activeElement?.tagName === "BUTTON" && document.activeElement?.getAttribute("type") === "submit"
    );
    recordCheck("C04_KEYBOARD_TAB_ORDER", pwFocused && btnFocused, { pwFocused, btnFocused });

    await Promise.all([page1.waitForURL(BASE + "/inicio/"), page1.keyboard.press("Enter")]);
    const rolePill = (await page1.locator(".role-pill").textContent()).trim();
    recordCheck("C05_LOGIN_254_DASHBOARD", rolePill === "Almacenero", { url: page1.url(), rolePill });
    await shot(page1, "01-F-ui-254-inicio.png");

    await Promise.all([page1.waitForURL(BASE + "/salir/"), page1.locator("a.sidebar-logout").click()]);
    await Promise.all([page1.waitForURL(BASE + "/"), page1.locator('button[type="submit"]').click()]);
    recordCheck("C06_LOGOUT_RETURN_LOGIN", page1.url() === BASE + "/", { url: page1.url() });
    await ctx1.close();

    // 2. Mobile 390x844 responsive check + wrong pw error visibility + Seller login
    const ctx2 = await browser.newContext({ locale: "es-PE", viewport: { width: 390, height: 844 } });
    await attachDiagnostics(ctx2, "mobile-390");
    const page2 = await ctx2.newPage();
    await page2.goto(BASE + "/", { waitUntil: "networkidle" });
    const mobileGeom = await page2.evaluate(() => {
      const w = window.innerWidth;
      const docScroll = document.documentElement.scrollWidth;
      const cards = [...document.querySelectorAll(".login-role-grid article, .login-card, [name=email], [name=password], button[type=submit]")].map((el) => {
        const r = el.getBoundingClientRect();
        return { tag: el.tagName, cls: el.className, left: r.left, right: r.right, width: r.width, clipped: r.right > w + 1 || r.left < -1 };
      });
      return {
        innerWidth: w,
        scrollWidth: docScroll,
        anyClipped: cards.some((c) => c.clipped),
        cardCount: cards.length,
        stylesheetsCount: document.styleSheets.length,
        cardBorderRadius: getComputedStyle(document.querySelector(".login-card")).borderRadius,
      };
    });
    recordCheck(
      "C07_MOBILE_390_NO_OVERFLOW",
      mobileGeom.scrollWidth <= mobileGeom.innerWidth &&
        !mobileGeom.anyClipped &&
        mobileGeom.stylesheetsCount >= 1 &&
        parseFloat(mobileGeom.cardBorderRadius || "0") > 0,
      mobileGeom
    );
    await shot(page2, "01-F-mobile-390-login.png");

    const badMobile = await submitPublicLogin(page2, CREDS.seller.email, "ClaveIncorrecta01F!");
    const clearedPw = await page2.locator('[name="password"]').inputValue();
    const errBox = await page2.locator('[data-testid="login-error"]').boundingBox();
    const errOverflow = await page2.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
    recordCheck(
      "C08_MOBILE_390_UNIFORM_ERROR_VISIBLE",
      badMobile.errorText.includes("Correo o contraseña incorrectos") && clearedPw === "" && !!errBox && errBox.width > 0 && !errOverflow,
      { errorText: badMobile.errorText, clearedPwLen: clearedPw.length, errBox, errOverflow }
    );
    await shot(page2, "01-F-mobile-390-error.png");

    // Log in seller with valid password (resets failure count from 1 -> 0) and inspect dashboard at 390px
    await page2.locator('[name="email"]').fill(CREDS.seller.email);
    await page2.locator('[name="password"]').fill(CREDS.seller.password);
    await Promise.all([page2.waitForURL(BASE + "/inicio/"), page2.locator('button[type="submit"]').click()]);
    const dashMobileOverflow = await page2.evaluate(() => ({
      innerWidth: window.innerWidth,
      scrollWidth: document.documentElement.scrollWidth,
      heading: document.querySelector("h1")?.textContent?.trim(),
    }));
    recordCheck("C09_MOBILE_390_SELLER_INICIO", dashMobileOverflow.scrollWidth <= dashMobileOverflow.innerWidth, dashMobileOverflow);
    await shot(page2, "01-F-mobile-390-inicio.png");
    await ctx2.close();

    // 3. 01-F-ADMIN-PERIMETRO-01: locked staff account bypasses / RN-17 via /admin/login/ -> /inicio/ (and gets 403 on /admin/identity/account/)
    const ctxStaff = await browser.newContext({ locale: "es-PE", viewport: { width: 1366, height: 768 } });
    await attachDiagnostics(ctxStaff, "staff-bypass");
    const pageStaff = await ctxStaff.newPage();
    await pageStaff.goto(BASE + "/", { waitUntil: "networkidle" });
    let fifthMsg = "";
    for (let i = 1; i <= 5; i++) {
      const res = await submitPublicLogin(pageStaff, CREDS.staff_admin.email, "WrongStaff01F!");
      if (i < 5) {
        recordCheck(`C10_STAFF_FAIL_${i}`, res.errorText.includes("Correo o contraseña incorrectos"), { i });
      } else {
        fifthMsg = res.errorText;
      }
    }
    recordCheck("C10_STAFF_LOCKED_5TH", fifthMsg.includes("15 minuto(s)"), { fifthMsg });

    const validBlocked = await submitPublicLogin(pageStaff, CREDS.staff_admin.email, CREDS.staff_admin.password);
    recordCheck(
      "C11_STAFF_GOOD_PASSWORD_BLOCKED_ON_PUBLIC",
      validBlocked.url === BASE + "/" && validBlocked.errorText.includes("15 minuto(s)"),
      validBlocked
    );
    await shot(pageStaff, "01-F-staff-bloqueado-publico.png");

    await pageStaff.goto(BASE + "/admin/login/?next=/admin/", { waitUntil: "networkidle" });
    const adminCsrfOk = await pageStaff.evaluate(() => !!document.querySelector('input[name="csrfmiddlewaretoken"]')?.value);
    recordCheck("C12_STAFF_ADMIN_LOGIN_CSRF", adminCsrfOk, { url: pageStaff.url() });
    await pageStaff.locator('input[name="username"]').fill(CREDS.staff_admin.email);
    await pageStaff.locator('input[name="password"]').fill(CREDS.staff_admin.password);
    await Promise.all([pageStaff.waitForURL(BASE + "/admin/"), pageStaff.locator('input[type="submit"]').click()]);
    const adminBody = await pageStaff.locator("#content").textContent();
    await shot(pageStaff, "01-F-staff-admin-landing.png");

    const respStaffModel = await pageStaff.goto(BASE + "/admin/identity/account/", { waitUntil: "domcontentloaded" });
    recordCheck("C13_STAFF_NO_MODEL_PERMS_403", respStaffModel.status() === 403, {
      status: respStaffModel.status(),
      adminBodySnippet: (adminBody || "").trim().slice(0, 120),
    });

    const respStaffInicio = await pageStaff.goto(BASE + "/inicio/", { waitUntil: "networkidle" });
    const staffNavHasEmp = (await pageStaff.locator('a[href="/empleados/"]').count()) > 0;
    recordCheck(
      "C14_STAFF_SHARED_SESSION_REACHS_INICIO",
      respStaffInicio.status() === 200 && pageStaff.url() === BASE + "/inicio/" && staffNavHasEmp,
      { status: respStaffInicio.status(), url: pageStaff.url(), staffNavHasEmp }
    );
    await shot(pageStaff, "01-F-staff-inicio-compartido.png");
    await ctxStaff.close();

    // 4. 01-F-ADMIN-PERIMETRO-01: locked superuser (commercial VENDEDOR role) bypasses / RN-17 via /admin/login/ -> /admin/identity/account/ (200) & /inicio/ (200) while /empleados/ is 403
    const ctxSu = await browser.newContext({ locale: "es-PE", viewport: { width: 1366, height: 768 } });
    await attachDiagnostics(ctxSu, "superuser-bypass");
    const pageSu = await ctxSu.newPage();
    await pageSu.goto(BASE + "/", { waitUntil: "networkidle" });
    for (let i = 1; i <= 5; i++) {
      await submitPublicLogin(pageSu, CREDS.super_seller.email, "WrongSu01F!");
    }
    const suBlocked = await submitPublicLogin(pageSu, CREDS.super_seller.email, CREDS.super_seller.password);
    recordCheck("C15_SUPERUSER_BLOCKED_ON_PUBLIC", suBlocked.errorText.includes("15 minuto(s)"), suBlocked);

    await pageSu.goto(BASE + "/admin/login/?next=/admin/", { waitUntil: "networkidle" });
    await pageSu.locator('input[name="username"]').fill(CREDS.super_seller.email);
    await pageSu.locator('input[name="password"]').fill(CREDS.super_seller.password);
    await Promise.all([pageSu.waitForURL(BASE + "/admin/"), pageSu.locator('input[type="submit"]').click()]);
    recordCheck("C16_SUPERUSER_ADMIN_BYPASS", pageSu.url() === BASE + "/admin/", { url: pageSu.url() });
    await shot(pageSu, "01-F-superuser-admin-index.png");

    const respSuAcc = await pageSu.goto(BASE + "/admin/identity/account/", { waitUntil: "networkidle" });
    const rowCount = await pageSu.locator("#result_list tbody tr").count();
    recordCheck("C17_SUPERUSER_ACCOUNT_ADMIN_200", respSuAcc.status() === 200 && rowCount >= 5, {
      status: respSuAcc.status(),
      rowCount,
    });
    await shot(pageSu, "01-F-superuser-account-admin.png");

    const respSuEmp = await pageSu.goto(BASE + "/empleados/", { waitUntil: "domcontentloaded" });
    recordCheck("C18_SUPERUSER_COMMERCIAL_RBAC_ENFORCED_403", respSuEmp.status() === 403, {
      status: respSuEmp.status(),
    });

    const respSuInicio = await pageSu.goto(BASE + "/inicio/", { waitUntil: "networkidle" });
    const suRolePill = (await pageSu.locator(".role-pill").textContent()).trim();
    recordCheck(
      "C19_SUPERUSER_SHARED_SESSION_REACHS_INICIO",
      respSuInicio.status() === 200 && suRolePill === "Vendedor",
      { status: respSuInicio.status(), suRolePill }
    );
    await shot(pageSu, "01-F-superuser-inicio-compartido.png");
    await ctxSu.close();

    const unexpectedResponses = manifest.failed_responses.filter(
      (r) =>
        !(r.status === 403 && (r.path === "/admin/identity/account/" || r.path === "/empleados/")) &&
        !(r.status === 404 && r.path === "/favicon.ico")
    );
    const unexpectedConsoleErrors = manifest.console_errors.filter(
      (c) => !c.text.includes("403") && !(c.text.includes("404") && unexpectedResponses.length === 0)
    );
    recordCheck(
      "C20_ZERO_PAGE_AND_ASSET_ERRORS",
      manifest.page_errors.length === 0 && unexpectedResponses.length === 0 && unexpectedConsoleErrors.length === 0,
      {
        page_errors: manifest.page_errors,
        unexpected_failed_responses: unexpectedResponses,
        failed_responses_summary: manifest.failed_responses,
        unexpected_console_errors: unexpectedConsoleErrors,
      }
    );
  } finally {
    await browser.close();
    fs.writeFileSync(path.join(OUT, "chrome-manifest.json"), JSON.stringify(manifest, null, 2) + "\n", "utf8");
  }
  console.log(JSON.stringify({ total_checks: manifest.checks.length, screenshots: manifest.screenshots }, null, 2));
})();
