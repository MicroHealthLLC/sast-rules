// License: MIT (c) MicroHealth, LLC. Test cases for the rule beside this file.
const wkhtmltoimage = require('wkhtmltoimage');

app.post('/img', function (req, res) {
  // ruleid: javascript.njsscan.ssrf.wkhtmltoimage-ssrf
  wkhtmltoimage.generate(req.body.url, {}).pipe(res);
});

pages.forEach((page, out) => {
  // ok: javascript.njsscan.ssrf.wkhtmltoimage-ssrf
  wkhtmltoimage.generate(page.url, {}).pipe(out);
});
