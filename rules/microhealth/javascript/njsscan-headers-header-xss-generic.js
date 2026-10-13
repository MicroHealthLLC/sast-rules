// License: MIT (c) MicroHealth, LLC. Test cases for the rule beside this file.
app.get('/x', function (req, res) {
  // ruleid: javascript.njsscan.headers.header-xss-generic
  res.set('X-XSS-Protection', 0);
  res.send('ok');
});

function headersFor(page, out) {
  // ok: javascript.njsscan.headers.header-xss-generic
  out.set('X-XSS-Protection', 0);
}
