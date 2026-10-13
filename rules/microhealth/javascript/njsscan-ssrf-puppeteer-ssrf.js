// License: MIT (c) MicroHealth, LLC. Test cases for the rule beside this file.
const puppeteer = require('puppeteer');

app.get('/shot', async function (req, res) {
  const page = await browser.newPage();
  // ruleid: javascript.njsscan.ssrf.puppeteer-ssrf
  await page.goto(req.query.url.trim());
  res.send('ok');
});

async function capture(scene, page) {
  // ok: javascript.njsscan.ssrf.puppeteer-ssrf
  await page.goto(scene.query.url.trim());
}
