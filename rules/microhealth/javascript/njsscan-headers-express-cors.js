// License: MIT (c) MicroHealth, LLC. Test cases for the rule beside this file.
app.get('/cors', function (req, res) {
  // ruleid: javascript.njsscan.headers.express-cors
  res.set('Access-Control-Allow-Origin', '*');
  res.send('ok');
});

function headersFor(map, out) {
  // ok: javascript.njsscan.headers.express-cors
  out.set('Access-Control-Allow-Origin', '*');
}
