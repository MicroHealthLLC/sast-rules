// License: MIT (c) MicroHealth, LLC. Test cases for the rule beside this file.
const phantom = require('phantom');

app.get('/shot', async function (req, res) {
  const page = await instance.createPage();
  // ruleid: javascript.njsscan.ssrf.phantom-ssrf
  await page.open(req.query.url.trim());
  res.send('ok');
});

async function preview(cfg, page) {
  // ok: javascript.njsscan.ssrf.phantom-ssrf
  await page.open(cfg.query.url.trim());
}
