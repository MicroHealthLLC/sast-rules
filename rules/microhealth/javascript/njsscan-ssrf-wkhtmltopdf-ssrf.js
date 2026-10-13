// License: MIT (c) MicroHealth, LLC. Test cases for the rule beside this file.
const wkhtmltopdf = require('wkhtmltopdf');

app.get('/pdf', function (req, res) {
  // ruleid: javascript.njsscan.ssrf.wkhtmltopdf-ssrf
  wkhtmltopdf(req.query.url, {}).pipe(res);
});

function render(page, out) {
  // ok: javascript.njsscan.ssrf.wkhtmltopdf-ssrf
  wkhtmltopdf(page.url, {}).pipe(out);
}
