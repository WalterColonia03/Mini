'use strict';

const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');

const { chromium } = require(
  path.join(os.homedir(), '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright-core')
);

const runDir = process.env.AUDIT03_REVAL_B_RUN_DIR;
const outDir = process.env.AUDIT03_REVAL_B_OUT_DIR;
const baseUrl = 'http://127.0.0.1:' + process.env.AUDIT03_REVAL_B_PORT;
const creds = JSON.parse(fs.readFileSync(path.join(runDir, '.credentials.json'), 'utf8'));
const ids = JSON.parse(fs.readFileSync(path.join(runDir, '.browser-ids.json'), 'utf8'));

const report = {
  chrome_version: null,
  desktop_ui_inventory: {},
  nav_active_audit: [],
  mobile_overflow_metrics: [],
  console_errors: [],
  page_errors: [],
  screenshots: [],
};

async function login(browser, alias, viewport) {
  const ctx = await browser.newContext({ viewport, locale: 'es-PE' });
  const page = await ctx.newPage();
  page.on('pageerror', e => report.page_errors.push(String(e)));
  page.on('console', m => { if (m.type() === 'error') report.console_errors.push(m.text()); });
  await page.goto(baseUrl + '/');
  await page.locator('[name=email]').fill(creds[alias].email);
  await page.locator('[name=password]').fill(creds[alias].password);
  await Promise.all([
    page.waitForURL(u => u.pathname === '/inicio/'),
    page.locator('button[type=submit]').click(),
  ]);
  await page.waitForSelector('h1');
  return { ctx, page };
}

(async () => {
  const browser = await chromium.launch({
    executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
    headless: true,
  });
  report.chrome_version = browser.version();

  try {
    // 0. HMAC proof check
    const probeCtx = await browser.newContext();
    const probePage = await probeCtx.newPage();
    const nonce = crypto.randomBytes(32).toString('hex');
    const r = await probePage.request.get(baseUrl + '/', { headers: { 'X-Audit03-Challenge': nonce } });
    const expected = crypto.createHmac('sha256', fs.readFileSync(path.join(runDir, '.django-key'))).update(nonce).digest('hex');
    assert.equal(r.headers()['x-audit03-proof'], expected);
    await probeCtx.close();

    // 1. Desktop 1366x900: inspect active nav highlighting, topbar h1, headings, buttons, helpers across ALL catalog GET routes
    const { ctx: adminCtx, page: adminPage } = await login(browser, 'admin', { width: 1366, height: 900 });
    const routes = [
      ['category-list', '/productos/categorias/'],
      ['category-create', '/productos/categorias/nueva/'],
      ['category-state-confirm', `/productos/categorias/${ids.cat_id}/estado/confirmar/`],
      ['product-list', '/productos/'],
      ['product-entry', '/productos/nuevo/'],
      ['product-created', `/productos/${ids.prod_id}/registrado/`],
      ['product-created-alias', `/productos/registrado/${ids.prod_id}/`],
      ['product-edit', `/productos/${ids.prod_id}/editar/`],
    ];

    for (const [name, route] of routes) {
      await adminPage.goto(baseUrl + route);
      await adminPage.waitForSelector('main');
      const info = await adminPage.evaluate(() => {
        const activeLinks = [...document.querySelectorAll('.sidebar-nav .nav-item.is-active')].map(el => ({
          text: el.innerText.trim(),
          href: el.getAttribute('href'),
        }));
        const h1 = document.querySelector('header.app-topbar h1')?.innerText.trim() || null;
        const mainH2 = [...document.querySelectorAll('main h2, main h3')].map(el => ({
          tag: el.tagName,
          text: el.innerText.trim(),
        }));
        const buttons = [...document.querySelectorAll('main button, main a.btn, main a.button')].map(el => ({
          tag: el.tagName,
          text: el.innerText.trim(),
          classes: el.className,
        }));
        const aside = document.querySelector('aside.info-panel')?.innerText.trim() || null;
        return { activeLinks, h1, mainH2, buttons, hasAside: Boolean(aside) };
      });
      report.nav_active_audit.push({ routeName: name, path: route, ...info });
    }

    // Also inspect ALMACENERO sidebar & /productos/ UI inventory
    const { ctx: whCtx, page: whPage } = await login(browser, 'warehouse', { width: 1366, height: 900 });
    await whPage.goto(baseUrl + '/productos/');
    report.desktop_ui_inventory.warehouse_prod_list = await whPage.evaluate(() => ({
      activeLinks: [...document.querySelectorAll('.sidebar-nav .nav-item.is-active')].map(el => el.innerText.trim()),
      h1: document.querySelector('header.app-topbar h1')?.innerText.trim(),
      headers: [...document.querySelectorAll('table th')].map(th => th.innerText.trim()),
      hasActionCol: [...document.querySelectorAll('table th')].some(th => th.innerText.trim() === 'Acciones'),
      badges: [...document.querySelectorAll('.badge')].map(b => b.innerText.trim()),
    }));
    await whCtx.close();
    await adminCtx.close();

    // 2. Mobile 390x844: inspect document overflow + internal container overflow + clipped nav items
    const { ctx: mobCtx, page: mobPage } = await login(browser, 'admin', { width: 390, height: 844 });
    for (const [name, route] of routes) {
      await mobPage.goto(baseUrl + route);
      await mobPage.waitForSelector('main');
      const m = await mobPage.evaluate(() => {
        const nav = document.querySelector('.sidebar-nav');
        const navRect = nav ? nav.getBoundingClientRect() : null;
        const clippedNavItems = nav
          ? [...nav.querySelectorAll('.nav-item')].filter(el => el.getBoundingClientRect().right > navRect.right + 1).map(el => el.innerText.trim())
          : [];
        const tableWrap = document.querySelector('.table-responsive');
        const activeNav = nav?.querySelector('.nav-item.is-active')?.innerText.trim() || null;
        return {
          docScrollWidth: document.documentElement.scrollWidth,
          innerWidth: window.innerWidth,
          docOverflow: document.documentElement.scrollWidth > window.innerWidth,
          navScrollWidth: nav ? nav.scrollWidth : null,
          navClientWidth: nav ? nav.clientWidth : null,
          navInternalOverflow: nav ? nav.scrollWidth > nav.clientWidth : false,
          clippedNavItems,
          activeNavVisible: activeNav,
          tableScrollWidth: tableWrap ? tableWrap.scrollWidth : null,
          tableClientWidth: tableWrap ? tableWrap.clientWidth : null,
          tableInternalOverflow: tableWrap ? tableWrap.scrollWidth > tableWrap.clientWidth : false,
        };
      });
      report.mobile_overflow_metrics.push({ routeName: name, path: route, ...m });
      if (name === 'product-list' || name === 'product-entry') {
        const shot = `b-mobile-${name}.png`;
        await mobPage.screenshot({ path: path.join(outDir, shot), fullPage: true });
        report.screenshots.push(shot);
      }
    }
    await mobCtx.close();

    fs.writeFileSync(path.join(outDir, 'browser-b-report.json'), JSON.stringify(report, null, 2), 'utf8');
    console.log(JSON.stringify({
      ok: true,
      nav_checked: report.nav_active_audit.length,
      mobile_checked: report.mobile_overflow_metrics.length,
      page_errors: report.page_errors.length,
      console_errors: report.console_errors.length,
    }));
  } finally {
    await browser.close();
  }
})();
