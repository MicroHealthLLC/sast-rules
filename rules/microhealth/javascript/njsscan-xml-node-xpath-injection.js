// License: MIT (c) MicroHealth, LLC. Test cases for the rule beside this file.
const xpath = require('xpath');

app.get('/xp', function (req, res) {
  // ruleid: javascript.njsscan.xml.node-xpath-injection
  const expr = xpath.parse(req.query.q);
  res.send(String(expr));
});

function compile(q, opts) {
  // ok: javascript.njsscan.xml.node-xpath-injection
  return xpath.parse(q);
}
