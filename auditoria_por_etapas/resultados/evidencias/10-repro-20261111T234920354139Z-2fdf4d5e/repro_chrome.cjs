
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { chromium } = require(path.join(os.homedir(), ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright-core"));
(async () => {
  const creds = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
  const base = process.argv[3];
  const shotDir = process.argv[4];
  const browser = await chromium.launch({ executablePath: "C:/Program Files/Google/Chrome/Application/chrome.exe", headless: true });
  const results = {};
  for (const [label, vp] of [["1366x900", { width: 1366, height: 900 }], ["1366x768", { width: 1366, height: 768 }]]) {
    const ctx = await browser.newContext({ locale: "es-PE", viewport: vp });
    const page = await ctx.newPage();
    await page.goto(base);
    await page.locator("[name=email]").fill(creds.seller.email);
    await page.locator("[name=password]").fill(creds.seller.password);
    await page.locator('button[type="submit"]').click();
    await page.waitForURL(base + "/inicio/");
    await page.goto(base + "/ventas/?query=At%C3%BAnEspecial");
    const m = await page.evaluate(() => {
      const docSW = document.documentElement.scrollWidth;
      const winW = window.innerWidth;
      const layout = document.querySelector(".sales-layout");
      const searchPanel = document.querySelector(".sales-search-panel");
      const draftPanel = document.querySelector(".sales-summary-panel");
      const wrap = document.querySelector(".table-wrap");
      const draftLines = Array.from(document.querySelectorAll(".draft-line"));
      return {
        docSW, winW,
        docOverflow: docSW > winW,
        layoutRight: layout ? Math.round(layout.getBoundingClientRect().right) : null,
        searchPanelW: searchPanel ? Math.round(searchPanel.getBoundingClientRect().width) : null,
        searchPanelSW: searchPanel ? searchPanel.scrollWidth : null,
        searchPanelCW: searchPanel ? searchPanel.clientWidth : null,
        draftPanelRight: draftPanel ? Math.round(draftPanel.getBoundingClientRect().right) : null,
        draftPanelSW: draftPanel ? draftPanel.scrollWidth : null,
        draftPanelCW: draftPanel ? draftPanel.clientWidth : null,
        wrapSW: wrap ? wrap.scrollWidth : null,
        wrapCW: wrap ? wrap.clientWidth : null,
        maxDraftLineSW: Math.max(0, ...draftLines.map(d => d.scrollWidth)),
        maxDraftLineCW: Math.max(0, ...draftLines.map(d => d.clientWidth)),
      };
    });
    results[label] = m;
    if (label === "1366x900") {
      await page.screenshot({ path: path.join(shotDir, "repro-1366x900.png"), fullPage: true });
    }
    await ctx.close();
  }
  await browser.close();
  console.log(JSON.stringify(results));
})();
